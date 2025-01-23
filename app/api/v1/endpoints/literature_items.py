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
    
    # Добавим проверку на дублирование или фильтрацию по всем полям
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
    # Создаем новый объект литературы с учётом всех полей
    literature_item = LiteratureItem(
        title=literature_item_data.title,
        description=literature_item_data.description,
        genre=literature_item_data.genre,
        publication_date=literature_item_data.publication_date,
        author_id=literature_item_data.author_id
    )

    db.add(literature_item)
    db.commit()
    db.refresh(literature_item)
    
    # Возвращаем данные с использованием схемы LiteratureItemResponse
    return LiteratureItemResponse(
        id=literature_item.id,
        title=literature_item.title,
        description=literature_item.description,
        genre=literature_item.genre,
        publication_date=literature_item.publication_date,
        available_copies=literature_item.available_copies,
        author_id=literature_item.author_id
    )

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

