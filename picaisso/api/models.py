# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

from typing import Optional

from pydantic import BaseModel


class ArtCreate(BaseModel):
    """ArtCreate model"""

    prompt: Optional[str] = None
    image: Optional[str] = None
    author: str

    class Config:
        """ArtCreate model config"""

        schema_extra = {
            "example": {
                "prompt": "A beautiful image of a cat",
                "image": "https://cdn.pixabay.com/photo/2017/02/20/18/03/cat-2083492_1280.jpg",
                "author": "Thomas Chaigneau",
            }
        }


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
