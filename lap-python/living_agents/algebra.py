"""
LIP-3 v0.2 Scope Algebra: Capability attenuation lattice, integer budget arithmetic, and resource matching.
"""

import re
from typing import Any, Dict, List, Optional, Set, Union

from .crypto_util import jcs, normalize_did, normalize_uri

# Seed Action Registry DAG — MUST stay in exact parity with the Node reference
# (lap-reference/src/algebra.js ACTION_REGISTRY_V0). Cross-implementation registry
# drift makes two conformant verifiers disagree, which is the FIPA failure mode.
ACTION_REGISTRY_V0: Dict[str, List[str]] = {
    "data:read": ["data:read:public"],
    "data:write": [],
    "finance:pay": ["finance:pay:escrow", "finance:pay:release"],
    "compute:exec": ["compute:exec:sandboxed"],
    "comm:send": [],
    "identity:present": [],
    "governance:revoke": [],
}

# LIP-3 §4: the ONLY timed windows are utc_hour and utc_day ("tx" and "epoch_total"
# are handled specially). Rolling windows are PROHIBITED in client-verifiable
# envelopes; unknown windows must fail closed, never be treated as buckets.
WINDOW_SECONDS: Dict[str, int] = {
    "utc_hour": 3600,
    "utc_day": 86400,
}


def is_registered_verb(act: str, registry: Dict[str, List[str]] = ACTION_REGISTRY_V0) -> bool:
    """LIP-3 §2: a verb exists only if the registry declares it (as key or child)."""
    if act == "*":
        return True
    if act in registry:
        return True
    return any(act in children for children in registry.values())


def dag_subsumes(
    parent_acts: Union[str, List[str]],
    child_acts: Union[str, List[str]],
    registry: Dict[str, List[str]] = ACTION_REGISTRY_V0,
) -> bool:
    """LIP-3 §2: parent action set subsumes child action set via registry DAG edges only.
    Unregistered verbs are invalid outright — even self-equal ones (parity with the
    Node reference; string content confers nothing)."""
    p_list = [parent_acts] if isinstance(parent_acts, str) else parent_acts
    c_list = [child_acts] if isinstance(child_acts, str) else child_acts

    if not all(is_registered_verb(a, registry) for a in [*p_list, *c_list]):
        return False
    if "*" in p_list:
        return True

    def expand(verb: str) -> Set[str]:
        out = {verb}
        for child in registry.get(verb, []):
            out.update(expand(child))
        return out

    p_allowed: Set[str] = set()
    for p in p_list:
        p_allowed.update(expand(p))

    return all(c in p_allowed for c in c_list)


def _parse_res(res: str) -> Dict[str, Any]:
    """Parse scheme://host/segments with terminal-only wildcard extraction.

    Parity with the Node reference: wildcards anywhere except the terminal
    position are a hard error, never a silent match.
    """
    norm = normalize_uri(res)
    m = re.match(r"^([a-z0-9+.-]+)://([^/]+)(/.*)?$", norm)
    if not m:
        raise ValueError(f"invalid resource URI: {res}")
    scheme, host, path = m.group(1), m.group(2), m.group(3) or ""
    segments = [s for s in path.split("/") if s]
    wildcard = None
    if segments and segments[-1] == "**":
        wildcard = "**"
        segments.pop()
    elif segments and segments[-1] == "*":
        wildcard = "*"
        segments.pop()
    if "*" in segments or "**" in segments:
        raise ValueError("wildcards are terminal-only")
    return {"scheme": scheme, "host": host, "segments": segments, "wildcard": wildcard}


def path_subsumes(parent_res: str, child_res: str) -> bool:
    """LIP-3 §2: segment-tokenized resource subsumption, terminal-only wildcards.

    ``**`` covers the subtree at/below the parent prefix; ``*`` covers exactly one
    extra segment and the child may not carry its own wildcard (no widening —
    a child ``**`` under a parent ``*`` is privilege escalation); an exact parent
    requires an identical, wildcard-free child.
    """
    p = _parse_res(parent_res)
    c = _parse_res(child_res)
    if p["scheme"] != c["scheme"] or p["host"] != c["host"]:
        return False
    prefix_ok = all(
        i < len(c["segments"]) and c["segments"][i] == seg
        for i, seg in enumerate(p["segments"])
    )
    if p["wildcard"] == "**":
        return len(c["segments"]) >= len(p["segments"]) and prefix_ok
    if p["wildcard"] == "*":
        return (
            len(c["segments"]) == len(p["segments"]) + 1
            and prefix_ok
            and c["wildcard"] is None
        )
    return (
        c["wildcard"] is None
        and len(c["segments"]) == len(p["segments"])
        and prefix_ok
    )


