# CloudOps Toolkit

[![CI](https://github.com/kaushalye1234/cloudops-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/kaushalye1234/cloudops-toolkit/actions/workflows/ci.yml)

A learning-focused command-line toolkit for repeatable Linux health checks,
network diagnostics, Docker inspection and backup automation.

> **Project status:** early, usable milestone. Local Linux and Docker operations
> are implemented. AWS automation is planned and is not presented as completed.

## Why this project exists

Cloud and DevOps engineers repeatedly inspect hosts, ports, disk capacity,
containers and backups. This project turns those tasks into small, testable
commands with predictable output and useful exit codes for automation.

## Current commands

```bash
cloudops health
cloudops disk --path / --warning 80
cloudops ports localhost 8080
cloudops containers
cloudops logs my-container --tail 100
```

Use `--json` before the command for machine-readable output:

```bash
cloudops --json disk --path /
```

## Bash automation

The `scripts/` directory includes guarded scripts for system health, disk
checks, port checks, Docker cleanup review and timestamped backups. Docker
cleanup is intentionally a dry run so it cannot unexpectedly delete data.

## Install locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e . pytest ruff
cloudops health
pytest -q
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`. The host
checks are designed primarily for Linux or WSL.

## Run with Docker

```bash
docker build -t cloudops-toolkit .
docker run --rm cloudops-toolkit health
```

Container health describes the container environment. Host Docker inspection
requires local installation because exposing the Docker socket to a container
grants powerful host access and is intentionally not enabled by default.

## Quality controls

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
- [x] Automated tests and CI
- [ ] Structured application log analysis
- [ ] Backup verification and retention policies
- [ ] Deployment helpers
- [ ] AWS inventory and health checks using `boto3`
- [ ] Prometheus-compatible metrics output

## Security notes

- Do not commit credentials, access keys or `.env` files.
- Review all cleanup output before deleting Docker resources.
- Backups should be restored and verified, not only created.
- Future AWS commands will use normal credential-provider chains rather than
  accepting secrets as command-line arguments.

## Author

Chamindu Kaushalya - Software Engineering undergraduate at SLIIT, currently
building hands-on Cloud and DevOps skills.

- GitHub: <https://github.com/kaushalye1234>
- LinkedIn: <https://linkedin.com/in/chamindu-kaushalya-gunarathne-991829351/>
