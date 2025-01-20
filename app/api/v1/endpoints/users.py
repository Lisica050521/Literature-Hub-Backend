from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.schemas import UserCreate
from app.schemas.user import UserUpdate
from app.schemas.user import UserListResponse, UserResponse
from app.utils import hash_password
from app.core.config import settings
from jose import jwt, JWTError

# Создаем роутер для обработки запросов, связанных с пользователями
router = APIRouter()

# Для получения токена из заголовков запроса
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def hash_password(password: str):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

# Функция для извлечения текущего пользователя из токена
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Функция для проверки роли администратора
def admin_required(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Требуется роль администратора."
        )
    return current_user

@router.post("/")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User created", "user": db_user}

@router.get("/", response_model=UserListResponse)
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    users = db.query(User).all()
    return UserListResponse(users=[UserResponse.from_orm(user) for user in users])

# Обновление информации текущего пользователя
@router.put("/me")
async def update_user_info(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Получаем текущего пользователя из базы
    db_user = db.query(User).filter(User.id == current_user.id).first()
    
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    
    # Обновляем разрешенные поля
    if user_update.username:
        db_user.username = user_update.username
    if user_update.password:
        db_user.hashed_password = hash_password(user_update.password)
    
    db.commit()
    db.refresh(db_user)
    return {"message": "Информация обновлена", "user": {"username": db_user.username}}