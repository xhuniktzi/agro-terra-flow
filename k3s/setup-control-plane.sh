#!/usr/bin/env bash
set -euo pipefail

echo "=============================================="
echo "  K3s — Instalación del Control Plane"
echo "=============================================="

if [[ $EUID -ne 0 ]]; then
  echo "[ERROR] Este script debe ejecutarse como root (sudo ./setup-control-plane.sh)"
  exit 1
fi

curl -sfL https://get.k3s.io | sh -s - server \
  --disable traefik \
  --write-kubeconfig-mode 644

echo ""
echo "[K3s] Esperando a que el API server esté disponible..."
until kubectl get nodes &>/dev/null; do
  sleep 2
done

echo ""
echo "=============================================="
echo "  Control Plane listo"
echo "=============================================="
echo ""
echo "  Estado del cluster:"
kubectl get nodes
echo ""

TOKEN=$(cat /var/lib/rancher/k3s/server/node-token)
IP=$(hostname -I | awk '{print $1}')

echo "  ┌──────────────────────────────────────────────────────────────┐"
echo "  │  DATOS PARA LOS WORKERS                                      │"
echo "  │                                                              │"
printf "  │  IP del control plane : %-36s│\n" "${IP}"
printf "  │  Token                : %-36s│\n" "${TOKEN:0:36}..."
echo "  └──────────────────────────────────────────────────────────────┘"
echo ""
echo "  Guarda estos valores y úsalos en setup-worker-infra.sh"
echo "  y setup-worker-apps.sh."
echo ""
echo "  ┌──────────────────────────────────────────────────────────────┐"
echo "  │  DESCARGAR KUBECONFIG A TU MÁQUINA LOCAL                    │"
echo "  │                                                              │"
echo "  │  Ejecuta esto en tu máquina local (no en la VM):            │"
echo "  │                                                              │"
printf "  │    scp <usuario>@%s:/etc/rancher/k3s/k3s.yaml . \n" "${IP}"
echo "  │                                                              │"
echo "  │  Luego edita el archivo descargado y reemplaza:             │"
echo "  │    server: https://127.0.0.1:6443                           │"
echo "  │  por:                                                        │"
printf "  │    server: https://%s:6443                        \n" "${IP}"
echo "  │                                                              │"
echo "  │  Finalmente configura kubectl en tu máquina local:          │"
echo "  │    export KUBECONFIG=~/k3s.yaml                             │"
echo "  │    kubectl get nodes                                         │"
echo "  └──────────────────────────────────────────────────────────────┘"
