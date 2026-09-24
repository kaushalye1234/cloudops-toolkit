"""Create a portable, compressed directory backup."""

from __future__ import annotations

import os
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def create_backup(source: str, destination: str) -> Path:
    source_path = Path(source).resolve()
    if not source_path.is_dir():
        raise ValueError(f"Source directory does not exist: {source}")

    destination_path = Path(destination).resolve()
    if destination_path == source_path or source_path in destination_path.parents:
        raise ValueError("Destination must be outside the source directory")

    destination_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    archive_path = destination_path / f"backup-{timestamp}.tar.gz"
    if archive_path.exists():
        raise FileExistsError(f"Backup already exists: {archive_path}")

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".cloudops-", suffix=".tar.gz", dir=destination_path, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        with tarfile.open(temporary_path, "w:gz") as archive:
            archive.add(source_path, arcname=source_path.name)
        os.replace(temporary_path, archive_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return archive_path
