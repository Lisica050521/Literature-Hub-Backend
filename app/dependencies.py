from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import verify_auth_token

# Создаем схему для извлечения токена из заголовка
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для получения текущего пользователя
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    # Используем verify_auth_token для декодирования токена и получения пользователя
    user = verify_auth_token(token, db)

    # Проверяем, найден ли пользователь
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user