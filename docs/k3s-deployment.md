# Despliegue en K3s — Cluster de 3 nodos

Simulación de un entorno de producción con separación de roles por nodo.

> Para desarrollo local rápido, ver [docker-compose.md](docker-compose.md).

---

## Topología del cluster

```
┌──────────────────────────────────────────────────────────────┐
│                    INTERNET                                   │
│                       │                                       │
│              Puerto 80 (Traefik)                              │
│                       │                                       │
│  ┌────────────────────▼─────────────────┐                    │
│  │  VM 1 — control-plane                │                    │
│  │  K3s server + Traefik (ingress)      │                    │
│  └────────────────┬─────────────────────┘                    │
│                   │  API server :6443                         │
│        ┌──────────┴──────────────┐                           │
│        │                         │                           │
│  ┌─────┴────────────┐   ┌────────┴─────────┐                │
│  │  VM 2            │   │  VM 3            │                │
│  │  worker-infra    │   │  worker-apps     │                │
│  │  role=infra      │   │  role=apps       │                │
│  │                  │   │                  │                │
│  │  • NATS          │   │  • Procesador    │                │
│  │  • TimescaleDB   │   │  • FastAPI       │                │
│  │  • Grafana       │   │  • Simulador     │                │
│  └──────────────────┘   └──────────────────┘                │
└──────────────────────────────────────────────────────────────┘
          ▲
          │ kubectl (desde tu máquina local vía kubeconfig)
   ┌──────┴──────┐
   │  Tu equipo  │
   └─────────────┘
```

> Todo el tráfico externo entra por **Traefik** en el puerto 80 del control plane.
> Los servicios internos (NATS, TimescaleDB) son ClusterIP — no accesibles desde fuera.

---

## Requisitos de cada VM

| VM | Rol | CPU | RAM | Disco |
|---|---|---|---|---|
| VM 1 | control-plane | 1 núcleo | 1 GB | 10 GB |
| VM 2 | worker-infra  | 2 núcleos | 2 GB | 20 GB |
| VM 3 | worker-apps   | 2 núcleos | 2 GB | 10 GB |

SO recomendado: **Ubuntu 22.04 LTS** o **Debian 12** en las 3 VMs.

> Las 3 VMs deben poder comunicarse entre sí. El control plane necesita
> los puertos 6443 (API K3s) y 80 (Traefik) accesibles externamente.

---

## Paso 1 — Control plane (en VM 1)

```bash
chmod +x k3s/setup-control-plane.sh
sudo ./k3s/setup-control-plane.sh
```

Al terminar muestra la **IP** y el **token** necesarios para los workers:

```
  IP del control plane : 192.168.1.10
  Token                : K107a3b...
```

---

## Paso 2 — Descargar kubeconfig a tu máquina local

```bash
scp <usuario>@192.168.1.10:/etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i 's/127.0.0.1/192.168.1.10/g' ~/.kube/config
kubectl get nodes   # verificar conexión
```

> A partir de aquí todos los comandos `kubectl` se ejecutan desde **tu máquina local**.

---

## Paso 3 — Workers (en VM 2 y VM 3)

```bash
# En VM 2 (infraestructura):
sudo CONTROL_PLANE_IP=192.168.1.10 K3S_TOKEN=K107a3b... \
     ./k3s/setup-worker-infra.sh

# En VM 3 (aplicaciones):
sudo CONTROL_PLANE_IP=192.168.1.10 K3S_TOKEN=K107a3b... \
     ./k3s/setup-worker-apps.sh
```

---

## Paso 4 — Etiquetar los nodos

El script `label-nodes.sh` requiere los nombres de los nodos como argumentos:

```bash
./k3s/label-nodes.sh <nombre-nodo-infra> <nombre-nodo-apps>

# Ejemplo:
./k3s/label-nodes.sh k3s-infra k3s-apps

# O manualmente:
kubectl label node <nombre-vm2> role=infra
kubectl label node <nombre-vm3> role=apps

kubectl get nodes --show-labels | grep role   # verificar
```

