# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

from os import getenv
from dotenv import load_dotenv

from pydantic import BaseSettings


class Settings(BaseSettings):
    # General
    project_name: str
    version: str
    description: str
    api_prefix: str
    debug: bool
    # Auth
    username: str
    password: str
    openssl_key: str
    algorithm: str
    # Model
    max_batch_size: int
    max_wait: int
    # S3
    bucket_name: str
    region_name: str
    access_key_id: str
    secret_access_key: str
    


load_dotenv()

settings = Settings(
    project_name=getenv("PROJECT_NAME"),
    version=getenv("VERSION"),
    description=getenv("DESCRIPTION"),
    api_prefix=getenv("API_PREFIX"),
    debug=getenv("DEBUG"),
    username=getenv("USERNAME"),
    password=getenv("PASSWORD"),
    openssl_key=getenv("OPENSSL_KEY"),
    algorithm=getenv("ALGORITHM"),
    max_batch_size=getenv("MAX_BATCH_SIZE"),
    max_wait=getenv("MAX_WAIT"),
    bucket_name=getenv("BUCKET_NAME"),
    region_name=getenv("REGION_NAME"),
    access_key_id=getenv("ACCESS_KEY_ID"),
    secret_access_key=getenv("SECRET_ACCESS_KEY"),
)