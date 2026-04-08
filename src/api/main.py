#!/usr/bin/env python3

import os
import pickle
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "agriculture")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "")

MODEL_PATH = os.getenv("MODEL_PATH", "/tmp/model.pkl")


def _entrenar_modelo() -> RandomForestClassifier:
    rng = np.random.default_rng(42)
    n = 2_000
    temperatura = rng.uniform(15, 38, n)
    humedad = rng.uniform(15, 95, n)
    ph = rng.uniform(5.0, 8.0, n)
    etiquetas = ((humedad < 40) | ((humedad < 60) & (temperatura > 28))).astype(int)
    idx_ruido = rng.choice(n, size=int(n * 0.05), replace=False)
    etiquetas[idx_ruido] = 1 - etiquetas[idx_ruido]
    X = np.column_stack([temperatura, humedad, ph])
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X, etiquetas)
    return clf


def cargar_modelo() -> RandomForestClassifier:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    modelo = _entrenar_modelo()
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(modelo, f)
    return modelo


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
        connect_timeout=5,
    )


class LecturaInput(BaseModel):
    temperatura: float = Field(..., ge=0, le=60)
    humedad: float = Field(..., ge=0, le=100)
    ph: float = Field(..., ge=0, le=14)


class PrediccionResponse(BaseModel):
    necesita_riego: bool
    confianza: float
    interpretacion: str


modelo: RandomForestClassifier = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global modelo
    print("[API] Cargando modelo ML...")
    modelo = cargar_modelo()
    print("[API] Modelo listo.")
    yield
    print("[API] Apagando.")


app = FastAPI(
    title="API de Agricultura de Precisión",
    description=(
        "Interfaz REST para consultar lecturas de sensores IoT almacenadas en "
        "TimescaleDB y ejecutar predicciones de riego con el modelo RandomForest."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "api": "ok",
        "base_de_datos": "ok" if db_ok else "error",
        "modelo_cargado": modelo is not None,
    }


@app.get("/datos/recientes")
def datos_recientes(
    limite: int = Query(50, ge=1, le=500),
    sensor_id: Optional[str] = Query(None),
):
    try:
        conn = get_conn()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Base de datos no disponible: {exc}")

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if sensor_id:
                cur.execute(
                    """
                    SELECT time, sensor_id, temperatura, humedad, ph,
                           necesita_riego, prediccion_confianza
                    FROM sensor_readings
                    WHERE sensor_id = %s
                    ORDER BY time DESC
                    LIMIT %s
                    """,
                    (sensor_id, limite),
                )
            else:
                cur.execute(
                    """
                    SELECT time, sensor_id, temperatura, humedad, ph,
                           necesita_riego, prediccion_confianza
                    FROM sensor_readings
                    ORDER BY time DESC
                    LIMIT %s
                    """,
                    (limite,),
                )
            filas = cur.fetchall()
        conn.close()

        return {
            "total": len(filas),
            "lecturas": [dict(f) for f in filas],
        }
    except Exception as exc:
        conn.close()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/datos/estadisticas")
def estadisticas():
    try:
        conn = get_conn()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Base de datos no disponible: {exc}")

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    sensor_id,
                    COUNT(*) AS total_lecturas,
                    ROUND(AVG(temperatura)::numeric, 2) AS temp_promedio,
                    ROUND(MIN(temperatura)::numeric, 2) AS temp_min,
                    ROUND(MAX(temperatura)::numeric, 2) AS temp_max,
                    ROUND(AVG(humedad)::numeric, 2) AS humedad_promedio,
                    ROUND(MIN(humedad)::numeric, 2) AS humedad_min,
                    ROUND(MAX(humedad)::numeric, 2) AS humedad_max,
                    ROUND(AVG(ph)::numeric, 3) AS ph_promedio,
                    SUM(necesita_riego::int) AS alertas_riego,
                    ROUND(
                        100.0 * SUM(necesita_riego::int) / COUNT(*),
                        1
                    ) AS pct_alertas_riego
                FROM sensor_readings
                WHERE time >= NOW() - INTERVAL '24 hours'
                GROUP BY sensor_id
                ORDER BY sensor_id
                """
            )
            filas = cur.fetchall()
        conn.close()

        return {
            "periodo": "últimas 24 horas",
            "sensores": [dict(f) for f in filas],
        }
    except Exception as exc:
        conn.close()
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/prediccion", response_model=PrediccionResponse)
def prediccion(datos: LecturaInput):
    if modelo is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible aún.")

    X = np.array([[datos.temperatura, datos.humedad, datos.ph]])
    proba = modelo.predict_proba(X)[0]
    necesita = bool(proba[1] >= 0.5)
    confianza = float(max(proba))

    if necesita:
        if confianza >= 0.85:
            interpretacion = "Riego urgente recomendado (alta confianza)."
        else:
            interpretacion = "Posible necesidad de riego. Verificar manualmente."
    else:
        interpretacion = "Condiciones adecuadas. No se requiere riego."

    return PrediccionResponse(
        necesita_riego=necesita,
        confianza=round(confianza, 4),
        interpretacion=interpretacion,
    )
