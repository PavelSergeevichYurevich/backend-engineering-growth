from decimal import Decimal
from .models import Account, IdempotencyRecords, Order, Transfer
from sqlalchemy import insert, select
from sqlalchemy.orm import Session


def create_order_with_idempotency_record(user_id: int, amount: Decimal, currency: str, idempotency_key: str, session: Session):
    stmt = insert(Order).values(
                user_id=user_id,
                amount=amount,
                currency=currency,
            ).returning(Order.id)
    order_id = session.execute(stmt).scalar_one()

    stmnt = insert(IdempotencyRecords).values(
                idempotency_key=idempotency_key,
                request_hash=f'{user_id}:{amount}:{currency}',
                order_id=order_id
            )
    session.execute(stmnt)
    return order_id
    
def get_idempotency_record_by_key(idempotency_key: str, session: Session):
    stmnt = select(IdempotencyRecords).where(IdempotencyRecords.idempotency_key == idempotency_key).with_for_update()
    record = session.execute(stmnt).scalar_one_or_none()
    return record

def get_accounts_for_update(from_account_id: int, to_account_id: int, session: Session):
    stmt1 = select(Account).where(Account.id == from_account_id).with_for_update()
    stmt2 = select(Account).where(Account.id == to_account_id).with_for_update()
    account1 = session.execute(stmt1).scalar_one_or_none()
    account2 = session.execute(stmt2).scalar_one_or_none()
    return account1, account2

def get_transfer_id(from_account_id: int, to_account_id: int, amount: Decimal, currency: str, session: Session):
    stmt = (
            insert(Transfer)
            .values(
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount=amount,
                currency=currency,
            )
            .returning(Transfer.id)
        )

    transfer_id = session.execute(stmt).scalar_one()
    return transfer_id