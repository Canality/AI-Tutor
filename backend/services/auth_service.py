from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from models.user import User
from schemas.auth import RegisterRequest
from utils.config import settings
from utils.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码（同步截断+详细日志）"""
    # 新增日志：打印验证时的原始密码
    logger.info(
        f"[密码验证] 原始密码: {repr(plain_password)}, 字符数: {len(plain_password)}, 字节数: {len(plain_password.encode('utf-8'))}")

    # 截断逻辑（和哈希时保持一致）
    plain_password_truncated = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    logger.info(f"[密码验证] 截断后密码: {repr(plain_password_truncated)}")

    result = pwd_context.verify(plain_password_truncated, hashed_password)
    logger.info(f"[密码验证] 验证结果: {'成功' if result else '失败'}")
    return result


def get_password_hash(password: str) -> str:
    """生成密码哈希（截断+详细日志）"""
    # 关键日志1：打印原始密码的所有细节（repr能显示隐藏字符）
    logger.info(f"[密码哈希] 收到的原始密码: {repr(password)}")
    logger.info(f"[密码哈希] 原始密码字符数: {len(password)}")
    logger.info(f"[密码哈希] 原始密码字节数: {len(password.encode('utf-8'))}")

    # 关键修复：截断密码到72字节（bcrypt最大支持长度）
    password_truncated = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

    # 关键日志2：打印截断后的密码
    logger.info(f"[密码哈希] 截断后密码: {repr(password_truncated)}")
    logger.info(f"[密码哈希] 截断后字节数: {len(password_truncated.encode('utf-8'))}")

    # 生成哈希
    password_hash = pwd_context.hash(password_truncated)
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
    # 关键日志1：打印注册接口收到的完整payload
    logger.info(f"[注册用户] 收到注册请求，完整payload: {payload.dict()}")
    logger.info(f"[注册用户] 收到的用户名: {payload.username}")
    logger.info(f"[注册用户] 收到的密码（repr）: {repr(payload.password)}")
    logger.info(f"[注册用户] 收到的密码字节数: {len(payload.password.encode('utf-8'))}")

    existing_user = await get_user_by_username(db, payload.username)
    if existing_user:
        logger.warning(f"[注册用户] 用户名已存在: {payload.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    password_hash = get_password_hash(payload.password)
    logger.info(f"[注册用户] 最终存储的密码哈希: {password_hash}")

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
    logger.info(f"[用户认证] 收到认证请求，用户名: {username}, 密码: {repr(password)}")
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