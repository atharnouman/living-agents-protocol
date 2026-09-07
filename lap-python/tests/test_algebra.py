"""
Unit tests for LIP-3 Scope Algebra in Python.
"""

from living_agents.algebra import (
    cap_subsumes,
    counterparty_subsumes,
    dag_subsumes,
    path_subsumes,
    verify_envelope_attenuation,
)


def test_dag_subsumes():
    """Action lattice: registry-declared edges only; unregistered verbs invalid outright."""
    assert dag_subsumes("finance:pay", "finance:pay:escrow")
    assert dag_subsumes("compute:exec", "compute:exec:sandboxed")
    assert dag_subsumes("finance:pay", "finance:pay")
    assert not dag_subsumes("finance:pay", "data:read")
    assert dag_subsumes("*", "finance:pay:escrow")
    assert dag_subsumes(["finance:pay", "data:read"], "data:read:public")
    # String prefixing confers nothing: unregistered sub-verb must fail even self-equal
    assert not dag_subsumes("compute:exec", "compute:exec:unconfined")
    assert not dag_subsumes("madeup:verb", "madeup:verb")


def test_ipv6_literal_resources():
    """LAP is layer-agnostic: IPv4/IPv6 only surfaces inside resource URIs.

    IPv6 literals are bracketed (RFC 3986 §3.2.2); host lowercasing already matches
    RFC 5952 canonical form. Node parity — see algebra.test.js.
    """
    assert path_subsumes("mcp://[2001:db8::1]:4107/billing/**", "mcp://[2001:DB8::1]:4107/billing/pay")
    assert not path_subsumes("mcp://[2001:db8::1]:4107/billing/**", "mcp://[2001:db8::2]:4107/billing/pay")
    assert not path_subsumes("mcp://[::1]:4107/billing/**", "mcp://127.0.0.1:4107/billing/pay")
    assert path_subsumes("http://[::1]:4107/pay", "http://[::1]:4107/pay")
    # Documented interop hazard: matching is TEXTUAL — expanded and compressed forms of
    # the same address do not match. Scopes MUST use RFC 5952 canonical form.
    assert not path_subsumes("mcp://[2001:db8:0:0:0:0:0:1]/x/**", "mcp://[2001:db8::1]/x/y")


def test_path_subsumes():
    """Resource matching: segment-tokenized, terminal-only wildcards, no widening."""
    import pytest

    assert path_subsumes("mcp://tools/**", "mcp://tools/billing/pay")
    assert path_subsumes("mcp://tools/billing/*", "mcp://tools/billing/pay")
    assert not path_subsumes("mcp://tools/billing/*", "mcp://tools/billing/admin/keys")
    assert not path_subsumes("mcp://tools/finance", "mcp://tools/finance_admin")
    # Widening is privilege escalation: child ** may not attenuate a parent *
    assert not path_subsumes("mcp://tools/a/*", "mcp://tools/a/**")
    # Non-terminal wildcards are a hard error, never a silent match
    with pytest.raises(ValueError, match="terminal-only"):
        path_subsumes("mcp://tools/**/secrets", "mcp://tools/x/secrets")
    # Host and scheme must match after normalization
    assert path_subsumes("MCP://Tools.Example.com/billing/**", "mcp://tools.example.com/billing/pay")
    assert not path_subsumes("mcp://tools-a/billing/**", "mcp://tools-b/billing/pay")


def test_cap_subsumes_timed_subdivision():
    """Cap attenuation: integer floor scaling; only spec windows exist; rolling prohibited."""
    parent = {"max_per_tx": 100, "max_cumulative": 2400, "unit": "USD", "window": "utc_day"}
    # utc_hour is 1/24th of utc_day: 2400 / 24 = 100
    valid_child = {"max_per_tx": 50, "max_cumulative": 100, "unit": "USD", "window": "utc_hour"}
    invalid_child = {"max_per_tx": 50, "max_cumulative": 101, "unit": "USD", "window": "utc_hour"}
    assert cap_subsumes(parent, valid_child)
    assert not cap_subsumes(parent, invalid_child)
    # LIP-3 §4: rolling windows are prohibited in client-verifiable envelopes —
    # unknown windows fail closed, they are never treated as buckets
    rolling_child = {"max_per_tx": 50, "max_cumulative": 100, "unit": "USD", "window": "rolling_day"}
    assert not cap_subsumes(parent, rolling_child)
    # A bare tx window cannot attenuate a windowed parent (rate-unboundedness)
    tx_child = {"max_per_tx": 50, "max_cumulative": 50, "unit": "USD", "window": "tx"}
    assert not cap_subsumes(parent, tx_child)


