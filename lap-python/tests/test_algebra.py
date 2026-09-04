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
