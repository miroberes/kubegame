# Kubernetes Kingdom: CKA Troubleshooting Mapping

**Status:** brainstorm. Companion to `kubernetes-kingdom-design.md` and `curse-design.md`.

**Purpose:** compare the game's debugging ladder with the CKA exam's Troubleshooting domain, to see what the game can teach and what it can't.

---

## 1. Background

Troubleshooting is the heaviest CKA domain, at about 30% of the exam (one source says 31%). Sources differ on the exact wording and weights of the competencies. Check the official curriculum on the CNCF / Linux Foundation pages before mapping to it, and again near any release, since the curriculum changes.

---

## 2. Mapping the CKA troubleshooting areas to the game

| CKA troubleshooting area | Typical exam tasks | Fits the game? |
|---|---|---|
| Container output streams | `logs`, `logs --previous`, `-c`, events | **Yes.** Already in Act I and the ladder (the dying chimneysweep pod, ImagePullBackOff) |
| Application failure | CrashLoopBackOff, bad image, missing ConfigMap or Secret, Pending pods | **Yes.** Most of the ladder |
| Services and networking | Selectors and endpoints, ports, DNS, NetworkPolicy, CNI | **Mostly.** See the DNS note in section 3 |
| Resource usage | `kubectl top`, quotas, limits | **Probably.** Needs metrics-server; check whether k3s bundles and enables it by default |
| Debugging pods | `kubectl exec`, `kubectl debug`, ephemeral containers | **Yes, but missing from the ladder.** The player's role needs the `pods/ephemeralcontainers` permission |
| Cluster and node problems | NotReady nodes, kubelet down, `journalctl`, `systemctl` | **Partly.** Cordons, taints, and node conditions work through the API. Fixing a kubelet needs node access |
| Cluster component failure | Broken API server, scheduler, or controller-manager (usually bad flags or paths in static pod manifests) | **No, not faithfully.** k3s runs the control plane in one process, with no static pod manifests to break |

---

## 3. Where the design conflicts with CKA-style troubleshooting

- **Node and control-plane work needs a node shell.** The exam has the candidate edit files on a node and restart services. The game's player is a non-root user in a restricted shell with no `sudo`. Giving them node root would also let them read the admin kubeconfig, which breaks the RBAC design.
- **k3s is not kubeadm.** Even with node access, there is no `systemctl restart kubelet` and no manifest directory to fix. The exam-practice specification flagged the same limit for kind.
- **`kube-system` is out of the player's reach.** A broken CoreDNS or kube-proxy can be diagnosed but not repaired, unless a narrow role is granted. The cleaner option is to put the faults in the player's own namespaces: a Service selector, a NetworkPolicy, a ConfigMap, or a quota.
- **DNS note.** A "works by IP, fails by name" fault is only fixable by the player if they have a narrow role over a village-level DNS setup.

---

## 4. Faults worth adding to the ladder

| Kingdom symptom (idea) | Kubernetes fault | What the player learns |
|---|---|---|
| Villagers refuse to move in | A node is cordoned or tainted, so pods stay Pending | `describe node`, `uncordon`, taints and tolerations |
| The wizard's house won't open up | A pod that can't be entered with `exec` (distroless) | `kubectl debug`, ephemeral containers |
| The mill is exhausted | A resource-hungry pod | `kubectl top`, resource limits |
| The telephone works by number, not by name | Service reachable by IP but not by name (DNS) | DNS vs IP, name resolution (needs a narrow role, see above) |
| The line connects but says nothing | Right selector, wrong `targetPort` | Checking more than one thing |

These are suggestions in addition to the seven curses in `curse-design.md`.

---

## 5. Realistic position for the game

- **Cover API-level troubleshooting in the main game,** and say clearly that this is the part of CKA troubleshooting the game teaches.
- **Treat node and control-plane breakage as an optional extension** on a different backend (a kubeadm-style VM). This matches the "extensible cluster backend" principle from the exam-practice specification.
- **Do not fake node tasks inside the container.** That would conflict with the "real Kubernetes, no simulated commands" rule.
- **Pacing differs from the exam.** The exam gives a task and a clock. The game gives a story and a symptom. The CKA fault types can be kept while the story, not a countdown, sets the pace.

---

## 6. To verify

- Current CKA curriculum, domain weights, and exact competency wording (official CNCF / Linux Foundation pages).
- Does k3s bundle and enable metrics-server by default? (`kubectl top`)
- Does k3s enforce NetworkPolicy out of the box?
- Can the restricted player role be granted `pods/ephemeralcontainers` cleanly for `kubectl debug`?

---

## 7. Open question

Should the game cover CKA-style troubleshooting as an **explicit goal** (the ladder is built to match the competencies), or **borrow the fault types** only where they fit the story? The answer decides whether a CKA mapping sheet is added to `curse-design.xlsx`.
