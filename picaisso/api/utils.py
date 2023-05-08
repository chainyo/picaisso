# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

import uuid

import aiohttp
from aiobotocore.session import get_session
from models import ArtCreate

from config import settings


async def upload_image(img_bytes: bytes, data: ArtCreate):
    session = get_session()
    async with session.create_client(
        "s3",
        region_name=settings.region_name,
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
    ) as client:
        img_key = f"{data.author}/{uuid.uuid4()}_{data.prompt}.jpg"
        await client.put_object(
            Bucket=settings.bucket_name,
            Key=img_key,
            Body=img_bytes,
            ContentType="image/jpeg",
        )


async def download_image(url: str) -> bytes:
    """
    Download image from url.

    Args:
        url (str): image url

    Returns:
        bytes: image bytes
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            image_data = await response.read()

    return image_data
