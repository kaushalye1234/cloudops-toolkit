#!/usr/bin/env bash
set -Eeuo pipefail
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed." >&2
  exit 1
fi
echo "Unused Docker objects that can be removed:"
docker system df
echo "Dry run only. Run 'docker system prune' manually after reviewing the output."
