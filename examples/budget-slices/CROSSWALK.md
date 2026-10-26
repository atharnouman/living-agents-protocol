# Cross-walk: AgentMeasure DELEGATION-001..008 against the slice rules

Written 2026-10-22 after an exchange on A2A #2121. The AgentMeasure delegation family is in [roy-tong/AgentMeasure](https://github.com/roy-tong/AgentMeasure) (MIT): `conformance/vectors/delegation-001-003.json` at commit `d7706787` (2026-09-18), `conformance/vectors/delegation-004-007.json` and `conformance/runners/run_delegation.py` at `daa9384c` (2026-09-19). The vector files were read as data and the runner as text; nothing from that repository was executed here. Our side is `slice_check.py` rules 1 to 6 and vectors SL-01 to SL-18. Updated 2026-10-26 for AgentMeasure commit `1b7d4e38`, made in answer to the two questions the first version of this table raised: 005a's bill now carries the double count, and DELEGATION-008 (`conformance/vectors/delegation-008.json`) sums N children against one parent budget. Only the two vector files were re-read at that commit, as data; the runner at that commit was not read, so its reported 23/23 is his statement, not checked here. AgentMeasure has said it will run our vectors through its invariants in the other direction and post its own table.

**Method.** These are hand-derived verdicts on analogous situations, not runs: the AgentMeasure runner takes counters and reports, the slice checker takes caps, so no vector was run through both tools. Each of the 23 AgentMeasure vectors was classified by the layer it pins, by whether one of the six slice rules (or the LIP-3 library behind them) says anything about the same situation, and by the verdict our side would give. Where the shapes do not overlap, the vector is listed as out of scope rather than forced to a verdict.

## The two families in one sentence

The slice rules act at issuance: a parent may only issue slices that fit inside what it holds, debited in the parent's window units. The AgentMeasure family pins the delegation record and its accounting: 002 and 007 at delegation time (structure, and whether a budget reached the child), 001, 003, 004, 005, 006 and 008 after spend (counting, roll-up, attribution). Two shapes appear in both: a number held by N parties as if each owned it (their 005c, our SL-02), and an over-subscribed allocation (their 008 input, our SL-04 and SL-18).

## Family table

| AgentMeasure | What it pins | When | Our side | Relation |
|---|---|---|---|---|
| 001 Delegation Must Not Be Counted as Operation | counting discipline | after spend | none | out of scope: the slice rules count nothing |
| 002 Delegation Depth DAG Enforcement | no cycles, bounded depth | delegation time | LIP-3 `depth` in the library, not the checker | partial: where an envelope carries `depth`, a child's must be at least one lower, so a hop from 0 is refused; without it there is no bound; cycles are never named, since no hop can widen authority |
| 003 Cross-Harness Delegation Cost Attribution | aggregation labels, lineage, no double count | after spend | none | out of scope; a parent spending what it has sliced away is a ledger matter, not a slice rule |
| 004 Under-count | child spend never rolls up | after spend | none | out of scope; within one issuance every share is debited, so none can go missing, but across separately issued envelopes one can, which LIP-3 §6 leaves to the issuer |
| 005 Over-count | inherited cumulative counter; shared instance N× | after spend | rules 5 and 6 | 005c matches SL-02 (one number held by N parties); 005a is the predicted disagreement: a slice is an allowance, not a spent-so-far counter |
| 006 Mis-attribution Across a Handoff | the billing record names the serving agent and model | after spend | none | out of scope; the slice rules carry no serving record and no model |
| 007 Non-propagation | a declared budget must reach the child | delegation time | rule 1 and the passport | overlap: a slice is the propagated budget; a child without a cap has no bound |
| 008 Roll-up (added 2026-10-26) | N children's spend summed against one parent budget | after spend | rule 5 (SL-04, SL-18) | the same input shows both layers: its slices are over-subscribed (350 × 3 > 1000), so the slice rules refuse both vectors when the three slices are checked as one set, while the roll-up fails only the one whose spend exceeds the budget; issued separately, each slice passes a per-envelope check and LIP-3 §6 leaves the sum to the issuer |

## Per-vector table

