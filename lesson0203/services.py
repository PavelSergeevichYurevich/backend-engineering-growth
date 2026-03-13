from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from .models import Account, Transfer


def transfer_transaction(
    from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    currency: str,
    session: Session,
    forced_failure: bool = False,
):
    if amount <= 0:
        raise HTTPException(status_code=422, detail="wrong amount")

    try:
        if from_account_id == to_account_id:
            raise HTTPException(status_code=422, detail="Id match")

        stmt1 = select(Account).where(Account.id == from_account_id).with_for_update()
        stmt2 = select(Account).where(Account.id == to_account_id).with_for_update()
        account1 = session.execute(stmt1).scalar_one_or_none()
        account2 = session.execute(stmt2).scalar_one_or_none()

        if not account1:
            raise HTTPException(status_code=404, detail="User 1 not find")
        if not account2:
            raise HTTPException(status_code=404, detail="User 2 not find")

        if account1.currency != currency or account2.currency != currency:
            raise HTTPException(status_code=409, detail="Not correct currency")
        if account1.balance < amount:
            raise HTTPException(status_code=409, detail="Not enough money")

        account1.balance -= amount
        if forced_failure:
            raise HTTPException(status_code=500, detail="test")

        account2.balance += amount
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
        session.commit()
        return {"transfer_id": transfer_id}

    except Exception:
        session.rollback()
        raise
