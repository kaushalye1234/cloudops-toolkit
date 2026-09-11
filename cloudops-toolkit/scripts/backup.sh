#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 SOURCE_DIRECTORY DESTINATION_DIRECTORY" >&2
  exit 2
fi
source_dir=$1
destination_dir=$2
if [[ ! -d "$source_dir" ]]; then
  echo "Source directory does not exist: $source_dir" >&2
  exit 1
fi
mkdir -p "$destination_dir"
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$destination_dir/backup-$timestamp.tar.gz"
tar -czf "$archive" -C "$(dirname "$source_dir")" "$(basename "$source_dir")"
echo "Backup created: $archive"
