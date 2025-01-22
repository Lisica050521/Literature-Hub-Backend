import jwt
from passlib.context import CryptContext
from fastapi import HTTPException
from app.core.config import settings

# Создаем контекст для работы с паролями
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция для хеширования пароля
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Функция для декодирования JWT токена
def decode_jwt(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403, detail="Token does not contain 'sub' claim")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")