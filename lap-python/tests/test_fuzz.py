"""Property-based fuzzing of the LIP-3 Scope Algebra (self-contained: no hypothesis, no deps).

The xorshift32 generator below is written identically in lap-reference/test/fuzz.test.js, so
both ports see the SAME random scopes; a committed digest of the decisions locks cross-port
parity. Properties: reflexivity, transitivity along attenuation chains, instantiation, no
widening, an exact-integer cap oracle, a budget-conservation oracle, typed errors only, and the
parity digest.  LAP_FUZZ_SEED=123 explores another seed (parity check skipped).
"""
import hashlib
import json
import os
import re
from pathlib import Path

from living_agents import (
    ACTION_REGISTRY_V0, cap_subsumes, path_subsumes, scope_subsumes, verify_envelope_attenuation,
)
from living_agents.algebra import cap_is_valid

DIGEST_PATH = Path(__file__).parent.parent.parent / "output" / "lip" / "test-vectors" / "algebra-fuzz-digest.json"
SEED = int(os.environ.get("LAP_FUZZ_SEED", "20260906"))
EXPLORING = "LAP_FUZZ_SEED" in os.environ


def xorshift32(seed):
    x = (seed & 0xFFFFFFFF) or 1

    def rnd():
        nonlocal x
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        return x / 4294967296

    return rnd


NUMS_VALID = [0, 1, 5, 100, 4200, 5000, 6000, 10000, 123456, 99999999, 123456789012345, 342563965713392, 8707531655995247, 9007199254740991]
ACTS_VALID = ["data:read", "data:read:public", "data:write", "finance:pay", "finance:pay:escrow", "finance:pay:release", "compute:exec", "compute:exec:sandboxed", "comm:send", "*"]
V = {
    "schemes": ["mcp", "https", "a2a", "MCP"],
    "hosts": ["tools.example.com", "Tools.Example.com", "api.example.org", "[::1]", "[2001:db8::1]", "127.0.0.1", "tools.example.com:4107"],
    "segs": ["a", "b", "billing", "pay", "admin", "keys", "x", "finance", "finance_admin", "A"],
    "badSegs": [".", "..", "%2e", "%2F", "a?x=1", "a#f", "", "*", "**"],
    "wildcards": [None, "*", "**"],
    "actsValid": ACTS_VALID,
    "actsAny": [*ACTS_VALID, "compute:exec:unconfined", "finance", "Finance:Pay", "", 42],
    "units": ["USD", "EUR"],
    "windowsValid": ["tx", "utc_hour", "utc_day", "epoch_total"],
    "windowsAny": ["tx", "utc_hour", "utc_day", "epoch_total", "rolling_day", "", None],
    "numsValid": NUMS_VALID,
    "numsAny": [*NUMS_VALID, -1, 1.5, "100", 9007199254740992, True, None],
    "dids": ["did:key:z6MkA", "did:key:z6MkB", "did:web:vendora.com", "DID:WEB:vendora.com", "did:web:Vendora.com", "did:web:other.example"],
    "depths": [0, 1, 2, 5, 16],
    "decays": [60, 300, 3600],
}
_MISSING = object()


def _str_list(x):
    return isinstance(x, list) and all(isinstance(s, str) for s in x)


