#!/usr/bin/env bash
set -Eeuo pipefail
python3 -m cloudops.cli disk "$@"
