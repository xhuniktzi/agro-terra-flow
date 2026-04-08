#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Uso: $0 <nombre-nodo-infra> <nombre-nodo-apps>"
  echo ""
  echo "Nodos disponibles:"
  kubectl get nodes -o wide
  exit 1
fi

INFRA_NODE="$1"
APPS_NODE="$2"

echo "Etiquetando nodo de infraestructura: ${INFRA_NODE}"
kubectl label node "${INFRA_NODE}" role=infra --overwrite

echo "Etiquetando nodo de aplicaciones   : ${APPS_NODE}"
kubectl label node "${APPS_NODE}"  role=apps  --overwrite

echo ""
echo "=== Estado del cluster ==="
kubectl get nodes --show-labels | grep -E "NAME|role="
echo ""
echo "=== Verificación de nodeSelector ==="
echo "Nodos con role=infra (NATS, TimescaleDB, Grafana):"
kubectl get nodes -l role=infra
echo ""
echo "Nodos con role=apps (Procesador, API, Simulador):"
kubectl get nodes -l role=apps