| Vector | AgentMeasure verdict | Our side | Agreement |
|---|---|---|---|
| del-001a separate count | PASS | out of scope | n/a |
| del-001b flattened count | FAIL | out of scope | n/a |
| del-001c zero delegation | PASS | out of scope | n/a |
| del-002a chain A→B→C, depth 0,1 | PASS | library: admissible when the root carries `depth` at least 2, since each hop must carry a smaller one; a root without `depth` is unbounded in both libraries, which 002 would fail | agree via the library, when depth is carried |
| del-002b cycle A→B→A | FAIL | library: no hop can widen authority (subsumption is reflexive, so a child may equal its parent but never exceed it), and where `depth` is carried it runs out; the rules never name a cycle. Invariant 30 is about the measurement graph, where a cycle makes the roll-up undefined | different question; both can hold |
| del-002c depth reaches the ceiling | FAIL (limit not enforced) | library: a hop from an envelope with `depth` 0 is refused | agree via the library |
| del-003a parent aggregates, labelled | PASS | out of scope | n/a |
| del-003b same cost in parent and child | FAIL | out of scope: a parent spending what it sliced away is a ledger matter | n/a |
| del-003c lineage preserved | PASS | out of scope | n/a |
| del-004a silent under-count | FAIL | out of scope (see the 004 row) | n/a |
| del-004b rolls up, labelled | PASS | out of scope | n/a |
| del-004c disclosed exclusion | PASS | out of scope | n/a |
| del-005a child inherits the parent's spent counter (since `1b7d4e38` the bill carries the double count: 258644 billed against 130072 true) | FAIL | no slice analogue: an allowance has no spent-so-far counter to inherit. The nearest shape, a sole child handed the whole remainder, is admissible (SL-01), and a parent's earlier spend is invisible to a static check | differs, as predicted |
| del-005b child starts from zero | PASS | SL-01, SL-03: a slice of its own | agree |
| del-005c shared instance, reported N× measured | FAIL | SL-02: one number held by N parties as if each owned it; refused at issuance by conservation, detected by 005c after spend | agree, one layer apart |
| del-006a served by A, billed to B | FAIL | out of scope: no serving record, no model | n/a |
| del-006b correct attribution | PASS | out of scope | n/a |
| del-006c subagent spans flattened to root | FAIL | out of scope | n/a |
| del-007a budget declared, not propagated; child overspends | FAIL | rule 1: a child without a cap is malformed; in LAP a child without an envelope has no authority at all, fail closed | agree |
| del-007b propagated, child within it | PASS | SL-01, SL-03 shape | agree |
| del-007c no budget declared, disclosed | PASS | the checker presumes a declared budget and does not apply; the LIP-3 library reads a parent without a cap as unbounded and admits any child, silently, where 007c requires the absence to be disclosed | agree via the library, minus the disclosure |
| del-008a every child within its slice, the sum over the parent budget (spend 1015 of 1000) | FAIL | SL-18: the three slices of 350 under a parent of 1000 are refused when checked as one set (1050 > 1000), before any child spends | agree, one layer apart: the same over-subscription, after spend and before it |
| del-008b sum of children within the parent budget (spend 915 of 1000) | PASS | SL-18: the same allocation, refused when checked as one set; what the children later spend does not change it | differs: the same over-subscription before it shows in spend; 008a's failure reason calls it an allocation gap mirroring LIP-3 §6; both verdicts hold |

**Totals (23).** Agree: 5 (005b, 005c, 007a, 007b, 008a). Agree via the library, with caveats: 3 (002a, 002c, 007c). Differs: 2 (005a, as predicted; 008b, the two layers on one input). Different question: 1 (002b). Out of scope: 12 (001, 003, 004, 006).

**How the two compose.** 007 gives spend ≤ slice for each child; rule 5 gives Σ slices ≤ budget for the set; together they imply Σ spend ≤ budget, which is 008's conclusion. The implication does not run backwards: 008b's spend is within the budget while its slices are not.

## What each family cannot see

- The slice rules cannot see spend. A child that stays inside its slice but is billed wrongly, or whose spend never rolls up, passes every slice rule (003, 004, 006). They also cannot see a parent's earlier spend, which is what 005a is about.
- Until 2026-10-26 the AgentMeasure family had no vector that sums N children against one parent budget (007b tests one `child_spend`). DELEGATION-008 now does, after spend. Its inputs carry the over-subscribed allocation (`budget_slices_sum` 1050) but its expectation tests spend only, so an over-subscription is not tested by the roll-up unless the spend itself crosses the budget (008b passes); SL-04 and SL-18 refuse it when the slices are checked as one set. 008a's failure reason calls this an allocation gap that mirrors LIP-3 §6. 005 detects counter inheritance, which over-issuance does not produce, since a child handed a view of the remainder still starts its own counter at zero.
- Neither family is a ledger. Within one issuance every share is debited, so none can go missing and the set cannot over-subscribe; across separately issued envelopes either can, and LIP-3 §6 leaves that to the issuer. Concurrent children drawing on one shared pool need reserve-then-settle at spend time (shape (b) in the A2A thread). Neither set of vectors models either.

## Provenance, three states

Suggested by AgentMeasure on 2026-10-21 and adopted: the checker reports the provenance outcome beside the verdict as `consistent`, `inconsistent` (which fails the set: SL-17) or `absent` (the fan-out is unprovable from the slices alone: the arithmetic verdict stands and the absence is reported as a finding). Hiding the fan-out from children can be a privacy property of the draft; the billable side still needs one party to hold `{parent, ordinal, of}` in a form it cannot edit after the fact, or a dispute has no arbiter. LAP does not define that record yet: LIP-3 §6 makes cross-sibling accounting an issuer duty without saying where the labels live, and the proposed `delegated-authority` audit-record extension is a candidate carrier for them. An issuer's own hash chain is not enough on its own, since the issuer can rewrite it, unless it is anchored or held by both parties. `expect_provenance` pins the state on every vector.