---

## Paso 5 — Verificar que los 3 nodos están Ready

```bash
kubectl get nodes
```

```
NAME                STATUS   ROLES           AGE   VERSION
k3s-control-plane   Ready    control-plane   5m    v1.34.x+k3s1
k3s-infra           Ready    <none>          3m    v1.34.x+k3s1
k3s-apps            Ready    <none>          2m    v1.34.x+k3s1
```

---

## Paso 6 — Publicar imágenes en Docker Hub

Las imágenes Python se publican una sola vez. Si ya están subidas
(`<tu-usuario>/agricultura-*:latest`), omitir este paso.

```bash
docker login

docker build -t <tu-usuario>/agricultura-processor:latest ./src/processor/
docker build -t <tu-usuario>/agricultura-api:latest       ./src/api/
docker build -t <tu-usuario>/agricultura-simulator:latest ./src/simulator/

docker push <tu-usuario>/agricultura-processor:latest
docker push <tu-usuario>/agricultura-api:latest
docker push <tu-usuario>/agricultura-simulator:latest
```

---

## Paso 7 — Aplicar todos los manifiestos

```bash
kubectl apply -f k8s/ --recursive
```

K3s descarga las imágenes automáticamente desde Docker Hub.
Los initContainers gestionan el orden de arranque.

---

## Paso 8 — Verificar el despliegue

```bash
kubectl get pods -n agricultura -o wide
```

Salida esperada:

```
NAME                      READY  STATUS    NODE
grafana-xxx               1/1    Running   k3s-infra
nats-xxx                  1/1    Running   k3s-infra
timescaledb-xxx           1/1    Running   k3s-infra
api-xxx                   1/1    Running   k3s-apps
processor-xxx             1/1    Running   k3s-apps
simulator-xxx             1/1    Running   k3s-apps
```

Verificar Traefik en kube-system:

```bash
kubectl get pods -n kube-system -l app=traefik
kubectl get svc  -n kube-system traefik   # debe mostrar EXTERNAL-IP
```

---

## Paso 9 — Acceder a los servicios

Sustituir `<IP-PUBLICA>` con la IP pública del control plane.
Las URLs usan [nip.io](https://nip.io) — DNS wildcard gratuito, sin configuración.

| Servicio | URL |
|---|---|
| Grafana | `http://grafana.<IP-PUBLICA>.nip.io` |
| FastAPI (Swagger) | `http://api.<IP-PUBLICA>.nip.io/docs` |

Credenciales de Grafana: `admin / admin`

Para probar la API en K3s:

```bash
IP=<IP-PUBLICA>

curl http://api.${IP}.nip.io/health
curl "http://api.${IP}.nip.io/datos/recientes?limite=10"
curl http://api.${IP}.nip.io/datos/estadisticas
curl -X POST http://api.${IP}.nip.io/prediccion \
  -H "Content-Type: application/json" \
  -d '{"temperatura": 32.0, "humedad": 35.0, "ph": 6.5}'
```

Ver [api-reference.md](api-reference.md) para detalles de cada endpoint.

---

## Eliminar el despliegue

```bash
# Eliminar cargas de trabajo (conserva el cluster K3s)
kubectl delete namespace agricultura
kubectl delete -f k8s/traefik/

# Desinstalar K3s completamente (ejecutar en cada VM)
# VM 1:    sudo /usr/local/bin/k3s-uninstall.sh
# VM 2/3:  sudo /usr/local/bin/k3s-agent-uninstall.sh
```

---

## Siguiente lectura

- [api-reference.md](api-reference.md) — Endpoints REST disponibles
- [database.md](database.md) — Consultas directas a TimescaleDB
- [configuration.md](configuration.md) — ConfigMaps y archivos de configuración
- [troubleshooting.md](troubleshooting.md) — Solución de problemas frecuentes
