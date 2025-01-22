from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.models import LiteratureItem
from app.models.author import Author
from app.models.user import User
from app.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.literature_item import LiteratureItemResponse
from app.schemas.literature_item import LiteratureItemCreate

from typing import List

router = APIRouter()

# Функция для проверки, является ли пользователь администратором
def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":  # Проверяем роль пользователя
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль администратора для выполнения этого действия."
        )
    return current_user

# Получение списка книг с фильтрацией по названию, жанру и дате публикации.
@router.get("/", response_model=List[LiteratureItemResponse])
async def get_items(
    db: Session = Depends(get_db),
    title: str | None = Query(None, description="Фильтр по названию"),
    genre: str | None = Query(None, description="Фильтр по жанру"),
    publication_date: str | None = Query(None, description="Фильтр по дате публикации"),
    limit: int = Query(10, ge=1, le=100, description="Количество записей на страницу"),
    offset: int = Query(0, ge=0, description="Смещение от начала списка")
):
    query = db.query(LiteratureItem)
    if title:
        query = query.filter(LiteratureItem.title.ilike(f"%{title}%"))
    if genre:
        query = query.filter(LiteratureItem.genre.ilike(f"%{genre}%"))
    if publication_date:
        query = query.filter(LiteratureItem.publication_date == publication_date)
    items = query.offset(offset).limit(limit).all()
    return items

# Получение информации о книге по её ID.
@router.get("/literature_items/{literature_id}", response_model=LiteratureItemResponse)
async def get_literature_item_by_id(
    literature_id: int, db: Session = Depends(get_db)
):
    literature_item = db.query(LiteratureItem).filter(LiteratureItem.id == literature_id).first()
    if not literature_item:
        raise HTTPException(status_code=404, detail="Literature item not found")
    return literature_item

# Получение книги с автором (с параметром include_author).
@router.get("/literature_items/{literature_id}/with_author", response_model=LiteratureItemResponse)
async def get_literature_item_with_author(
    literature_id: int, db: Session = Depends(get_db), include_author: bool = Query(False)
):
    literature_item = db.query(LiteratureItem).filter(LiteratureItem.id == literature_id).first()
    if not literature_item:
        raise HTTPException(status_code=404, detail="Literature item not found")

    if include_author:
        # Получение информации о авторе
        literature_item.author = db.query(Author).filter(Author.id == literature_item.author_id).first()
    
    return literature_item

# Обновление информации о книге по её ID (только для администратора).
@router.put("/literature_items/{literature_id}", response_model=LiteratureItemResponse)
async def update_literature_item(
    literature_id: int,
    literature_item_data: LiteratureItemCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)  # Используем проверку на администратора
):
    literature_item = db.query(LiteratureItem).filter(LiteratureItem.id == literature_id).first()
    if not literature_item:
        raise HTTPException(status_code=404, detail="Literature item not found")
    
    # Обновление данных о книге
    literature_item.title = literature_item_data.title
    literature_item.description = literature_item_data.description
    db.commit()
    db.refresh(literature_item)
    return literature_item

# Создание новой книги (только для администратора).
@router.post("/literature_items", response_model=LiteratureItemResponse)
async def create_literature_item(
    literature_item_data: LiteratureItemCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    literature_item = LiteratureItem(**literature_item_data.dict())
    db.add(literature_item)
    db.commit()
    db.refresh(literature_item)
    return LiteratureItemResponse(**literature_item.__dict__)

# Удаление книги по ID (только для администратора).
@router.delete("/literature_items/{literature_id}", response_model=LiteratureItemResponse)
async def delete_literature_item(
    literature_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    literature_item = db.query(LiteratureItem).filter(LiteratureItem.id == literature_id).first()
    if not literature_item:
        raise HTTPException(status_code=404, detail="Literature item not found")
    
    db.delete(literature_item)
    db.commit()
    return LiteratureItemResponse(**literature_item.__dict__)