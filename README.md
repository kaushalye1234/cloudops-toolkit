# CloudOps Toolkit

[![CI](https://github.com/kaushalye1234/cloudops-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/kaushalye1234/cloudops-toolkit/actions/workflows/ci.yml)

A learning-focused command-line toolkit for repeatable Linux health checks, network diagnostics, Docker inspection, service checks, backup automation and local system reporting.

> **Project status:** early, usable milestone. Local Linux and Docker operations are implemented. AWS automation is planned and is not presented as completed.

## Why this project exists

Cloud and DevOps engineers repeatedly inspect hosts, ports, disk capacity, services, containers, logs, backups and system reports. This project turns those tasks into small, testable commands with predictable output and useful exit codes for automation.

This repository is part of my DevOps and Cloud internship preparation. It focuses on practical Linux, Bash, Docker, Python CLI design, testing and CI/CD skills.

## Current Features

- Check basic Linux system health
- Check disk usage with warning thresholds
- Test TCP port connectivity
- Inspect running Docker containers
- Read recent Docker container logs
- Create compressed directory backups
- Check Linux service status with `systemctl`
- Generate timestamped local system reports
- Run automated tests and linting with GitHub Actions

## Current Commands

```bash
cloudops health
cloudops disk --path / --warning 80
cloudops ports github.com 443
cloudops containers
cloudops logs task-manager-backend --tail 20
cloudops backup src backups
cloudops services docker ssh
cloudops report
```

Use `--json` before supported check commands for machine-readable output:

```bash
cloudops --json disk --path /
cloudops --json containers
```

## Reports

The `report` command creates a timestamped text report in the `reports/` directory. Generated reports are ignored by Git so local machine output is not committed accidentally.

```bash
cloudops report
ls reports
```

## Bash Automation

The `scripts/` directory includes guarded scripts for system health, disk checks, port checks, Docker cleanup review and timestamped backups. Docker cleanup is intentionally a dry run so it cannot unexpectedly delete data.

Example backup script usage:

```bash
bash scripts/backup.sh src backups
```

## Install Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e . pytest ruff
cloudops health
pytest
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`. The host checks are designed primarily for Linux or WSL.

## Run With Docker

```bash
docker build -t cloudops-toolkit .
docker run --rm cloudops-toolkit health
```

Container health describes the container environment. Host Docker inspection requires local installation because exposing the Docker socket to a container grants powerful host access and is intentionally not enabled by default.

## Quality Controls

Every push and pull request runs:

- Python tests with `pytest`
- Python linting with `ruff`
- Bash analysis with `shellcheck`
- A Docker image build and smoke test

## Roadmap

- [x] System health and disk checks
- [x] TCP port diagnostics
- [x] Docker container and log inspection
- [x] Safe local backup script
- [x] Backup command in the Python CLI
- [x] Linux service status command
- [x] Local system report command
- [x] Automated tests and CI
- [ ] Structured application log analysis
- [ ] Backup verification and retention policies
- [ ] Deployment helpers
- [ ] AWS inventory and health checks using `boto3`
- [ ] Prometheus-compatible metrics output

## Security Notes

- Do not commit credentials, access keys or `.env` files.
- Review all cleanup output before deleting Docker resources.
- Backups should be restored and verified, not only created.
- Future AWS commands will use normal credential-provider chains rather than accepting secrets as command-line arguments.

## Author

Chamindu Kaushalya - Software Engineering undergraduate at SLIIT, currently building hands-on Cloud and DevOps skills.

- GitHub: <https://github.com/kaushalye1234>
- LinkedIn: <https://linkedin.com/in/chamindu-kaushalya-gunarathne-991829351/>
