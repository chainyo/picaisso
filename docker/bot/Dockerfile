FROM python:3.10-slim as python-base

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential

COPY docker/bot/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY picaisso/bot/main.py /app/main.py
COPY config/bot/.env /app/.env
WORKDIR /app

ENTRYPOINT [ "python", "main.py"]
