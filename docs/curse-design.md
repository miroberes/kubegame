# Kubernetes Kingdom: The Curse

> **Spoiler warning:** this document reveals puzzle structure and solutions.

**Status:** brainstorm. Nothing here is decided yet. Companion to `kubernetes-kingdom-design.md`.

---

## 1. The idea

The curse is something in the cluster and the kingdom that stops it from functioning properly. It has two layers:

1. **Many small curses.** Small things that don't work, each a different failure class. The player fixes them to learn basic debugging. The result of each fix leads to the next level.
2. **One main spell.** The ultimate curse, which the player can only break after learning enough Kubernetes. Where it sits in the infrastructure decides what the finale teaches.

---

## 2. The small curses (the debugging ladder)

Each is a different failure class with its own diagnostic path, disguised as something wrong in the kingdom. They all fit the standard toolkit: `get`, `describe`, `logs`, and events.

| Kingdom symptom | Kubernetes fault | What the player learns |
|---|---|---|
| The chimney sweep doesn't answer | Service selector doesn't match pod labels, so there are no endpoints | Labels, selectors, `kubectl get endpoints` |
| The poster-pod keeps dying | CrashLoopBackOff from a bad command | `kubectl logs`, `kubectl logs --previous` |
| The messenger never arrives | ImagePullBackOff from a typo in the image name | `kubectl describe`, events |
| The operator wakes but can't read its directory | Missing ConfigMap or Secret key | `kubectl describe`, config wiring |
| The telephone line is dead | Wrong `targetPort`, or a NetworkPolicy blocking traffic | Ports, network policies |
| Villagers can't settle | Pods stuck Pending (quota, resource requests, or taint) | Scheduling, quotas |
| The herald "has no standing" | ServiceAccount without a role | `Forbidden` errors, `kubectl auth can-i`; the bridge to Act III |

### How fixes lead to the next level

Make progress state-driven, in the cluster. A small in-cluster "town crier" (a CronJob or controller) checks for healthy conditions and then creates the next RoleBinding or ConfigMap. For example, once the sweep's Service has endpoints, it grants access to the wizard's house.

This matches the native-behavior and state-based principles. Nothing is faked.

---

## 3. The main spell: where it could sit

### Option 1: The Keeper (workload level)

A controller keeps recreating the curse, so deleting the cursed object does nothing.

- **Teaches:** reconciliation. Fix the owner, not the child.
- **Assessment:** works well as a mid-boss, but too shallow for the finale.

### Option 2: The Decree (API / admission level)

A ValidatingAdmissionPolicy rejects changes to the royal resources.

- **Teaches:** admission control and reading policy denials.
- **Strength:** the denial message is custom text, so the curse can speak in story voice through a native error. This also helps with the story-line question from the main design document.
- **Caveat:** needs a recent enough Kubernetes version (verify).

### Option 3: The Seal (identity level)

The curse object can only be changed by a user called `king`, and no king exists. The player must:

1. Create a key.
2. Submit a CSR.
3. Approve the CSR.
4. Bind a role.
5. Add the credentials to their kubeconfig.
6. Switch context to the king.
7. Break the spell.

- **Teaches:** CSRs, certificate approval, roles and bindings, kubeconfig contexts.
- **Assessment:** matches the Act III outline exactly (switch context, create CSRs), so it is the most coherent choice.

### Option 4: Combined boss

The Keeper makes the curse reappear, the Seal means only the king can stop it, and the Decree is optional flavor. The final blow is a plain native `kubectl delete` run as `king`.

The finale also teaches RBAC escalation prevention: a player trying to bind a role they don't hold gets Kubernetes's own refusal, and learns why.

### Recommendation

Use the **Seal** as the core, with the **Keeper** as the "it keeps coming back" twist.

---

## 4. Optional story ties

Ideas to accept or reject:

- **7777:** the curse's own voice. A Service with nothing behind it until late in Act II.
- **The wizard:** he knows the spell but is himself bound by it.
- **The Tooth Fairy's gift:** it grants the right to approve certificates.

---

## 5. To verify before committing

- Does k3s enforce NetworkPolicy out of the box? (The dead telephone line fault relies on it.)
- Does k3s sign client CSRs out of the box? (The Seal depends on it.)
- Which Kubernetes version ships admission policies? (The Decree depends on ValidatingAdmissionPolicy.)
- Does the image include `openssl`? (The player needs it for the key and certificate request.)

---

## 6. Open question

Does the main spell feel right as an identity problem (a missing king), or should it sit lower in the stack, with the player breaking it closer to the workload level?
