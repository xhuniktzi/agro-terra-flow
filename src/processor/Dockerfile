FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY processor.py .

ENV NATS_URL=nats://nats:4222 \
    DB_HOST=timescaledb \
    DB_PORT=5432 \
    DB_NAME=agriculture \
    DB_USER=admin \
    DB_PASS="" \
    MODEL_PATH=/tmp/model.pkl

CMD ["python", "processor.py"]
