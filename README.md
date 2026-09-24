# CloudOps Toolkit

[![CI](https://github.com/kaushalye1234/cloudops-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/kaushalye1234/cloudops-toolkit/actions/workflows/ci.yml)

CloudOps Toolkit is a small Python CLI for repeatable Linux host and Docker checks. It turns common operations tasks—checking disk pressure, testing a TCP endpoint, inspecting containers and logs, checking services, and validating backups—into commands with predictable output and automation-friendly exit codes.

> **Scope:** this project demonstrates local Linux, Bash, Docker, Python packaging, testing, and GitHub Actions. It does not currently implement AWS or Kubernetes operations.

## Why it exists

An operator often needs a quick answer before deeper troubleshooting: Is the disk nearly full? Can this host reach a port? Is a service active? Is Docker responding? Can a backup actually be opened? The toolkit puts those checks behind one installable command instead of a collection of untested snippets.

For a reviewer, the main engineering evidence is:

- an installable `src/`-layout Python package with no runtime dependencies;
- explicit success and failure exit codes suitable for scripts and CI;
- safe backup behavior, including no overwrite and no destination-inside-source;
- unit and CLI regression tests for host-tool failures and malformed output;
- Bash, package-install, and disposable Docker demonstrations;
- GitHub Actions jobs for tests, lint, ShellCheck, package use, and Docker use.

## Quick start

Linux or WSL with Python 3.10 or newer is the primary environment.

```bash
git clone https://github.com/kaushalye1234/cloudops-toolkit.git
cd cloudops-toolkit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ".[dev]"

cloudops health
cloudops disk --path / --warning 80
cloudops doctor
```

The development extra installs Pytest and Ruff for `cloudops scan`. Runtime commands themselves use only the Python standard library and host tools they explicitly inspect.

## Five-minute reproducible demo

After installation, leave the repository and run the toolkit from a temporary directory:

```bash
mkdir -p /tmp/cloudops-demo/app
printf 'service=ready\n' > /tmp/cloudops-demo/app/config.txt
cd /tmp/cloudops-demo

cloudops --json disk --path / --warning 101
cloudops backup app backups
cloudops verify-backup "$(find backups -name 'backup-*.tar.gz' -print -quit)"
cloudops report --output-dir reports
find backups reports -type f
```

`101` keeps this demonstration independent of the machine's current disk usage. A real alert threshold should normally be between 80 and 90.

Example output, shortened for readability:

```text
{
  "status": "ok",
  "message": "Disk usage for /: 42.18%",
  "details": {"path": "/", "warning_percent": 101.0}
}
Backup created: /tmp/cloudops-demo/backups/backup-20260924T090233Z.tar.gz
[OK] Backup archive is readable: backups/backup-20260924T090233Z.tar.gz
Report created: reports/system-report-20260924T090233Z.txt
```

For an automated version of this check, run `bash scripts/verify-installed.sh`. It builds and installs the package into a fresh virtual environment, changes to `/tmp`, exercises the commands, and removes its temporary files.

## Practical Docker operations demo

This demonstration builds the toolkit image, starts a disposable Python HTTP service from that image, discovers its random host port, and then uses the installed toolkit to test the port, find the container, and read its logs. It removes the container automatically and uses no paid service.

From the repository root with Docker running:

```bash
source .venv/bin/activate
bash scripts/docker-ops-demo.sh
```

The key output looks like this:

```text
3/5 Wait for the service and check its TCP port
[OK] 127.0.0.1:49153 is reachable
4/5 Inspect the running container
[OK] Found cloudops-demo-service-1234 (cloudops-toolkit:demo, Up 1 second)
5/5 Generate traffic and inspect recent container logs
200
Demo passed. The disposable container will now be removed.
```

This is a local Docker operations workflow, not a claim of Kubernetes or cloud-platform deployment experience.

## Commands

| Command | Purpose | Success behavior |
| --- | --- | --- |
| `cloudops health` | Summarize disk status and load averages | Exit `0` for OK/warning |
| `cloudops disk --path / --warning 80` | Check usage against a threshold | Exit `0` for OK/warning |
| `cloudops ports HOST PORT` | Attempt a TCP connection | Exit `0` when reachable |
| `cloudops containers` | List running Docker containers | Exit `0` when Docker responds |
| `cloudops logs CONTAINER --tail 20` | Read recent container logs | Return Docker's exit code |
| `cloudops backup SOURCE DESTINATION` | Create a timestamped `.tar.gz` | Never overwrite an archive |
| `cloudops verify-backup ARCHIVE` | Parse an archive before trusting it | Exit `0` when readable |
| `cloudops services docker ssh` | Query Linux services with `systemctl` | Exit `0` only when all are active |
| `cloudops report --output-dir reports` | Write a timestamped host report | Create a non-empty text file |
| `cloudops scan --project PATH` | Run Ruff and Pytest for a checkout | Exit `0` when both pass |
| `cloudops doctor` | Find local development/operations tools | Exit `1` when any are missing |

Place `--json` before `health`, `disk`, `containers`, or `services` for machine-readable output. For example:

```bash
cloudops --json containers
```

Host-state commands can legitimately return `1`: a closed port, inactive service, missing Docker daemon, corrupt backup, or incomplete development environment is a diagnostic result rather than a Python crash.

## Architecture

```text
cloudops command
    |
    +-- argparse routing and exit-code policy        src/cloudops/cli.py
    |
    +-- portable checks and structured CheckResult  src/cloudops/checks.py
    |
    +-- atomic compressed backup creation           src/cloudops/backup.py
    |
    +-- host interfaces
          +-- Python stdlib: disk, sockets, tar, reports
          +-- systemctl: Linux service state
          +-- Docker CLI: containers and logs
```

The CLI keeps portable logic in Python and treats `systemctl` and Docker as explicit host boundaries. Tests replace those boundaries with controlled responses, while the Docker demo verifies the real integration when a daemon is available.

## Development and quality checks

```bash
source .venv/bin/activate
cloudops scan --project "$PWD"
shellcheck scripts/*.sh
bash scripts/verify-installed.sh
docker build -t cloudops-toolkit:test .
docker run --rm cloudops-toolkit:test disk --path / --warning 101
```

You can invoke the installed scan command from elsewhere by passing the checkout explicitly:

```bash
cd /tmp
cloudops scan --project /path/to/cloudops-toolkit
```

GitHub Actions runs Python tests and Ruff, verifies a fresh installed package outside the checkout, checks every Bash script with ShellCheck, builds the Docker image, runs a container smoke check, and executes the Docker operations demo. The test job also uploads a generated system report artifact.

## Safety choices

- Docker cleanup is review-only; `scripts/docker-cleanup.sh` never deletes resources.
- Backup destinations inside the source are rejected to prevent self-inclusion.
- Backup files are written through a temporary file and moved into place only after creation.
- Existing timestamped backup archives are not overwritten.
- The Docker demo uses a unique container name, a random loopback port, and cleanup on exit.
- Credentials, `.env` files, generated reports, and local backups should not be committed.

## Limitations

- The host checks target Linux/WSL. Native Windows service management is not implemented.
- Service checks require `systemctl`; Docker checks require a reachable Docker daemon.
- Backup verification proves that an archive can be parsed, not that a full disaster-recovery restore has succeeded.
- Reports are local text files; there is no metrics backend, dashboard, alert manager, or remote agent.
- AWS inventory, deployment helpers, Kubernetes checks, retention policies, and structured log analysis remain future work.

## What I built

I designed the command structure and exit-code behavior, implemented the Python checks and backup workflow, added guarded Bash helpers, packaged the CLI, wrote the automated tests, created the GitHub Actions pipeline, and built the installed-package and disposable-Docker demonstrations. I also documented the failure modes so the portfolio shows what is implemented and what is not.

## Author

Chamindu Kaushalya — Software Engineering undergraduate at SLIIT, building hands-on Linux, Docker, Python automation, testing, and CI/CD skills.

- GitHub: <https://github.com/kaushalye1234>
- LinkedIn: <https://linkedin.com/in/chamindu-kaushalya-gunarathne-991829351/>
