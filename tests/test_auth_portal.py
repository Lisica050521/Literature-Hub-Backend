import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.schemas.auth_token import AuthToken
from app.schemas.login import LoginRequest

@pytest.fixture()
def db():
    # Создание нового сессии для тестов
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def test_user(db):
    # Проверка, что пользователь с таким именем не существует
    existing_user = db.query(User).filter(User.username == "testuser").first()
    if not existing_user:
        # Создание тестового пользователя
        user = User(username="testuser", hashed_password=hash_password("testpassword"))
        db.add(user)
        db.commit()
        db.refresh(user)
    return existing_user or db.query(User).filter(User.username == "testuser").first()

@pytest.fixture()
def client():
    # Настройка клиента для тестов
    with TestClient(app) as client:
        yield client

# Успешная аутентификация (валидные данные)
def test_authenticate_user_success(client, test_user):
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()

# Неверные учетные данные (неверное имя пользователя или пароль)
def test_authenticate_user_invalid_credentials(client):
    login_data = {
        "username": "wronguser",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect username or password"

# Пустое имя пользователя или пароль
def test_empty_username_or_password(client):
    # Пустое имя пользователя
    login_data = {
        "username": "",
        "password": "testpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect username or password"

    # Пустой пароль
    login_data = {
        "username": "testuser",
        "password": ""
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect username or password"

# Неверный формат данных
def test_invalid_json_format(client):
    # Невалидный формат данных (например, отсутствуют обязательные поля)
    login_data = {
        "user": "testuser",  # неверное имя поля
        "pwd": "testpassword"  # неверное имя поля
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 422  # Ошибка валидации