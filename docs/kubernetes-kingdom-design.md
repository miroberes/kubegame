# Kubernetes Kingdom: Design and Development Base

> **Spoiler warning:** this document contains puzzle solutions. Keep it out of the public front door (e.g. `docs/solutions/` in the repo), not in the main README.

**Status:** early draft. Act I is built, Act II is partly built, Act III is not started. This document consolidates the design decisions made so far and the work that remains.

---

## 1. Vision

A text-adventure game that teaches people to operate a Kubernetes cluster. The player solves story puzzles, and each puzzle requires a real kubectl skill. The story gives the learner a reason to run each command.

- **Audience:** learners who want to start somewhere, including total beginners. The player is not expected to build the game's environment, just as a player of any game does not build the engine.
- **Goal of the project:** a free, open project that serves as a portfolio piece.
- **Learning arc:** Observe (Act I), Connect (Act II), Authorize (Act III).

---

## 2. Game structure

### Act I: The Gate (`default` namespace)

| Step | Player action | Solution | Result | Source |
|---|---|---|---|---|
| 1. Start | Reads the welcome page | `curl startgame` | Shows plot and first quest | `default/instructionspod.yaml`, `startgamesvc.yaml` |
| 2. Inspect gate | Reads gate logs | `kubectl logs gate -c cluelogger` | "Whisper the magic key phrase... under the doormat" | `default/gatepod.yaml` |
| 3. Find phrase | Runs `inspect doormat` | Phrase is `openk8s`; the gate shows `k8s`, and the floor under the doormat shows `nk8s` | Descriptions come from `inspect gate` and `inspect doormat` | `gatepod.yaml` (cluelogger), `08-doormat-pod.yaml`, `06-doormat.yaml` |
| 4. Whisper | Speaks the phrase | `kubectl exec -it gate -- sh /scripts/check_phrase.sh openk8s` | "Correct... Use the command: open gate" | `gatepod.yaml` |

### Act II: The Village (`village` namespace)

| Step | Player action | Solution | Result | Source |
|---|---|---|---|---|
| 5. Enter village | Runs the command | `switch village` | Player arrives in the village | none yet |
| 6. Read poster | Calls the chimney sweep | `kubectl exec player -it -- wget -O - chimneysweep` | "Call wizard on his phone..." | `chimneysweep.yaml`, `poster-on-the-chimney.yaml` |
| 7. Call wizard | Dials the wizard | `wget -O - telephone:8081` | "Use the command: enter wizardshouse" | `telephone-operatorpod.yaml`, `telephonesvc.yaml` |
| 8. Enter wizard's house | Runs the command | `enter wizardshouse` | Door opens | none yet, not designed yet, nothing follows |
| 9. Call Tooth Fairy | Dials port 8082 | `wget -O - telephone:8082` | Voicemail: teeth, gifts, "tooth's special story" | `toothfairymessagecm.yaml` |
| 10. Booth clue | Reads booth logs | `kubectl logs telephone-booth` | Recent calls: 8082, 8081, 7777 | `telephone-boothpod.yaml` |

Cross-namespace note: the `player` pod stays in `village`. See "Acting across namespaces" in section 4 for how calls work once the player has entered the wizard's house.

### Act III: Roles (not started)

- After unlocking a namespace, a command updates the player's role.
- Players switch context to another user to gain access.
- Players learn to create CSRs for users.
- Players contrast identity types: they start as a ServiceAccount (a real API object) and later learn that a certificate user such as `king` is only a name in a certificate.

Planned shape: Acts I and II hand the player roles passively. Act III flips this. The player runs `kubectl auth can-i`, inspects bindings, and creates a CSR and a binding themselves.

---

## 3. Design principles (decided)

1. **Stay as close to native Kubernetes as possible.** What the player learns must transfer to a real cluster.
2. **Namespace switching is never locked.** In real Kubernetes, switching namespace is only a context setting and grants nothing. A gated `switch` would teach the wrong mental model.
3. **RBAC is the real gate.** The `village` namespace exists from the start. "Unlocking" it means the gate puzzle grants the player rights there. A player who skips ahead can arrive early but meets a native `Forbidden` error.
4. **Commands are visible aliases, not hidden magic.** Raw kubectl is verbose and flag-heavy, so the game offers it as story-voiced commands. The player can always discover the real command by typing `alias`. The command list can itself be a quest.
5. **Native errors are never replaced, only supplemented.** The native error carries the lesson (user, verb, resource, namespace). An optional story line adds meaning. Story lines contain no technical claims.
6. **Fade the training wheels over the acts.** Act I leans on story commands, Act II mixes story commands and raw commands, Act III is raw kubectl, because roles, contexts, and CSRs have no good shortcut.

