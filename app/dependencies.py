from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.utils import decode_jwt

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
    # Декодируем JWT токен и извлекаем ID пользователя
    user_id = decode_jwt(token)

    # Ищем пользователя в базе данных по ID
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user