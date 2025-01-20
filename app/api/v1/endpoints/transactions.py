from fastapi import APIRouter, HTTPException, Depends, status
from fastapi import Body
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
from typing import List
from app.core.logging import logger

router = APIRouter()

# Функция для проверки, является ли пользователь администратором
def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":  # Проверяем роль пользователя
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль администратора для выполнения этого действия."
        )
    return current_user

# Эндпоинт для выдачи книги пользователю (только для администраторов)
@router.post("/issue/{book_id}", response_model=IssueBookResponse)
async def issue_book(
    book_id: int, 
    user: dict = Body(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user_id = user["user_id"]

    # Администратор не может выдать книгу себе или другому администратору
    user_obj = db.query(User).filter(User.id == user_id).first()
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден."
        )
    if current_user.id == user_id or user_obj.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор может выдать книгу только читателю."
        )

    # Проверка наличия доступных экземпляров книги
    book = db.query(LiteratureItem).filter(LiteratureItem.id == book_id, LiteratureItem.available_copies > 0).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена или отсутствуют доступные экземпляры."
        )

    # Проверка, что пользователь имеет менее 5 невозвращенных книг
    user_transactions = db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.return_date == None).all()
    if len(user_transactions) >= 5:
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

# Эндпоинт для возврата книги, доступен только администратору
@router.post("/return/{transaction_id}", response_model=ReturnBookResponse)
async def return_book(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Получаем транзакцию по ID
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    # Если транзакция не найдена
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция для этой книги и пользователя не найдена."
        )

    # Проверка, что книга уже была возвращена
    if transaction.return_date is not None:
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

# Эндпоинт для получения транзакций пользователя. Доступен как админу так и читателю
@router.get("/transactions", response_model=List[TransactionResponse])
async def get_user_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # Здесь доступ только для текущего пользователя
    user_id: int = None  # Параметр для администратора, который может указать другого пользователя
):
    # Если это администратор и передан user_id, ищем транзакции для другого пользователя
    if current_user.role == "admin" and user_id:
        transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    else:
        # Если это читатель, то показываем только его транзакции
        transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()

    return [
        TransactionResponse.from_orm(transaction)
        for transaction in transactions
    ]