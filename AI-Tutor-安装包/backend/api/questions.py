from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from models.user import User
from schemas.question import QuestionCreate, QuestionDetailResponse, QuestionUpdate
from services.auth_service import get_current_user
from services.question_service import (
    create_question,
    delete_question,
    get_question_by_id,
    list_questions,
    update_question,
)

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("", response_model=QuestionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_question_endpoint(
    payload: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await create_question(db, current_user.id, payload)
    return question


@router.get("", response_model=list[QuestionDetailResponse])
async def list_questions_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    questions = await list_questions(db, current_user.id, skip=skip, limit=limit)
    return questions


@router.get("/{question_id}", response_model=QuestionDetailResponse)
async def get_question_endpoint(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await get_question_by_id(db, question_id, current_user.id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question


@router.put("/{question_id}", response_model=QuestionDetailResponse)
async def update_question_endpoint(
    question_id: int,
    payload: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await get_question_by_id(db, question_id, current_user.id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return await update_question(db, question, payload)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question_endpoint(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await get_question_by_id(db, question_id, current_user.id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    await delete_question(db, question)
