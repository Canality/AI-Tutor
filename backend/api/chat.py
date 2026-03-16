from fastapi import APIRouter

router = APIRouter(prefix="/chat")


@router.post("/ask")
async def ask_question():
    return {"message": "Ask endpoint"}


@router.post("/ask-stream")
async def ask_question_stream():
    return {"message": "Ask stream endpoint"}