---

## 4. The commands

### Definitions (aliases)

```bash
alias lookaround='kubectl get pods,services'
alias inspect='kubectl logs'
alias switch='kubectl config set-context --current --namespace'
alias whisper='kubectl exec -n default gate -- sh /scripts/check_phrase.sh'
alias call='kubectl exec -n village player -- wget -O -'
```

The `-n` flags matter: `kubectl exec` looks in the current namespace, so without them `whisper` and `call` would fail with NotFound as soon as the player has used `switch` to leave the pod's namespace (see "Acting across namespaces" below).

Extra words the player types land at the end of the expanded command:

- `switch village` runs `kubectl config set-context --current --namespace village`.
- `inspect gate -c cluelogger` works as written. The player supplies the container (the Act I lesson). A bare `inspect gate` gets kubectl's own "choose one of" error.
- `whisper openk8s` runs the check script on the gate.
- `call telephone:8081` and `call chimneysweep` both work.

### Naming decision

`sns` (the original namespace-switch command) was dropped. It was an abbreviation, which is the "cryptic raw command" problem in a shorter form. Every other command is a verb in the story's voice, so it became **`switch`** for the namespace change.

Places to update:

- `gatepod.yaml`: success message becomes "Use the command: enter village".
- Telephone operator output (step 7): becomes "Use the command: enter wizardshouse".
- Step 5 in the brief: solution becomes `switch village`. Step 8 stays `enter wizardshouse` until its design exists.

### Known limits of plain aliases

- No story lines under errors (aliases cannot see output). The wrapper above fixes this.
- No "what you actually did" line. The `alias` listing replaces it.
- `switch nowhere` succeeds silently and fails on the next command (`set-context` does not check that the namespace exists).
- `call` needs the full target (`telephone:8081`), with no port shortcut.
- Aliases only expand in interactive shells, which is fine for a player at a prompt.
- `call` hard-codes the pod name `player` and its namespace `village` (see open issues and "Acting across namespaces").

### Acting across namespaces (two routes)

A pod's namespace is fixed when it is created, so the `player` pod does not move. What `switch` changes is the context's default namespace. Acting across namespaces is normal Kubernetes: any pod can reach any Service in any namespace by a qualified name (`service.namespace`), and short names resolve only within the caller's own namespace. What actually limits reach is RBAC (for kubectl access) and NetworkPolicy (for pod traffic).

The player's shell is not inside the cluster, so the `player` pod exists only as a launch point for in-cluster calls. Two common real-world practices exist, and each teaches a different lesson. The game teaches both:

| | Route A: fixed pod, `exec` | Route B: throwaway pod, `kubectl run` |
|---|---|---|
| Commands | `kubectl exec -n village player -- wget -O - telephone.village:8081` | `kubectl run tmp --rm -it --image=<pinned> --image-pull-policy=IfNotPresent -n <ns> -- sh` |
| Core lesson | Fully qualified names; namespaces don't block reach | Creating a pod where you need it, where short names resolve naturally, and cleaning up after |
| Side lessons | `exec`, `-n` | Image choice, `--rm`, needing `create` rights on pods in that namespace |
| Where it fits | Start of Act II (village) | After the player has earned rights in a new namespace |

Suggested order in Act II:

1. **Village:** the standing `player` pod and `exec`. Short names work because the pod is in `village`.
2. **Wizard's house:** the player has no pod there and has two valid routes: call from the village pod with a qualified name, or create a throwaway pod in the house. A hint from the phone booth or the wizard can point at either.
3. **Later (optional):** an obstacle that favors one route, for example a NetworkPolicy that only accepts traffic from inside the house (making Route B the working one). Leave both routes open unless a lesson needs steering. This should be a deliberate choice.

Validation looks at cluster state, not at how the player got there, so both routes complete the puzzle.

Notes:

