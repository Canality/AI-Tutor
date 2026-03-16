from fastapi import APIRouter

router = APIRouter(prefix="/exercises")


@router.get("/recommend")
async def get_recommended_exercises():
    return {"message": "Recommend exercises endpoint"}


@router.get("/plan")
async def get_study_plan():
    return {"message": "Study plan endpoint"}
