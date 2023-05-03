# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

from os import getenv
from typing import Optional, Union

from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, validator
from pydantic.dataclasses import dataclass


@dataclass
class Settings:
    # General Configuration
    project_name: str
    version: str
    description: str
    api_prefix: str
    debug: bool
    # Authentication
    username: str
    password: str
    openssl_key: str
    algorithm: str
    # Model Configuration
    max_batch_size: int
    max_wait: float
    model_name: str
    model_precision: str
    n_steps: int
    # S3 Configuration
    bucket_name: Optional[str] = None
    region_name: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    using_s3: bool = Field(init=False)

    @validator("username", "password", "openssl_key", "algorithm")
    def authentication_parameters_must_not_be_none(cls, value: str, field: str):
        """Check that the authentication parameters are not None."""
        if value is None:
            raise ValueError(f"{field.name} must not be None, please verify the `config/api/.env` file.")
        return value

    @validator("max_batch_size", "max_wait", "n_steps")
    def model_parameters_must_be_positive(cls, value: Union[int, float], field: str):
        """Check that the model parameters are positive."""
        if value <= 0:
            raise ValueError(f"{field.name} must be positive.")
        return value

    @validator("username", "password")
    def authentication_parameters_must_not_be_default(cls, value: str, field: str):
        """Check that the authentication parameters are not the default ones."""
        if value == "admin" or value == "password" or value == "change_me_for_something_more_secure":
            raise ValueError(f"{field.name} must not be the default one, please verify the `config/api/.env` file.")
        return value

    @validator("openssl_key")
    def openssl_key_must_not_be_default(cls, value: str):
        """Check that the openssl key is not the default one."""
        if value == "1234567890abcdef":
            raise ValueError(f"openssl_key must not be the default one, please verify the `config/api/.env` file.")
        return value

    @validator("model_precision")
    def model_precision_must_be_valid(cls, value: str):
        """Check that the model precision is valid."""
        if value not in {"fp16", "fp32", "bf16"}:
            raise ValueError("model_precision must be either `fp16`, `fp32` or `bf16`.")
        return value

    def __post_init__(self):
        """Post init hook."""
        self.using_s3 = all([self.bucket_name, self.region_name, self.access_key_id, self.secret_access_key])

        if self.using_s3:
            logger.warning("S3 credentials are set, the S3 storage will be used.")
        else:
            logger.warning("S3 credentials are not set, the S3 storage will not be used.")


load_dotenv()

settings = Settings(
    project_name=getenv("PROJECT_NAME", "PicAIsso"),
    version=getenv("VERSION", "1.0.0"),
    description=getenv(
        "DESCRIPTION", "🎨 Imagine what Picasso could have done with AI. Self-host your StableDiffusion API."
    ),
    api_prefix=getenv("API_PREFIX", "/api/v1"),
    debug=getenv("DEBUG", True),
    username=getenv("USERNAME", None),
    password=getenv("PASSWORD", None),
    openssl_key=getenv("OPENSSL_KEY", None),
    algorithm=getenv("ALGORITHM", "HS256"),
    max_batch_size=getenv("MAX_BATCH_SIZE", 1),
    max_wait=getenv("MAX_WAIT", 0.5),
    model_name=getenv("MODEL_NAME", "prompthero/openjourney"),
    model_precision=getenv("MODEL_PRECISION", "fp16"),
    n_steps=getenv("N_STEPS", 50),
    bucket_name=getenv("BUCKET_NAME", None),
    region_name=getenv("REGION_NAME", None),
    access_key_id=getenv("ACCESS_KEY_ID", None),
    secret_access_key=getenv("SECRET_ACCESS_KEY", None),
)
