# Kubernetes Kingdom Adventure

A text adventure where you learn Kubernetes by playing. You type story-named commands in a shell, and each one runs a real `kubectl` command against a live cluster.

Plot: A mysterious curse has befallen the kingdom. Only the brave who master Kubernetes commands can unlock its secrets and lift the curse.

CKAD Exam Tips: https://miroberes.github.io/

## Run the game

You need Docker. Build the image from the repo root, then start the game:

```
docker build -f image/Dockerfile -t kingdom/game .
docker run -it --rm --privileged --cgroupns=host kingdom/game
```

`--privileged` and `--cgroupns=host` are needed for the k3s cluster to start inside the container. The game takes about a minute to load.

## Start playing

Maybe you should `inspect gate` to learn how it can be opened.

Type `help` at any time to see the commands available where you are.
