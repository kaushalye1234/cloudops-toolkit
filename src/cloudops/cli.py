"""Command-line interface for local operations checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from cloudops.checks import (
    CheckResult,
    disk_check,
    docker_check,
    port_check,
    system_health,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cloudops", description="Local Linux and container operations toolkit")
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
    else:
        process = subprocess.run(
            ["docker", "logs", "--tail", str(args.tail), args.container],
            check=False,
        )
        return process.returncode

    print_result(result, args.json)
    return 0 if result.status in {"ok", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
