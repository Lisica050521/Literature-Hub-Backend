from pydantic import BaseModel

class LiteratureItemBase(BaseModel):
    title: str
    description: str | None = None

class LiteratureItemCreate(LiteratureItemBase):
    author_id: int

class LiteratureItemResponse(LiteratureItemBase):
    id: int
    author_id: int

    class Config:
        orm_mode = True
