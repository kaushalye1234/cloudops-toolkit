"""Portable system checks used by the CloudOps CLI."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    status: str
    message: str
    details: dict[str, object]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def disk_check(path: str = "/", warning_percent: float = 80.0) -> CheckResult:
    target = Path(path)
    if not target.exists():
        return CheckResult("critical", f"Path does not exist: {path}", {"path": path})

    usage = shutil.disk_usage(target)
    used_percent = round((usage.used / usage.total) * 100, 2) if usage.total else 0.0
    status = "warning" if used_percent >= warning_percent else "ok"
    return CheckResult(
        status,
        f"Disk usage for {target}: {used_percent}%",
        {
            "path": str(target),
            "used_percent": used_percent,
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "warning_percent": warning_percent,
        },
    )


def port_check(host: str, port: int, timeout: float = 2.0) -> CheckResult:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return CheckResult("ok", f"{host}:{port} is reachable", {"host": host, "port": port})
    except OSError as exc:
        return CheckResult(
            "critical",
            f"{host}:{port} is not reachable",
            {"host": host, "port": port, "error": str(exc)},
        )


def docker_check() -> CheckResult:
    if shutil.which("docker") is None:
        return CheckResult("critical", "Docker CLI is not installed", {})

    result = subprocess.run(
        ["docker", "ps", "--format", "{{json .}}"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        return CheckResult("critical", "Docker daemon is unavailable", {"error": result.stderr.strip()})

    containers = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    return CheckResult(
        "ok",
        f"Docker is available; {len(containers)} running container(s)",
        {"running_containers": containers},
    )


def system_health(path: str = "/", warning_percent: float = 80.0) -> CheckResult:
    disk = disk_check(path, warning_percent)
    load = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
    status = disk.status
    return CheckResult(
        status,
        "System health check completed",
        {
            "disk": asdict(disk),
            "load_average_1m": round(load[0], 2),
            "load_average_5m": round(load[1], 2),
            "load_average_15m": round(load[2], 2),
        },
    )
