#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $# -lt 2 ]]; then
  echo "Usage: $0 HOST PORT [--timeout SECONDS]" >&2
  exit 2
fi
python3 -m cloudops.cli ports "$@"