- **Commands:** `call` stays an alias for Route A. Route B is taught as the raw `kubectl run` command, since Act II is where raw commands start to appear.
- **Story:** a line such as "your voice travels back through the village telephone" can explain why a call from the wizard's house originates in the village.
- **NetworkPolicy:** a policy in the wizard's house treats traffic from the `village` pod as external. Make that deliberate, not accidental.
- **RBAC and images for Route B:** see section 5 and the open issues.

### Optional: story layer via a shared helper

If story lines are wanted, aliases can point at one helper function. The commands stay aliases and `alias` still shows the real command, now prefixed with `story`.

```bash
story() {
  local errfile rc ns
  errfile=$(mktemp)
  "$@" 2>"$errfile"; rc=$?
  cat "$errfile" >&2
  if [ $rc -ne 0 ]; then
    ns=$(sed -n 's/.*in the namespace "\([^"]*\)".*/\1/p' "$errfile" | head -n1)
    if grep -qi forbidden "$errfile"; then
      case "$ns" in
        village)      echo "The villagers turn their backs on you. You have no standing here yet." ;;
        wizardshouse) echo "The door stays shut. The wizard does not know you." ;;
        *)            echo "The way is barred. You have no standing here yet." ;;
      esac
    elif grep -qi 'notfound\|not found' "$errfile"; then
      echo "Nothing here answers to that name."
    fi
  fi
  rm -f "$errfile"
  return $rc
}

alias lookaround='story kubectl get pods,services'
alias inspect='story kubectl logs'
alias switch='story kubectl config set-context --current --namespace'
alias whisper='story kubectl exec -n default gate -- sh /scripts/check_phrase.sh'
alias call='story kubectl exec -n village player -- wget -O -'
```

Notes:

- Output format is layered: native error first, then the story line. Unknown errors get no story line.
- Fade-out: making `story` an empty pass-through in Act III returns the commands to plain native behavior.
- Keep matches narrow (Forbidden, NotFound). A wrong story line over a different real error is worse than none.
- Raw commands (`kubectl exec`, `wget`) bypass this layer, so players will see story lines only when they use commands.
- A fuller function-based prototype (with a `switch` existence check, a `call <port>` shortcut, and a "command behind the command" line) was drafted in `commands.sh`. It was judged more than needed for a first version.

### Story layer via a kubectl wrapper (preferred)

Because the player's shell lives in the game's own container (section 6), the story layer can sit in front of `kubectl` itself instead of in a helper behind each alias. A wrapper script is placed ahead of the real binary on `PATH`. It runs the real kubectl, passes everything through, and adds a story line after known failures.

Benefits over the `story` helper:

- Story lines appear whether the player used a story command **or** the raw `kubectl` command, so behavior is consistent.
- The commands go back to being plain aliases of `kubectl ...`, so `alias` shows the real command with no `story` prefix.
- The fade-out is one switch: in Act III the wrapper stops adding lines.

Sketch (must be tested, see cautions below):

```bash
#!/usr/bin/env bash
# /usr/local/bin/kubectl  (ahead of the real binary on PATH)
REAL=/usr/local/libexec/kubectl.real
ACT=$("$REAL" get configmap kingdom-state -n default \
        -o jsonpath='{.data.act}' 2>/dev/null)          # progress lives in the cluster
ACT=${ACT:-2}
[ "$ACT" = "3" ] && exec "$REAL" "$@"                   # Act III: native only

errfile=$(mktemp); trap 'rm -f "$errfile"' EXIT
"$REAL" "$@" 2> >(tee "$errfile" >&2)                   # stderr streams live and is copied
rc=$?
wait $! 2>/dev/null                                     # let the copy finish (bash 4.4+)

if [ $rc -ne 0 ]; then
  ns=$(sed -n 's/.*in the namespace "\([^"]*\)".*/\1/p' "$errfile" | head -n1)
  if grep -qi forbidden "$errfile"; then
    case "$ns" in
      village)      echo "The villagers turn their backs on you. You have no standing here yet." ;;
      wizardshouse) echo "The door stays shut. The wizard does not know you." ;;
      *)            echo "The way is barred. You have no standing here yet." ;;
    esac
  elif grep -qi 'notfound\|not found' "$errfile"; then
    echo "Nothing here answers to that name."
  fi
fi
exit $rc
```

Commands then become plain aliases again (as in the definitions above).

