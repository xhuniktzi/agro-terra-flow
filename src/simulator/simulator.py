#!/usr/bin/env python3

import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
PUBLISH_INTERVAL = float(os.getenv("PUBLISH_INTERVAL_SECONDS", "5"))
STARTUP_DELAY = int(os.getenv("STARTUP_DELAY_SECONDS", "20"))
MQTT_TOPIC = "sensores/datos"

SENSOR_IDS = ["sensor-01", "sensor-02", "sensor-03"]

SENSOR_PROFILES = {
    "sensor-01": {"temp_range": (20, 32), "hum_range": (30, 85), "ph_range": (6.0, 7.5)},
    "sensor-02": {"temp_range": (22, 35), "hum_range": (25, 80), "ph_range": (6.2, 7.4)},
    "sensor-03": {"temp_range": (21, 33), "hum_range": (20, 75), "ph_range": (5.5, 7.0)},
}


def generate_reading(sensor_id: str) -> dict:
    profile = SENSOR_PROFILES[sensor_id]
    return {
        "sensor_id": sensor_id,
        "temperatura": round(random.uniform(*profile["temp_range"]), 2),
        "humedad": round(random.uniform(*profile["hum_range"]), 2),
        "ph": round(random.uniform(*profile["ph_range"]), 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Conectado al broker {MQTT_HOST}:{MQTT_PORT}")
    else:
        print(f"[MQTT] Fallo de conexión, código de retorno: {rc}")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[MQTT] Desconexión inesperada (rc={rc}). Reconectando...")


def main():
    print("=" * 60)
    print("  Simulador de sensores IoT — Agricultura de Precisión")
    print("=" * 60)
    print(f"  Broker  : {MQTT_HOST}:{MQTT_PORT}")
    print(f"  Sensores: {', '.join(SENSOR_IDS)}")
    print(f"  Intervalo: {PUBLISH_INTERVAL}s | Delay inicio: {STARTUP_DELAY}s")
    print("=" * 60)

    if STARTUP_DELAY > 0:
        print(f"[Simulador] Esperando {STARTUP_DELAY}s para que el procesador "
              "inicialice el stream de JetStream en NATS...")
        time.sleep(STARTUP_DELAY)

    client = mqtt.Client(client_id="simulador-iot", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            break
        except Exception as exc:
            print(f"[Simulador] No se pudo conectar al broker: {exc}. "
                  "Reintentando en 5s...")
            time.sleep(5)

    client.loop_start()

    print("[Simulador] Publicando lecturas. Ctrl-C para detener.\n")

    try:
        while True:
            for sensor_id in SENSOR_IDS:
                reading = generate_reading(sensor_id)
                payload = json.dumps(reading)
                result = client.publish(MQTT_TOPIC, payload, qos=1)

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(
                        f"[{reading['sensor_id']}] "
                        f"T={reading['temperatura']:5.1f}°C  "
                        f"H={reading['humedad']:5.1f}%  "
                        f"pH={reading['ph']:.2f}  "
                        f"ts={reading['timestamp']}"
                    )
                else:
                    print(f"[{sensor_id}] Error al publicar (rc={result.rc})")

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print("\n[Simulador] Detenido por el usuario.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
