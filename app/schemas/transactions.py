from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pydantic import Field

class TransactionResponse(BaseModel):
    book_id: int = Field(computed=True)
    loan_date: datetime
    return_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class IssueBookResponse(BaseModel):
    message: str
    transaction_id: int
    due_date: datetime

    class Config:
        from_attributes = True

class ReturnBookResponse(BaseModel):
    message: str
    transaction_id: int

    class Config:
        from_attributes = True