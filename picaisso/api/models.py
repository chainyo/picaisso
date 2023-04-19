# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

from pydantic import BaseModel


class ArtCreate(BaseModel):
    """ArtCreate model"""
    prompt: str
    author: str


class Image(BaseModel):
    """Image model"""
    content: bytes
    

class SignedUrl(BaseModel):
    """SignedUrl model"""
    url: str


class Token(BaseModel):
    """Token model"""
    access_token: str
    token_type: str
    

class TokenData(BaseModel):
    """TokenData model"""
    username: str = None
