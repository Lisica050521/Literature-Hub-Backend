from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.models.user import User
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция для проверки пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Функция для хеширования пароля
def hash_password(password):
    return pwd_context.hash(password)

# Функция для проверки учетных данных пользователя
def verify_user_credentials(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Генерация токена авторизации
def generate_auth_token(data: dict, expires_delta: timedelta | None = None):
    user_id = data.get("user_id")
    role = data.get("role")
    
    if expires_delta is None:
        expires_delta = timedelta(minutes=15)

    to_encode = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Функция для проверки и извлечения пользователя по токену
def verify_auth_token(token: str, db: Session):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        role = payload.get("role")
    except jwt.exceptions.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user