from cloudops.checks import disk_check, port_check


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
