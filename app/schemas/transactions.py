from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TransactionResponse(BaseModel):
    book_id: int
    loan_date: datetime
    return_date: Optional[datetime] = None

    class Config:
        from_attributes = True