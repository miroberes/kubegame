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
| 3. Find phrase | Searches under the doormat | Phrase is `openplease` | Hint is in the logs only | `gatepod.yaml` (init script) |
| 4. Whisper | Speaks the phrase | `kubectl exec -it gate -- sh /scripts/check_phrase.sh openplease` | "Correct... Use the spell: enter village" | `gatepod.yaml` |

### Act II: The Village (`village` namespace)

| Step | Player action | Solution | Result | Source |
|---|---|---|---|---|
| 5. Enter village | Casts the spell | `enter village` | Player arrives in the village | none yet |
| 6. Read poster | Calls the chimney sweep | `kubectl exec player -it -- wget -O - chimneysweep` | "Call wizard on his phone..." | `chimneysweep.yaml`, `poster-on-the-chimney.yaml` |
| 7. Call wizard | Dials the wizard | `wget -O - telephone:8081` | "Use the spell: enter wizardshouse" | `telephone-operatorpod.yaml`, `telephonesvc.yaml` |
| 8. Enter wizard's house | Casts the spell | `enter wizardshouse` | Door opens | none yet, nothing follows |
| 9. Call Tooth Fairy | Dials port 8082 | `wget -O - telephone:8082` | Voicemail: teeth, gifts, "tooth's special story" | `toothfairymessagecm.yaml` |
| 10. Booth clue | Reads booth logs | `kubectl logs telephone-booth` | Recent calls: 8082, 8081, 7777 | `telephone-boothpod.yaml` |

### Act III: Roles (not started)

- After unlocking a namespace, a spell updates the player's role.
- Players switch context to another user to gain access.
- Players learn to create CSRs for users.

Planned shape: Acts I and II hand the player roles passively. Act III flips this. The player runs `kubectl auth can-i`, inspects bindings, and creates a CSR and a binding themselves.

---

## 3. Design principles (decided)

1. **Stay as close to native Kubernetes as possible.** What the player learns must transfer to a real cluster.
2. **Namespace switching is never locked.** In real Kubernetes, switching namespace is only a context setting and grants nothing. A gated `enter` would teach the wrong mental model.
3. **RBAC is the real gate.** The `village` namespace exists from the start. "Unlocking" it means the gate puzzle grants the player rights there. A player who skips ahead can arrive early but meets a native `Forbidden` error.
4. **Spells are visible aliases, not hidden magic.** Raw kubectl is verbose and flag-heavy, so the game offers it as story-voiced spells. The player can always discover the real command by typing `alias`. The spellbook can itself be a quest.
5. **Native errors are never replaced, only supplemented.** The native error carries the lesson (user, verb, resource, namespace). An optional story line adds meaning. Story lines contain no technical claims.
6. **Fade the training wheels over the acts.** Act I leans on spells, Act II mixes spells and raw commands, Act III is raw kubectl, because roles, contexts, and CSRs have no good shortcut.

---

## 4. The spells

### Definitions (aliases)

```bash
alias lookaround='kubectl get pods,services'
alias inspect='kubectl logs'
alias enter='kubectl config set-context --current --namespace'
alias whisper='kubectl exec gate -- sh /scripts/check_phrase.sh'
alias call='kubectl exec player -- wget -O -'
```

Extra words the player types land at the end of the expanded command:

- `enter village` runs `kubectl config set-context --current --namespace village`.
- `inspect gate -c cluelogger` works as written. The player supplies the container (the Act I lesson). A bare `inspect gate` gets kubectl's own "choose one of" error.
- `whisper openplease` runs the check script on the gate.
- `call telephone:8081` and `call chimneysweep` both work.

### Naming decision

`sns` (the original namespace-switch spell) was dropped. It was an abbreviation, which is the "cryptic raw command" problem in a shorter form. Every other spell is a verb in the story's voice, so it became **`enter`**. This matches the quest log's own wording ("Enter village", "Enter wizard's house").

Places to update:

