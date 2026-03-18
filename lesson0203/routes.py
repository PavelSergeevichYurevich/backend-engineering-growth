from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .db import get_session
from .schemas import CreateOrder, TransferRequest
from .services import create_order, get_order_by_id_cached, transfer_transaction

router = APIRouter()


@router.post('/transfer/', status_code=status.HTTP_201_CREATED)
def transfer(payload: TransferRequest, session: Session = Depends(get_session)):
    return transfer_transaction(
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        currency=payload.currency,
        forced_failure=payload.forced_failure,
        session=session,
    )

@router.post('/orders/', status_code=status.HTTP_201_CREATED)
def create_order_and_key(payload: CreateOrder, session: Session = Depends(get_session)):
    
    result =  create_order(
        user_id=payload.user_id,
        amount=payload.amount,
        currency=payload.currency,
        idempotency_key=payload.idempotency_key,
        session=session,
    )

    if result['status'] == 'replayed':
        return JSONResponse(status_code=200, content={'order_id': result['order_id']})
    elif result['status'] == 'created':
        return {'order_id': result['order_id']}
    else:
        raise HTTPException(status_code=500, detail='Unknown status')
    
@router.get('/orders/{order_id}')
def get_order(order_id: int, session: Session = Depends(get_session)):
    return get_order_by_id_cached(order_id, session)