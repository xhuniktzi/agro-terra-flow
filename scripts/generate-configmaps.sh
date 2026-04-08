#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/3] Generando k8s/nats/configmap.yaml..."
kubectl create configmap nats-config -n agricultura \
  --from-file=nats.conf=nats/nats.conf \
  --dry-run=client -o yaml > k8s/nats/configmap.yaml

echo "[2/3] Generando k8s/grafana/configmap.yaml..."
kubectl create configmap grafana-provisioning -n agricultura \
  --from-file=datasource.yaml=grafana/provisioning/datasources/timescaledb.yaml \
  --from-file=dashboard-provider.yaml=grafana/provisioning/dashboards/dashboard.yaml \
  --from-file=sensores.json=grafana/provisioning/dashboards/sensores.json \
  --dry-run=client -o yaml > k8s/grafana/configmap.yaml

echo "[3/3] Generando k8s/timescaledb/configmap.yaml..."
kubectl create configmap timescaledb-init -n agricultura \
  --from-file=init.sql=db/init.sql \
  --dry-run=client -o yaml > k8s/timescaledb/configmap.yaml

echo ""
echo "Listo. Aplica los cambios con:"
echo "  kubectl apply -f k8s/ --recursive"
