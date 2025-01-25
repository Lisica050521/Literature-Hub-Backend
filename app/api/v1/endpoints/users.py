from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.models import User
from app.utils import hash_password
from app.core.config import settings
from typing import Dict

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Временное хранилище для отслеживания контекста пользователя (можно заменить на Redis или базу данных).
user_registration_context: Dict[str, Dict] = {}

# Пароль для администратора.
ADMIN_PASSWORD = "1234567"

# Хэширование пароля.
def hash_password(password: str):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

# Первый шаг: пользователь вводит имя и пароль.
@router.post("/register/start")
async def start_registration(
    username: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Проверяем, существует ли пользователь с таким именем.
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Пользователь с таким именем уже существует"
        )

    # Сохраняем имя пользователя и пароль в контексте.
    user_registration_context[username] = {"password": password}
    return {"message": "Введите, кем вы хотите зарегистрироваться: читателем или администратором"}

# Второй шаг: пользователь выбирает роль.
@router.post("/register/choose_role")
async def choose_role(
    username: str = Form(...), 
    role_choice: str = Form(...),
    db: Session = Depends(get_db)
):
    # Проверяем, есть ли пользователь в контексте регистрации.
    if username not in user_registration_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Сначала нужно ввести имя пользователя и пароль"
        )

    # Сохраняем выбор роли.
    if role_choice not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Некорректный выбор роли"
        )
    
    user_registration_context[username]["role"] = role_choice

    # Если выбрана роль "admin", запрашиваем код.
    if role_choice == "admin":
        return {"message": "Введите код администратора для завершения регистрации"}
    
     # Если выбрана роль "user", завершаем регистрацию.
    hashed_password = hash_password(user_registration_context[username]["password"])
    db_user = User(username=username, hashed_password=hashed_password, role="user")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Удаляем пользователя из контекста.
    user_registration_context.pop(username, None)

    return {"message": "Регистрация завершена. Ваша роль: читатель"}

# Третий шаг: проверка кода администратора.
@router.post("/register/confirm_admin")
async def confirm_admin(
    username: str = Form(...), 
    admin_code: str = Form(...),
    db: Session = Depends(get_db)
):
    # Проверяем, есть ли пользователь в контексте регистрации.
    if username not in user_registration_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Сначала нужно ввести имя пользователя и пароль"
        )

    # Проверяем, выбрал ли пользователь роль "admin".
    if user_registration_context[username].get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Вы не выбирали роль администратора"
        )

    # Проверяем код администратора.
    if admin_code != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код администратора. Попробуйте снова"
        )

    # Если код правильный, создаём пользователя.
    hashed_password = hash_password(user_registration_context[username]["password"])
    db_user = User(username=username, hashed_password=hashed_password, role="admin")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Удаляем пользователя из контекста.
    user_registration_context.pop(username, None)

    return {"message": "Регистрация завершена. Ваша роль: администратор"}