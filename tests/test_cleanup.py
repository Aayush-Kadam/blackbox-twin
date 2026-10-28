import pytest

from blackbox_twin.oracle import OracleFailure, ProcessOracle


def test_transient_windows_directory_lock_retries(tmp_path, monkeypatch):
    script = tmp_path / "bad.py"
    script.write_text("print('x'*1000, flush=True)")
    oracle = ProcessOracle(script, timeout=2.0, max_response_bytes=100)
    original_cleanup = oracle.temp.cleanup
    calls = 0

    def locked_once():
        nonlocal calls
        calls += 1
        if calls == 1:
            error = PermissionError(13, "injected sharing violation")
            error.winerror = 32
            raise error
        original_cleanup()

    monkeypatch.setattr(oracle.temp, "cleanup", locked_once)
    with pytest.raises(OracleFailure, match="response_too_large"):
        oracle.reset()
    assert calls == 2
    assert oracle.cleanup_error is None
    assert oracle.process.poll() is not None


def test_persistent_cleanup_failure_cannot_mask_primary(tmp_path, monkeypatch):
    script = tmp_path / "bad.py"
    script.write_text("print('x'*1000, flush=True)")
    oracle = ProcessOracle(script, timeout=2.0, max_response_bytes=100)
    original_cleanup = oracle.temp.cleanup

    def denied():
        raise PermissionError("injected persistent cleanup failure")

    monkeypatch.setattr(oracle.temp, "cleanup", denied)
    try:
        with pytest.raises(OracleFailure, match="response_too_large.*cleanup_failure"):
            oracle.reset()
        assert "persistent cleanup failure" in oracle.cleanup_error
        assert oracle.process.poll() is not None
    finally:
        original_cleanup()