class Gen:
    def __init__(self, rng, valid):
        self.rng, self.valid = rng, valid

    def rint(self, n):
        return int(self.rng() * n)

    def pick(self, arr):
        return arr[self.rint(len(arr))]

    def res(self, clean):
        scheme, host, n = self.pick(V["schemes"]), self.pick(V["hosts"]), self.rint(4)
        segs = []
        for _ in range(n):
            r = self.rng()
            segs.append(self.pick(V["badSegs"]) if (not clean and r < 0.06) else self.pick(V["segs"]))
        wc = self.pick(V["wildcards"])
        tail = (("/" if segs else "") + wc) if wc else ""
        return f"{scheme}://{host}/{'/'.join(segs)}{tail}"

    def act(self):
        r, pool = self.rng(), (V["actsValid"] if self.valid else V["actsAny"])
        if r < 0.6:
            return self.pick(pool)
        n = 1 + self.rint(2)
        return [self.pick(pool) for _ in range(n)]

    def cap(self):
        r = self.rng()
        if r < 0.25:
            return _MISSING
        unit = self.pick(V["units"])
        window = self.pick(V["windowsValid"] if self.valid else V["windowsAny"])
        tx = self.pick(V["numsValid"] if self.valid else V["numsAny"])
        cum = self.pick(V["numsValid"] if self.valid else V["numsAny"])
        if self.valid and tx > cum:
            tx, cum = cum, tx
        return {"max_per_tx": tx, "max_cumulative": cum, "unit": unit, "window": window}

    def cp(self):
        r = self.rng()
        if r < 0.4:
            return _MISSING
        na, nd = self.rint(3), self.rint(2)
        allow = [self.pick(V["dids"]) for _ in range(na)]
        deny = [self.pick(V["dids"]) for _ in range(nd)]
        if not self.valid and self.rng() < 0.08:
            return {"allow": "did:key:z6MkA"}
        return {"allow": allow, "deny": deny}

    def scope(self):
        s = {"v": "lap-scope-v0"}
        if not self.valid and self.rng() < 0.05:
            alt = self.pick(["lap-scope-v1", 7, None])
            if alt is None:
                del s["v"]
            else:
                s["v"] = alt
        s["act"] = self.act()
        s["res"] = self.res(self.valid)
        if not self.valid and self.rng() < 0.05:
            alt = self.pick([_MISSING, None, 42, "not a uri"])
            if alt is _MISSING:
                del s["res"]
            else:
                s["res"] = alt
        c = self.cap()
        if c is not _MISSING:
            s["cap"] = c
        p = self.cp()
        if p is not _MISSING:
            s["cp"] = p
        if self.rng() < 0.5:
            s["depth"] = self.pick(V["depths"])
        if self.rng() < 0.5:
            s["decay_max_sec"] = self.pick(V["decays"])
        if not self.valid and self.rng() < 0.03:
            return self.pick([None, "junk", 42])
        return s

    @staticmethod
    def descendants(verb):
        out = [verb]
        for ch in ACTION_REGISTRY_V0.get(verb, []):
            out.extend(Gen.descendants(ch))
        return out

    @staticmethod
    def split_res(r):
        origin, path = r.split("://", 1)[0] + "://" + r.split("://", 1)[1].split("/", 1)[0], r.split("://", 1)[1].split("/", 1)[1]
        segs = path.split("/") if path else []
        wc = None
        if segs and segs[-1] == "**":
            wc = "**"
            segs.pop()
        elif segs and segs[-1] == "*":
            wc = "*"
            segs.pop()
        return origin, segs, wc

    @staticmethod
    def _usable_cap(cap):
        ok_int = lambda v: isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 2**53 - 1  # noqa: E731
        return isinstance(cap, dict) and ok_int(cap.get("max_per_tx")) and ok_int(cap.get("max_cumulative")) and isinstance(cap.get("window"), str) and isinstance(cap.get("unit"), str)

    @staticmethod
    def can_attenuate(p):
        act = p.get("act") if isinstance(p, dict) else None
        return isinstance(p, dict) and isinstance(p.get("res"), str) and re.match(r"^[^:]+://[^/]+/", p["res"]) is not None and (isinstance(act, str) or (isinstance(act, list) and len(act) > 0))

    def attenuate(self, parent):
        """A child that SHOULD be subsumed by `parent` (when parent is valid) — with rare, deliberate overshoots.
        Malformed parent parts are copied verbatim so "any"-mode pairs stay identical across ports."""
        c = {"v": "lap-scope-v0"}
        p_acts = parent["act"] if isinstance(parent["act"], list) else [parent["act"]]
        base = self.pick(p_acts)
        c["act"] = self.pick([a for a in V["actsValid"] if a != "*"]) if base == "*" else self.pick(self.descendants(base))
        origin, segs, wc = self.split_res(parent["res"])
        if wc == "**":
            extra = self.rint(3)
            for _ in range(extra):
                segs.append(self.pick(V["segs"]))
            k = self.pick([None, "*", "**"])
            if k:
                segs.append(k)
        elif wc == "*":
            segs.append(self.pick(V["segs"]) if self.rng() < 0.5 else "*")
        c["res"] = f"{origin}/{'/'.join(segs)}"
        if self._usable_cap(parent.get("cap")):
            p = parent["cap"]
            window, scale = p["window"], 1
            if p["window"] == "utc_day" and self.rng() < 0.5:
                window, scale = "utc_hour", 24
            cum_max, tx_max = p["max_cumulative"] // scale, p["max_per_tx"]
            k = self.rint(1001)
            cum = (cum_max * k) // 1000
            if self.rng() < 0.15:
                cum = cum_max + 1
            tx = tx_max if tx_max <= cum else cum
            if self.rng() < 0.1:
                tx = tx_max + 1
            c["cap"] = {"max_per_tx": tx, "max_cumulative": cum, "unit": p["unit"], "window": window}
        elif "cap" in parent:
            c["cap"] = parent["cap"]
        elif self.rng() < 0.3:
            c["cap"] = {"max_per_tx": 1, "max_cumulative": 5, "unit": "USD", "window": "tx"}
        cp = parent.get("cp")
        if "cp" in parent and not (isinstance(cp, dict) and _str_list(cp.get("allow") or []) and _str_list(cp.get("deny") or [])):
            c["cp"] = cp
        elif cp:
            p_allow = parent["cp"].get("allow") or []
            allow = [a for a in p_allow if self.rng() < 0.7]
            if not allow and p_allow:
                allow = [p_allow[0]]
            deny = list(parent["cp"].get("deny") or [])
            if self.rng() < 0.3:
                deny.append(self.pick(V["dids"]))
            c["cp"] = {"allow": allow, "deny": deny}
        if "depth" in parent:
            c["depth"] = max(0, parent["depth"] - 1)
        if "decay_max_sec" in parent:
            c["decay_max_sec"] = parent["decay_max_sec"]
        return c

    def concrete(self, pattern):
        origin, segs, wc = self.split_res(pattern)
        if wc == "*":
            segs.append(self.pick(V["segs"]))
        if wc == "**":
            extra = self.rint(3)
            for _ in range(extra):
                segs.append(self.pick(V["segs"]))
        return f"{origin}/{'/'.join(segs)}"


