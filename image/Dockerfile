# Build from the repo root: docker build -f image/Dockerfile -t kingdom/game .
# Run with: docker run --privileged --cgroupns=host kingdom/game
# (--cgroupns=host is required for the kubelet to start on cgroup v2.)
ARG K3S_VERSION=v1.33.4-k3s1
ARG ALPINE_VERSION=3.22

FROM rancher/k3s:${K3S_VERSION} AS k3s

FROM alpine:${ALPINE_VERSION}

RUN apk add --no-cache bash vim iptables ip6tables ca-certificates procps

# k3s and its helper binaries (CNI plugins, kubectl), copied from the upstream image.
# They go last on PATH so Alpine's own tools win on name clashes.
COPY --from=k3s /bin /opt/k3s/bin
ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/k3s/bin:/opt/k3s/bin/aux"
# Login shells reset PATH, so link kubectl where every shell finds it.
RUN ln -s /opt/k3s/bin/kubectl /usr/local/bin/kubectl

# Same volumes as the upstream k3s image. containerd's overlay snapshotter
# cannot run on the container's own filesystem.
VOLUME ["/var/lib/cni", "/var/lib/kubelet", "/var/lib/rancher/k3s", "/var/log"]

COPY image/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh
COPY image/welcome.txt /game/welcome.txt
COPY image/commands.sh /etc/kingdom/commands.sh
COPY image/commands.d/ /etc/kingdom/commands.d/

# Game manifests. wizardsphone.yaml and wrongnumbermessagecm.yaml are left out
# until the telephone book replaces the duplicate telephone Service.
COPY image/manifests/ /game/manifests/
COPY chimneysweep.yaml nginx-config-toothfairyphonecm.yaml nginx-config-wizardsphonecm.yaml \
     player.yaml poster-on-the-chimney.yaml telephone-boothpod.yaml telephone-operatorpod.yaml \
     telephonesvc.yaml toothfairymessagecm.yaml wizardsmessagecm.yaml /game/manifests/
COPY default/gatepod.yaml default/instructionspod.yaml default/startgamesvc.yaml /game/manifests/default/

ENTRYPOINT ["/entrypoint.sh"]
CMD []
