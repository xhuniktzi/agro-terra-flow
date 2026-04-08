# API REST (FastAPI)

La API expone endpoints para consultar datos de los sensores y ejecutar predicciones de riego bajo demanda.

Documentación interactiva Swagger disponible en `/docs` una vez desplegada.

---

## Base URL

| Modo | URL base |
|---|---|
| Docker Compose | `http://localhost:8000` |
| K3s | `http://api.<IP-PUBLICA>.nip.io` |

---

## Endpoints

### `GET /health`

Estado de salud del servicio.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok"
}
```

---

### `GET /datos/recientes`

Últimas lecturas de sensores almacenadas en TimescaleDB.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `limite` | int | 10 | Cantidad de lecturas a devolver |

```bash
curl "http://localhost:8000/datos/recientes?limite=10"
```

---

### `GET /datos/estadisticas`

Estadísticas agregadas de las últimas 24 horas por sensor.

```bash
curl http://localhost:8000/datos/estadisticas
```

---

### `POST /prediccion`

Ejecuta el modelo RandomForest para predecir si se necesita riego.

**Body (JSON):**

```json
{
  "temperatura": 32.0,
  "humedad": 35.0,
  "ph": 6.5
}
```

```bash
curl -X POST http://localhost:8000/prediccion \
     -H "Content-Type: application/json" \
     -d '{"temperatura": 32.0, "humedad": 35.0, "ph": 6.5}'
```

**Respuesta esperada:**

```json
{
  "necesita_riego": true,
  "confianza": 0.92,
  "interpretacion": "Riego urgente recomendado (alta confianza)."
}
```

---

## Rangos de datos válidos

Estos son los rangos usados para generar los datos sintéticos de entrenamiento del [modelo ML](ml-model.md):

| Variable | Mínimo | Máximo | Unidad |
|---|---|---|---|
| `temperatura` | 20.0 | 30.0 | °C |
| `humedad` | 30.0 | 80.0 | % |
| `ph` | 5.5 | 7.5 | — |

Valores fuera de estos rangos producirán predicciones menos confiables.

---

## Siguiente lectura

- [ml-model.md](ml-model.md) — Detalles del modelo de predicción
- [database.md](database.md) — Esquema y consultas en TimescaleDB
