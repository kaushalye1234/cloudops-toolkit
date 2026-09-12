from cloudops.cli import main


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
    code = main(["services", "docker"])

    assert code == 0


def test_scan_command_runs_quality_checks(monkeypatch, capsys):
    commands = []

    class CompletedProcess:
        returncode = 0

    def fake_run(command, check=False):
        commands.append(command)
        return CompletedProcess()

    monkeypatch.setattr("cloudops.cli.subprocess.run", fake_run)

    code = main(["scan"])

    assert code == 0
    assert commands == [["ruff", "check", "src", "tests"], ["pytest"]]
    assert "Running: ruff check src tests" in capsys.readouterr().out
