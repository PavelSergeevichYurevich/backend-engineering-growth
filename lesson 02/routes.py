from decimal import Decimal
from .services import transfer_transaction
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()

@router.post('/transfer/')
async def transfer(
    from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    currency: str,
    session: AsyncSession = Depends(get_session)
    ):
    result = await transfer_transaction(from_account_id,
        to_account_id,
        amount,
        currency,
        session=session)
    return result