# TimescaleDB — Esquema y consultas

TimescaleDB (extensión de PostgreSQL) almacena las lecturas de sensores como series temporales con particionamiento automático.

---

## Esquema

La inicialización se define en `db/init.sql` y se ejecuta automáticamente al crear el contenedor.

**Hypertable principal:** `sensor_readings`

| Columna | Tipo | Descripción |
|---|---|---|
| `time` | TIMESTAMPTZ | Timestamp de la lectura (clave de partición) |
| `sensor_id` | TEXT | Identificador del sensor (sensor-01, sensor-02, sensor-03) |
| `temperatura` | DOUBLE PRECISION | Temperatura en °C |
| `humedad` | DOUBLE PRECISION | Humedad relativa en % |
| `ph` | DOUBLE PRECISION | pH del suelo |
| `necesita_riego` | BOOLEAN | Resultado de la predicción ML |
| `confianza` | DOUBLE PRECISION | Confianza de la predicción (0–1) |

**Vista predefinida:** `v_estadisticas_sensor` — estadísticas agregadas de las últimas 24 horas.

---

## Acceso a la consola SQL

```bash
# Docker Compose
docker compose exec timescaledb psql -U admin -d agriculture

# K3s
kubectl exec -it -n agricultura deployment/timescaledb -- psql -U admin -d agriculture
```

---

## Consultas útiles

### Contar lecturas totales

```sql
SELECT COUNT(*) FROM sensor_readings;
```

### Últimas 15 lecturas

```sql
SELECT time, sensor_id, temperatura, humedad, ph, necesita_riego
FROM sensor_readings ORDER BY time DESC LIMIT 15;
```

### Estadísticas últimas 24 h (vista predefinida)

```sql
SELECT * FROM v_estadisticas_sensor;
```

### Promedio por minuto con time_bucket (función TimescaleDB)

```sql
SELECT
    time_bucket('1 minute', time) AS minuto,
    sensor_id,
    ROUND(AVG(temperatura)::numeric, 2) AS temp_prom,
    ROUND(AVG(humedad)::numeric, 2)     AS hum_prom
FROM sensor_readings
WHERE time >= NOW() - INTERVAL '1 hour'
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```

---

## Siguiente lectura

- [api-reference.md](api-reference.md) — Endpoints que consultan estos datos
- [configuration.md](configuration.md) — Configuración de la conexión a la base de datos
