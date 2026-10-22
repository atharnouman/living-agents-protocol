#!/usr/bin/env python3
"""Budget slices: can a parent hand these children their slices without the total growing?

A static check, run at delegation time, of the rule "a child gets a slice, not a view of the
whole" (shape (a) in the A2A #2121 thread). It answers one question per vector: given a parent
budget and the slices it wants to issue, is the set admissible? The rules are LIP-3 sections 4
and 6 of the Living Agents Protocol, restated here in plain Python with no dependencies, so the
file can be read in five minutes and run anywhere:

  1. Every cap is well-formed: non-negative exact integers (minor units, so a decimal string such
     as "12.50" USD is 1250), max_per_tx <= max_cumulative, a non-empty unit, a known window.
  2. A child's unit equals the parent's, and its per-call ceiling (max_per_tx) does not exceed
     the parent's.
  3. Windows: a `tx` (per-call) parent admits only `tx` children; a timed parent admits a timed
     child whose window is the same or shorter and divides it; a wider child window is refused.
  4. The debit of a child is its allocation converted into the PARENT's window units:
     an hourly child of a daily parent debits 24 x its max_cumulative. This is the "24x trap":
     24 hourly children of 1/24 each look individually fine and together allow 24x the budget.
  5. Children are debited in canonical order; the running remainder never goes negative.
  6. Optional provenance: a slice MAY carry {"provenance": {"parent": id, "ordinal": k, "of": n}}
     so the child learns it holds "k of n", not "the whole remainder". The outcome has three states,
     reported beside the verdict: CONSISTENT (every slice carries it, one parent, `of` equal to the
     number of slices, ordinals exactly 1..n), INCONSISTENT (a failure: three slices each labelled
     "1 of 1" pass the arithmetic and fail here, the labels are the lie), and ABSENT (no slice carries
     it: the fan-out is UNPROVABLE from the slices alone, a finding rather than a pass). Hiding the
     fan-out from children can be a privacy property of the draft; the billable side still needs at
     least one party (an issuer record or a ledger) to hold {parent, ordinal, of} in a form it cannot
     edit after the fact, or a dispute has no arbiter. Which party is the draft's decision.

What this does NOT do, stated plainly: it is not a runtime ledger. Concurrent children drawing on
one shared pool need reserve-then-settle accounting at the moment of spend (shape (b)); a static
check cannot see siblings that are issued separately or spend in parallel. The algebra makes each
issuance sound; the issuer still has to account across everything it signs.

Usage:  python slice_check.py vectors.json        (exit 1 if any vector's verdict differs from
        python slice_check.py vectors.json -v     its `expect`; -v prints the per-child trace)
"""
import json
import sys

WINDOW_SECONDS = {"utc_hour": 3600, "utc_day": 86400}
VALID_WINDOWS = {"tx", "utc_hour", "utc_day", "epoch_total"}
MAX_SAFE = 2**53 - 1  # the JSON interop bound: JavaScript verifiers lose exactness above it


def is_amount(x):
    return isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= MAX_SAFE


def cap_problem(cap):
    """Rule 1. Returns None for a well-formed cap, else the reason."""
    if not isinstance(cap, dict):
        return "cap is not an object"
    if not is_amount(cap.get("max_per_tx")) or not is_amount(cap.get("max_cumulative")):
        return "max_per_tx and max_cumulative must be non-negative exact integers"
    if cap["max_per_tx"] > cap["max_cumulative"]:
        return "max_per_tx exceeds max_cumulative"
    if not isinstance(cap.get("unit"), str) or not cap["unit"]:
        return "unit must be a non-empty string"
    if cap.get("window") not in VALID_WINDOWS:
        return f"window must be one of {sorted(VALID_WINDOWS)}"
    return None


def slice_problem(parent, child):
    """Rules 2 and 3. Returns None when the child is a valid slice of the parent, else the reason."""
    if child["unit"] != parent["unit"]:
        return f"unit {child['unit']} differs from the parent's {parent['unit']}"
    if child["max_per_tx"] > parent["max_per_tx"]:
        return f"max_per_tx {child['max_per_tx']} exceeds the parent's {parent['max_per_tx']}"
    pw, cw = parent["window"], child["window"]
    if pw in ("tx", "epoch_total"):
        if cw != pw:
            return f"a {pw} parent admits only {pw} children (a timed child would re-base the budget)"
        if child["max_cumulative"] > parent["max_cumulative"]:
            return f"max_cumulative {child['max_cumulative']} exceeds the parent's {parent['max_cumulative']}"
        return None
    if cw in ("tx", "epoch_total"):
        return f"a {cw} child of a timed parent has no bounded rate"
    p_sec, c_sec = WINDOW_SECONDS[pw], WINDOW_SECONDS[cw]
    if c_sec > p_sec or p_sec % c_sec != 0:
        return f"child window {cw} is wider than, or does not divide, the parent window {pw}"
    scaled_max = (parent["max_cumulative"] * c_sec) // p_sec  # integer floor: identical in every language
    if child["max_cumulative"] > scaled_max:
        return f"max_cumulative {child['max_cumulative']} per {cw} exceeds {scaled_max} (the parent's {parent['max_cumulative']} per {pw}, scaled)"
    return None


