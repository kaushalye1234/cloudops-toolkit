#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cloudops_bin=${CLOUDOPS_BIN:-cloudops}
image=${CLOUDOPS_DEMO_IMAGE:-cloudops-toolkit:demo}
container="cloudops-demo-service-$$"

cleanup() {
  docker rm --force "$container" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for this demo." >&2
  exit 1
fi
if ! command -v "$cloudops_bin" >/dev/null 2>&1 && [[ ! -x "$cloudops_bin" ]]; then
  echo "Install CloudOps Toolkit first or set CLOUDOPS_BIN to its executable." >&2
  exit 1
fi

echo "1/5 Build the toolkit image"
if [[ ${CLOUDOPS_DEMO_SKIP_BUILD:-0} != "1" ]]; then
  docker build --tag "$image" "$repo_root"
else
  echo "Using prebuilt image: $image"
fi

echo "2/5 Start a disposable HTTP service on a random host port"
docker run --detach --name "$container" --publish 127.0.0.1::8080 \
  --entrypoint python "$image" -u -m http.server 8080 >/dev/null
host_binding=$(docker port "$container" 8080/tcp)
host_port=${host_binding##*:}

echo "3/5 Wait for the service and check its TCP port"
for _attempt in {1..30}; do
  if "$cloudops_bin" ports 127.0.0.1 "$host_port" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done
"$cloudops_bin" ports 127.0.0.1 "$host_port"

echo "4/5 Inspect the running container"
container_output=$("$cloudops_bin" --json containers)
python3 -c '
import json
import sys

result = json.load(sys.stdin)
target = sys.argv[1]
matches = [item for item in result["details"]["running_containers"] if item["Names"] == target]
if len(matches) != 1:
    raise SystemExit(f"Expected one container named {target}; found {len(matches)}")
item = matches[0]
print(f"[OK] Found {item['\''Names'\'']} ({item['\''Image'\'']}, {item['\''Status'\'']})")
' "$container" <<< "$container_output"

echo "5/5 Generate traffic and inspect recent container logs"
python3 -c \
  "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:${host_port}', timeout=5).status)"
"$cloudops_bin" logs "$container" --tail 5

echo "Demo passed. The disposable container will now be removed."
