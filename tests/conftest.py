from pathlib import Path

import pytest

from blackbox_twin.cli import load_target
from blackbox_twin.contracts import QueryBudget
from blackbox_twin.oracle import ProcessOracle, Session
from blackbox_twin.storage import Recorder

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def session(tmp_path):
    target, script = load_target(ROOT / "examples/order_processing/target.json")
    recorder = Recorder(tmp_path / "evidence.sqlite", {"test": True})
    oracle = ProcessOracle(script)
    wrapped = Session(oracle, target, QueryBudget(), recorder)
    yield wrapped
    wrapped.post("test_teardown")
    oracle.close()
    recorder.close("test_completed")