- `gatepod.yaml`: success message becomes "Use the spell: enter village".
- Telephone operator output (step 7): becomes "Use the spell: enter wizardshouse".
- Steps 5 and 8 in the brief: solutions become `enter village` and `enter wizardshouse`.

### Known limits of plain aliases

- No story lines under errors (aliases cannot see output).
- No "what you actually did" line. The `alias` listing replaces it.
- `enter nowhere` succeeds silently and fails on the next command (`set-context` does not check that the namespace exists).
- `call` needs the full target (`telephone:8081`), with no port shortcut.
- Aliases only expand in interactive shells, which is fine for a player at a prompt.
- `call` hard-codes the pod name `player` (see open issues).

### Optional: story layer via a shared helper

If story lines are wanted, aliases can point at one helper function. The spells stay aliases and `alias` still shows the real command, now prefixed with `story`.

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
alias enter='story kubectl config set-context --current --namespace'
alias whisper='story kubectl exec gate -- sh /scripts/check_phrase.sh'
alias call='story kubectl exec player -- wget -O -'
```

Notes:

- Output format is layered: native error first, then the story line. Unknown errors get no story line.
- Fade-out: making `story` an empty pass-through in Act III returns the spells to plain native behavior.
- Keep matches narrow (Forbidden, NotFound). A wrong story line over a different real error is worse than none.
- Raw commands (`kubectl exec`, `wget`) bypass this layer, so players will see story lines only when they use spells.
- A fuller function-based prototype (with an `enter` existence check, a `call <port>` shortcut, and a "spell behind the spell" line) was drafted in `spells.sh`. It was judged more than needed for a first version.

### `use`

The brief names `use` but never defines it. Its role is undecided.

---

## 5. RBAC design

The village exists from the start. Access is controlled by RBAC.

- **Restricted player identity.** The player must not hold cluster-admin credentials. The environment hands them a ServiceAccount or user with only Act I rights (for example `logs` and `exec` on the gate pod). Without this, no `Forbidden` error ever fires.
- **Unlocking = a RoleBinding.** Solving the gate puzzle makes `check_phrase.sh` (or the gate pod) create a RoleBinding granting the player rights in `village`. The unlock is a real object, discoverable with `kubectl get rolebindings -n village`.
- **Privilege escalation rules.** The gate pod's ServiceAccount needs permission to create RoleBindings in `village`. Kubernetes blocks escalation, so it also needs the `bind` verb on the specific Role it hands out.
- **Minimum first grant.** Step 6 needs `pods/exec` in `village` (the player pod lives there). The wizard's house gets its own binding when the telephone puzzle is solved.
- **Namespace lookups.** If a spell checks that a namespace exists, the player's role needs `get` on namespaces.
- **What RBAC does not control.** In-cluster traffic such as the `wget` calls between pods is unaffected. Act II's "locks" are RBAC (kubectl access), while its "puzzles" are networking. Keep these separate when designing content.
- **Side effect.** Restricting `get pod gate -o yaml` closes the spoiler leak where `openplease` is readable in plain text in the manifest. A player can still `cat` the script from inside the pod, which is a legitimate advanced move.

### Error layering example

```
Error from server (Forbidden): pods is forbidden: User "player" cannot list resource "pods" in namespace "village"
The villagers turn their backs on you. You have no standing here yet.
```

The native line names the user, verb, resource, and namespace, which feeds `kubectl auth can-i list pods -n village` later. The word "yet" hints that something the player does will change it.

---

## 6. Delivery: how players run the game

### Decision: a Docker image

Players run the game locally via Docker. The only prerequisite is Docker.

```bash
docker run -it --rm --privileged -v kingdom-save:/var/lib/rancher kingdom/game
```

Image contents:

- A small cluster (k3s is the usual choice).
- The game manifests, applied at startup.
- The restricted kubeconfig for the player identity (admin credentials never in the player's shell).
- The aliases in the player's bashrc.
- A save volume (progress persists between runs; deleting the volume resets the game).

### Caveats to resolve

- **`curl startgame` does not work automatically.** `startgame` is an in-cluster Service name. A shell inside the k3s container is not a pod and will not resolve cluster DNS names. Options: a game-shell alias that curls the service's ClusterIP or a NodePort, printing the welcome page at startup, or starting the player's shell in a pod (which would change the later `kubectl exec player` steps).
- **`--privileged` looks alarming.** k3s needs it or a long list of capabilities. Explain it on the download page and test whether a narrower flag set works.
- **Docker Desktop licensing.** Larger companies may need a paid license. Check current terms. Podman or Colima may work, but k3s support there must be tested.
- **Resources.** A cluster in a container needs a few GB of RAM, which older laptops may struggle with.
- **Everything is local,** so players can read manifests and solutions.
- **Unverified.** Exact registry limits, k3s capability requirements, and platform terms were not checked and need verification.

### Options considered and rejected

| Option | Why rejected |
|---|---|
| Install kind/minikube/kubectl on the player's laptop | Setup wall for beginners; touches the player's own shell config and machine |
| Browser playground on a third-party platform | Dependency on third-party terms, limits, and commercial-use rules |
| Own hosted sandbox | Ongoing cost and maintenance, abuse risk (free compute) |
| Subscription or pay-per-use | Not needed for a free portfolio project; adds payments, licensing, and piracy concerns |

---

## 7. Release model

- **Free and open source**, public repo, public image. Costs reduce to the maintainer's time, registry limits, and a small site.
- **License:** pick one (MIT or Apache 2.0 are typical).
- **Registry:** GitHub Container Registry is the natural fit. Check current limits and terms.
- **Remaining costs:** image bandwidth, rebuilds when Kubernetes/k3s/Docker change, user support ("it doesn't start on my machine").

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
3. **Player pod name:** `player.yaml` names it `playerpod`, the README uses `player`.
4. **Undefined spells:** `use` and the final definitions of the others (see section 4). `sns` is replaced by `enter`.
5. **Spoiler leak:** the phrase is plain text in `gatepod.yaml` (mitigated by RBAC, see section 5).
6. **Undefined story:** the curse, the 7777 line, the wizard's house, and the Tooth Fairy's reward have no content.

### README

- The `inspect` alias uses `-c main-container`, which does not exist in the gate pod. The working container is `cluelogger`.

### New from the design discussion

7. **Restricted player identity** and the RBAC manifests do not exist yet.
8. **`check_phrase.sh` must create the RoleBinding** for the village (and the gate's ServiceAccount needs the `bind` permission).
9. **`curl startgame` resolution** inside the Docker environment (section 6).
10. **`use` has no defined role.**
11. **Manifest strings still say `sns`.**

---

## 9. Open decisions

- Plain aliases only, or aliases plus the `story` helper?
- Is the wizard's house a namespace or something smaller? If smaller, should `enter` still cover it?
- Should the player see a `Forbidden` error early on purpose (a quest line sending them to `village` too soon), or should the story steer them there only after the gate is solved?
- Should story lines be scenario-specific, error-type-based, or a mix (error-type default with scenario overrides)?
- What does `use` do?
- Which container runtimes are supported (Docker only, or also Podman/Colima)?
- What are the payoffs for the wizard's house, the Tooth Fairy, and the 7777 line? (7777 could be a deliberate red herring.)

---

## 10. Suggested build order

1. Settle the open issues: 8082 conflict, duplicate `telephone` Service, `player` vs `playerpod`, and rename `sns` to `enter` in the manifests.
2. Create the restricted player identity and the Act I RBAC, with the RoleBinding created on solving the gate.
3. Build the Docker image: k3s, manifests, restricted kubeconfig, aliases, save volume, and a working `startgame`.
4. Give the wizard's house and the Tooth Fairy real payoffs.
5. Add CI with an automated Act I smoke test, plus the README, GIF, license, and `DESIGN.md`.
6. Release Acts I and II. Build Act III (roles, contexts, CSRs) as a second milestone.
