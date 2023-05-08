# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

import asyncio
import io

from dependencies import authenticate_user, get_current_user
from diffusion_service import DiffusionService
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi import status as http_status
from fastapi.responses import HTMLResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from models import ArtCreate, Token
from PIL import Image
from utils import download_image, upload_image

from config import settings


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    debug=settings.debug,
)

service = DiffusionService(
    model_name=settings.model_name,
    task=settings.task,
    dtype=settings.model_precision,
    n_steps=settings.n_steps,
    max_batch_size=settings.max_batch_size,
    max_wait=settings.max_wait,
)


@app.on_event("startup")
async def startup_event():
    logger.debug("Starting up...")
    asyncio.create_task(service.runner())


@app.get("/", tags=["status"])
async def health_check():
    """Health check endpoint"""
    split_description = settings.description.split(".")
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
            <p class="mt-2 text-gray-600">{split_description[0]}</p>
            <p class="text-gray-600">{split_description[1]}</p>
            <p class="mt-8 text-gray-500">Want access? Contact me: <a class="text-blue-400 text-underlined" href="mailto:t.chaigneau.tc@gmail.com?subject=Access">t.chaigneau.tc@gmail.com</a></p>
            <p class="mt-8">👇</p>
            <a href="/docs">
                <button class="mt-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Docs</button>
            </a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=content, media_type="text/html")


@app.post(
    f"{settings.api_prefix}/generate",
    tags=["generate"],
    status_code=http_status.HTTP_200_OK,
)
async def generate(
    data: ArtCreate,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),  # for authentication purposes
):
    """Generate an image from a prompt or an image url, or both."""
    image = None
    if data.image:
        img_bytes = await download_image(data.image)
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    if data.prompt and image:
        res = await service.process_input(prompt=data.prompt, image=image)
    elif data.prompt:
        res = await service.process_input(prompt=data.prompt)
    elif image:
        res = await service.process_input(image=image)
    else:
        raise HTTPException(status_code=400, detail="Please provide a prompt or an image URL.")

    if isinstance(res, ValueError):
        return Response(content=res.args[0], media_type="text/plain")

    elif isinstance(res, Image.Image):
        with io.BytesIO() as buffer:
            res.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()

        if settings.using_s3:
            background_tasks.add_task(upload_image, img_bytes.getvalue())

        return Response(content=img_bytes, media_type="image/png")

    else:
        raise ValueError(f"Unknown type {type(res)}")


@app.post(
    f"{settings.api_prefix}/auth",
    response_model=Token,
    tags=["authentication"],
    status_code=http_status.HTTP_200_OK,
)
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

    uvicorn.run("main:app", host="0.0.0.0", port=7681, reload=True)
