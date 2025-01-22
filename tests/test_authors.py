from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import Author
from app.schemas.author import AuthorCreate, AuthorResponse
from app.schemas.literature_item import LiteratureItemResponse
from sqlalchemy.orm import Session
from typing import Generator
import pytest


# Используем TestClient для тестирования FastAPI приложения
client = TestClient(app)

# Фикстура для работы с базой данных
@pytest.fixture(scope="module")
def db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Тестирование получения списка авторов
def test_get_authors(db):
    # Создаем автора для теста
    new_author = Author(name="Test Author", bio="Test Bio")
    db.add(new_author)
    db.commit()
    db.refresh(new_author)

    # Выполняем запрос к эндпоинту
    response = client.get("/authors/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert "name" in response.json()[0]
    assert "id" in response.json()[0]

# Тестирование получения литературы для конкретного автора
def test_get_literature_items_for_author(db):
    # Создаем автора для теста
    new_author = Author(name="Author With Books", bio="Author Bio")
    db.add(new_author)
    db.commit()
    db.refresh(new_author)

    # Создаем несколько книг для этого автора
    literature_item_1 = LiteratureItemResponse(title="Book 1", author_id=new_author.id)
    literature_item_2 = LiteratureItemResponse(title="Book 2", author_id=new_author.id)
    db.add(literature_item_1)
    db.add(literature_item_2)
    db.commit()

    # Выполняем запрос к эндпоинту для получения литературы
    response = client.get(f"/authors/{new_author.id}/literature_items")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert "title" in response.json()[0]

# Тестирование создания нового автора (для администратора)
def test_create_author(db):
    # Данные для нового автора
    author_data = AuthorCreate(name="New Author", bio="Bio of new author")

    # Выполняем запрос на создание нового автора
    response = client.post("/authors/", json=author_data.dict())
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "New Author"
    assert response.json()["bio"] == "Bio of new author"