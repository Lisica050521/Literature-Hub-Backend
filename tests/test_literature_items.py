from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import User, LiteratureItem, Author
from app.schemas.literature_item import LiteratureItemCreate
from app.core.security import hash_password
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

# Фикстура для создания администратора
@pytest.fixture()
def admin_user(db):
    # Создание администратора для тестов
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            hashed_password=hash_password("adminpassword"),
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin

# Фикстура для аутентификации администратора и получения токена
def authenticate_user(client, username, password):
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]

# Тестирование создания новой книги (для администратора)
def test_create_literature_item(db, admin_user):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Создание автора для теста (например, через фикстуру или вручную)
    new_author = Author(name="Test Author", bio="Test Bio")
    db.add(new_author)
    db.commit()
    db.refresh(new_author)

    # Данные для новой книги
    literature_item_data = LiteratureItemCreate(
        title="New Book",
        description="Description of new book",
        author_id=new_author.id
    )

    # Выполняем запрос на создание новой книги с токеном администратора
    response = client.post(
        "/literature/literature_items",
        json=literature_item_data.dict(),
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверяем, что статус ответа 200 (успех)
    assert response.status_code == 200

    # Проверяем, что в ответе есть ID новой книги
    assert "id" in response.json()

    # Проверяем, что данные в ответе совпадают с ожидаемыми
    assert response.json()["title"] == "New Book"
    assert response.json()["description"] == "Description of new book"

    # Проверяем, что книга была создана в базе данных
    created_item = db.query(LiteratureItem).filter_by(title="New Book").first()

    assert created_item is not None
    assert created_item.description == "Description of new book"

# Тестирование получения списка книг с фильтрацией
def test_get_literature_items(db):
    
     # Очистка таблиц перед тестом
    db.query(LiteratureItem).delete()
    db.query(Author).delete()
    db.commit()
    
    new_author = Author(name="Test Author", bio="Test Bio")
    db.add(new_author)
    db.commit()
    db.refresh(new_author)

    # Создаем книги для теста
    literature_item_1 = LiteratureItem(title="Book 1", genre="Fiction", publication_date="2023-01-01", author_id=new_author.id)
    literature_item_2 = LiteratureItem(title="Book 2", genre="Non-fiction", publication_date="2024-01-01", author_id=new_author.id)
    db.add(literature_item_1)
    db.add(literature_item_2)
    db.commit()
    db.refresh(literature_item_1)
    db.refresh(literature_item_2)

    # Выполняем запрос с фильтром по названию
    response = client.get("/literature", params={"title": "Book 1"})
    
    assert response.status_code == 200
    assert len(response.json()) == 1  # Ожидаем 1 элемент
    assert response.json()[0]["title"] == "Book 1"

# Тестирование получения книги по ID
def test_get_literature_item_by_id(db):
    
    # Создаем автора для книги
    new_author = Author(name="Test Author", bio="Test Bio")
    db.add(new_author)
    db.commit()
    db.refresh(new_author)

    # Создаем книгу для теста
    literature_item = LiteratureItem(title="Book 1", genre="Fiction", publication_date="2023-01-01", author_id=new_author.id
    )
    db.add(literature_item)
    db.commit()
    db.refresh(literature_item)

    # Выполняем запрос для получения книги по ID
    response = client.get(f"/literature/literature_items/{literature_item.id}")
    assert response.status_code == 200

    assert response.json()["title"] == "Book 1"
    response_data = response.json()
    assert response.json()["genre"] == "Fiction"
    assert response.json()["publication_date"] == "2023-01-01"

# Тестирование обновления книги (только для администратора)
def test_update_literature_item(db, admin_user):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Создаем автора для теста
    new_author = Author(name="Test Author", bio="Test Bio")
    db.add(new_author)
    db.commit()
    db.refresh(new_author)

    # Создаем книгу для теста
    literature_item = LiteratureItem(title="Old Book", genre="Fiction", publication_date="2023-01-01", author_id=new_author.id)
    db.add(literature_item)
    db.commit()
    db.refresh(literature_item)

    # Данные для обновления книги
    updated_data = LiteratureItemCreate(title="Updated Book", description="Updated description", genre="Non-fiction", publication_date="2025-01-01", author_id=new_author.id)

    # Выполняем запрос на обновление книги
    response = client.put(f"/literature/literature_items/{literature_item.id}", json=updated_data.dict(), headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Book"
    assert response.json()["description"] == "Updated description"

# Тестирование удаления книги (только для администратора)
def test_delete_literature_item(db, admin_user):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Создаем автора для теста
    new_author = Author(name="Test Author", bio="Test Bio")
    db.add(new_author)
    db.commit()
    db.refresh(new_author)

    # Создаем книгу для теста
    literature_item = LiteratureItem(title="Book to Delete", genre="Fiction", publication_date="2023-01-01", author_id=new_author.id)
    db.add(literature_item)
    db.commit()
    db.refresh(literature_item)

    # Выполняем запрос на удаление книги
    response = client.delete(f"/literature/literature_items/{literature_item.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["title"] == "Book to Delete"
