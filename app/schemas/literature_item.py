from pydantic import BaseModel
from typing import Optional, List

class LiteratureItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class LiteratureItemCreate(LiteratureItemBase):
    author_id: int

class LiteratureItemResponse(LiteratureItemBase):
    id: int
    author_id: int

    class Config:
        from_attributes = True