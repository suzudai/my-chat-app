from fastapi import APIRouter

router = APIRouter()

@router.get("/data")
async def get_data():
    return {"message": "Hello from the new API"} 