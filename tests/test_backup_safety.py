
from datetime import UTC, datetime

import pytest

from cloudops import backup


def test_backup_does_not_overwrite_concurrent_archive(
    tmp_path, monkeypatch
):
    source = tmp_path / "app"
    source.mkdir()
    (source / "config.txt").write_text("safe")

    destination = tmp_path / "backups"
    destination.mkdir()

    class FixedDateTime:
        @staticmethod
        def now(tz):
            return datetime(2026, 11, 14, 6, 31, tzinfo=UTC)

    monkeypatch.setattr(backup, "datetime", FixedDateTime)

    target = destination / "backup-20261114T063100Z.tar.gz"
    existing_data = b"another process backup"

    original_open = backup.tarfile.open

    def simulate_race(*args, **kwargs):
        # Another process creates the archive
        # after our initial existence check.
        target.write_bytes(existing_data)
        return original_open(*args, **kwargs)

    monkeypatch.setattr(
        backup.tarfile, "open", simulate_race
    )

    with pytest.raises(FileExistsError):
        backup.create_backup(
            str(source), str(destination)
        )

    assert target.read_bytes() == existing_data
    assert not list(destination.glob(".cloudops-*.tar.gz"))
