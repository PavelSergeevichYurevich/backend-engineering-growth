from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from .models import Transfer, Account


async def transfer_transaction(from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    currency: str,
    session: AsyncSession):
    if amount <= 0:
        raise HTTPException(status_code=422, detail='wrong amount')
    try:
        if from_account_id == to_account_id:
            raise HTTPException(status_code=422, detail='Id match')
        stmnt1 = select(Account).where(Account.id == from_account_id).with_for_update()
        stmnt2 = select(Account).where(Account.id == to_account_id).with_for_update()
        result1 = await session.execute(stmnt1)
        account1 = result1.scalar_one_or_none()
        result2 = await session.execute(stmnt2)
        account2 = result2.scalar_one_or_none()
        if not account1:
            raise HTTPException(status_code=404,detail='User 1 not find')
        if not account2:
            raise HTTPException(status_code=404,detail='User 2 not find')
       
        if account1.currency != currency or account2.currency != currency:
            raise HTTPException(status_code=409, detail='Not correct currency')
        if account1.balance < amount:
            raise HTTPException(status_code=409, detail="Not enough money")
        account1.balance -= amount
        account2.balance += amount
        stmt = (
            insert(Transfer)
            .values(from_account_id=from_account_id, to_account_id=to_account_id, amount=amount, currency=currency)
            .returning(Transfer)
        )

        result = await session.execute(stmt)
        transfer = result.scalar_one()

        await session.commit()
        return {'transfer_id': transfer.id}

    except Exception:
        await session.rollback()
        raise
    

    
    