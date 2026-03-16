from fastapi import APIRouter

router = APIRouter(prefix="/upload")


@router.post("/image")
async def upload_image():
    return {"message": "Upload image endpoint"}