def cap_subsumes(parent_cap: Optional[Dict[str, Any]], child_cap: Optional[Dict[str, Any]]) -> bool:
    """LIP-3 §4: Two-dimensional cap rule with integer floor arithmetic."""
    if not parent_cap:
        return True
    if not child_cap:
        return False
    if child_cap.get("unit") != parent_cap.get("unit"):
        return False
    if child_cap.get("max_per_tx", 0) > parent_cap.get("max_per_tx", 0):
        return False

    pw = parent_cap.get("window")
    cw = child_cap.get("window")

    if pw == "tx":
        return child_cap.get("max_cumulative", 0) <= parent_cap.get("max_cumulative", 0)

    if pw == "epoch_total":
        return cw == "epoch_total" and child_cap.get("max_cumulative", 0) <= parent_cap.get("max_cumulative", 0)

    if cw in ("tx", "epoch_total"):
        return False

    p_sec = WINDOW_SECONDS.get(pw or "")
    c_sec = WINDOW_SECONDS.get(cw or "")
    if not p_sec or not c_sec or c_sec > p_sec or p_sec % c_sec != 0:
        return False

    # Integer floor division: guarantees identical verdicts across language ports
    scaled_max = (parent_cap.get("max_cumulative", 0) * c_sec) // p_sec
    return child_cap.get("max_cumulative", 0) <= scaled_max


def _parse_counterparties(cp: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not cp:
        return {"base": "UNIVERSE", "deny": set()}
    allow = cp.get("allow", [])
    deny = {normalize_did(d) for d in cp.get("deny", [])}
    if not allow:
        return {"base": "UNIVERSE", "deny": deny}
    return {"base": {normalize_did(a) for a in allow}, "deny": deny}


def counterparty_subsumes(parent_cp: Optional[Dict[str, Any]], child_cp: Optional[Dict[str, Any]]) -> bool:
    """LIP-3 §5: Counterparty allow/deny set containment."""
    p = _parse_counterparties(parent_cp)
    c = _parse_counterparties(child_cp)

    # All parent denies must be denied by child
    for d in p["deny"]:
        if d not in c["deny"]:
            return False

    if p["base"] == "UNIVERSE":
        return True
    if c["base"] == "UNIVERSE":
        return False

    # Child allow base must be subset of parent allow base
    for member in c["base"]:
        if member not in p["base"] or member in p["deny"]:
            return False

    return True


def scope_subsumes(
    parent: Dict[str, Any],
    child: Dict[str, Any],
    registry: Dict[str, List[str]] = ACTION_REGISTRY_V0,
) -> bool:
    """LIP-3 §6: Full scope subsumption check."""
    if parent.get("v") != "lap-scope-v0" or child.get("v") != "lap-scope-v0":
        return False
    if not dag_subsumes(parent.get("act", []), child.get("act", []), registry):
        return False
    if not path_subsumes(parent.get("res", ""), child.get("res", "")):
        return False
    if not counterparty_subsumes(parent.get("cp"), child.get("cp")):
        return False
    if parent.get("depth") is not None:
        if child.get("depth") is None or child.get("depth") > parent.get("depth") - 1:
            return False
    if parent.get("decay_max_sec") is not None:
        if child.get("decay_max_sec") is None or child.get("decay_max_sec") > parent.get("decay_max_sec"):
            return False
    return True


def verify_envelope_attenuation(
    parent_scopes: List[Dict[str, Any]],
    child_scopes: List[Dict[str, Any]],
    registry: Dict[str, List[str]] = ACTION_REGISTRY_V0,
) -> Dict[str, Any]:
    """LIP-3 §6: Envelope-level verification with budget conservation and canonical ordering."""
    parents = sorted(parent_scopes, key=lambda s: jcs(s))
    children = sorted(child_scopes, key=lambda s: jcs(s))
    remaining = [p.get("cap", {}).get("max_cumulative", float("inf")) for p in parents]

    for c in children:
        matched = False
        for i, p in enumerate(parents):
            if not scope_subsumes(p, c, registry):
                continue
            if p.get("cap") and not cap_subsumes(p.get("cap"), c.get("cap")):
                continue
            if p.get("cap"):
                c_cum = c.get("cap", {}).get("max_cumulative", float("inf"))
                if c_cum > remaining[i]:
                    continue
                remaining[i] -= c_cum
            matched = True
            break
        if not matched:
            return {"ok": False, "rejected": c}

    return {"ok": True}
