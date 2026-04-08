# Despliegue con Docker Compose (desarrollo local)

Modo de desarrollo rápido para levantar todo el pipeline en una sola máquina.

> Para despliegue en cluster K3s de 3 nodos, ver [k3s-deployment.md](k3s-deployment.md).

---

## Requisitos

- Docker Engine 24+ y Docker Compose v2
- 4 GB de RAM disponibles
- Puertos libres: 4222, 1883, 8222, 5432, 8000, 3000

---

## 1. Preparar el entorno

```bash
cp .env.example .env          # Editar si se desean cambiar credenciales
```

Ver [configuration.md](configuration.md) para detalles sobre las variables de entorno.

---

## 2. Construir imágenes e iniciar servicios

```bash
docker compose up --build -d
```

La primera vez tarda ~2–3 minutos por la descarga de imágenes base.

---

## 3. Verificar que todos los servicios estén corriendo

```bash
docker compose ps
```

Salida esperada (todos en estado `running`):

```
NAME          IMAGE                          STATUS          PORTS
nats          nats:2.10-alpine               Up (healthy)    0.0.0.0:4222->4222, 0.0.0.0:1883->1883, 0.0.0.0:8222->8222
timescaledb   timescale/timescaledb:...      Up (healthy)    0.0.0.0:5432->5432
processor     agricultura/processor:latest   Up
api           agricultura/api:latest         Up              0.0.0.0:8000->8000
grafana       grafana/grafana:10.3.3         Up              0.0.0.0:3000->3000
simulator     agricultura/simulator:latest   Up
```

---

## 4. Ver el flujo de datos en tiempo real

```bash
docker compose logs -f processor   # lectura → predicción ML → DB
docker compose logs -f simulator   # lecturas publicadas por los sensores
```

**Salida esperada del procesador:**

```
[sensor-01] T= 24.3°C  H= 68.5%  pH=6.85  → OK   ✓  conf=0.92
[sensor-02] T= 31.8°C  H= 33.2%  pH=6.40  → RIEGO ⚠  conf=0.89
[sensor-03] T= 27.1°C  H= 52.0%  pH=5.95  → OK   ✓  conf=0.81
```

---

## 5. Acceder a los servicios

| Servicio | URL | Credenciales |
|---|---|---|
| Grafana | <http://localhost:3000> | admin / admin |
| FastAPI (Swagger) | <http://localhost:8000/docs> | — |
| NATS monitoring | <http://localhost:8222> | — |

Para probar la API, ver [api-reference.md](api-reference.md).

---

## 6. Detener el experimento

```bash
docker compose down        # Detiene contenedores, conserva volúmenes
docker compose down -v     # Detiene contenedores y borra todos los datos
```

---

## Siguiente lectura

- [api-reference.md](api-reference.md) — Endpoints REST disponibles
- [database.md](database.md) — Consultas de verificación en TimescaleDB
- [troubleshooting.md](troubleshooting.md) — Solución de problemas frecuentes
