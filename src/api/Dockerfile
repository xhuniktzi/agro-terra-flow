FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV DB_HOST=timescaledb \
    DB_PORT=5432 \
    DB_NAME=agriculture \
    DB_USER=admin \
    DB_PASS="" \
    MODEL_PATH=/tmp/model.pkl

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
