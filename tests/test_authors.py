import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.auth_token import AuthToken
from app.schemas.author import AuthorCreate
from app.schemas.literature_item import LiteratureItemCreate
from app.core.security import generate_auth_token
from datetime import timedelta
import jwt
from app.core.config import settings

# Создаем фикстуру для генерации токена
@pytest.fixture()
def token(test_admin):
    # Включаем роль в данные
    return generate_auth_token(data={"user_id": test_admin.id, "role": "admin"}, expires_delta=timedelta(hours=1))

# Фикстура для подключения к базе данных
@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Фикстура для создания пользователя администратора
@pytest.fixture()
def test_admin(db):
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(username="admin", hashed_password="hashed_password")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# Фикстура для данных автора
@pytest.fixture()
def author_data():
    return AuthorCreate(name="John Doe", bio="Some biography")

# Фикстура для клиента
@pytest.fixture()
def client():
    with TestClient(app) as client:
        yield client

# Фикстура для создания автора
@pytest.fixture()
def create_author(client, author_data, token):
    response = client.post(
        "/authors/", json=author_data.dict(), headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    return response.json()  # возвращаем данные созданного автора

# Тест создания автора
def test_create_author(client, db, test_admin, author_data, token):
    response = client.post(
        "/authors/", json=author_data.dict(), headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == author_data.name
    assert response.json()["bio"] == author_data.bio

def test_auth_token_sub_is_int(token):
    # Декодируем токен для проверки его содержимого
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    assert isinstance(payload["sub"], str)
    
    # Поскольку мы передаем user_id, проверим, что оно соответствует ожидаемому id пользователя
    assert payload["sub"] == 1  # Замените на id пользователя, которое вы передаете в токене

    # Проверим роль
    assert payload["role"] == "admin"

# Тест создания литературы для автора
def test_create_literature_for_author(client, db, create_author):
    literature_data = LiteratureItemCreate(
        title="Test Book",
        description="A description of the book",
        author_id=create_author["id"]  # доступ к id через ключ
    )
    response = client.post("/literature_items/", json=literature_data.dict())
    assert response.status_code == 200
    assert response.json()["title"] == literature_data.title
    assert response.json()["description"] == literature_data.description
    assert response.json()["author_id"] == literature_data.author_id