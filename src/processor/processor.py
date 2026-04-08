#!/usr/bin/env python3

import asyncio
import json
import os
import pickle
import sys
import time

import nats
import nats.js.errors
import psycopg2
import numpy as np
from sklearn.ensemble import RandomForestClassifier

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "agriculture")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "")
MODEL_PATH = os.getenv("MODEL_PATH", "/tmp/model.pkl")

STREAM_NAME = "iot-data"
STREAM_SUBJECT = "sensores.>"
CONSUMER_NAME = "processor-group"


def train_model() -> RandomForestClassifier:
    print("[Modelo] Generando 2 000 muestras sintéticas de entrenamiento...")
    rng = np.random.default_rng(42)
    n = 2_000

    temperatura = rng.uniform(15, 38, n)
    humedad = rng.uniform(15, 95, n)
    ph = rng.uniform(5.0, 8.0, n)

    etiquetas = ((humedad < 40) | ((humedad < 60) & (temperatura > 28))).astype(int)

    idx_ruido = rng.choice(n, size=int(n * 0.05), replace=False)
    etiquetas[idx_ruido] = 1 - etiquetas[idx_ruido]

    X = np.column_stack([temperatura, humedad, ph])

    modelo = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    modelo.fit(X, etiquetas)

    acc = modelo.score(X, etiquetas)
    print(f"[Modelo] Entrenado — precisión en entrenamiento: {acc:.3f}")
    return modelo


def load_or_train_model() -> RandomForestClassifier:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            modelo = pickle.load(f)
        print(f"[Modelo] Cargado desde {MODEL_PATH}")
        return modelo

    modelo = train_model()
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(modelo, f)
    print(f"[Modelo] Guardado en {MODEL_PATH}")
    return modelo


def connect_db() -> psycopg2.extensions.connection:
    for intento in range(12):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                user=DB_USER, password=DB_PASS,
                connect_timeout=5,
            )
            print("[DB] Conectado a TimescaleDB")
            return conn
        except Exception as exc:
            print(f"[DB] No disponible ({exc}). Reintentando ({intento + 1}/12) en 5s...")
            time.sleep(5)
    print("[DB] No se pudo conectar. Abortando.")
    sys.exit(1)


def insertar_lectura(
    conn: psycopg2.extensions.connection,
    lectura: dict,
    necesita_riego: bool,
    confianza: float,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sensor_readings
                (time, sensor_id, temperatura, humedad, ph,
                 necesita_riego, prediccion_confianza)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                lectura["timestamp"],
                lectura["sensor_id"],
                float(lectura["temperatura"]),
                float(lectura["humedad"]),
                float(lectura["ph"]),
                necesita_riego,
                round(confianza, 4),
            ),
        )
    conn.commit()


def hacer_prediccion(modelo, lectura: dict) -> tuple[bool, float]:
    X = np.array([[lectura["temperatura"], lectura["humedad"], lectura["ph"]]])
    proba = modelo.predict_proba(X)[0]
    necesita_riego = bool(proba[1] >= 0.5)
    confianza = float(max(proba))
    return necesita_riego, confianza


async def procesar_mensaje(msg, modelo, db_conn):
    try:
        lectura = json.loads(msg.data.decode("utf-8"))

        for campo in ("sensor_id", "temperatura", "humedad", "ph", "timestamp"):
            if campo not in lectura:
                raise ValueError(f"Campo faltante: {campo}")

        necesita_riego, confianza = hacer_prediccion(modelo, lectura)
        insertar_lectura(db_conn, lectura, necesita_riego, confianza)

        estado = "RIEGO ⚠" if necesita_riego else "OK   ✓"
        print(
            f"[{lectura['sensor_id']}] "
            f"T={lectura['temperatura']:5.1f}°C  "
            f"H={lectura['humedad']:5.1f}%  "
            f"pH={lectura['ph']:.2f}  "
            f"→ {estado}  conf={confianza:.2f}"
        )

        await msg.ack()

    except json.JSONDecodeError as exc:
        print(f"[Procesador] JSON inválido: {exc}")
        await msg.nak()
    except Exception as exc:
        print(f"[Procesador] Error procesando mensaje: {exc}")
        await msg.nak()


async def main():
    print("=" * 60)
    print("  Procesador de streaming — Agricultura de Precisión")
    print("=" * 60)

    modelo = load_or_train_model()

    db_conn = connect_db()

    nc = None
    for intento in range(12):
        try:
            nc = await nats.connect(
                NATS_URL,
                max_reconnect_attempts=5,
                reconnect_time_wait=2,
            )
            print(f"[NATS] Conectado a {NATS_URL}")
            break
        except Exception as exc:
            print(f"[NATS] No disponible ({exc}). Reintentando ({intento + 1}/12) en 5s...")
            await asyncio.sleep(5)

    if nc is None:
        print("[NATS] No se pudo conectar. Abortando.")
        sys.exit(1)

    js = nc.jetstream()

    try:
        info = await js.stream_info(STREAM_NAME)
        print(f"[JetStream] Stream '{STREAM_NAME}' ya existe "
              f"(mensajes almacenados: {info.state.messages})")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name=STREAM_NAME, subjects=[STREAM_SUBJECT])
        print(f"[JetStream] Stream '{STREAM_NAME}' creado (sujetos: {STREAM_SUBJECT})")

    async def handler(msg):
        await procesar_mensaje(msg, modelo, db_conn)

    sub = await js.subscribe(
        "sensores.datos",
        stream=STREAM_NAME,
        durable=CONSUMER_NAME,
        cb=handler,
        manual_ack=True,
    )

    print(f"[Procesador] Escuchando mensajes en '{STREAM_NAME}/sensores.datos'...\n")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n[Procesador] Deteniendo...")
    finally:
        await sub.unsubscribe()
        await nc.drain()
        db_conn.close()
        print("[Procesador] Cerrado limpiamente.")


if __name__ == "__main__":
    asyncio.run(main())
