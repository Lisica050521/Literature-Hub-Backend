from pydantic import BaseModel
from typing import Optional, List

class LiteratureItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class LiteratureItemCreate(LiteratureItemBase):
    author_id: int

class LiteratureItemResponse(LiteratureItemBase):
    id: int
    title: str
    description: Optional[str] = None
    publication_date: Optional[str] = None
    genre: Optional[str] = None
    available_copies: Optional[int] = 0 
    author_id: int

    class Config:
        from_attributes = True