import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.schemas.auth_token import AuthToken

@pytest.fixture()
def db():
    # Создание новой сессии для тестов
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@pytest.fixture()
def test_user(db):
    # Создание тестового пользователя
    user = db.query(User).filter(User.username == "testuser").first()
    if not user:
        user = User(
            username="testuser",
            hashed_password=hash_password("testpassword"),
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@pytest.fixture()
def client():
    # Настройка клиента для тестов
    with TestClient(app) as client:
        yield client

def authenticate_user(client, username, password):
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_create_user(client, admin_user):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")
    
    new_user_data = {
        "username": "newuser",
        "password": "newpassword",
        "role": "user"
    }
    response = client.post(
        "/users/",
        json=new_user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created"

def test_get_users(client, admin_user, test_user):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")
    
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    users = response.json()["users"]
    assert any(user["username"] == "admin" for user in users)
    assert any(user["username"] == "testuser" for user in users)

def test_update_user_info(client, test_user):
    # Аутентификация тестового пользователя
    token = authenticate_user(client, "testuser", "testpassword")
    
    updated_data = {
        "username": "updateduser",
        "password": "updatedpassword"
    }
    response = client.put(
        "/users/me",
        json=updated_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Информация обновлена"
    assert response.json()["user"]["username"] == "updateduser"
