from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import User, Transaction, LiteratureItem, Author
from app.schemas.literature_item import LiteratureItemCreate
from app.schemas.transactions import TransactionResponse
from app.core.security import hash_password
from sqlalchemy.orm import Session
from typing import Generator
from datetime import datetime, timedelta
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
    # Очистка базы данных перед началом каждого теста
    try:
        db.rollback()  # Откатываем незавершённые транзакции
        db.query(Transaction).delete()  # Удаляем дочерние записи
        db.query(User).delete()  # Удаляем родительские записи
        db.query(LiteratureItem).delete()  # Удаляем книги
        db.commit()  # Применяем изменения
    except Exception:
        db.rollback()
        raise

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

@pytest.fixture()
def literature_item(db):
    # Создаем автора для теста
    new_author = Author(name="Test Author", bio="Test Bio")
    db.add(new_author)
    db.commit()
    db.refresh(new_author)

    # Создаем Pydantic модель книги для теста
    literature_item_create = LiteratureItemCreate(
        title="Test Book", 
        author_id=new_author.id, 
        publication_date="2023-01-01", 
        genre="Fiction",
        description="Test Book Description"
    )

    # Преобразуем Pydantic модель в SQLAlchemy модель
    literature_item_db = LiteratureItem(
        title=literature_item_create.title,
        description=literature_item_create.description,
        author_id=literature_item_create.author_id,
        publication_date=literature_item_create.publication_date,
        genre=literature_item_create.genre,
        available_copies=1  # Устанавливаем хотя бы одну копию для книги
    )

    # Сохраняем литературу в базе данных
    db.add(literature_item_db)
    db.commit()
    db.refresh(literature_item_db)

    return literature_item_db

@pytest.fixture()
def test_transactions(db, testuser, literature_item):
    # Создание нескольких тестовых транзакций для пользователя
    transactions = []
    for i in range(3):
        transaction = Transaction(
            user_id=testuser.id,
            literature_item_id=literature_item.id,
            loan_date=datetime.utcnow() - timedelta(days=i),
            due_date=datetime.utcnow() + timedelta(days=14 - i),
        )
        db.add(transaction)
        transactions.append(transaction)

    db.commit()

    # Проверка: убедиться, что транзакции сохранены
    assert db.query(Transaction).filter(Transaction.user_id == testuser.id).count() == 3
    
    transactions_pydantic = [
    TransactionResponse.model_validate(transaction)
    for transaction in transactions
    ]

    return transactions_pydantic  # Возвращаем уже преобразованные в Pydantic объекты


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

