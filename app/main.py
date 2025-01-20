import logging
from fastapi import FastAPI, HTTPException
from app.api.v1.endpoints import literature_items, authors, users, auth_portal, transactions
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание всех таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Инициализация FastAPI приложения
app = FastAPI(title="Literature Hub API", version="1.0.0")

# Подключение роутеров
app.include_router(auth_portal.router, prefix="/auth", tags=["Authentication"])
app.include_router(literature_items.router, prefix="/literature", tags=["Literature Items"])
app.include_router(authors.router, prefix="/authors", tags=["Authors"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])

@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to the Literature Hub API!"}

# Логирование ошибок в транзакциях:
@app.post("/transactions/")
async def create_transaction(transaction_data: dict):
    try:
        logger.info(f"Transaction creation request: {transaction_data}")
        return {"message": "Transaction created successfully!"}
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Transaction creation failed")