The current act is read from a ConfigMap in the cluster (the player's role needs `get` on that one object), so progress is state in Kubernetes and not a side file. The cost is one extra API call per command. A plain file inside the container would also work, since nothing leaves the container, but the cluster-state version matches the state-based principle.

Cautions:

- **Keep stdout, stderr, and the exit status intact.** Scripts and any validator that calls kubectl depend on them.
- **Test interactive modes** (`exec -it`, `logs -f`, `edit`, `port-forward`). Copying stderr as it streams avoids buffering, but the ordering of the story line after the native error needs checking.
- **Keep matches narrow** (Forbidden, NotFound). An unrecognized error gets no story line.
- **Be honest about it.** Players on a real cluster will not have the wrapper. The fade-out handles this, and a short intro note or a command-list quest can reveal it.
- **Limits:** it only sees output in the player's shell. Errors inside pods (application logs) are game content you control anyway.

The `story` helper above remains the fallback if the player's shell is ever not in the game container.

### `use`

The brief names `use` but never defines it. Its role is undecided.

---

## 5. RBAC design

The village exists from the start. Access is controlled by RBAC.

- **Restricted player identity (decided): a ServiceAccount named `player-sa` in `default`.** The player must not hold cluster-admin credentials. They get a ServiceAccount with only Act I rights. Without this, no `Forbidden` error ever fires. The name avoids a clash with the `player` pod and follows the common `-sa` convention. Kubernetes names are lowercase letters, digits, and hyphens, and must not start with `system:`.
- **Identity, Role, binding.** A ServiceAccount is only an identity. A new one has almost no rights (just basic discovery permissions). Privilege comes from a RoleBinding joining it to a Role. Every unlock in the game is: an identity, a Role describing what is allowed, and a binding joining them. A player who creates a new ServiceAccount gets nothing until a binding exists.
- **Unlocking = a RoleBinding.** Solving the gate puzzle makes `check_phrase.sh` (or the gate pod) create a RoleBinding granting the player rights in `village`. The unlock is a real object, discoverable with `kubectl get rolebindings -n village`. The subject is the `default` namespace's ServiceAccount, named explicitly (cross-namespace subjects are normal):

  ```yaml
  subjects:
    - kind: ServiceAccount
      name: player-sa
      namespace: default
  ```
- **Privilege escalation rules.** The gate pod's ServiceAccount needs permission to create RoleBindings in `village`. Kubernetes blocks escalation, so it also needs the `bind` verb on the specific Role it hands out.
- **Who creates the RoleBinding.** Two options. In-cluster: `check_phrase.sh` creates it, which keeps all puzzle logic inside Kubernetes (more native) but requires the gate's ServiceAccount to have `create` on rolebindings and `bind` on the Role. Engine-side: the container's startup/engine script, holding the admin credentials, creates it after observing the solved state (no `bind` setup needed, but puzzle logic lives outside the world).
- **Minimum first grant.** Step 6 needs `pods/exec` in `village` (the player pod lives there). The wizard's house gets its own binding when the telephone puzzle is solved.
- **Throwaway-pod route (section 4).** Creating a pod in a namespace is a permission the player earns through that namespace's RoleBinding, so the unlock has a visible effect. `kubectl run -it --rm` needs more than `create` on pods: it also has to watch the pod, attach to it, and delete it afterward. The exact verbs and subresources must be tested. A `Forbidden` on creation is a good trigger for a story line.
- **Namespace lookups.** If a command checks that a namespace exists, the player's role needs `get` on namespaces.
- **What RBAC does not control.** In-cluster traffic such as the `wget` calls between pods is unaffected. Act II's "locks" are RBAC (kubectl access), while its "puzzles" are networking. Keep these separate when designing content.
- **Spoiler leak (correction).** An earlier version of this document claimed that restricting `get pod gate -o yaml` closes the leak. That is probably wrong: `kubectl logs` and `kubectl exec` first fetch the pod, so the player needs `get` on pods, and with it `kubectl get pod gate -o yaml` works too (restricting by `resourceNames` limits which pods, not what is shown). If the phrase sits in the pod spec (command or args), it is readable. Mitigation to test: keep the phrase out of the spec, for example in a Secret the init script reads (the spec then shows only a reference, and the player has no rights on secrets), or inside the image. A player can still read the script from inside the pod, which is a legitimate advanced move. Verify the `get` requirement on the pinned kubectl version.

### Provisioning `player-sa` (startup script)

1. Create the ServiceAccount in `default` (where Act I lives).
2. Create a token and write a kubeconfig that uses it.
3. Grant Act I rights with a Role and RoleBinding.

**Token lifetime.** `kubectl create token` issues short-lived tokens by default, and a play session can outlast one. Options: request a longer duration, or use a long-lived token stored in a Secret of type `kubernetes.io/service-account-token` (considered legacy, but simpler for a local game). Check what the pinned k3s version allows.

### Pods and ServiceAccounts

- A pod acts as the ServiceAccount named in its `serviceAccountName`, or the namespace's `default` ServiceAccount if none is named. That `default` identity has no rights. Keep it separate from `player-sa`. Do not run the `player` pod under `player-sa` unless that is a deliberate lesson.
- **A pod can only use a ServiceAccount from its own namespace.** Setting `serviceAccountName: player-sa` on a pod in `village` fails, because `player-sa` lives in `default`. This is why the `village` RoleBinding names its subject's namespace explicitly. It is also a lesson: identities belong to namespaces.
- `serviceAccountName` cannot be changed on a running pod, so fixing a pod's identity means deleting and recreating it.
- Anyone who can create pods in a namespace can run them as any ServiceAccount in that namespace, which is a real privilege-escalation path and a possible Act III lesson.

**Example lesson (from the discussion): the herald who can't read the decree.** A herald pod in `village` logs a `Forbidden` error naming `system:serviceaccount:village:default`. The player confirms with `kubectl auth can-i get configmaps --as=system:serviceaccount:village:default -n village`, then creates a ServiceAccount, a Role for the decree ConfigMap, and a RoleBinding, and recreates the herald with `serviceAccountName` set.

### Self-inspection tools for the player

- `kubectl get rolebindings -n village`: who was granted access.
- `kubectl describe rolebinding <name>`: the exact Role and subject.
- `kubectl auth can-i --list`: what the current identity may do.
- `kubectl auth whoami` exists in newer kubectl versions. Verify against the pinned version.

### Error layering example

```
Error from server (Forbidden): pods is forbidden: User "system:serviceaccount:default:player-sa" cannot list resource "pods" in API group "" in the namespace "village"
The villagers turn their backs on you. You have no standing here yet.
```

The native line names the user (a ServiceAccount's full system name, which includes its namespace), the verb, the resource, the API group, and the namespace. That feeds `kubectl auth can-i list pods -n village` later. The exact wording should be confirmed against the pinned Kubernetes version. The story helper only reads the namespace after "in the namespace", so it works unchanged. The word "yet" hints that something the player does will change it.

---

## 6. Delivery: how players run the game

### Constraint (decided)

**The game must not touch anything on the host.** No bind mounts, no Docker socket, no host-installed tools beyond Docker itself, and no leftover volumes unless the player opts in.

This rules out the Compose + kind architecture borrowed from the exam-practice specification (section 11): an engine container creating a kind cluster needs the Docker socket (control of the player's whole Docker daemon), and the specification's kubeconfig and workspace are host bind mounts.

### Decision: one self-contained container

```bash
docker run -it --rm --privileged ghcr.io/<owner>/kingdom
```

Everything runs inside that one container. Exiting the shell removes the container and everything in it.

```text
Container
├── k3s (single-node cluster, started at launch)
├── game manifests (baked into the image, applied at startup)
├── startup/engine script (admin credentials, RBAC setup, progress state)
└── player shell (non-root user)
    ├── commands (aliases)
    ├── kubectl story wrapper
    ├── Bash, Vim, basic utilities
    └── restricted kubeconfig only
```

Startup sequence (entrypoint script):

1. Start k3s and wait until it is ready.
2. Create the `player-sa` ServiceAccount, its token, and a kubeconfig that uses it, written inside the container (see "Provisioning `player-sa`" in section 5).
3. Apply the manifests (namespaces including `village`, pods, services, Act I RBAC, the `kingdom-state` ConfigMap).
4. Print the welcome text and open the player's shell as the non-root player user.

### Credentials: the player must not be root

k3s writes an admin kubeconfig inside the container. If the player's shell ran as root, the player could read it and bypass RBAC, and every `Forbidden` error would be fake. So:

- The player shell runs as an unprivileged user.
- The admin kubeconfig and k3s data directory stay root-only.
- There is no `sudo` in the image.

This is flavor-level protection, not a hard boundary. A determined player who controls Docker can always `docker exec` as root, which is acceptable for a learning game.

### Installing the commands and the story layer

Everything is baked into the image at build time. The player installs nothing.

| Path | Contents |
|---|---|
| `/usr/local/libexec/kubectl.real` | The real kubectl, pinned and checksum-verified at build time, not on `PATH` |
| `/usr/local/bin/kubectl` | The wrapper script (section 4), which calls the real binary by absolute path |
| `/etc/kingdom/commands.rc` | The aliases, sourced from `/etc/bash.bashrc` |
| `/game/manifests/` | The game manifests applied at startup |

The wrapper intercepts a plain `kubectl` because `/usr/local/bin` precedes `/usr/bin` on `PATH`. Build-time test: `command -v kubectl` must return `/usr/local/bin/kubectl`.

Dockerfile outline (untested, base image and k3s packaging unverified):

```dockerfile
FROM debian:12-slim
ARG TARGETARCH
ARG KUBECTL_VERSION          # keep within one minor version of the bundled k3s
ARG K3S_VERSION

RUN apt-get update \
 && apt-get install -y --no-install-recommends bash vim curl ca-certificates iptables \
 && rm -rf /var/lib/apt/lists/*

# Real kubectl (pinned, checksum-verified at build time, not on PATH)
RUN mkdir -p /usr/local/libexec \
 && curl -fsSLo /usr/local/libexec/kubectl.real \
      "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" \
 && curl -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl.sha256" \
      | awk '{print $1"  /usr/local/libexec/kubectl.real"}' | sha256sum -c - \
 && chmod 0755 /usr/local/libexec/kubectl.real

# k3s (download, pin, and verify per the k3s release process)
# ...

# Player user, wrapper, commands, manifests, entrypoint
RUN useradd -m player
COPY workstation/kubectl-wrapper /usr/local/bin/kubectl
COPY workstation/commands.rc       /etc/kingdom/commands.rc
COPY manifests/                  /game/manifests/
COPY entrypoint.sh               /entrypoint.sh
RUN chmod 0755 /usr/local/bin/kubectl /entrypoint.sh \
 && echo 'source /etc/kingdom/commands.rc' >> /etc/bash.bashrc
ENTRYPOINT ["/entrypoint.sh"]
```

Checks: confirm that the player's interactive bash reads `/etc/bash.bashrc` (distro-dependent), that shell completion works through the wrapper, and that the engine/startup script calls the real binary so story lines never appear in its output.

### Why `--privileged`

A node must run containers itself (namespaces, overlay mounts, cgroups), set up pod networking (bridges, iptables), and reach kernel interfaces that a default container hides or makes read-only. `--privileged` lifts all those restrictions at once. It writes no host files, but it grants broad rights, so "touches nothing" is true for files and not for privileges. State this plainly on the download page.

On Docker Desktop (Mac, Windows), containers run inside a Linux VM, so the exposure is that VM. On native Linux it is the real host.

Test plan to narrow it (unverified): start from the smallest plausible set (specific `--cap-add` values, `--security-opt` overrides for seccomp/AppArmor, tmpfs mounts, cgroup settings) and add until k3s boots, on native Linux, Docker Desktop, and Podman. Alternatives were considered and rejected: rootless modes (fragile), Sysbox (requires a host install), VM-based setups (bigger prerequisite), API-server-only (no pods, so `logs`/`exec`/`wget` stop working).

### Progress and persistence

- **Default:** ephemeral. With `--rm`, every run starts at the gate.
- **Without `--rm`:** progress survives `docker stop` and `docker start` inside the container's own filesystem, and disappears when the container is deleted.
- **Opt-in volume:** an explicit "save my progress" option for players who want it (for example mounting a named volume for k3s state). Off by default so the default run leaves nothing behind.
- Progress state itself (the current act) lives in the cluster (`kingdom-state` ConfigMap), not in a file.

### Offline operation

The image contains everything: k3s, kubectl, manifests, scenario images. Pin and test versions together. For offline distribution, provide the image as a file that can be loaded with `docker load`. Avoid runtime downloads from public registries.

### `curl startgame`

A shell in the same container as the node can likely reach the Service's cluster IP, but the name will not resolve through cluster DNS. A hosts entry or an alias, or printing the welcome page at startup, is probably enough. Needs testing.

### Caveats

- `--privileged` (above).
- Docker Desktop has commercial licensing terms for larger companies; check current rules. Podman or Colima may work but k3s support there must be tested.
- A cluster needs a few GB of RAM and the image is large.
- Everything is local, so players can read manifests and solutions.
- ARM and x86 players both need to be served (multi-architecture image).
- Unverified: k3s-in-container behavior, exact flag sets, platform terms.

### Options considered

| Option | Outcome |
|---|---|
| Install kind/minikube/kubectl on the player's laptop | Rejected: setup wall for beginners; touches the player's machine |
| Docker Compose + kind + workstation container (exam-practice spec) | Rejected for this game: needs the Docker socket and host bind mounts, which violates "touches nothing on the host" |
| Browser terminal backed by a container running in the cloud | Possible later add-on using the same image; costs money per active player, needs strong isolation (privileged containers for strangers are risky), abuse controls, idle shutdown, and session orchestration; no offline play |
| Third-party browser playground | Rejected as the main path: dependency on third-party terms, limits, and commercial-use rules |
| Subscription or pay-per-use | Rejected: not needed for a free portfolio project |

---

## 7. Release model

- **Free and open source**, public repo, public image. Costs reduce to the maintainer's time, registry limits, and a small site.
- **License:** pick one (MIT or Apache 2.0 are typical).
- **Registry:** see the Registry subsection below.
- **Remaining costs:** image bandwidth (the offline bundle with kind node images is large), rebuilds when Kubernetes/k3s/Docker change, user support ("it doesn't start on my machine").

### Registry

Publish the image to **GitHub Container Registry (GHCR)** as the primary registry, since the repo and CI are on GitHub and Actions can push with the built-in token.

- GitHub documents container image storage and bandwidth as currently free, with advance notice promised before that changes. "Currently" is not "permanently."
- Anonymous pulls of public images are supported, so players need no account.
- Third-party summaries report no rate limit on public pulls and free public storage and bandwidth. These come from secondary sources, so confirm on GitHub's own documentation.
- Optional mirror on Docker Hub for discoverability. Its free tier rate-limits pulls (sources disagree on the exact figures: 100 or 200 per 6 hours for anonymous users), which could hurt a launch or a classroom. A Sponsored Open Source program exists that removes limits for qualifying projects.
- Check per-layer and per-image size limits and test a push of the real image early, since the bundle will be large.
- Build a multi-architecture image (x86 and ARM) in CI.
- Keep a build-from-source path as an escape hatch in case registry terms change.

### What makes it work as a portfolio piece

- A one-command start with a short terminal GIF in the README.
- A playable slice (Acts I and II with real payoffs) over three half-built acts. Act III can be a roadmap.
- A `DESIGN.md` documenting the decisions in this file.
- CI (GitHub Actions) that builds the image and runs a smoke test, such as solving Act I automatically.
- A spoiler-free README, with walkthroughs under `docs/solutions/`.
- A "Contributing" section, since the game is made of self-contained puzzles.

---

## 8. Open issues

### From the original brief

1. **Port 8082 conflict:** `wizardsphone.yaml` says "Wrong number" while the operator pod serves the Tooth Fairy.
2. **Duplicate `telephone` Services:** `wizardsphone.yaml` and `telephonesvc.yaml` both define `telephone` in `village`.
3. **Player pod name:** `player.yaml` names it `playerpod`, the README uses `player`. Decision: the pod is `player` (matches the README and the other pods' naming), the RBAC identity is `player-sa`. `player.yaml` and its pod name need updating.
4. **Undefined commands:** `use` and the final definitions of the others (see section 4). `sns` is replaced by `switch`.
5. **Spoiler leak:** the phrase is plain text in `gatepod.yaml`. RBAC probably does not fix this (see the correction in section 5). Move the phrase out of the pod spec.
6. **Undefined story:** the curse, the 7777 line, the wizard's house, and the Tooth Fairy's reward have no content.

### README

- The `inspect` alias uses `-c main-container`, which does not exist in the gate pod. The working container is `cluelogger`.

### New from the design discussion

7. **Restricted player identity** and the RBAC manifests do not exist yet.
8. **`check_phrase.sh` must create the RoleBinding** for the village (and the gate's ServiceAccount needs the `bind` permission).
9. **`curl startgame` resolution** inside the container (section 6).
10. **`use` has no defined role.**
11. **Manifest strings still say `sns`.**
12. **Player must not be root** in the container, or the admin kubeconfig is readable and RBAC is bypassed (section 6).
13. **Narrowing `--privileged`** is untested (section 6 test plan).
14. **kubectl wrapper** needs testing for interactive modes, stream separation, and exit codes.
15. **Base image and k3s packaging** for the single container are not decided or verified.
16. **Alias namespaces:** `whisper` and `call` now name their namespace (`-n default`, `-n village`). The pod name and namespace still need to be settled (issue 3).
17. **RBAC verbs for `kubectl run --rm -it`** are untested (section 5).
18. **Throwaway pod image:** needs a pinned tag preloaded into the cluster's image store, with `--image-pull-policy=IfNotPresent`, since an unpinned `latest` tag defaults to always pulling and fails offline. How k3s imports preloaded images is unverified.
19. **Stray pods:** `--rm` cleans up after a normal exit, but a player who disconnects leaves pods behind. Consider cleanup by the engine or a TTL.
20. **`player-sa` token lifetime** and k3s behavior for long-lived tokens (section 5).
21. **`player-sa` RBAC manifests** (Role, RoleBinding, Act I rights) do not exist yet.
22. **`get` on pods is required** for `logs` and `exec`, which affects the spoiler mitigation (section 5). Verify.
23. **Exact `Forbidden` wording** for ServiceAccounts should be confirmed against the pinned version, and the story helper's pattern re-tested.

---

## 9. Open decisions

- Plain aliases only, or aliases plus the `story` helper?
- Is the wizard's house a namespace or something smaller? If smaller, should `enter` still cover it?
- Should the player see a `Forbidden` error early on purpose (a quest line sending them to `village` too soon), or should the story steer them there only after the gate is solved?
- Should story lines be scenario-specific, error-type-based, or a mix (error-type default with scenario overrides)?
- What does `use` do?
- Add the herald lesson (pod identity) to the debugging ladder in `curse-design.md`?
- Long-lived token for `player-sa`, or a long duration on a created token?
- Should a later obstacle steer the player toward one route (fixed pod vs. throwaway pod), or leave both open?
- Is one standing pod per namespace ever needed, or are the two routes enough?
- Which container runtimes are supported (Docker only, or also Podman/Colima)?
- Who creates the village RoleBinding: `check_phrase.sh` in the cluster, or the startup/engine script (section 5)?
- Should the engine also validate puzzle state (as in the exam-practice spec), or does the in-cluster logic suffice?
- Is a fresh start on every run acceptable, or should progress persist by default?
- Is a hosted browser version worth adding later, using the same image?
- Which cluster inside the container: k3s (assumed) or something else?
- What are the payoffs for the wizard's house, the Tooth Fairy, and the 7777 line? (7777 could be a deliberate red herring.)

---

## 10. Suggested build order

1. Settle the open issues: 8082 conflict, duplicate `telephone` Service, `player` vs `playerpod`, and rename `sns` to `switch` in the manifests.
2. Create the restricted player identity and the Act I RBAC, with the RoleBinding created on solving the gate.
3. Run the `--privileged` narrowing experiment, then build the single container: k3s, manifests, non-root player user, restricted kubeconfig, aliases, kubectl wrapper, startup script, and a working `startgame`.
4. Give the wizard's house and the Tooth Fairy real payoffs.
5. Add CI (multi-architecture build, push to GHCR, automated Act I smoke test), plus the README, GIF, license, and `DESIGN.md`.
6. Release Acts I and II. Build Act III (roles, contexts, CSRs) as a second milestone.

---

## 11. Relation to the exam-practice specification

The local-kubernetes-game specification targets CKAD/CKA/CKS drills with real tools and no story. This game borrows several ideas from it: a separate player shell with real tools, offline-first with pinned and tested versions, state-based validation, and mission-level reset.

It does not adopt its Compose + kind architecture, because that needs the Docker socket and host bind mounts, which violates this game's rule of touching nothing on the host (section 6). The single self-contained container delivers the same player experience inside one container.

The two can be seen as a progression. The story game's commands fade out until Act III is plain kubectl, and that end state is where exam-style practice begins. The specification's own caveat applies to its scope, not ours: node-level CKA/CKS tasks (etcd, kubelet, control-plane services) cannot be reproduced on kind or k3s in a container, but this game's content is API-level. Keep the cluster backend replaceable anyway.