def test_cap_subsumes_epoch_total():
    """Test epoch_total attenuates only to epoch_total."""
    parent = {"max_per_tx": 500, "max_cumulative": 5000, "unit": "USD", "window": "epoch_total"}
    valid_child = {"max_per_tx": 100, "max_cumulative": 1000, "unit": "USD", "window": "epoch_total"}
    invalid_window = {"max_per_tx": 100, "max_cumulative": 1000, "unit": "USD", "window": "utc_day"}

    assert cap_subsumes(parent, valid_child)
    assert not cap_subsumes(parent, invalid_window)


def test_counterparty_subsumes():
    """Test counterparty allow and deny containment."""
    p_universe = None
    c_specific = {"allow": ["did:key:z6MkAlice..."]}
    assert counterparty_subsumes(p_universe, c_specific)

    p_allow = {"allow": ["did:key:z6MkAlice...", "did:key:z6MkBob..."]}
    c_allow = {"allow": ["did:key:z6MkAlice..."]}
    assert counterparty_subsumes(p_allow, c_allow)

    p_deny = {"deny": ["did:key:z6MkEvil..."]}
    c_no_deny = {"allow": ["did:key:z6MkEvil..."]}
    assert not counterparty_subsumes(p_deny, c_no_deny)


def test_envelope_attenuation_budget_conservation():
    """Test multi-scope budget conservation prevents duplicate budget claims."""
    parent_scopes = [
        {
            "v": "lap-scope-v0",
            "act": ["finance:pay"],
            "res": "mcp://tools/**",
            "cap": {"max_per_tx": 100, "max_cumulative": 100, "unit": "USD", "window": "tx"},
        }
    ]

    # Two children requesting 60 USD each (sum 120 > 100 parent budget)
    child_scopes = [
        {
            "v": "lap-scope-v0",
            "act": ["finance:pay"],
            "res": "mcp://tools/a",
            "cap": {"max_per_tx": 60, "max_cumulative": 60, "unit": "USD", "window": "tx"},
        },
        {
            "v": "lap-scope-v0",
            "act": ["finance:pay"],
            "res": "mcp://tools/b",
            "cap": {"max_per_tx": 60, "max_cumulative": 60, "unit": "USD", "window": "tx"},
        },
    ]

    result = verify_envelope_attenuation(parent_scopes, child_scopes)
    assert not result["ok"]


# ---- v0.3 fuzz-round findings (2026-09-08; see llm-collab/IMPROVEMENTS-LOG.md) ----
import pytest  # noqa: E402
from living_agents import (  # noqa: E402
    cap_subsumes, counterparty_subsumes, path_subsumes, scope_is_valid, scope_subsumes, verify_envelope_attenuation,
)


