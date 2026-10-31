# Build from the repo root: docker build -f image/Dockerfile -t kingdom/game .
# Run with: docker run --privileged --cgroupns=host kingdom/game
# (--cgroupns=host is required for the kubelet to start on cgroup v2.)
ARG K3S_VERSION=v1.33.4-k3s1

FROM rancher/k3s:${K3S_VERSION}

COPY image/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD []
