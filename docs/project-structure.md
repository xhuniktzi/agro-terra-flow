# Estructura del proyecto

```
.
├── .env.example                           # Variables de entorno (template)
├── .gitignore                             # Archivos excluidos del repo
├── docker-compose.yml                     # Entorno de desarrollo local
├── README.md                              # Punto de entrada de la documentación
│
├── docs/                                  # Documentación detallada
│   ├── docker-compose.md                  # Guía de despliegue local
│   ├── k3s-deployment.md                  # Guía de despliegue en K3s (3 nodos)
│   ├── api-reference.md                   # Endpoints REST
│   ├── ml-model.md                        # Modelo de Machine Learning
│   ├── database.md                        # Esquema y consultas TimescaleDB
│   ├── configuration.md                   # Variables de entorno y ConfigMaps
│   ├── troubleshooting.md                 # Solución de problemas
│   └── project-structure.md               # Este archivo
│
├── nats/
│   └── nats.conf                          # Config NATS: MQTT + JetStream
│
├── db/
│   └── init.sql                           # Hypertable + índices + vista SQL
│
├── grafana/
│   └── provisioning/
│       ├── datasources/timescaledb.yaml   # Datasource automático
│       └── dashboards/
│           ├── dashboard.yaml             # Provider de dashboards
│           └── sensores.json              # Dashboard con 7 paneles
│
├── src/
│   ├── simulator/
│   │   ├── simulator.py                   # Generador de datos sintéticos vía MQTT
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── processor/
│   │   ├── processor.py                   # JetStream → RandomForest → TimescaleDB
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── api/
│   │   ├── main.py                        # FastAPI: /health /datos /prediccion
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── ml/
│       ├── train.py                       # Entrenamiento autónomo del modelo
│       └── requirements.txt
│
├── model/
│   └── model.pkl                          # Modelo serializado (no versionado)
│
├── scripts/
│   └── generate-configmaps.sh             # Regenera k8s/*/configmap.yaml
│
├── k3s/
│   ├── setup-control-plane.sh             # Instala K3s en el nodo control plane
│   ├── setup-worker-infra.sh              # Une el nodo de infraestructura
│   ├── setup-worker-apps.sh               # Une el nodo de aplicaciones
│   └── label-nodes.sh                     # Etiqueta los nodos con su rol
│
└── k8s/                                   # Manifiestos Kubernetes
    ├── 00-namespace.yaml
    ├── traefik/                           # Ingress controller
    │   ├── 00-rbac.yaml
    │   ├── 01-deployment.yaml
    │   ├── 02-service.yaml
    │   └── 03-ingress.yaml
    ├── nats/          (configmap, pvc, deployment, service)
    ├── timescaledb/   (secret, pvc, configmap, deployment, service)
    ├── processor/     (deployment)
    ├── api/           (deployment, service)
    ├── grafana/       (pvc, configmap, deployment, service)
    └── simulator/     (deployment)
```

---

## Componentes de software

| Directorio | Descripción | Documentación |
|---|---|---|
| `src/simulator/` | Genera lecturas IoT sintéticas y las publica vía MQTT | [docker-compose.md](docker-compose.md) |
| `src/processor/` | Consume de NATS JetStream, ejecuta ML, escribe en DB | [ml-model.md](ml-model.md) |
| `src/api/` | API REST con FastAPI | [api-reference.md](api-reference.md) |
| `src/ml/` | Script de entrenamiento del modelo RandomForest | [ml-model.md](ml-model.md) |

## Infraestructura

| Directorio | Descripción | Documentación |
|---|---|---|
| `k8s/` | Manifiestos Kubernetes para K3s | [k3s-deployment.md](k3s-deployment.md) |
| `k3s/` | Scripts de instalación de K3s | [k3s-deployment.md](k3s-deployment.md) |
| `nats/` | Configuración del broker NATS | [configuration.md](configuration.md) |
| `db/` | Inicialización de TimescaleDB | [database.md](database.md) |
| `grafana/` | Provisioning de datasources y dashboards | [configuration.md](configuration.md) |
| `scripts/` | Utilidades (regenerar ConfigMaps) | [configuration.md](configuration.md#regenerar-configmaps-k3s) |
