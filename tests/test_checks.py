import json
import subprocess

from cloudops.checks import disk_check, docker_check, port_check


def test_disk_check_for_existing_path_is_not_critical(tmp_path):
    result = disk_check(str(tmp_path), warning_percent=101)
    assert result.status == "ok"
    assert result.details["used_percent"] >= 0


def test_disk_check_for_missing_path_is_critical(tmp_path):
    result = disk_check(str(tmp_path / "missing"))
    assert result.status == "critical"


def test_closed_port_is_reported_as_critical():
    result = port_check("127.0.0.1", 1, timeout=0.1)
    assert result.status == "critical"


def test_docker_timeout_is_reported(monkeypatch):
    monkeypatch.setattr("cloudops.checks.shutil.which", lambda _name: "/usr/bin/docker")

    def time_out(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("docker", 10)

    monkeypatch.setattr("cloudops.checks.subprocess.run", time_out)

    result = docker_check()

    assert result.status == "critical"
    assert "10 seconds" in result.message


def test_invalid_docker_output_is_reported(monkeypatch):
    monkeypatch.setattr("cloudops.checks.shutil.which", lambda _name: "/usr/bin/docker")

    class CompletedProcess:
        returncode = 0
        stdout = "not-json\n"
        stderr = ""

    monkeypatch.setattr("cloudops.checks.subprocess.run", lambda *_args, **_kwargs: CompletedProcess())

    result = docker_check()

    assert result.status == "critical"
    assert result.message == "Docker returned an unexpected response"
    assert json.loads(result.to_json())["status"] == "critical"
