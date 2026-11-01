#!/bin/sh
# Container entrypoint. Runs as root; later steps drop to the player user.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "entrypoint must run as root" >&2
  exit 1
fi

ADMIN_KUBECONFIG=/etc/rancher/k3s/k3s.yaml
K3S_LOG=/var/log/k3s.log
SETUP_LOG=/var/log/kingdom-setup.log

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

kubectl --kubeconfig "$ADMIN_KUBECONFIG" wait --for=condition=Ready node --all --timeout="${timeout}s" >>"$SETUP_LOG" 2>&1

# Step 2: create the village namespace, the restricted player identity, and the game objects.
# The default ServiceAccount is created asynchronously after the API starts; pods need it.
elapsed=0
until kubectl --kubeconfig "$ADMIN_KUBECONFIG" get serviceaccount default -n default >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$timeout" ]; then
    echo "default ServiceAccount not created within ${timeout}s; see $K3S_LOG" >&2
    exit 1
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done

kubectl --kubeconfig "$ADMIN_KUBECONFIG" apply -R -f /game/manifests >>"$SETUP_LOG" 2>&1

kubectl --kubeconfig "$ADMIN_KUBECONFIG" wait --for=condition=Ready pod --all -n default --timeout="${timeout}s" >>"$SETUP_LOG" 2>&1 &
wait_pid=$!
spin_i=0
while kill -0 "$wait_pid" 2>/dev/null; do
  case $((spin_i % 4)) in 0) spin_c='|' ;; 1) spin_c='/' ;; 2) spin_c='-' ;; *) spin_c='\' ;; esac
  printf '\rLoading the Kubernetes kingdom %s ' "$spin_c" >&2
  spin_i=$((spin_i + 1))
  sleep 0.2
done
printf '\r%-30s\r' ' ' >&2
wait "$wait_pid" || { echo "The kingdom did not finish loading. See $SETUP_LOG" >&2; exit 1; }

# Step 3: give the player a restricted kubeconfig. The admin kubeconfig stays root-only.
PLAYER_USER=player
PLAYER_HOME=/home/$PLAYER_USER
PLAYER_KUBECONFIG=$PLAYER_HOME/.kube/config

chmod 0600 "$ADMIN_KUBECONFIG"
mkdir -p /home
if ! id "$PLAYER_USER" >/dev/null 2>&1; then
  adduser -D -h "$PLAYER_HOME" -s /bin/bash "$PLAYER_USER"
fi
mkdir -p "$(dirname "$PLAYER_KUBECONFIG")"

CA_FILE=$(mktemp)
kubectl --kubeconfig "$ADMIN_KUBECONFIG" config view --raw \
  -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d >"$CA_FILE"
TOKEN=$(kubectl --kubeconfig "$ADMIN_KUBECONFIG" create token player -n default --duration=12h)

rm -f "$PLAYER_KUBECONFIG"
kubectl config --kubeconfig="$PLAYER_KUBECONFIG" set-cluster kingdom \
  --server=https://127.0.0.1:6443 --certificate-authority="$CA_FILE" --embed-certs=true >>"$SETUP_LOG" 2>&1
kubectl config --kubeconfig="$PLAYER_KUBECONFIG" set-credentials player --token="$TOKEN" >>"$SETUP_LOG" 2>&1
kubectl config --kubeconfig="$PLAYER_KUBECONFIG" set-context kingdom \
  --cluster=kingdom --user=player --namespace=default >>"$SETUP_LOG" 2>&1
kubectl config --kubeconfig="$PLAYER_KUBECONFIG" use-context kingdom >/dev/null
rm -f "$CA_FILE"

chown -R "$PLAYER_USER:$PLAYER_USER" "$PLAYER_HOME/.kube"
chmod 0600 "$PLAYER_KUBECONFIG"

printf 'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\nexport KUBECONFIG=%s\n. /etc/kingdom/commands.sh\n' "$PLAYER_KUBECONFIG" >"$PLAYER_HOME/.profile"
chown "$PLAYER_USER:$PLAYER_USER" "$PLAYER_HOME/.profile"

# Step 4: welcome text.
printf '\n'
cat /game/welcome.txt
printf 'Version %s\n' "$(cat /game/VERSION)"

# Step 5: replace this process with the player's login shell, running as the unprivileged user.
exec su -l "$PLAYER_USER" -c "exec bash -l"
