from fastapi import FastAPI
from app.api.v1.endpoints import literature_items, authors, users, auth_portal, transactions
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Literature Hub API", version="1.0.0")

app.include_router(auth_portal.router, prefix="/auth", tags=["Authentication"])
app.include_router(literature_items.router, prefix="/literature", tags=["Literature Items"])
app.include_router(authors.router, prefix="/authors", tags=["Authors"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])

@app.get("/")
def root():
    return {"message": "Welcome to the Literature Hub API!"}