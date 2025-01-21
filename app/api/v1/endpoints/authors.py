from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.models import Author
from app.models.user import User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.author import AuthorResponse
from app.schemas.literature_item import LiteratureItemResponse
from app.schemas.author import AuthorCreate
from app.schemas.literature_item import LiteratureItemCreate
from app.models.literature_item import LiteratureItem


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

@router.get("/", response_model=List[AuthorResponse])
async def get_authors(
    db: Session = Depends(get_db),
    name: str | None = Query(None, description="Фильтр по имени или фамилии автора"),
    limit: int = Query(10, ge=1, le=100, description="Количество записей на страницу"),
    offset: int = Query(0, ge=0, description="Смещение от начала списка")
):
    query = db.query(Author)
    if name:
        # Разделяем имя на части (если они есть)
        name_parts = name.split()
        if len(name_parts) == 2:
            # Фильтруем по фамилии (вторая часть строки)
            query = query.filter(Author.name.ilike(f"%{name_parts[1]}%"))
        else:
            # Если передано только одно слово (например, фамилия)
            query = query.filter(Author.name.ilike(f"%{name}%"))
    authors = query.offset(offset).limit(limit).all()
    return authors

@router.get("/{author_id}/literature_items", response_model=List[LiteratureItemResponse])
async def get_literature_items_for_author(
    author_id: int,  # Параметр пути для получения литературы конкретного автора
    db: Session = Depends(get_db)  # Получаем сессию БД
):
    # Запрашиваем автора по ID
    author = db.query(Author).filter(Author.id == author_id).first()

    # Если автор не найден, возвращаем ошибку 404
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    # Возвращаем литературу, принадлежащую автору (используем связь между моделями)
    return author.literature_items

# Эндпоинт для создания нового автора (только для администратора)
@router.post("/", response_model=AuthorResponse)
async def create_author(
    author_data: AuthorCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    author = Author(name=author_data.name, bio=author_data.bio)
    db.add(author)
    db.commit()
    db.refresh(author)

    return AuthorResponse(**author.__dict__)