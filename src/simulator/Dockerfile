FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY simulator.py .

ENV MQTT_HOST=nats \
    MQTT_PORT=1883 \
    PUBLISH_INTERVAL_SECONDS=5 \
    STARTUP_DELAY_SECONDS=20

CMD ["python", "simulator.py"]
