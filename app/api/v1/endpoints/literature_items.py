from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import LiteratureItem
from app.db.session import get_db
from app.schemas.literature_item import LiteratureItemResponse
from typing import List

router = APIRouter()

@router.get("/", response_model=List[LiteratureItemResponse])
async def get_items(db: Session = Depends(get_db)):
    items = db.query(LiteratureItem).all()
    return items