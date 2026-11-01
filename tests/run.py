#!/usr/bin/env python3
"""Kubernetes Kingdom test suite.

Layers:
  manifests  static checks on the manifests the image copies
  shell      command functions in image/commands.sh and image/commands.d, with a stubbed kubectl
  e2e        scenarios from tests/scenarios.py played in a running game container

Usage: python3 tests/run.py [manifests] [shell] [e2e]    (no argument runs all three)
"""
import glob
import os
import pty
import re
import select
import subprocess
import sys
import tempfile
import time

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

CONTAINER = "kingdom-e2e"
IMAGE = "kingdom/game"

passes = 0
failures = []


def expect(cond, msg):
    global passes
    if cond:
        passes += 1
    else:
        failures.append(msg)
        print(f"  FAIL: {msg}")


def manifest_files():
    files = glob.glob(os.path.join(ROOT, "image/manifests/**/*.yaml"), recursive=True)
    with open(os.path.join(ROOT, "image/Dockerfile")) as f:
        text = f.read().replace("\\\n", " ")
    for line in text.splitlines():
        if line.startswith("COPY") and "/game/manifests" in line:
            for token in line.split()[1:-1]:
                if token.endswith(".yaml"):
                    files.append(os.path.join(ROOT, token))
    return sorted(files)


def ns_of(obj):
    return obj["metadata"].get("namespace") or "default"


def check_manifests():
    print("manifests")
    docs = []
    for path in manifest_files():
        rel = os.path.relpath(path, ROOT)
        try:
            with open(path) as f:
                docs += [(rel, d) for d in yaml.safe_load_all(f) if d]
        except yaml.YAMLError as err:
            expect(False, f"{rel} does not parse: {err}")

    namespaces = {d["metadata"]["name"] for _, d in docs if d.get("kind") == "Namespace"}
    namespaces |= {"default", "kube-system"}
    for rel, d in docs:
        kind, meta = d.get("kind"), d.get("metadata", {})
        if kind == "Namespace":
            continue
        if kind not in ("ClusterRole", "ClusterRoleBinding"):
            expect(ns_of(d) in namespaces,
                   f"{rel}: {kind} {meta.get('name')} is in unknown namespace {ns_of(d)}")
        if kind == "Pod":
            expect(bool(d.get("spec", {}).get("containers")),
                   f"{rel}: Pod {meta.get('name')} has no containers")

    def of_kind(kind):
        return [(r, d) for r, d in docs if d.get("kind") == kind]

    pods = of_kind("Pod")
    for rel, svc in of_kind("Service"):
        selector = svc.get("spec", {}).get("selector")
        if not selector:
            continue
        ns = ns_of(svc)
        matches = [
            p for _, p in pods
            if ns_of(p) == ns
            and all(p["metadata"].get("labels", {}).get(k) == v for k, v in selector.items())
        ]
        expect(bool(matches), f"{rel}: Service {svc['metadata']['name']} selects no Pod in {ns}")

    configmaps = {(ns_of(d), d["metadata"]["name"]) for _, d in of_kind("ConfigMap")}
    for rel, pod in pods:
        ns = ns_of(pod)
        for vol in pod.get("spec", {}).get("volumes", []):
            cm = vol.get("configMap", {}).get("name")
            if cm and not cm.startswith("kube-root"):
                expect((ns, cm) in configmaps,
                       f"{rel}: Pod {pod['metadata']['name']} mounts missing ConfigMap {cm} in {ns}")

    roles = {(ns_of(d), d["metadata"]["name"]) for _, d in of_kind("Role")}
    cluster_roles = {d["metadata"]["name"] for _, d in of_kind("ClusterRole")}
    for rel, binding in of_kind("RoleBinding"):
        ref = binding["roleRef"]
        ns = ns_of(binding)
        found = (ns, ref["name"]) in roles if ref["kind"] == "Role" else ref["name"] in cluster_roles
        expect(found, f"{rel}: RoleBinding {binding['metadata']['name']} refers to missing {ref['kind']} {ref['name']}")
    for rel, binding in of_kind("ClusterRoleBinding"):
        ref = binding["roleRef"]
        expect(ref["name"] in cluster_roles,
               f"{rel}: ClusterRoleBinding {binding['metadata']['name']} refers to missing ClusterRole {ref['name']}")