def debit(parent, child):
    """Rule 4: the child's allocation in the parent's window units."""
    p_sec, c_sec = WINDOW_SECONDS.get(parent["window"]), WINDOW_SECONDS.get(child["window"])
    if p_sec and c_sec:
        return (child["max_cumulative"] * p_sec) // c_sec
    return child["max_cumulative"]


def provenance_state(children):
    """Rule 6: "consistent", "inconsistent" or "absent" (fan-out unprovable from the slices alone)."""
    if not any("provenance" in c for c in children):
        return "absent"
    return "inconsistent" if provenance_problem(children) else "consistent"


def provenance_problem(children):
    """Rule 6 (optional). Returns None when no slice carries provenance or the set is consistent."""
    tagged = [c for c in children if "provenance" in c]
    if not tagged:
        return None
    if len(tagged) != len(children):
        return "some slices carry provenance and some do not"
    ps = [c["provenance"] for c in children]
    for p in ps:
        if not isinstance(p, dict) or not isinstance(p.get("parent"), str) or not is_amount(p.get("ordinal")) or not is_amount(p.get("of")):
            return "provenance needs parent (a string), ordinal and of (non-negative exact integers)"
    if len({p["parent"] for p in ps}) != 1:
        return "slices name different parents"
    if {p["of"] for p in ps} != {len(children)}:
        return f"`of` must equal the number of slices issued ({len(children)})"
    ordinals = sorted(p["ordinal"] for p in ps)
    if ordinals != list(range(1, len(children) + 1)):
        return f"ordinals must be exactly 1..{len(children)} without repeats, got {ordinals}"
    return None


def check_slices(parent, children):
    """Rules 1-6 over a parent cap and the list of slices it wants to issue.
    Returns (ok, reason, trace, provenance): the verdict, its reason, one trace line per child, and
    the provenance state ("consistent", "inconsistent" or "absent"), which is reported beside the
    verdict rather than folded into it, so an absent fan-out record is a finding, not a pass."""
    trace = []
    prov = provenance_state(children)
    problem = cap_problem(parent)
    if problem:
        return False, f"parent: {problem}", trace, prov
    for i, child in enumerate(children):
        problem = cap_problem(child)
        if problem:
            return False, f"child {i}: {problem}", trace, prov
    problem = provenance_problem(children)
    if problem:
        return False, f"provenance: {problem}", trace, prov
    remaining = parent["max_cumulative"]
    # Canonical order (LIP-3 section 6): sorted by the canonical JSON of the cap, so every
    # implementation debits in the same order and reaches the same verdict.
    ordered = sorted(children, key=lambda c: json.dumps(c, sort_keys=True, separators=(",", ":")))
    for child in ordered:
        problem = slice_problem(parent, child)
        if problem:
            trace.append(f"  refuse {fmt(child)}: {problem}")
            return False, problem, trace, prov
        d = debit(parent, child)
        if d > remaining:
            trace.append(f"  refuse {fmt(child)}: debits {d} per {parent['window']} but only {remaining} of {parent['max_cumulative']} remains")
            return False, f"conservation: the slices total more than the parent (this child debits {d}, {remaining} remained)", trace, prov
        remaining -= d
        trace.append(f"  admit  {fmt(child)}: debits {d} per {parent['window']}, {remaining} remains")
    return True, f"all slices admitted, {remaining} of {parent['max_cumulative']} unallocated", trace, prov


def fmt(cap):
    p = cap.get("provenance")
    tag = f" [{p.get('ordinal')} of {p.get('of')}]" if isinstance(p, dict) else ""
    return f"{cap.get('max_per_tx')}/call, {cap.get('max_cumulative')}/{cap.get('window')} {cap.get('unit')}{tag}"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    verbose = "-v" in argv
    data = json.load(open(argv[1], encoding="utf-8"))
    failures, unprovable = 0, 0
    for v in data["vectors"]:
        ok, reason, trace, prov = check_slices(v["parent"], v["children"])
        got = "ok" if ok else "reject"
        mark = "PASS" if got == v["expect"] else "FAIL"
        # A vector may also pin the provenance state; a mismatch is a failure like any other.
        if "expect_provenance" in v and v["expect_provenance"] != prov:
            mark = "FAIL"
        failures += mark == "FAIL"
        unprovable += prov == "absent"
        label = {"consistent": "provenance consistent", "inconsistent": "provenance INCONSISTENT",
                 "absent": "fan-out UNPROVABLE (no provenance)"}[prov]
        print(f"{mark}  {v['id']}  expect {v['expect']:<6} got {got:<6}  {label:<34}  {v['title']}")
        print(f"      {reason}")
        if verbose:
            print("\n".join(trace))
    n = len(data["vectors"])
    print(f"\n{n - failures} of {n} vectors agree with their expected verdict; {unprovable} carry no provenance (fan-out unprovable from the slices alone)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
