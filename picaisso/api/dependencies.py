# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

from datetime import datetime, timedelta
from loguru import logger
from typing import Union

from fastapi import Depends, HTTPException
from fastapi import status as http_status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt

from config import settings
from models import TokenData


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth")


def _get_username() -> str:
    return settings.username


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Create access token for user"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else :
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, settings.openssl_key, algorithm=settings.algorithm)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    credentials: str = Depends(_get_username),
) -> str:
    """Get current user"""
    credentials_exception = HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.openssl_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except JWTError:
        raise credentials_exception

    if token_data.username != credentials:
        raise credentials_exception

    return username


async def authenticate_user(username: str, password: str) -> dict:
    """Authenticate user"""
    if username != settings.username or password != settings.password:
        
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=1440)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    logger.debug(f"Generate access token!")
    
    return {"access_token": access_token, "token_type": "bearer"}
