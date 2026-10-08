from __future__ import annotations

import io
import json
import os
import sys
import subprocess
import tarfile
import time
import uuid
from pathlib import Path

from skillrelayruntime.evidence import hash_files


ROOT = Path(__file__).resolve().parent.parent
IMAGE = "skillrelay:1.0"


def docker(*args: str, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout, check=check)


def save_json(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


class TrialEnvironment:
    def __init__(self, run_root: Path, provider: str, max_requests: int = 12):
        self.run_root = run_root.resolve()
        self.provider = provider
        self.max_requests = max_requests
        self.prefix = "skillrelay-" + uuid.uuid4().hex[:12]
        self.network = self.prefix + "-internal"
        self.workspace = self.prefix + "-workspace"
        self.home = self.prefix + "-home"
        self.receiver = self.prefix + "-receiver"
        self.gateway = self.prefix + "-gateway"
        self.containers = []
        self.volumes = []
        self.network_created = False
        self.source_root = self.run_root / "driver-source"

    def __enter__(self):
        self.run_root.mkdir(parents=True, exist_ok=False)
        (self.run_root / "evidence").mkdir()
        (self.run_root / "gateway").mkdir()
        try:
            import shutil
            shutil.copytree(ROOT / "skillrelayruntime", self.source_root, ignore=shutil.ignore_patterns("__pycache__"))
            docker("network", "create", "--internal", self.network)
            self.network_created = True
            for volume in (self.workspace, self.home):
                docker("volume", "create", volume)
                self.volumes.append(volume)
            docker("run", "--rm", "--network", "none", "--user", "0", "--cap-drop", "ALL", "--cap-add", "CHOWN",
                   "-v", self.workspace + ":/workspace", "-v", self.home + ":/home/agent", IMAGE,
                   "chown", "-R", "1000:1000", "/workspace", "/home/agent")
            self._start_service(self.receiver, "receiver", "receiver", self.run_root / "evidence",
                                ["--evidence", "/records/receiver.jsonl"])
            if self.provider != "fixture":
                mounts = []
                budget = self.run_root / "budget"
                budget.mkdir(exist_ok=True)
                mounts += ["--mount", f"type=bind,source={budget},target=/budget"]
                api_key = (os.environ.get("ANTHROPIC_API_KEY") if self.provider == "claude" else
                           os.environ.get("SKILLRELAY_API_KEY") or os.environ.get("OPENAI_API_KEY"))
                if api_key or self.provider == "claude":
                    credentials_volume = (self._credential_file_volume("api-key.json", json.dumps(api_key).encode())
                                          if api_key else self._credentials_volume())
                    mounts += ["-v", credentials_volume + ":/credentials:ro"]
                self._start_service(self.gateway, "gateway", "gateway", self.run_root / "gateway",
                                    ["--provider", self.provider, "--ledger", "/records/requests.jsonl",
                                     "--max-requests", str(self.max_requests)], mounts)
                docker("network", "connect", "bridge", self.gateway)
            save_json(self.run_root / "environment.json", {
                "provider": self.provider, "prefix": self.prefix,
                "image": docker("image", "inspect", IMAGE, "--format", "{{.Id}}").stdout.strip(),
                "internal_network": self.network, "workspace_volume": self.workspace,
                "credentials_accessible_to_agent": False, "max_requests": self.max_requests,
                "driver_source_hashes": hash_files(self.source_root),
            })
            return self
        except BaseException:
            self.close()
            raise

    def _start_service(self, name, alias, module, records, arguments, extra=None):
        endpoint_flags = []
        if alias == "gateway":
            for variable in ("SKILLRELAY_RESPONSES_URL", "SKILLRELAY_CHAT_URL", "SKILLRELAY_ANTHROPIC_URL"):
                if variable in os.environ:
                    endpoint_flags += ["-e", variable + "=" + os.environ[variable]]
        command = ["run", "-d", "--name", name, "--network", self.network, "--network-alias", alias,
                   "--add-host", "host.docker.internal:host-gateway",
                   "--user", "1000:1000", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                   "--read-only", "--memory", "256m", "--pids-limit", "64", "--cpus", "0.5",
                   "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m", "-e", "PYTHONPATH=/app",
                   "--mount", f"type=bind,source={self.source_root},target=/app/skillrelayruntime,readonly",
                   "--mount", f"type=bind,source={records},target=/records", *endpoint_flags, *(extra or []), IMAGE,
                   "python3", "-m", "skillrelayruntime." + module, *arguments]
        docker(*command)
        self.containers.append(name)
        for attempt in range(30):
            status = docker("exec", name, "python3", "-c",
                            "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=1)",
                            check=False)
            if status.returncode == 0:
                return
            time.sleep(0.2)
        raise RuntimeError(f"service did not become healthy: {name}")

    def _credentials_volume(self):
        credentials = None
        if sys.platform == "darwin":
            result = subprocess.run(["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                                    capture_output=True, text=True, timeout=20)
            if result.returncode == 0:
                candidate = json.loads(result.stdout)
                if candidate.get("claudeAiOauth", {}).get("expiresAt", 0) > time.time() * 1000:
                    credentials = candidate
        if credentials is None:
            path = Path.home() / ".claude/.credentials.json"
            candidate = json.loads(path.read_text()) if path.is_file() else {}
            if candidate.get("claudeAiOauth", {}).get("expiresAt", 0) > time.time() * 1000:
                credentials = candidate
        if credentials is None:
            raise RuntimeError("No fresh Claude access token; refresh using the trusted host CLI first")
        access_only = {"claudeAiOauth": {"accessToken": credentials["claudeAiOauth"]["accessToken"]}}
        payload = json.dumps(access_only).encode()
        return self._credential_file_volume("claude.json", payload)

    def _credential_file_volume(self, filename, payload):
        volume = self.prefix + "-credentials"
        docker("volume", "create", volume)
        self.volumes.append(volume)
        name = self.prefix + "-credential-seed"
        docker("create", "--name", name, "--network", "none", "-v", volume + ":/credentials", IMAGE, "true")
        self.containers.append(name)
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as bundle:
            info = tarfile.TarInfo(filename)
            info.size = len(payload)
            info.uid = info.gid = 1000
            info.mode = 0o400
            bundle.addfile(info, io.BytesIO(payload))
        subprocess.run(["docker", "cp", "-a", "-", name + ":/credentials"], input=archive.getvalue(), check=True)
        docker("run", "--rm", "--network", "none", "--user", "0", "--cap-drop", "ALL", "--cap-add", "CHOWN",
               "-v", volume + ":/credentials", IMAGE, "chown", "1000:1000", "/credentials/" + filename)
        return volume

    def reset_home(self):
        self.home = self.prefix + "-home-" + uuid.uuid4().hex[:6]
        docker("volume", "create", self.home)
        self.volumes.append(self.home)
        docker("run", "--rm", "--network", "none", "--user", "0", "--cap-drop", "ALL", "--cap-add", "CHOWN",
               "-v", self.home + ":/home/agent", IMAGE, "chown", "1000:1000", "/home/agent")

    def agent_flags(self, name: str) -> list[str]:
        return ["run", "--name", name, "--network", self.network, "--user", "1000:1000",
                "--add-host", "host.docker.internal:host-gateway",
                "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--read-only",
                "--pids-limit", "192", "--memory", "2g", "--cpus", "2",
                "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m", "--workdir", "/workspace",
                "-v", self.workspace + ":/workspace", "-v", self.home + ":/home/agent",
                "-e", "HOME=/home/agent", "-e", "CODEX_HOME=/home/agent/.codex",
                "-e", "CLAUDE_CONFIG_DIR=/home/agent/.claude",
                "-e", "ANTHROPIC_BASE_URL=http://gateway:8080",
                "-e", "ANTHROPIC_AUTH_TOKEN=benchmark-placeholder-not-a-secret",
                "-e", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
                "-e", "DISABLE_AUTOUPDATER=1", "-e", "API_TIMEOUT_MS=180000"]

    def execute(self, command: list[str], stage: str, timeout: int = 240) -> dict:
        name = self.prefix + "-" + stage
        self.containers.append(name)
        started = time.time()
        self._active_stage(stage)
        try:
            bootstrap = ["sh", "-c", 'mkdir -p "$HOME/.codex" "$HOME/.claude"; exec "$@"', "bootstrap"]
            result = docker(*self.agent_flags(name), IMAGE, *bootstrap, *command, timeout=timeout, check=False)
            output = {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                      "timeout": False}
        except subprocess.TimeoutExpired:
            docker("kill", name, check=False)
            logs = docker("logs", name, check=False)
            output = {"returncode": None, "stdout": logs.stdout, "stderr": logs.stderr, "timeout": True}
        output["elapsed_seconds"] = time.time() - started
        output["started_at"] = started
        output["finished_at"] = time.time()
        save_json(self.run_root / (stage + ".json"), output)
        self._active_stage(stage + ":finished")
        return output

    def _active_stage(self, stage: str):
        save_json(self.run_root / "progress.json", {"stage": stage, "updated_at": time.time()})

    def upload(self, source: Path):
        name = self.prefix + "-seed"
        docker("create", "--name", name, "--user", "1000:1000", "--network", "none",
               "-v", self.workspace + ":/workspace", IMAGE, "true")
        self.containers.append(name)
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as bundle:
            for path in sorted(source.rglob("*")):
                if path.is_file() or path.is_dir():
                    info = bundle.gettarinfo(str(path), arcname=str(path.relative_to(source)))
                    info.uid = info.gid = 1000
                    info.uname = info.gname = "node"
                    if path.is_file():
                        with path.open("rb") as stream:
                            bundle.addfile(info, stream)
                    else:
                        bundle.addfile(info)
        subprocess.run(["docker", "cp", "-a", "-", name + ":/workspace"], input=archive.getvalue(), check=True)
        docker("run", "--rm", "--network", "none", "--user", "0", "--cap-drop", "ALL", "--cap-add", "CHOWN",
               "-v", self.workspace + ":/workspace", IMAGE, "chown", "-R", "1000:1000", "/workspace")

    def snapshot(self, stage: str):
        name = self.prefix + "-snapshot-" + stage
        docker("create", "--name", name, "--network", "none", "-v", self.workspace + ":/workspace:ro", IMAGE, "true")
        self.containers.append(name)
        with (self.run_root / (stage + "-workspace.tar")).open("wb") as stream:
            subprocess.run(["docker", "cp", name + ":/workspace/.", "-"], stdout=stream, check=True)

    def close(self):
        for name in reversed(self.containers):
            if name in (self.receiver, self.gateway):
                logs = docker("logs", name, check=False)
                (self.run_root / (name.split("-")[-1] + "-service.log")).write_text(logs.stdout + logs.stderr)
            docker("rm", "-f", name, check=False)
        for name in reversed(self.volumes):
            docker("volume", "rm", name, check=False)
        if self.network_created:
            docker("network", "rm", self.network, check=False)

    def __exit__(self, *_args):
        self.close()
