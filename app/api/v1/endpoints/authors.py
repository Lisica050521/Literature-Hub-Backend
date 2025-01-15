from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_authors():
    return {"message": "List of authors"}