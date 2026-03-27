from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from lesson0203.cache import get_order_from_cache, invalidate_order_cache, set_order_cache
from .repositories import create_order_with_idempotency_record, get_accounts_for_update, get_idempotency_record_by_key, get_transfer_id   
from .models import Order
import logging
logger = logging.getLogger(__name__)


def transfer_transaction(
    from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    currency: str,
    session: Session,
    forced_failure: bool = False,
):
    if amount <= 0:
        logger.info('transfer.failed', extra={
            'reason': 'wrong amount', 
            'amount': amount, 
            'from_account_id': from_account_id, 
            'to_account_id': to_account_id})
        raise HTTPException(status_code=422, detail='wrong amount')

    try:
        if from_account_id == to_account_id:
            raise HTTPException(status_code=422, detail='Id match')

        account1, account2 = get_accounts_for_update(from_account_id=from_account_id, to_account_id=to_account_id, session=session)

        if not account1:
            raise HTTPException(status_code=404, detail='User 1 not find')
        
        if not account2:
            raise HTTPException(status_code=404, detail='User 2 not find')

        if account1.currency != currency or account2.currency != currency:
            raise HTTPException(status_code=409, detail='Not correct currency')
        if account1.balance < amount:
            raise HTTPException(status_code=409, detail='Not enough money')

        account1.balance -= amount
        if forced_failure:
            raise HTTPException(status_code=500, detail='test')

        account2.balance += amount
        transfer_id = get_transfer_id(from_account_id=from_account_id, to_account_id=to_account_id, amount=amount, currency=currency, session=session)
        session.commit()
        logger.info('transfer.completed', extra={
            'from_account_id': from_account_id,
            'to_account_id': to_account_id, 
            'amount': amount, 
            'currency': currency, 
            'transfer_id': transfer_id})
        return {'transfer_id': transfer_id}
    
    except HTTPException as e:
        reason = e.detail if isinstance(e.detail, str) else 'HTTP error'
        logger.info('transfer.failed', 
            extra={
            'reason': reason,
            'from_account_id': from_account_id,
            'to_account_id': to_account_id,
            'amount': amount,
            'currency': currency
        })
        

        session.rollback()
        raise

    except Exception:
        logger.exception('transfer.failed', extra={
            'from_account_id': from_account_id,
            'to_account_id': to_account_id,
            'amount': amount,
            'currency': currency
        })
        session.rollback()
        raise

def create_order(user_id: int, amount: Decimal, currency: str, idempotency_key: str, session: Session):
    try:
        try:
            order_id = create_order_with_idempotency_record(user_id=user_id, amount=amount, currency=currency, idempotency_key=idempotency_key, session=session)
            session.commit()
            on_order_created(order_id)
            logger.info('order.created', extra={
                'order_id': order_id,
                'user_id': user_id,
                'amount': amount,
                'currency': currency,
                'idempotency_key': idempotency_key
            })
            return {'status':'created', 'order_id': order_id}

        except IntegrityError:
            session.rollback()
            record = get_idempotency_record_by_key(idempotency_key=idempotency_key, session=session)
            if record:
                if record.request_hash == f'{user_id}:{amount}:{currency}':
                    logger.info('order.replayed', extra={
                        'order_id': record.order_id,
                        'user_id': user_id,
                        'amount': amount,
                        'currency': currency,
                        'idempotency_key': idempotency_key
                    })
                    return {'status':'replayed', 'order_id': record.order_id}
                else:
                    raise HTTPException(status_code=409, detail='Idempotency key conflict') 
            else:
                logger.error('order.creation_failed.unexpected', extra={
                    'user_id': user_id,
                    'amount': amount,
                    'currency': currency,
                    'idempotency_key': idempotency_key
                })
                raise HTTPException(status_code=500, detail='Unknown error')
    except HTTPException as e:
        reason = e.detail if isinstance(e.detail, str) else 'HTTP error'
        logger.info('order.creation_failed', extra={
            'reason': reason,
            'user_id': user_id,
            'amount': amount,
            'currency': currency,
            'idempotency_key': idempotency_key
        })
        session.rollback()
        raise
    except Exception:
        logger.exception('order.creation_failed.unexpected', extra={
            'user_id': user_id,
            'amount': amount,
            'currency': currency,
            'idempotency_key': idempotency_key
        })
        session.rollback()
        raise

def get_order_by_id_cached(order_id: int, session):
    cached = get_order_from_cache(order_id)
    if cached:
        logger.info('order.cache_hit', extra={'order_id': order_id})
        return cached  # cache hit

    stmt = select(Order).where(Order.id == order_id)
    order = session.execute(stmt).scalar_one_or_none()
    if not order:
        logger.info('order.cache_miss', extra={'order_id': order_id, 'reason': 'not found'})
        raise HTTPException(status_code=404, detail='Order not found')

    result = {
        'order_id': order.id,
        'user_id': order.user_id,
        'amount': str(order.amount),
        'currency': order.currency,
    }
    set_order_cache(order_id, result)  # cache miss -> fill cache
    return result


def on_order_created(order_id: int):
    # вариант 1: invalidate
    invalidate_order_cache(order_id)

def get_user_orders_by_id(user_id: int, limit: int, session):
    stmnt = select(Order).where(Order.user_id == user_id).order_by(desc(Order.created_at)).limit(limit)
    result = session.execute(stmnt)
    orders = result.scalars().all()
    ret_result = {
        'orders': [{'order_id': order.id,
                    'user_id': order.user_id,
                    'amount': str(order.amount),
                    'currency': order.currency
                    }
                    for order in orders 
                    ]
    }
    return ret_result