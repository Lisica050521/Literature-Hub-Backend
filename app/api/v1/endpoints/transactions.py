import logging
from fastapi import APIRouter, HTTPException, Depends, status, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.literature_item import LiteratureItem
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.transactions import TransactionResponse
from app.schemas.transactions import IssueBookResponse
from app.schemas.transactions import ReturnBookResponse
from datetime import datetime
from typing import List, Optional
from app.core.logging import logger
from sqlalchemy import cast, UUID

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

router = APIRouter()

# Функция для проверки, является ли пользователь администратором.
def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль администратора для выполнения этого действия."
        )
    return current_user

# Выдача книги пользователю (только для администраторов).
@router.post("/issue/{book_id}", response_model=IssueBookResponse)
async def issue_book(
    book_id: int, 
    user: dict = Body(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user_id = user["user_id"]

    logger.info(f"Attempting to issue book ID {book_id} to user ID {user_id} by admin ID {current_user.id}")

    # Администратор выдает книгу только читателю.
    user_obj = db.query(User).filter(User.id == user_id).first()
    if not user_obj:
        logger.error(f"User ID {user_id} not found for book issue.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден."
        )
    if current_user.id == user_id or user_obj.role == "admin":
        logger.error(f"Admin cannot issue book to themselves or another admin: Admin ID {current_user.id}, User ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор может выдать книгу только читателю."
        )

    # Проверка наличия доступных экземпляров книги
    book = db.query(LiteratureItem).filter(LiteratureItem.id == book_id, LiteratureItem.available_copies > 0).first()
    if not book:
        logger.error(f"Book ID {book_id} not available for issue.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена или отсутствуют доступные экземпляры."
        )

    # Проверка, что пользователь имеет менее 5 невозвращенных книг
    user_transactions = db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.return_date == None).all()
    if len(user_transactions) >= 5:
        logger.error(f"User ID {user_id} already has 5 unreturned books.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже имеет 5 не возвращенных книг."
        )

    # Создание транзакции
    transaction = Transaction(user_id=user_id, literature_item_id=book.id)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Уменьшение количества доступных экземпляров книги
    book.available_copies -= 1
    db.commit()

    # Логирование успешной выдачи книги
    logger.info(f"Book issued: {book.title}, Transaction ID: {transaction.id}, User ID: {user_id}")

    return {"message": "Книга выдана", "transaction_id": transaction.id, "due_date": transaction.due_date}

# Возврат книги (только для администраторов).
@router.post("/return/{transaction_id}", response_model=ReturnBookResponse)
async def return_book(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Логируем начало обработки запроса возврата
    logger.info(f"Attempting to return book with Transaction ID {transaction_id} by Admin ID {current_user.id}")

    # Получаем транзакцию по ID
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    # Если транзакция не найдена
    if not transaction:
        logger.error(f"Transaction ID {transaction_id} not found for book return.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция для этой книги и пользователя не найдена."
        )

    # Проверка, что книга уже была возвращена
    if transaction.return_date is not None:
        logger.error(f"Book already returned: Transaction ID {transaction_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Книга уже была возвращена."
        )

    # Закрытие транзакции
    transaction.return_date = datetime.utcnow()
    db.commit()  # Сохраняем изменения
    db.refresh(transaction)

    # Увеличение доступных экземпляров книги
    book = db.query(LiteratureItem).filter(LiteratureItem.id == transaction.literature_item_id).first()
    if book:
        book.available_copies += 1
        db.commit()  # Сохраняем изменения в таблице книг

    # Логируем возврат
    logger.info(f"Book returned: {book.title}, Transaction ID: {transaction.id}, User ID: {transaction.user_id}")

    return {"message": "Книга возвращена", "transaction_id": transaction.id}

# Получение транзакций пользователя.
@router.get("/transactions/{user_id}", response_model=List[TransactionResponse])
async def get_user_transactions(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Admin ID {current_user.id} is fetching transactions for User ID {user_id if user_id else current_user.id}")

    # Если текущий пользователь не администратор и пытается получить данные другого пользователя
    if current_user.role != "admin" and current_user.id != user_id:
        logger.error(f"User {current_user.id} unauthorized to access transactions of User {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль администратора для выполнения этого действия."
        )

    # Получаем транзакции пользователя
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()

    if not transactions:
        logger.info(f"No transactions found for User {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакции пользователя не найдены."
        )

    # Логируем успешное получение транзакций
    logger.info(f"Transactions retrieved for User {user_id} by User {current_user.id}")

    # Возвращаем список транзакций
    return [TransactionResponse.from_orm(transaction) for transaction in transactions]