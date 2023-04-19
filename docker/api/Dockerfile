FROM nvcr.io/nvidia/pytorch:22.01-py3

COPY docker/api/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN pip install --ignore-installed uvicorn==0.20.0

COPY picaisso/api /app/api
COPY config/api/.env /app/.env
WORKDIR /app

ENTRYPOINT ["python", "api/main.py"]
