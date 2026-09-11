from cloudops.cli import main


def test_disk_command_returns_success_for_valid_path(tmp_path, capsys):
    code = main(["disk", "--path", str(tmp_path), "--warning", "101"])
    assert code == 0
    assert "[OK]" in capsys.readouterr().out


def test_invalid_port_returns_usage_error(capsys):
    code = main(["ports", "localhost", "70000"])
    assert code == 2
    assert "Port must be" in capsys.readouterr().err
