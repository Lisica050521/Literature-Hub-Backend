from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import Field

class TransactionResponse(BaseModel):
    transaction_id: int = Field(..., alias="id")
    book_id: int
    loan_date: datetime
    return_date: Optional[datetime] = None

    class Config:
        from_attributes = True
        allow_population_by_field_name = True

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