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
        # Keep the primary-failure assertions above; teardown also encounters real
        # Windows process-directory release delays after the injected failure.
        monkeypatch.setattr(oracle.temp, "cleanup", original_cleanup)
        oracle._cleanup_temp()


@pytest.mark.parametrize("error", [BrokenPipeError("disconnected"), OSError(22, "invalid pipe")])
def test_broken_pipe_is_terminal_before_exit_status_is_visible(monkeypatch, error):
    from types import SimpleNamespace

    def broken_write(_):
        raise error

    exited = False

    def wait_for_exit(timeout):
        nonlocal exited
        assert timeout <= 0.1
        exited = True
        return 0

    oracle = ProcessOracle.__new__(ProcessOracle)
    oracle.closed = False
    oracle.timeout = 2.0
    oracle.process = SimpleNamespace(
        stdin=SimpleNamespace(write=broken_write),
        poll=lambda: 0 if exited else None,
        wait=wait_for_exit,
    )
    failures = []
    monkeypatch.setattr(oracle, "_close_after_failure", failures.append)
    with pytest.raises(OracleFailure, match="process_eof: broken subprocess pipe"):
        oracle._exchange({"control": "reset"})
    assert len(failures) == 1
