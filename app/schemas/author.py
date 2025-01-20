from pydantic import BaseModel
from typing import List, Optional

class AuthorBase(BaseModel):
    name: str
    bio: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class AuthorResponse(AuthorBase):
    id: int
    literature_items: List[str] = []

    class Config:
        from_attributes = True