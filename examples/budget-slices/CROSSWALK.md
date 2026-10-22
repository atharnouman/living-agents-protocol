# Cross-walk: AgentMeasure DELEGATION-001..007 against the slice rules

Written 2026-10-22 after an exchange on A2A #2121. The AgentMeasure delegation family is in [roy-tong/AgentMeasure](https://github.com/roy-tong/AgentMeasure) (MIT): `conformance/vectors/delegation-001-003.json` at commit `d7706787` (2026-09-18), `conformance/vectors/delegation-004-007.json` and `conformance/runners/run_delegation.py` at `daa9384c` (2026-09-19). The vector files were read as data; the runner was read as text and not executed here. Our side is `slice_check.py` rules 1 to 6 and vectors SL-01 to SL-17 at the commit that adds this file. AgentMeasure is running our vectors through its invariants in the other direction and posting its own table.

**Method.** Each of the 21 AgentMeasure vectors was classified by the layer it pins (allocation at issuance, measurement after spend, delegation structure, attribution), by whether one of the six slice rules says anything about the same situation, and by the verdict the slice rules would give on that situation. Where the shapes do not overlap, the vector is listed as out of scope rather than forced to a verdict.

## The two families in one sentence

The slice rules act **before spend**: a parent may only issue slices that fit inside what it holds, debited in the parent's window units. The AgentMeasure delegation family acts **after spend**: what a parent reports must match what its children actually spent, attributed to the agent that served each turn. The same failures appear in both, one layer apart: a child handed a view of the whole remainder (SL-02) is the inherited counter of DELEGATION-005a; children that are each fine alone and N× together (SL-08) are the shared-instance multiplication of 005c.

## Family table

| AgentMeasure | What it pins | Layer | Slice rule(s) | Relation |
|---|---|---|---|---|
| 001 Delegation Must Not Be Counted as Operation | counting discipline | measurement | none | out of scope: the slice rules count nothing |
| 002 Delegation Depth DAG Enforcement | structure: no cycles, bounded depth | structure | not in the checker; LIP-3 `depth` in the library | partial: a child envelope's remaining depth must be strictly smaller than its parent's, so chains terminate; cycles are not named |
| 003 Cross-Harness Delegation Cost Attribution | aggregation labels, lineage, no double count | measurement | none | out of scope; 003b (double count) is the measurement twin of SL-02 |
| 004 Under-count | child spend never rolls up | measurement | none | out of scope at this layer: an allocation is debited when issued, so a share cannot be invisible at issuance; the under-count exists only in reporting |
| 005 Over-count | inherited cumulative counter; shared instance N× | measurement | rules 4, 5, 6 | same failure geometry: 005a ↔ SL-02 and SL-17, 005c ↔ SL-08; we refuse at issuance, they detect after the fact |
| 006 Mis-attribution Across a Handoff | the billing record names the serving agent and model | attribution | none in the checker; LAP's receipt names the signing agent key per call | out of scope; handoff timing is not modelled |
| 007 Non-propagation | a declared budget must reach the child | enforcement reach | rule 1 and the passport | overlap: a slice is the propagated budget; a child without a cap has no bound |

## Per-vector table

| Vector | AgentMeasure verdict | Under the slice rules | Agreement |
|---|---|---|---|
| del-001a separate count | PASS | out of scope | n/a |
| del-001b flattened count | FAIL | out of scope | n/a |
| del-001c zero delegation | PASS | out of scope | n/a |
| del-002a chain A→B→C, depth 0,1 | PASS | library: admissible when the root's remaining depth is at least 2 (each hop strictly decreases it) | agree in effect |
| del-002b cycle A→B→A | FAIL | library: not a failure as such; B's re-delegation to A is one more attenuation, authority only shrinks, and depth exhausts the chain. Cycles are never named | different framing |
| del-002c depth reaches the ceiling | FAIL (limit not enforced) | library: a hop from an envelope with remaining depth 0 is refused | agree in effect |
| del-003a parent aggregates, labelled | PASS | out of scope | n/a |
| del-003b same cost in parent and child | FAIL | out of scope (the allocation twin, SL-02, is refused) | n/a |
| del-003c lineage preserved | PASS | out of scope | n/a |
| del-004a silent under-count | FAIL | out of scope (cannot occur at issuance) | n/a |
| del-004b rolls up, labelled | PASS | out of scope | n/a |
| del-004c disclosed exclusion | PASS | out of scope | n/a |
| del-005a child inherits the parent's counter | FAIL | SL-02: a child handed the parent's whole remainder alongside a sibling is refused by conservation; SL-17: labels that say "whole remainder" are refused by provenance | agree, one layer apart |
| del-005b child starts from zero | PASS | SL-01, SL-03: a slice of its own | agree |
| del-005c shared instance, reported N× measured | FAIL | SL-08: N children each a fair share, N× together, refused by the debit in parent units | agree, one layer apart |
| del-006a served by A, billed to B | FAIL | out of scope; the LAP receipt is signed over the call by the server and names the agent key that signed the request, so a billing record naming another agent contradicts the receipt | n/a |
| del-006b correct attribution | PASS | out of scope | n/a |
| del-006c subagent spans flattened to root | FAIL | out of scope | n/a |
| del-007a budget declared, not propagated; child overspends | FAIL | rule 1: a child without a cap is malformed; in LAP a child without an envelope has no authority at all, fail closed | agree |
| del-007b propagated, child within it | PASS | SL-01, SL-03 shape | agree |
| del-007c no budget declared, disclosed | PASS | the checker presumes a declared budget and is out of scope here; the LIP-3 library reads a parent without a cap as unbounded and admits any child, which matches the disclosed PASS | agree via the library; the checker does not apply |

**Totals.** Agree in effect: 7 (002a, 002c, 005a, 005b, 005c, 007a, 007b). Different framing: 1 (002b). Checker out of scope, library agrees: 1 (007c). Out of scope: 12 (001, 003, 004, 006).

## What each family cannot see

- The slice rules cannot see spend. A child that stays inside its slice but is billed wrongly, or whose spend never rolls up, passes every slice rule. That is DELEGATION-003, 004 and 006.
- The AgentMeasure family cannot see issuance. A parent that hands every child the whole remainder passes 004 and 007 until the children spend; 005 catches it only once the counters show the inheritance. SL-02, SL-08 and SL-17 refuse it before any spend.
- Neither family is a ledger. Concurrent children drawing on one shared pool need reserve-then-settle at spend time (shape (b) in the A2A thread), which neither set of vectors models.

## Provenance, three states

Suggested by AgentMeasure on 2026-10-21 and adopted here: the checker reports the provenance outcome beside the verdict as `consistent`, `inconsistent` (a failure: SL-17) or `absent` (the fan-out is unprovable from the slices alone: a finding, not a pass). Hiding the fan-out from children can be a privacy property of the draft; the billable side still needs one party, an issuer record or a ledger, to hold `{parent, ordinal, of}` in a form it cannot edit after the fact, or a dispute has no arbiter. In LAP that party is the issuer's signed log, or an audit record of the delegation; which one is the draft's decision. `expect_provenance` pins the state on every vector.
