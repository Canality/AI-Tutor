from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from models.user import User
from schemas.auth import RegisterRequest
from utils.config import settings
from utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    logger.info(
        f"[密码验证] 原始密码: {repr(plain_password)}, 字节数: {len(plain_password.encode('utf-8'))}")
    
    # bcrypt 检查
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    result = bcrypt.checkpw(plain_bytes, hashed_bytes)
    logger.info(f"[密码验证] 验证结果: {'成功' if result else '失败'}")
    return result


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    logger.info(f"[密码哈希] 收到的原始密码: {repr(password)}, 字节数: {len(password.encode('utf-8'))}")
    
    # bcrypt 自动生成 salt 并哈希
    password_bytes = password.encode('utf-8')
    # bcrypt 会自动处理超过72字节的情况
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    password_hash = hashed.decode('utf-8')
    logger.info(f"[密码哈希] 生成的哈希值: {password_hash}")
    return password_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    logger.info(f"[Token生成] 生成的token: {token}")
    return token


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    logger.info(f"[注册用户] 收到注册请求，用户名: {payload.username}")

    existing_user = await get_user_by_username(db, payload.username)
    if existing_user:
        logger.warning(f"[注册用户] 用户名已存在: {payload.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    password_hash = get_password_hash(payload.password)
    logger.info(f"[注册用户] 密码哈希生成成功")

    user = User(
        username=payload.username,
        email=None,
        password_hash=password_hash,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info(f"[注册用户] 用户创建成功，用户ID: {user.id}")
    return user


async def authenticate_user(
        db: AsyncSession, username: str, password: str
) -> Optional[User]:
    logger.info(f"[用户认证] 收到认证请求，用户名: {username}")
    user = await get_user_by_username(db, username)
    if not user:
        logger.warning(f"[用户认证] 用户不存在: {username}")
        return None
    if not verify_password(password, user.password_hash):
        logger.warning(f"[用户认证] 密码验证失败，用户名: {username}")
        return None
    logger.info(f"[用户认证] 用户认证成功，用户名: {username}")
    return user


async def get_current_user(
        token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = await get_user_by_username(db, username)
    if user is None:
        raise credentials_exception

    return user
