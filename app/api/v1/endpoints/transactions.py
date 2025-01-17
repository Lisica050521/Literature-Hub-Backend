from fastapi import APIRouter, HTTPException, Depends, status
from fastapi import Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.literature_item import LiteratureItem
from app.dependencies import get_current_user
from app.models.user import User
from datetime import datetime

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
@router.post("/issue/{book_id}")
async def issue_book(
    book_id: int,  # только book_id в URL
    user: dict = Body(...),  # теперь user_id приходит как часть тела запроса
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Только администратор может выдавать
):
    user_id = user["user_id"]  # Извлекаем user_id из тела запроса

    # Проверка, что администратор не выдает книгу себе
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор может выдать книгу только читателю."
        )

    # Проверка, что книга доступна для выдачи
    book = db.query(LiteratureItem).filter(LiteratureItem.id == book_id, LiteratureItem.available_copies > 0).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена или отсутствуют доступные экземпляры."
        )

    # Проверка, что пользователь не превысил лимит в 5 книг
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

    # Уменьшаем количество доступных экземпляров книги
    book.available_copies -= 1
    db.commit()

    return {"message": "Книга выдана", "transaction_id": transaction.id, "due_date": transaction.due_date}

# Эндпоинт для возврата книги, доступен только администратору
@router.post("/return/{transaction_id}")
async def return_book(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Админ проверяет роль
):
    # Найти транзакцию по id
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена."
        )

    # Проверить, что книга уже не была возвращена
    if transaction.return_date is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Книга уже была возвращена."
        )

    # Обновить дату возврата
    transaction.return_date = datetime.utcnow()
    db.commit()
    db.refresh(transaction)

    # Увеличиваем количество доступных экземпляров книги
    book = db.query(LiteratureItem).filter(LiteratureItem.id == transaction.literature_item_id).first()
    if book:
        book.available_copies += 1
        db.commit()

    return {"message": "Книга возвращена", "transaction_id": transaction.id}

# Эндпоинт для получения транзакций пользователя
@router.get("/transactions")
async def get_user_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Здесь доступ только для текущего пользователя
):
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    return {
        "transactions": [
            {
                "book_id": transaction.literature_item_id,
                "loan_date": transaction.loan_date,
                "return_date": transaction.return_date
            }
            for transaction in transactions
        ]
    }