"""Command-line interface for local operations checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

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

    services = commands.add_parser("services", help="Check Linux system services")
    services.add_argument(
        "names",
        nargs="*",
        default=["docker", "ssh"],
        help="Service names to check",
    )

    report = commands.add_parser("report", help="Generate a local system report")
    report.add_argument("--output-dir", default="reports")

    commands.add_parser("scan", help="Run local quality and test checks")

    logs = commands.add_parser("logs", help="Read recent Docker container logs")
    logs.add_argument("container")
    logs.add_argument("--tail", type=int, default=50)

    return parser


def print_result(result: CheckResult, as_json: bool) -> None:
    if as_json:
        print(result.to_json())
        return

    print(f"[{result.status.upper()}] {result.message}")

    for key, value in result.details.items():
        print(f"  {key}: {json.dumps(value) if isinstance(value, (dict, list)) else value}")


def check_services(names: list[str]) -> list[str]:
    service_lines = []
    for name in names:
        process = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True,
            text=True,
            check=False,
        )
        status = process.stdout.strip() or process.stderr.strip()
        service_lines.append(f"{name}: {status}")
    return service_lines


def run_scan() -> int:
    checks = [
        ["ruff", "check", "src", "tests"],
        ["pytest"],
    ]
    failed = False

    for command in checks:
        print(f"Running: {' '.join(command)}")
        process = subprocess.run(command, check=False)
        if process.returncode != 0:
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
    service_lines = check_services(["docker", "ssh"])

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
                *service_lines,
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
        process = subprocess.run(
            ["bash", "scripts/backup.sh", args.source, args.destination],
            check=False,
        )
        return process.returncode

    elif args.command == "services":
        for line in check_services(args.names):
            print(line)
        return 0

    elif args.command == "report":
        report_path = write_report(args.output_dir)
        print(f"Report created: {report_path}")
        return 0

    elif args.command == "scan":
        return run_scan()

    elif args.command == "logs":
        process = subprocess.run(
            ["docker", "logs", "--tail", str(args.tail), args.container],
            check=False,
        )
        return process.returncode

    else:
        parser.error("Unknown command")

    print_result(result, args.json)
    return 0 if result.status in {"ok", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