SECS = {"utc_hour": 3600, "utc_day": 86400}


def oracle_cap_subsumes(p, c):
    if c["unit"] != p["unit"] or c["max_per_tx"] > p["max_per_tx"]:
        return False
    if p["window"] in ("tx", "epoch_total"):
        return c["window"] == p["window"] and c["max_cumulative"] <= p["max_cumulative"]
    if c["window"] not in SECS:
        return False
    p_s, c_s = SECS[p["window"]], SECS[c["window"]]
    if c_s > p_s or p_s % c_s != 0:
        return False
    return c["max_cumulative"] <= (p["max_cumulative"] * c_s) // p_s


def oracle_debit(p, c):
    p_s, c_s = SECS.get(p["window"]), SECS.get(c["window"])
    return (c["max_cumulative"] * p_s) // c_s if (p_s and c_s) else c["max_cumulative"]


def decide(f):
    try:
        r = f()
        if r is True or r is False:
            return "T" if r else "F"
        return "T" if isinstance(r, dict) and r.get("ok") is True else "F"
    except ValueError as e:
        m = str(e)
        return "E:" + m.split(":")[0] if m.startswith("LAP_ERR_") else "X:" + type(e).__name__
    except Exception as e:  # noqa: BLE001 — the point is to catch everything
        return "X:" + type(e).__name__


def j(x):
    return json.dumps(x, sort_keys=True, default=str)


def test_fuzz_1_reflexivity():
    g = Gen(xorshift32(SEED ^ 1), True)
    for _ in range(400):
        s = g.scope()
        same = dict(s)
        if "depth" in s:
            same["depth"] = s["depth"] - 1
        want = ("depth" not in s) or s["depth"] >= 1
        assert scope_subsumes(s, same) is want, f"reflexivity: {j(s)}"


