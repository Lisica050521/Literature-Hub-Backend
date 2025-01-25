from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import User
from app.utils import hash_password
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

@pytest.fixture(scope="function", autouse=True)
def clear_db(db):
    # Очистка базы данных после каждого теста
    try:
        yield  # Выполняется до теста
    finally:
        db.rollback()  # Откатываем незавершённые транзакции
        db.query(User).delete()  # Удаляем пользователей
        db.commit()  # Применяем изменения

@pytest.fixture()
def testuser(db):
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

# Тест на первый шаг регистрации
def test_start_registration(db):
    response = client.post(
        "/users/register/start",
        data={"username": "newuser", "password": "newpassword"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Введите, кем вы хотите зарегистрироваться: читателем или администратором"}

# Тест на выбор роли
def test_choose_role(db):
    # Регистрируем пользователя
    client.post("/users/register/start", data={"username": "newuser", "password": "newpassword"})
    
    response = client.post(
        "/users/register/choose_role",
        data={"username": "newuser", "role_choice": "user"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Регистрация завершена. Ваша роль: читатель"}

    # Проверяем, что пользователь зарегистрирован как "user"
    user = db.query(User).filter(User.username == "newuser").first()
    assert user is not None
    assert user.role == "user"

# Тест на выбор роли с ошибкой
def test_choose_role_invalid(db):
    # Регистрируем пользователя
    client.post("/users/register/start", data={"username": "newuser", "password": "newpassword"})
    
    response = client.post(
        "/users/register/choose_role",
        data={"username": "newuser", "role_choice": "invalidrole"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Некорректный выбор роли"}

# Тест на подтверждение администратора
def test_confirm_admin(db):
    # Регистрируем пользователя
    client.post("/users/register/start", data={"username": "newuser", "password": "newpassword"})
    client.post("/users/register/choose_role", data={"username": "newuser", "role_choice": "admin"})
    
    response = client.post(
        "/users/register/confirm_admin",
        data={"username": "newuser", "admin_code": "1234567"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Регистрация завершена. Ваша роль: администратор"}

    # Проверяем, что пользователь зарегистрирован как "admin"
    user = db.query(User).filter(User.username == "newuser").first()
    assert user is not None
    assert user.role == "admin"