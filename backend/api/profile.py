from fastapi import APIRouter

router = APIRouter(prefix="/profile")


@router.get("/")
async def get_profile():
    return {"message": "Get profile endpoint"}


@router.put("/")
async def update_profile():
    return {"message": "Update profile endpoint"}
