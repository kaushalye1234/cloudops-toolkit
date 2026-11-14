#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python_bin=${PYTHON_BIN:-python3}
audit_dir=$(mktemp -d /tmp/cloudops-installed-XXXXXX)
server_pid=""

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
  fi
  rm -rf -- "$audit_dir"
}
trap cleanup EXIT

"$python_bin" -m venv "$audit_dir/venv"
"$audit_dir/venv/bin/pip" install --quiet "${repo_root}[dev]"

mkdir -p "$audit_dir/run/app"
printf 'service=ready\n' > "$audit_dir/run/app/config.txt"
cd "$audit_dir/run"

cloudops="$audit_dir/venv/bin/cloudops"
port=$("$audit_dir/venv/bin/python" -c \
  'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
"$audit_dir/venv/bin/python" -m http.server "$port" --bind 127.0.0.1 > server.log 2>&1 &
server_pid=$!

for _attempt in {1..20}; do
  if "$cloudops" ports 127.0.0.1 "$port" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

"$cloudops" health --warning 101
"$cloudops" disk --path / --warning 101
"$cloudops" ports 127.0.0.1 "$port"
"$cloudops" backup app backups
archive=$(find backups -name 'backup-*.tar.gz' -print -quit)
"$cloudops" verify-backup "$archive"
"$cloudops" report --output-dir reports
"$cloudops" --json disk --path / --warning 101
"$cloudops" scan --project "$repo_root"

# These commands intentionally report host state and may return 1 when a tool,
# service, or Docker daemon is unavailable. They must still fail cleanly.
"$cloudops" services cloudops-demo-missing || [[ $? -eq 1 ]]
"$cloudops" doctor || [[ $? -eq 1 ]]
"$cloudops" containers >/dev/null || [[ $? -eq 1 ]]

test -s "$archive"
find reports -name 'system-report-*.txt' -type f -size +0c -print -quit | grep -q .
printf 'Installed-package audit passed from %s\n' "$PWD"