def test_fuzz_2_chains_transitive_and_non_vacuous():
    g = Gen(xorshift32(SEED ^ 11), True)
    held = 0
    for _ in range(600):
        a = g.scope()
        b = g.attenuate(a)
        c = g.attenuate(b)
        if scope_subsumes(a, b) and scope_subsumes(b, c):
            held += 1
            assert scope_subsumes(a, c) is True, f"transitivity broken: {j({'a': a, 'b': b, 'c': c})}"
    assert held >= 120, f"premise held only {held}/600 times"


def test_fuzz_3_instantiation():
    g = Gen(xorshift32(SEED ^ 3), True)
    for _ in range(400):
        p = g.res(True)
        c = g.concrete(p)
        assert path_subsumes(p, c) is True, f"instantiation: {p} should cover {c}"


def test_fuzz_4_no_widening():
    g = Gen(xorshift32(SEED ^ 4), True)
    for _ in range(400):
        p = g.res(True)
        origin, segs, wc = g.split_res(p)
        if wc != "**":
            wider = f"{origin}/{'/'.join([*segs, '**' if wc == '*' else '*'])}"
            assert path_subsumes(p, wider) is False, f"widened: {p} must not cover {wider}"
        head, _, rest = p.partition("://")
        other = head + "://not-the-same.example/" + rest.split("/", 1)[1]
        assert path_subsumes(p, other) is False, f"origin: {p} must not cover {other}"


def test_fuzz_5_cap_rule_matches_exact_oracle():
    g = Gen(xorshift32(SEED ^ 5), True)
    dflt = {"max_per_tx": 100, "max_cumulative": 100000, "unit": "USD", "window": "utc_day"}
    trues = 0
    for _ in range(1500):
        p, c = g.cap(), g.cap()
        p = dflt if p is _MISSING else p
        c = dflt if c is _MISSING else c
        want = oracle_cap_subsumes(p, c)
        assert cap_subsumes(p, c) is want, f"cap oracle: {j({'p': p, 'c': c})}"
        trues += want
    for _ in range(600):
        s = g.scope()
        if not s.get("cap"):
            s["cap"] = dflt
        c = g.attenuate(s)["cap"]
        want = cap_is_valid(c) and oracle_cap_subsumes(s["cap"], c)
        assert cap_subsumes(s["cap"], c) is want, f"cap oracle (attenuated): {j({'p': s['cap'], 'c': c})}"
        trues += want
    assert trues > 200, f"oracle accepted only {trues} pairs"


def test_fuzz_6_conservation_matches_exact_oracle():
    g = Gen(xorshift32(SEED ^ 9), True)
    accepted = 0
    for _ in range(400):
        parent = g.scope()
        if not parent.get("cap"):
            parent["cap"] = {"max_per_tx": 100, "max_cumulative": 100000, "unit": "USD", "window": "utc_day"}
        n = 1 + g.rint(4)
        children = [g.attenuate(parent) for _ in range(n)]
        try:
            got = verify_envelope_attenuation([parent], children)["ok"]
        except ValueError as e:
            got = "E:" + str(e).split(":")[0]
        if any(not cap_is_valid(c.get("cap")) for c in children):
            assert got == "E:LAP_ERR_CAP_SCHEMA", j({"parent": parent, "children": children})
            continue
        all_sub = all(scope_subsumes(parent, c) for c in children)
        total = sum(oracle_debit(parent["cap"], c["cap"]) for c in children)
        want = all_sub and total <= parent["cap"]["max_cumulative"]
        assert got is want, f"conservation: {j({'parent': parent, 'children': children})}"
        accepted += want
    assert accepted > 40, f"conservation oracle accepted only {accepted}/400"


# "any"-mode cases: a third of the pairs and half of the children are attenuations, so the accept path is exercised too.
def _any_pair(g):
    p = g.scope()
    r = g.rng()
    c = g.attenuate(p) if (r < 0.35 and g.can_attenuate(p)) else g.scope()
    return p, c


