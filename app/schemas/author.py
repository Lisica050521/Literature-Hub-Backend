from pydantic import BaseModel
from typing import List, Optional
from app.schemas.literature_item import LiteratureItemResponse

class AuthorBase(BaseModel):
    name: str
    bio: Optional[str] = None

    class Config:
        from_attributes = True

class AuthorCreate(AuthorBase):
    pass

class AuthorResponse(AuthorBase):
    id: str
    literature_items: List[LiteratureItemResponse] = []

    class Config:
        from_attributes = True