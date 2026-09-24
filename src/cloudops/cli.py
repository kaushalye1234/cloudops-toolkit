"""Command-line interface for local operations checks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from cloudops.backup import create_backup
from cloudops.checks import (
    CheckResult,
    disk_check,
    docker_check,
    port_check,
    system_health,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cloudops",
        description="Local Linux and container operations toolkit",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    commands = parser.add_subparsers(dest="command", required=True)

    health = commands.add_parser("health", help="Check system health")
    health.add_argument("--path", default="/")
    health.add_argument("--warning", type=float, default=80.0)

    disk = commands.add_parser("disk", help="Check disk usage")
    disk.add_argument("--path", default="/")
    disk.add_argument("--warning", type=float, default=80.0)

    ports = commands.add_parser("ports", help="Test a TCP endpoint")
    ports.add_argument("host")
    ports.add_argument("port", type=int)
    ports.add_argument("--timeout", type=float, default=2.0)

    commands.add_parser("containers", help="Show running Docker containers")

    backup = commands.add_parser("backup", help="Create a compressed backup of a directory")
    backup.add_argument("source")
    backup.add_argument("destination")

    verify_backup = commands.add_parser(
        "verify-backup",
        help="Verify that a backup archive is readable",
    )
    verify_backup.add_argument("archive")

    services = commands.add_parser("services", help="Check Linux system services")
    services.add_argument(
        "names",
        nargs="*",
        default=["docker", "ssh"],
        help="Service names to check",
    )

    report = commands.add_parser("report", help="Generate a local system report")
    report.add_argument("--output-dir", default="reports")

    scan = commands.add_parser("scan", help="Run quality checks for a source checkout")
    scan.add_argument(
        "--project",
        default=".",
        help="Path to the project checkout (default: current directory)",
    )
    commands.add_parser("doctor", help="Check local DevOps tool availability")

    logs = commands.add_parser("logs", help="Read recent Docker container logs")
    logs.add_argument("container")
    logs.add_argument("--tail", type=non_negative_int, default=50)

    return parser


def print_result(result: CheckResult, as_json: bool) -> None:
    if as_json:
        print(result.to_json())
        return

    print(f"[{result.status.upper()}] {result.message}")

    for key, value in result.details.items():
        print(f"  {key}: {json.dumps(value) if isinstance(value, (dict, list)) else value}")


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be zero or greater")
    return parsed


def check_services(names: list[str]) -> list[CheckResult]:
    if shutil.which("systemctl") is None:
        return [
            CheckResult("critical", f"{name}: systemctl is not installed", {"service": name})
            for name in names
        ]

    results = []

    for name in names:
        try:
            process = subprocess.run(
                ["systemctl", "is-active", name],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except subprocess.TimeoutExpired:
            results.append(
                CheckResult("critical", f"{name}: systemctl timed out", {"service": name})
            )
            continue

        status = process.stdout.strip() or process.stderr.strip()
        check_status = "ok" if process.returncode == 0 and status == "active" else "critical"
        results.append(
            CheckResult(check_status, f"{name}: {status or 'unknown'}", {"service": name})
        )

    return results


def verify_backup_archive(archive: str) -> int:
    archive_path = Path(archive)

    if not archive_path.exists():
        print(f"[CRITICAL] Backup archive does not exist: {archive}")
        return 1

    if not archive_path.is_file():
        print(f"[CRITICAL] Backup archive is not a file: {archive}")
        return 1

    try:
        with tarfile.open(archive_path, "r:gz") as backup:
            backup.getmembers()
    except (OSError, tarfile.TarError) as exc:
        print(f"[CRITICAL] Backup archive is not readable: {archive}")
        print(str(exc))
        return 1
    else:
        print(f"[OK] Backup archive is readable: {archive}")
        return 0


def run_scan(project: str) -> int:
    project_path = Path(project).resolve()
    if not (project_path / "pyproject.toml").is_file():
        print(f"[CRITICAL] No pyproject.toml found in: {project_path}", file=sys.stderr)
        return 1

    checks = [
        [sys.executable, "-m", "ruff", "check", "src", "tests"],
        [sys.executable, "-m", "pytest"],
    ]
    failed = False

    for command in checks:
        display_command = " ".join(command[2:])
        print(f"Running in {project_path}: {display_command}")
        process = subprocess.run(command, cwd=project_path, check=False)

        if process.returncode != 0:
            failed = True

    return 1 if failed else 0


def run_doctor() -> int:
    failed = False

    print(f"[OK] python found at {sys.executable}")

    for module in ["ruff", "pytest"]:
        if importlib.util.find_spec(module) is not None:
            print(f"[OK] {module} Python module is installed")
        else:
            print(f"[WARNING] {module} Python module is not installed")
            failed = True

    for tool in ["git", "docker", "systemctl", "tar", "shellcheck"]:
        path = shutil.which(tool)

        if path:
            print(f"[OK] {tool} found at {path}")
        else:
            print(f"[WARNING] {tool} not found")
            failed = True

    return 1 if failed else 0


def write_report(output_dir: str) -> Path:
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = report_dir / f"system-report-{timestamp}.txt"

    health = system_health()
    disk = disk_check()
    docker = docker_check()
    service_results = check_services(["docker", "ssh"])

    report_path.write_text(
        "\n".join(
            [
                "CloudOps System Report",
                f"Generated at: {timestamp}",
                "",
                "Health",
                f"- {health.status.upper()}: {health.message}",
                "",
                "Disk",
                f"- {disk.status.upper()}: {disk.message}",
                "",
                "Docker",
                f"- {docker.status.upper()}: {docker.message}",
                "",
                "Services",
                *(f"- {result.status.upper()}: {result.message}" for result in service_results),
                "",
            ]
        ),
        encoding="utf-8",
    )

    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "health":
        result = system_health(args.path, args.warning)

    elif args.command == "disk":
        result = disk_check(args.path, args.warning)

    elif args.command == "ports":
        if not 1 <= args.port <= 65535:
            print("Port must be between 1 and 65535", file=sys.stderr)
            return 2

        result = port_check(args.host, args.port, args.timeout)

    elif args.command == "containers":
        result = docker_check()

    elif args.command == "backup":
        try:
            archive_path = create_backup(args.source, args.destination)
        except (OSError, ValueError) as exc:
            print(f"[CRITICAL] {exc}", file=sys.stderr)
            return 1
        print(f"Backup created: {archive_path}")
        return 0

    elif args.command == "verify-backup":
        return verify_backup_archive(args.archive)

    elif args.command == "services":
        results = check_services(args.names)
        for result in results:
            print_result(result, args.json)
        return 0 if all(result.status == "ok" for result in results) else 1

    elif args.command == "report":
        report_path = write_report(args.output_dir)
        print(f"Report created: {report_path}")
        return 0

    elif args.command == "scan":
        return run_scan(args.project)

    elif args.command == "doctor":
        return run_doctor()

    elif args.command == "logs":
        if shutil.which("docker") is None:
            print("[CRITICAL] Docker CLI is not installed", file=sys.stderr)
            return 1
        try:
            process = subprocess.run(
                ["docker", "logs", "--tail", str(args.tail), args.container],
                timeout=10,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print("[CRITICAL] Docker did not respond within 10 seconds", file=sys.stderr)
            return 1
        return process.returncode

    else:
        parser.error("Unknown command")

    print_result(result, args.json)
    return 0 if result.status in {"ok", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
