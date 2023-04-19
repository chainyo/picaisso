# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

import asyncio
import io
from loguru import logger
from PIL import Image

from fastapi import BackgroundTasks, FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi import status as http_status
from fastapi.security import OAuth2PasswordRequestForm

from config import settings
from dependencies import get_current_user, authenticate_user
from diffusion_model import DiffusionService
from models import ArtCreate, SignedUrl, Token
from upload_s3 import upload_image


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    debug=settings.debug,
)

service = DiffusionService()


@app.on_event("startup")
async def startup_event():
    logger.debug("Starting up...")
    asyncio.create_task(service.runner())


@app.get("/", tags=["status"])
async def health_check():
    """Health check endpoint"""
    content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.project_name}</title>
        <link href="https://unpkg.com/tailwindcss@^2/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="h-screen mx-auto text-center flex min-h-full items-center justify-center bg-gray-100 text-gray-700">
        <div class="container mx-auto p-4">
            <h1 class="text-4xl font-medium">{settings.project_name}</h1>
            <p class="text-gray-600">Version: {settings.version}</p>
            <p class="text-gray-600">{settings.description}</p>
            <p class="mt-16 text-gray-500">Want access? Contact us: <a class="text-blue-400 text-underlined" href="mailto:t.chaigneau.tc@gmail.com?subject=Access">t.chaigneau.tc@gmail.com</a></p>
            <a href="/docs">
                <button class="mt-8 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Docs</button>
            </a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=content, media_type="text/html")


@app.post(
    f"{settings.api_prefix}/generate",
    tags=["generate"],
    response_model=SignedUrl,
    status_code=http_status.HTTP_200_OK
)
async def generate(
    data: ArtCreate,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),  # for authentication purposes
):
    out_img = await service.process_input(data.prompt)
    img_to_send = Image.fromarray((out_img * 255).astype("uint8"))
    with io.BytesIO() as buffer:
        img_bytes = img_to_send.save(buffer, format="JPEG")
        img_bytes = buffer.getvalue()
        
    background_tasks.add_task(upload_image, img_bytes, data)
    
    return Response(content=img_bytes, media_type="image/jpeg")
    

@app.post(f"{settings.api_prefix}/auth", response_model=Token, tags=["authentication"], status_code=http_status.HTTP_200_OK)
async def authentication(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Authenticate a user"""
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Authenticating user {form_data.username}")
    return user


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("main:app", host="0.0.0.0", port=7680, reload=True)
