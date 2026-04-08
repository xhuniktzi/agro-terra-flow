#!/usr/bin/env bash
set -euo pipefail

echo "=============================================="
echo "  K3s — Instalación del Worker (Aplicaciones)"
echo "=============================================="

if [[ $EUID -ne 0 ]]; then
  echo "[ERROR] Ejecutar como root: sudo CONTROL_PLANE_IP=x K3S_TOKEN=y ./setup-worker-apps.sh"
  exit 1
fi

if [[ -z "${CONTROL_PLANE_IP:-}" ]]; then
  echo "[ERROR] Define CONTROL_PLANE_IP con la IP del nodo control plane."
  echo "  Ejemplo: sudo CONTROL_PLANE_IP=192.168.1.10 K3S_TOKEN=xxx ./setup-worker-apps.sh"
  exit 1
fi

if [[ -z "${K3S_TOKEN:-}" ]]; then
  echo "[ERROR] Define K3S_TOKEN con el token obtenido del control plane."
  exit 1
fi

echo "[K3s] Uniendo el cluster en ${CONTROL_PLANE_IP}:6443..."

curl -sfL https://get.k3s.io | \
  K3S_URL="https://${CONTROL_PLANE_IP}:6443" \
  K3S_TOKEN="${K3S_TOKEN}" \
  sh -s - agent

echo ""
echo "=============================================="
echo "  Worker de aplicaciones unido al cluster"
echo "=============================================="
echo ""
echo "  Nombre de este nodo: $(hostname)"
echo ""
echo "  Ahora ve al nodo CONTROL PLANE y ejecuta:"
echo ""
echo "    kubectl label node $(hostname) role=apps"
echo ""
echo "  Luego actualiza las referencias de imagen en los manifiestos"
echo "  (k8s/processor/, k8s/api/, k8s/simulator/) con la URL de tu"
echo "  registro y aplica con kubectl apply."
