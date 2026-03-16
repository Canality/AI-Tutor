from fastapi import APIRouter

router = APIRouter(prefix="/auth")


@router.post("/register")
async def register():
    return {"message": "Register endpoint"}


@router.post("/login")
async def login():
    return {"message": "Login endpoint"}


@router.get("/me")
async def get_current_user():
    return {"message": "Get current user endpoint"}
