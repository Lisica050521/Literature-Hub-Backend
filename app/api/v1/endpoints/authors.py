from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import Author
from app.db.session import get_db
from app.schemas.author import AuthorResponse
from typing import List

router = APIRouter()

@router.get("/", response_model=List[AuthorResponse])
async def get_authors(db: Session = Depends(get_db)):
    authors = db.query(Author).all()
    return authors