from decimal import Decimal

from pydantic import BaseModel


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal
    currency: str
    forced_failure: bool = False