# Тестирование выдачи книги (для администратора)
def test_issue_book(db, admin_user, testuser, literature_item):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Запрос на выдачу книги
    issue_data = {
        "user_id": testuser.id  # Указываем ID тестового пользователя
    }

    response = client.post(
        f"/transactions/issue/{literature_item.id}",
        json=issue_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка успешной выдачи книги
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Книга выдана"

    # Проверяем, что транзакция создана в базе данных
    transaction = db.query(Transaction).filter_by(user_id=testuser.id).first()
    assert transaction is not None
    assert transaction.literature_item_id == literature_item.id
    assert transaction.return_date is None

# Администратор может выдать книгу только читателю
def test_admin_cannot_issue_book_to_themselves_or_another_admin(db, admin_user, testuser, literature_item):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Попытка выдать книгу самому себе
    issue_data = {
        "user_id": admin_user.id  # Администратор не может выдать книгу себе
    }

    response = client.post(
        f"/transactions/issue/{literature_item.id}",
        json=issue_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка ошибки, что администратор не может выдать книгу самому себе
    assert response.status_code == 400
    assert "detail" in response.json()
    assert response.json()["detail"] == "Администратор может выдать книгу только читателю."

    # Попытка выдать книгу другому админу
    another_admin = User(
    role="admin",
    username="admin2",
    hashed_password=hash_password("password2")  # Хешируем пароль
    )
    db.add(another_admin)
    db.commit()

    issue_data["user_id"] = another_admin.id  # Попытка выдать книгу другому админу

    response = client.post(
        f"/transactions/issue/{literature_item.id}",
        json=issue_data,
        headers={"Authorization": f"Bearer {token}"}
    )


# Книга не найдена или отсутствуют доступные экземпляры
def test_book_not_found_or_no_available_copies(db, admin_user, testuser, literature_item):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Обновляем количество копий до нуля
    literature_item.available_copies = 0
    db.commit()

    # Запрос на выдачу книги
    issue_data = {
        "user_id": testuser.id
    }

    response = client.post(
        f"/transactions/issue/{literature_item.id}",
        json=issue_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка, что книга не найдена или нет доступных экземпляров
    assert response.status_code == 404
    assert "detail" in response.json()
    assert response.json()["detail"] == "Книга не найдена или отсутствуют доступные экземпляры."

#  Пользователь уже имеет 5 не возвращенных книг
def test_user_has_5_unreturned_books(db, admin_user, testuser, literature_item):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Симуляция того, что у пользователя уже есть 5 невозвращенных книг
    for _ in range(5):
        db.add(Transaction(user_id=testuser.id, literature_item_id=literature_item.id))
    db.commit()

    # Запрос на выдачу книги
    issue_data = {
        "user_id": testuser.id
    }

    response = client.post(
        f"/transactions/issue/{literature_item.id}",
        json=issue_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка, что ошибка возникает при попытке выдать книгу
    assert response.status_code == 400
    assert "detail" in response.json()
    assert response.json()["detail"] == "Пользователь уже имеет 5 не возвращенных книг."

# Тестирование возврата книги (для администратора)
def test_return_book(db, admin_user, testuser, literature_item):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Создаем транзакцию для теста
    transaction = Transaction(user_id=testuser.id, literature_item_id=literature_item.id, loan_date=datetime.utcnow(), due_date=datetime.utcnow() + timedelta(days=14))
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Запрос на возврат книги
    response = client.post(
        f"/transactions/return/{transaction.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка успешного возврата книги
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Книга возвращена"

    # Проверяем, что транзакция обновилась в базе данных
    db.refresh(transaction)
    assert transaction.return_date is not None
    assert transaction.return_date <= datetime.utcnow()

    # Проверяем, что количество доступных экземпляров книги увеличилось
    book = db.query(LiteratureItem).filter(LiteratureItem.id == literature_item.id).first()
    assert book.available_copies > 0

# Книга уже была возвращена
def test_book_already_returned(db, admin_user, testuser, literature_item):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Создаем транзакцию для теста
    transaction = Transaction(user_id=testuser.id, literature_item_id=literature_item.id, return_date=datetime.utcnow())
    db.add(transaction)
    db.commit()

    # Запрос на возврат книги
    response = client.post(
        f"/transactions/return/{transaction.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка, что книга уже была возвращена
    assert response.status_code == 400
    assert "detail" in response.json()
    assert response.json()["detail"] == "Книга уже была возвращена."

# Транзакция не найдена
def test_transaction_not_found(db, admin_user, literature_item):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Запрос на возврат несуществующей транзакции
    response = client.post(
        f"/transactions/return/99999",  # Транзакция с таким ID не существует
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка, что транзакция не найдена
    assert response.status_code == 404
    assert "detail" in response.json()
    assert response.json()["detail"] == "Транзакция для этой книги и пользователя не найдена."

# Получение транзакций пользователя как администратор
def test_get_user_transactions_as_admin(db, admin_user, testuser, test_transactions):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Запрос транзакций для тестового пользователя
    response = client.get(
        f"/transactions/transactions/{testuser.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверяем успешное выполнение запроса
    assert response.status_code == 200
    response_data = response.json()

    # Логирование для отладки
    print("Response status:", response.status_code)
    print("Response body:", response.json())

    # Проверяем количество транзакций
    assert len(response_data) == len(test_transactions)

    # Сравниваем данные транзакций
    for txn, expected_txn in zip(response_data, test_transactions):
        assert txn["id"] == expected_txn.transaction_id
        assert txn["book_id"] == expected_txn.book_id
        assert txn["loan_date"] == expected_txn.loan_date.isoformat()
        assert txn["return_date"] == (expected_txn.return_date.isoformat() if expected_txn.return_date else None)


# Получение транзакций пользователя как обычный пользователь
def test_get_user_transactions_as_user(db, testuser, test_transactions):
    # Аутентификация пользователя
    token = authenticate_user(client, "testuser", "testpassword")

    # Запрос своих транзакций
    response = client.get(
        f"/transactions/transactions/{testuser.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверяем успешное выполнение запроса
    assert response.status_code == 200
    response_data = response.json()

    # Проверяем количество транзакций
    assert len(response_data) == len(test_transactions)

    # Сравниваем данные транзакций
    for txn, expected_txn in zip(response_data, test_transactions):
        assert txn["id"] == expected_txn.transaction_id
        assert txn["book_id"] == expected_txn.book_id
        assert txn["loan_date"] == expected_txn.loan_date.isoformat()
        assert txn["return_date"] == (expected_txn.return_date.isoformat() if expected_txn.return_date else None)

# Пользователь пытается получить доступ к чужим транзакциям
def test_unauthorized_user_access(db, testuser, admin_user):
    # Аутентификация пользователя
    token = authenticate_user(client, "testuser", "testpassword")

    # Попытка пользователя получить транзакции другого пользователя
    response = client.get(
        f"/transactions/transactions/{admin_user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка на отказ в доступе
    assert response.status_code == 403
    assert response.json()["detail"] == "Требуется роль администратора для выполнения этого действия."

# Проверка отсутствия транзакций у пользователя
def test_no_transactions_found(db, admin_user):
    # Аутентификация администратора
    token = authenticate_user(client, "admin", "adminpassword")

    # Запрос транзакций для пользователя без транзакций
    response = client.get(
        "/transactions/transactions/non-existent-user-id",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Проверка, что транзакции не найдены
    assert response.status_code == 404
    assert response.json()["detail"] == "Транзакции пользователя не найдены."
