# Solución de problemas

Problemas frecuentes y cómo resolverlos en ambos modos de despliegue.

---

## El procesador no recibe mensajes

El simulador espera 25 segundos (initContainer / delay) para que el procesador
cree el stream JetStream. Si el procesador tardó más, reiniciar el simulador:

```bash
# Docker Compose
docker compose restart simulator

# K3s
kubectl rollout restart deployment/simulator -n agricultura
```

---

## TimescaleDB no inicia en WSL (Docker Compose)

```bash
docker compose down -v
docker compose up timescaledb -d
```

Esperar a que pase el healthcheck, luego levantar el resto:

```bash
docker compose up -d
```

---

## Grafana no muestra el dashboard

1. Verificar que los archivos de provisioning estén montados:

   ```bash
   # Docker Compose
   docker compose exec grafana ls /etc/grafana/provisioning/dashboards/

   # K3s
   kubectl exec -n agricultura deployment/grafana -- \
     ls /etc/grafana/provisioning/dashboards/
   # Debe aparecer: dashboard-provider.yaml  sensores.json
   ```

2. En Grafana: ir a **Dashboards > Browse** > carpeta **"Agricultura de Precisión"**.
3. Si no aparece, cambiar el time range a **Last 15 minutes**.

---

## Puerto 80 no accesible desde internet (K3s en cloud)

Verificar que la regla de firewall permita `tcp:80` hacia el nodo control plane.

En GCP: VPC network > Firewall > agregar regla que permita `tcp:80`.

---

## Pod en `Pending` (K3s)

```bash
kubectl describe pod <nombre> -n agricultura
```

Revisar "Events:" — usualmente falta el label `role=infra` o `role=apps` en el nodo:

```bash
kubectl get nodes --show-labels | grep role
```

Ver [k3s-deployment.md](k3s-deployment.md#paso-4--etiquetar-los-nodos) para etiquetar nodos.

---

## Pod en `ImagePullBackOff` (K3s)

```bash
kubectl describe pod <nombre> -n agricultura
```

Verificar que la imagen existe en Docker Hub y que el nombre es correcto.
Ver [k3s-deployment.md](k3s-deployment.md#paso-6--publicar-imágenes-en-docker-hub).

---

## Traefik sin EXTERNAL-IP (K3s)

```bash
kubectl get svc traefik -n kube-system
```

Si EXTERNAL-IP está en `<pending>`, K3s ServiceLB no asignó IP. Verificar que el puerto 80 no está en uso en el control plane.

---

## Regenerar ConfigMaps tras cambiar una configuración

Ver [configuration.md](configuration.md#regenerar-configmaps-k3s).

---

## Siguiente lectura

- [docker-compose.md](docker-compose.md) — Despliegue local
- [k3s-deployment.md](k3s-deployment.md) — Despliegue en cluster
