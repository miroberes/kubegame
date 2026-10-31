#!/bin/sh
# Container entrypoint. Runs as root; later steps drop to the player user.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "entrypoint must run as root" >&2
  exit 1
fi

ADMIN_KUBECONFIG=/etc/rancher/k3s/k3s.yaml
K3S_LOG=/var/log/k3s.log

# Step 1: start k3s and wait until the API server and node are ready.
mkdir -p "$(dirname "$K3S_LOG")"
k3s server \
  --write-kubeconfig "$ADMIN_KUBECONFIG" \
  --write-kubeconfig-mode 0600 \
  >"$K3S_LOG" 2>&1 &

timeout=300
elapsed=0
until kubectl --kubeconfig "$ADMIN_KUBECONFIG" get --raw=/readyz >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$timeout" ]; then
    echo "k3s API did not become ready within ${timeout}s; see $K3S_LOG" >&2
    exit 1
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done

until [ -n "$(kubectl --kubeconfig "$ADMIN_KUBECONFIG" get nodes -o name 2>/dev/null)" ]; do
  if [ "$elapsed" -ge "$timeout" ]; then
    echo "no node registered within ${timeout}s; see $K3S_LOG" >&2
    exit 1
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done

kubectl --kubeconfig "$ADMIN_KUBECONFIG" wait --for=condition=Ready node --all --timeout="${timeout}s"

echo "k3s is ready."
