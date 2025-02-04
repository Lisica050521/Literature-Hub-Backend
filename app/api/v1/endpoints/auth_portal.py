from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.security import verify_user_credentials, generate_auth_token
from app.core.config import settings
from app.schemas.auth_token import AuthToken
from app.schemas.login import LoginRequest
from app.dependencies import get_db

router = APIRouter()

# Аутентификация пользователя.
@router.post("/login", response_model=AuthToken)
def authenticate_user(login_data: LoginRequest, db: Session = Depends(get_db)):

    # Проверяем, что имя пользователя и пароль не пустые
    if not login_data.username or not login_data.password:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )

    user = verify_user_credentials(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )
    token_lifespan = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = generate_auth_token(
        data={"user_id": user.id, "role": user.role},
        expires_delta=token_lifespan
    )
    return {"access_token": access_token, "token_type": "bearer"}