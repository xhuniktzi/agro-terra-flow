# Configuración

Referencia de variables de entorno, archivos de configuración y cómo regenerar los ConfigMaps de Kubernetes.

---

## Variables de entorno (`.env`)

Copiar `.env.example` a `.env` antes de iniciar Docker Compose:

```bash
cp .env.example .env
```

| Variable | Default | Descripción |
|---|---|---|
| `POSTGRES_USER` | `admin` | Usuario de TimescaleDB |
| `POSTGRES_PASSWORD` | *(vacío)* | Contraseña de TimescaleDB |
| `POSTGRES_DB` | `agriculture` | Nombre de la base de datos |
| `PUBLISH_INTERVAL_SECONDS` | `5` | Intervalo de publicación del simulador (segundos) |
| `STARTUP_DELAY_SECONDS` | `20` | Tiempo de espera del simulador antes de publicar |

> **Nota:** En Docker Compose se usa el archivo `.env`. En K3s, las credenciales se inyectan vía `k8s/timescaledb/secret.yaml`.

---

## Archivos de configuración

### NATS (`nats/nats.conf`)

Configuración del broker con soporte MQTT nativo y JetStream habilitado:

- Puerto NATS: 4222
- Puerto MQTT: 1883
- Puerto HTTP monitoring: 8222
- JetStream: almacenamiento en `/data`, máx. 256 MB en memoria, 1 GB en disco

### Grafana provisioning (`grafana/provisioning/`)

- `datasources/timescaledb.yaml` — Conexión automática a TimescaleDB
- `dashboards/dashboard.yaml` — Provider que carga dashboards desde archivos
- `dashboards/sensores.json` — Dashboard de IoT con 7 paneles

### Base de datos (`db/init.sql`)

Script de inicialización que crea:

- Extensión TimescaleDB
- Hypertable `sensor_readings` con particionamiento por timestamp
- Índices para consultas frecuentes
- Vista `v_estadisticas_sensor`

---

## Regenerar ConfigMaps (K3s)

Los archivos en `nats/`, `grafana/provisioning/` y `db/` son la **fuente de verdad**. Los ConfigMaps de Kubernetes en `k8s/` se generan a partir de ellos.

Después de modificar cualquier archivo de configuración:

```bash
./scripts/generate-configmaps.sh
kubectl apply -f k8s/ --recursive
```

El script `generate-configmaps.sh` regenera:

- `k8s/nats/configmap.yaml` ← desde `nats/nats.conf`
- `k8s/grafana/configmap.yaml` ← desde `grafana/provisioning/*`
- `k8s/timescaledb/configmap.yaml` ← desde `db/init.sql`

---

## Siguiente lectura

- [docker-compose.md](docker-compose.md) — Despliegue local
- [k3s-deployment.md](k3s-deployment.md) — Despliegue en cluster
- [project-structure.md](project-structure.md) — Ubicación de cada archivo