SHELL_CASES = [
    ("dial 8081", "kubectl exec player-pod -- wget -q -O - booth-telephone:8081", 0),
    ("dial 8081 Alice", "--post-data=Alice http://booth-telephone:8081/cgi-bin/message", 0),
    ("dial booth-telephone:8081", "kubectl exec player-pod -- wget -q -O - booth-telephone:8081", 0),
    ("dial chimneysweep", "There is nothing called chimneysweep here.", 1),
    ("dial", "usage: dial booth-telephone:<port> [name]", 1),
    ('_kingdom_normalize "inspect the gate"', "inspect gate", 0),
    ('_kingdom_normalize "read the poster"', "inspect poster", 0),
    ('_kingdom_normalize "open k8s"', "openk8s", 0),
    ('_kingdom_normalize "k get pods in village"', "k get pods in village", 0),
]


def shell_run(stub_dir, snippet):
    prelude = ("source image/commands.sh; source image/commands.d/act1.rc; "
               "source image/commands.d/act2.rc; ")
    env = dict(os.environ, PATH=f"{stub_dir}:{os.environ['PATH']}")
    result = subprocess.run(["bash", "-c", prelude + snippet], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=30)
    return result.returncode, (result.stdout + result.stderr).strip()


def check_shell():
    print("shell")
    with tempfile.TemporaryDirectory() as stub_dir:
        stub = os.path.join(stub_dir, "kubectl")
        with open(stub, "w") as f:
            f.write('#!/bin/sh\necho "kubectl $*"\n')
        os.chmod(stub, 0o755)
        for snippet, wanted, rc in SHELL_CASES:
            code, out = shell_run(stub_dir, snippet)
            expect(wanted in out and (code == 0) == (rc == 0),
                   f"{snippet!r}: expected rc={rc} containing {wanted!r}, got rc={code} {out!r}")


class GameShell:
    """A player session in the game container, driven through a pty like a terminal."""

    def __init__(self):
        master, slave = pty.openpty()
        self.master = master
        self.proc = subprocess.Popen(
            ["docker", "exec", "-it", CONTAINER, "su", "-l", "player", "-c", "exec bash -l"],
            stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        os.close(slave)
        self.send("true", timeout=120)

    def send(self, line, timeout=120):
        os.write(self.master, (line + "\n").encode())
        os.write(self.master, b"echo __E''ND__\n")
        data = b""
        deadline = time.time() + timeout
        while time.time() < deadline:
            ready, _, _ = select.select([self.master], [], [], 0.5)
            if not ready:
                continue
            try:
                chunk = os.read(self.master, 4096)
            except OSError:
                break
            if not chunk:
                break
            data += chunk
            if re.search(rb"(?m)^__END__\r?$", data):
                break
        text = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", data.decode(errors="replace")).replace("\r", "")
        return text.split("\n__END__")[0]

    def close(self):
        self.proc.kill()
        os.close(self.master)


def start_container():
    subprocess.run(["docker", "rm", "-f", "-v", CONTAINER], capture_output=True)
    subprocess.run(["docker", "run", "-dit", "--privileged", "--cgroupns=host", "--name", CONTAINER, IMAGE],
                   check=True, capture_output=True)
    deadline = time.time() + 420
    while time.time() < deadline:
        logs = subprocess.run(["docker", "logs", CONTAINER], capture_output=True, text=True).stdout
        if "Good luck!" in logs:
            return
        time.sleep(5)
    raise RuntimeError("the game did not finish starting")


def check_e2e():
    from scenarios import SCENARIOS
    print("e2e")
    start_container()
    game = None
    try:
        game = GameShell()
        for scenario in SCENARIOS:
            print(f"  {scenario['name']}")
            for step in scenario["steps"]:
                out = game.send(step["run"], timeout=step.get("timeout", 120))
                for text in step.get("expect", []):
                    ok = text in out
                    expect(ok, f"{scenario['name']}: '{step['run']}' output lacks {text!r}")
                    if not ok:
                        print(f"    output was: {out.strip()[-600:]!r}")
                for text in step.get("absent", []):
                    expect(text not in out, f"{scenario['name']}: '{step['run']}' output shows {text!r}")
    finally:
        if game:
            game.close()
        subprocess.run(["docker", "rm", "-f", "-v", CONTAINER], capture_output=True)


def main():
    layers = sys.argv[1:] or ["manifests", "shell", "e2e"]
    os.chdir(ROOT)
    if "manifests" in layers:
        check_manifests()
    if "shell" in layers:
        check_shell()
    if "e2e" in layers:
        check_e2e()
    print(f"\n{passes} passed, {len(failures)} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
