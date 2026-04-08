# AgroTerraFlow

Pipeline abierto de Big Data para agricultura de precisión, con simulación IoT, predicción de riego por ML y orquestación con K3s / Docker Compose.

---

## Arquitectura

```
Simulador IoT (Python + paho-mqtt)
    │  publica JSON vía MQTT  (topic: sensores/datos)
    ▼
NATS Server  [broker MQTT nativo + JetStream]
    │  stream persistido: iot-data  (subject: sensores.datos)
    ▼
Procesador Python
    │  ① consume JetStream
    │  ② ejecuta RandomForest (scikit-learn)
    │  ③ escribe en hypertable
    ▼
TimescaleDB  [PostgreSQL 16 + extensión TimescaleDB]
    │  hypertable: sensor_readings
    ├──▶ Grafana  [dashboards en tiempo real]
    └──▶ FastAPI  [API REST: consultas + inferencia ML bajo demanda]

Todo el tráfico externo pasa por Traefik (ingress controller).
```

---

## Componentes y licencias

| Componente | Versión | Licencia | Rol |
|---|---|---|---|
| NATS Server | 2.10 | Apache 2.0 | Broker MQTT + streaming (JetStream) |
| TimescaleDB | 2.14 (community) | Apache 2.0 | Almacenamiento de series temporales |
| PostgreSQL | 16 | PostgreSQL License | Motor de base de datos |
| Grafana | 10.3 | AGPL 3.0 | Visualización y dashboards |
| FastAPI | 0.110 | MIT | API REST |
| scikit-learn | 1.4 | BSD 3-Clause | Modelo ML (RandomForest) |
| Python | 3.11 | PSF License | Lenguaje base |
| K3s | 1.34+ | Apache 2.0 | Orquestación de contenedores |
| Traefik | 2.10 | MIT | Ingress controller |
| paho-mqtt | 1.6 | EPL 2.0 / EDL 1.0 | Cliente MQTT para el simulador |

Todos los componentes tienen licencia libre u open source reconocida por la OSI o la FSF.

---

## Inicio rápido (Docker Compose)

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

| Servicio | URL |
|---|---|
| Grafana | <http://localhost:3000> (admin / admin) |
| FastAPI (Swagger) | <http://localhost:8000/docs> |
| NATS monitoring | <http://localhost:8222> |

Para instrucciones completas, ver [docs/docker-compose.md](docs/docker-compose.md).

---

## Documentación

| Documento | Descripción |
|---|---|
| [Despliegue con Docker Compose](docs/docker-compose.md) | Guía paso a paso para desarrollo local |
| [Despliegue en K3s (3 nodos)](docs/k3s-deployment.md) | Cluster con separación de roles por VM |
| [API REST](docs/api-reference.md) | Endpoints, parámetros y ejemplos |
| [Modelo de ML](docs/ml-model.md) | Entrenamiento, variables e integración |
| [Base de datos](docs/database.md) | Esquema TimescaleDB y consultas útiles |
| [Configuración](docs/configuration.md) | Variables de entorno, NATS, Grafana, ConfigMaps |
| [Solución de problemas](docs/troubleshooting.md) | Errores frecuentes y cómo resolverlos |
| [Estructura del proyecto](docs/project-structure.md) | Árbol de archivos y directorios |
