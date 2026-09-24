import sys
import tarfile
from unittest.mock import patch

import pytest

from cloudops.checks import CheckResult
from cloudops.cli import main, write_report


def test_disk_command_returns_success_for_valid_path(tmp_path, capsys):
    code = main(["disk", "--path", str(tmp_path), "--warning", "101"])
    assert code == 0
    assert "[OK]" in capsys.readouterr().out


def test_invalid_port_returns_usage_error(capsys):
    code = main(["ports", "localhost", "70000"])
    assert code == 2
    assert "Port must be" in capsys.readouterr().err


def test_backup_command_creates_archive(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "backups"

    source.mkdir()
    (source / "hello.txt").write_text("hello", encoding="utf-8")

    code = main(["backup", str(source), str(destination)])

    assert code == 0
    assert list(destination.glob("backup-*.tar.gz"))


def test_backup_works_outside_repository(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "hello.txt").write_text("hello", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["backup", "source", "backups"]) == 0
    archive_path = next((tmp_path / "backups").glob("*.tar.gz"))
    with tarfile.open(archive_path, "r:gz") as archive:
        assert archive.extractfile("source/hello.txt").read() == b"hello"


def test_backup_rejects_destination_inside_source(tmp_path, capsys):
    source = tmp_path / "source"
    source.mkdir()
    assert main(["backup", str(source), str(source / "backups")]) == 1
    assert "outside the source" in capsys.readouterr().err
    assert not (source / "backups").exists()


def test_report_command_creates_report(tmp_path):
    output_dir = tmp_path / "reports"

    code = main(["report", "--output-dir", str(output_dir)])

    assert code == 0

    reports = list(output_dir.glob("system-report-*.txt"))
    assert reports

    content = reports[0].read_text(encoding="utf-8")
    assert "CloudOps System Report" in content
    assert "Health" in content
    assert "Disk" in content
    assert "Docker" in content
    assert "Services" in content


def test_services_command_returns_success():
    class CompletedProcess:
        returncode = 0
        stdout = "active\n"
        stderr = ""

    with patch("cloudops.cli.shutil.which", return_value="/usr/bin/systemctl"), patch(
        "cloudops.cli.subprocess.run", return_value=CompletedProcess()
    ):
        code = main(["services", "docker"])

    assert code == 0


def test_scan_command_runs_quality_checks(tmp_path, monkeypatch, capsys):
    commands = []
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    class CompletedProcess:
        returncode = 0

    def fake_run(command, cwd, check=False):
        commands.append((command, cwd))
        return CompletedProcess()

    monkeypatch.setattr("cloudops.cli.subprocess.run", fake_run)

    code = main(["scan", "--project", str(tmp_path)])

    assert code == 0
    assert commands == [
        ([sys.executable, "-m", "ruff", "check", "src", "tests"], tmp_path),
        ([sys.executable, "-m", "pytest"], tmp_path),
    ]
    assert "ruff check src tests" in capsys.readouterr().out


def test_scan_rejects_directory_without_project(tmp_path, capsys):
    assert main(["scan", "--project", str(tmp_path)]) == 1
    assert "No pyproject.toml" in capsys.readouterr().err


def test_services_reports_missing_systemctl(monkeypatch, capsys):
    monkeypatch.setattr("cloudops.cli.shutil.which", lambda _name: None)

    assert main(["services", "docker"]) == 1
    assert "systemctl is not installed" in capsys.readouterr().out


def test_doctor_detects_modules_in_running_environment(monkeypatch, capsys):
    monkeypatch.setattr("cloudops.cli.importlib.util.find_spec", lambda _name: object())
    monkeypatch.setattr("cloudops.cli.shutil.which", lambda name: f"/usr/bin/{name}")

    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "pytest Python module is installed" in output
    assert "shellcheck found" in output


def test_report_survives_missing_systemctl(tmp_path, monkeypatch):
    monkeypatch.setattr("cloudops.cli.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "cloudops.cli.docker_check",
        lambda: CheckResult("critical", "Docker CLI is not installed", {}),
    )

    report_path = write_report(str(tmp_path))

    assert "systemctl is not installed" in report_path.read_text(encoding="utf-8")


def test_negative_log_tail_is_rejected(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["logs", "demo", "--tail", "-1"])

    assert exc_info.value.code == 2
    assert "zero or greater" in capsys.readouterr().err


def test_verify_backup_command_accepts_valid_archive(tmp_path, capsys):
    source = tmp_path / "source"
    source.mkdir()
    (source / "hello.txt").write_text("hello", encoding="utf-8")

    backup_dir = tmp_path / "backups"

    assert main(["backup", str(source), str(backup_dir)]) == 0

    archives = list(backup_dir.glob("*.tar.gz"))
    assert len(archives) == 1

    assert main(["verify-backup", str(archives[0])]) == 0

    output = capsys.readouterr().out
    assert "[OK] Backup archive is readable" in output


def test_verify_backup_command_rejects_missing_archive(capsys):
    assert main(["verify-backup", "missing-backup.tar.gz"]) == 1

    output = capsys.readouterr().out
    assert "[CRITICAL] Backup archive does not exist" in output


def test_verify_backup_rejects_corrupt_archive(tmp_path, capsys):
    archive = tmp_path / "broken.tar.gz"
    archive.write_text("not an archive", encoding="utf-8")

    assert main(["verify-backup", str(archive)]) == 1
    assert "not readable" in capsys.readouterr().out
