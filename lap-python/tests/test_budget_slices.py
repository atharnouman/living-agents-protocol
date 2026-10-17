"""The budget-slice vectors (examples/budget-slices/vectors.json) get the same verdict from three
implementations: the dependency-free checker in examples/budget-slices/slice_check.py, this port's
LIP-3 algebra (cap_subsumes plus envelope-level conservation), and the vectors' own `expect`.
"""
import importlib.util
import json
from pathlib import Path

import pytest

from living_agents import verify_envelope_attenuation

HERE = Path(__file__).parent.parent.parent / "examples" / "budget-slices"
VECTORS = json.loads((HERE / "vectors.json").read_text(encoding="utf-8"))["vectors"]

_spec = importlib.util.spec_from_file_location("slice_check", HERE / "slice_check.py")
slice_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(slice_check)


def _scope(cap):
    return {"v": "lap-scope-v0", "act": "finance:pay", "res": "ap2://rails/pay/**", "cap": cap}


def _library_verdict(vec):
    try:
        return verify_envelope_attenuation([_scope(vec["parent"])], [_scope(c) for c in vec["children"]])["ok"]
    except ValueError:  # LAP_ERR_CAP_SCHEMA / LAP_ERR_SCOPE_SCHEMA: a malformed cap is a refusal
        return False


@pytest.mark.parametrize("vec", VECTORS, ids=[v["id"] for v in VECTORS])
def test_checker_library_and_vector_agree(vec):
    expected = vec["expect"] == "ok"
    checker_ok, reason, _ = slice_check.check_slices(vec["parent"], vec["children"])
    assert checker_ok == expected, f"{vec['id']} checker: {reason}"
    assert _library_verdict(vec) == expected, f"{vec['id']} library disagrees with the vector"


def test_the_24x_trap_is_what_the_debit_rule_refuses():
    parent = {"max_per_tx": 1000, "max_cumulative": 100000, "unit": "USD", "window": "utc_day"}
    hourly = {"max_per_tx": 1000, "max_cumulative": 4166, "unit": "USD", "window": "utc_hour"}
    assert slice_check.debit(parent, hourly) == 4166 * 24
    ok, reason, trace = slice_check.check_slices(parent, [hourly, hourly])
    assert not ok and reason.startswith("conservation") and len(trace) == 2
