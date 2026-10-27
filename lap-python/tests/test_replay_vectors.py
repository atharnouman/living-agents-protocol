"""LIP-4 Micro-Core replay vectors (output/lip/test-vectors/microcore-replay-vectors.json), shared with
the Node suite: the idempotency claim under authority replacement and key reuse (LIP-4 section 2
step 3 and step 6, 0.4.14). Each vector is a sequence of steps against one fresh cache and the
envelope check; the two ports must give the same outcome at every step.
"""
import json
from pathlib import Path

import pytest

from living_agents import IdempotencyCache, check_invocation

VECTORS_PATH = Path(__file__).parent.parent.parent / "output" / "lip" / "test-vectors" / "microcore-replay-vectors.json"
V = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def _scope(scope):
    return scope if isinstance(scope, str) else tuple(scope)


def _identity(name):
    return None if name is None else tuple(V["identities"][name])


def run(vector):
    cache = IdempotencyCache()
    for n, step in enumerate(vector["steps"], 1):
        op, where = step["op"], f"{vector['id']} step {n} ({step['op']})"
        if op in ("claim", "lookup"):
            out = getattr(cache, op)(_scope(step["scope"]), step["key"], _identity(step.get("identity")))
            assert out["status"] == step["expect"], where
            if "expect_result" in step:
                assert out["receipt"] == step["expect_result"], where
        elif op == "store":
            cache.store(_scope(step["scope"]), step["key"], step["result"], _identity(step.get("identity")))
        elif op in ("complete", "mark_indeterminate", "release", "abandon"):
            try:
                if op == "complete":
                    cache.complete(_scope(step["scope"]), step["key"], step["result"])
                else:
                    getattr(cache, op)(_scope(step["scope"]), step["key"])
                got = "ok"
            except ValueError:
                got = "error"
            assert got == step.get("expect", "ok"), where
        elif op == "check_invocation":
            try:
                check_invocation(V["envelopes"][step["envelope"]], act=step["act"], resource=step["resource"],
                                 amount=step.get("amount"), unit=step.get("unit"),
                                 enforce_magnitude=step.get("enforce_magnitude", True))
                got = "ok"
            except ValueError as e:
                got = str(e).split(":")[0]
            assert got == step["expect"], where
        else:
            raise AssertionError(f"{where}: unknown op")


@pytest.mark.parametrize("vector", V["vectors"], ids=[v["id"] for v in V["vectors"]])
def test_replay_vector(vector):
    run(vector)


def test_the_vector_file_covers_the_faults_the_reviews_found():
    names = " ".join(v["name"] for v in V["vectors"])
    for phrase in ("cap was cut", "another request", "two principals", "without an identity", "never overwritten", "audiences"):
        assert phrase in names, phrase
    assert len(V["vectors"]) >= 18
