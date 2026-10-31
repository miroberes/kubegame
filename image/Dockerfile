# Build from the repo root: docker build -f image/Dockerfile -t kingdom/game .
# Run with: docker run --privileged --cgroupns=host kingdom/game
# (--cgroupns=host is required for the kubelet to start on cgroup v2.)
ARG K3S_VERSION=v1.33.4-k3s1

FROM rancher/k3s:${K3S_VERSION}

COPY image/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh

# Game manifests. wizardsphone.yaml and wrongnumbermessagecm.yaml are left out
# until the telephone book replaces the duplicate telephone Service.
COPY image/manifests/ /game/manifests/
COPY chimneysweep.yaml nginx-config-toothfairyphonecm.yaml nginx-config-wizardsphonecm.yaml \
     player.yaml poster-on-the-chimney.yaml telephone-boothpod.yaml telephone-operatorpod.yaml \
     telephonesvc.yaml toothfairymessagecm.yaml wizardsmessagecm.yaml /game/manifests/
COPY default/gatepod.yaml default/instructionspod.yaml default/startgamesvc.yaml /game/manifests/default/

ENTRYPOINT ["/entrypoint.sh"]
CMD []