def test_v03_reflexive_star_closed_syntax_and_typed_schema_errors():
    assert path_subsumes("mcp://h/a/*", "mcp://h/a/*") is True  # the same set (was False)
    assert path_subsumes("mcp://h/a/*", "mcp://h/a/**") is False  # still never widen
    assert path_subsumes("mcp://h/a/*", "mcp://h/a/b/*") is False
    assert path_subsumes("mcp://h/a/*", "mcp://h/b/*") is False
    for bad in ["mcp://h/a?x=1", "mcp://h/a#f", "mcp://h//a", "mcp://h/a//b", "mcp://h?x/a", "not a uri", "", 42, None]:
        with pytest.raises(ValueError, match="LAP_ERR_RES"):
            path_subsumes("mcp://h/**", bad)
    assert path_subsumes("mcp://h/a/", "mcp://h/a") is True  # one trailing slash is tolerated

    def S(**over):
        s = {"v": "lap-scope-v0", "act": "finance:pay", "res": "ap2://rails/stripe/**"}
        s.update(over)
        return {k: v for k, v in s.items() if v is not ...}

    ok = S(res="mcp://h/**")
    malformed = [None, "junk", 42, [], S(res=...), S(res=None), S(act=7), S(act=[7]), S(act=...), S(cp={"allow": "did:key:z6MkA"}),
                 S(cp={"deny": [1]}), S(depth=-1), S(depth=17), S(depth="2"), S(decay_max_sec=None), S(v=7), S(v=...)]
    for bad in malformed:
        assert scope_is_valid(bad) is False, bad
        assert scope_subsumes(ok, bad) is False
        assert scope_subsumes(bad, ok) is False
        with pytest.raises(ValueError, match="LAP_ERR_SCOPE_SCHEMA"):
            verify_envelope_attenuation([ok], [bad])
        with pytest.raises(ValueError, match="LAP_ERR_SCOPE_SCHEMA"):
            verify_envelope_attenuation([bad], [ok])
    with pytest.raises(ValueError, match="LAP_ERR_SCOPE_SCHEMA"):
        verify_envelope_attenuation(ok, [ok])
    assert scope_is_valid(ok) is True
    assert counterparty_subsumes({"allow": "x"}, {}) is False
    assert scope_subsumes(S(act=...), S(act=...)) is False  # a missing act is not "grants nothing is a subset of grants nothing"
    assert counterparty_subsumes({"allow": ["did:web:vendora.com"]}, {"allow": ["DID:WEB:vendora.com"]}) is True
    assert counterparty_subsumes({"allow": ["did:key:z6MkA"]}, {"allow": ["did:key:Z6MKA"]}) is False  # did:key ids are case-sensitive
    # effective sets: a member the child itself denies does not count against it (this port lacked the skip — found by the fuzzer)
    AB = {"allow": ["did:key:z6MkA", "did:key:z6MkB"], "deny": ["did:key:z6MkA"]}
    assert counterparty_subsumes(AB, {"allow": ["did:key:z6MkA", "did:key:z6MkB"], "deny": ["did:key:z6MkA"]}) is True
    assert counterparty_subsumes(AB, {"allow": ["did:key:z6MkA"], "deny": []}) is False
    # parity: JSON envelopes are consumed by JS verifiers too, so both ports reject above 2^53-1
    assert cap_subsumes({"max_per_tx": 1, "max_cumulative": 2**53 - 1, "unit": "USD", "window": "tx"},
                        {"max_per_tx": 1, "max_cumulative": 1, "unit": "USD", "window": "tx"}) is True
    assert cap_subsumes({"max_per_tx": 1, "max_cumulative": 2**53, "unit": "USD", "window": "tx"},
                        {"max_per_tx": 1, "max_cumulative": 1, "unit": "USD", "window": "tx"}) is False
    assert cap_subsumes({}, {"max_per_tx": 1, "max_cumulative": 1, "unit": "USD", "window": "tx"}) is False  # {} is a malformed cap, not "no cap"


def test_v03_exact_integer_window_arithmetic_matches_node():
    def S(**o):
        return {"v": "lap-scope-v0", "act": "finance:pay", **o}

    P = {"unit": "USD", "window": "utc_day", "max_per_tx": 1, "max_cumulative": 8707531655995247}
    assert cap_subsumes(P, {"unit": "USD", "window": "utc_hour", "max_per_tx": 1, "max_cumulative": 362813818999801}) is True
    assert cap_subsumes(P, {"unit": "USD", "window": "utc_hour", "max_per_tx": 1, "max_cumulative": 362813818999802}) is False
    parent = S(res="mcp://h/**", cap={"unit": "USD", "window": "utc_day", "max_per_tx": 1, "max_cumulative": 8221535177121408})
    child = S(res="mcp://h/x", cap={"unit": "USD", "window": "utc_hour", "max_per_tx": 1, "max_cumulative": 342563965713392})
    assert verify_envelope_attenuation([parent], [child])["ok"] is True
    extra = S(res="mcp://h/y", cap={"unit": "USD", "window": "utc_hour", "max_per_tx": 1, "max_cumulative": 1})
    assert verify_envelope_attenuation([parent], [child, extra])["ok"] is False
