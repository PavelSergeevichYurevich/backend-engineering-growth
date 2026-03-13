from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .db import get_session
from .schemas import TransferRequest
from .services import transfer_transaction

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
