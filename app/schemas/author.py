from pydantic import BaseModel
from typing import List

class AuthorBase(BaseModel):
    name: str
    bio: str | None = None

class AuthorCreate(AuthorBase):
    pass

class AuthorResponse(AuthorBase):
    id: int
    literature_items: List[str] = []

    class Config:
        orm_mode = True