def _envelope_case(g):
    np_, nc = 1 + g.rint(2), 1 + g.rint(3)
    P = [g.scope() for _ in range(np_)]
    C = []
    for _ in range(nc):
        r = g.rng()
        C.append(g.attenuate(P[0]) if (r < 0.5 and g.can_attenuate(P[0])) else g.scope())
    return P, C


def test_fuzz_7_typed_errors_only():
    g = Gen(xorshift32(SEED ^ 13), False)
    seen, untyped = {"T": 0, "F": 0, "E": 0}, set()

    def tally(d):
        if d[0] == "X":
            untyped.add(d)
        else:
            seen[d[0]] += 1

    for _ in range(2000):
        p, c = _any_pair(g)
        tally(decide(lambda: scope_subsumes(p, c)))
    for _ in range(400):
        P, C = _envelope_case(g)
        tally(decide(lambda: verify_envelope_attenuation(P, C)))
    assert not untyped, f"untyped errors: {' '.join(sorted(untyped))}"
    assert seen["T"] > 0 and seen["E"] > 0, f"non-vacuity: {seen}"


def test_fuzz_8_cross_port_parity_digest():
    g = Gen(xorshift32(SEED ^ 7), False)
    out = []
    for _ in range(1500):
        p, c = _any_pair(g)
        out.append(decide(lambda: scope_subsumes(p, c)))
    for _ in range(300):
        P, C = _envelope_case(g)
        out.append(decide(lambda: verify_envelope_attenuation(P, C)))
    digest = hashlib.sha256(",".join(out).encode("ascii")).hexdigest()
    counts = {"T": 0, "F": 0, "E": 0, "X": 0}
    for d in out:
        counts[d[0]] += 1
    assert counts["X"] == 0, "untyped errors would make the digest meaningless"
    if EXPLORING:
        return
    expected = json.loads(DIGEST_PATH.read_text(encoding="utf-8"))
    assert counts == expected["decisions"], f"decision counts differ from Node: {counts} vs {expected['decisions']}"
    assert digest == expected["digest"], "decision digest differs from the committed one: the ports diverged"


def test_fuzz_6b_multi_parent_conservation_is_sound():
    # F5 (Gemini hostile review): property 6 only ever used a single parent. Here 2-3 overlapping
    # parents share a child; greedy.ok must imply a feasible full assignment exists (soundness).
    g = Gen(xorshift32(SEED ^ 23), True)

    def feasible(parents, children):
        budget = [(int(p["cap"]["max_cumulative"]) if p.get("cap") else None) for p in parents]

        def go(i):
            if i == len(children):
                return True
            c = children[i]
            for jx, p in enumerate(parents):
                if not scope_subsumes(p, c):
                    continue
                if budget[jx] is None:
                    if go(i + 1):
                        return True
                    continue
                d = oracle_debit(p["cap"], c["cap"])
                if d > budget[jx]:
                    continue
                budget[jx] -= d
                if go(i + 1):
                    return True
                budget[jx] += d
            return False

        return go(0)

    accepted = 0
    for _ in range(500):
        np_ = 2 + g.rint(2)
        parents = []
        for _ in range(np_):
            s = g.scope()
            s["res"] = "mcp://h/pay/**"
            if not s.get("cap"):
                s["cap"] = {"max_per_tx": 100, "max_cumulative": 100000, "unit": "USD", "window": "utc_day"}
            s["depth"] = 5
            s.pop("cp", None)
            s.pop("decay_max_sec", None)
            parents.append(s)
        nc = 1 + g.rint(4)
        children = [g.attenuate(parents[g.rint(np_)]) for _ in range(nc)]
        if any(not cap_is_valid(c.get("cap")) for c in children):
            continue
        try:
            got = verify_envelope_attenuation(parents, children)["ok"]
        except ValueError:
            continue
        assert (not got) or feasible(parents, children), f"unsound multi-parent accept: {j({'parents': parents, 'children': children})}"
        accepted += got
    assert accepted > 30, f"multi-parent accept rate too low ({accepted}/500) to test soundness"
