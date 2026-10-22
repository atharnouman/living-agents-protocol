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


def _strip(cap):
    return {k: v for k, v in cap.items() if k != "provenance"}  # the algebra knows caps, not labels


def _library_verdict(vec):
    try:
        return verify_envelope_attenuation([_scope(_strip(vec["parent"]))], [_scope(_strip(c)) for c in vec["children"]])["ok"]
    except ValueError:  # LAP_ERR_CAP_SCHEMA / LAP_ERR_SCOPE_SCHEMA: a malformed cap is a refusal
        return False


@pytest.mark.parametrize("vec", VECTORS, ids=[v["id"] for v in VECTORS])
def test_checker_library_and_vector_agree(vec):
    expected = vec["expect"] == "ok"
    checker_ok, reason, _, provenance = slice_check.check_slices(vec["parent"], vec["children"])
    assert checker_ok == expected, f"{vec['id']} checker: {reason}"
    assert provenance == vec["expect_provenance"], f"{vec['id']} provenance state"   # pinned per vector
    # The library checks the arithmetic (rules 1-5); provenance (rule 6) is the checker's alone,
    # so a vector refused only for its labels must pass the library's arithmetic.
    library_expected = True if reason.startswith("provenance") else expected
    assert _library_verdict(vec) == library_expected, f"{vec['id']} library disagrees with the vector"


def test_provenance_catches_the_lie_the_arithmetic_cannot():
    by_id = {v["id"]: v for v in VECTORS}
    ok, reason, _, prov = slice_check.check_slices(by_id["SL-17"]["parent"], by_id["SL-17"]["children"])
    assert not ok and reason.startswith("provenance") and "number of slices issued (3)" in reason
    assert prov == "inconsistent"
    assert _library_verdict(by_id["SL-17"]) is True          # 3 x 30000 <= 100000: the caps are fine
    ok, reason, trace, prov = slice_check.check_slices(by_id["SL-16"]["parent"], by_id["SL-16"]["children"])
    assert ok and prov == "consistent" and "[1 of 2]" in trace[0] + trace[1]
    # Three states, not two: a set with no provenance passes the arithmetic but its fan-out is
    # unprovable from the slices alone, a finding rather than a pass (suggested on A2A #2121).
    ok, _, _, prov = slice_check.check_slices(by_id["SL-03"]["parent"], by_id["SL-03"]["children"])
    assert ok and prov == "absent"


def test_the_24x_trap_is_what_the_debit_rule_refuses():
    parent = {"max_per_tx": 1000, "max_cumulative": 100000, "unit": "USD", "window": "utc_day"}
    hourly = {"max_per_tx": 1000, "max_cumulative": 4166, "unit": "USD", "window": "utc_hour"}
    assert slice_check.debit(parent, hourly) == 4166 * 24
    ok, reason, trace, _ = slice_check.check_slices(parent, [hourly, hourly])
    assert not ok and reason.startswith("conservation") and len(trace) == 2
