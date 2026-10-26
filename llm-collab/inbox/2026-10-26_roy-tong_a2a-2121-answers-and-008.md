# Third reply on A2A #2121: answers to the two questions, 005a fixed, DELEGATION-008 added (roy-tong, 2026-10-26)

**Source.** https://github.com/a2aproject/A2A/issues/2121#issuecomment-6406205185 (2026-10-26 01:28 UTC) and AgentMeasure commit `1b7d4e38` ("delegation: 005a bill carries the double count; add DELEGATION-008 roll-up", whose message says it answers the cross-walk questions on A2A #2121).

**What it says.**
- On the three-state choice: "no push-back from us; we think you chose right." `inconsistent` failing the set while `absent` keeps its arithmetic verdict beside the unprovable label is "exactly the separation we argued for"; the pair "admissible, unprovable" never reading as "consistent" is "the property that matters"; `expect_provenance` is "the right forcing function".
- Q1, 005a: "you read it correctly." The bill carried no double count; the FAIL hung on the snapshot signature. Fixed: 005a now bills 258644 (parent 128572 + child 130072), so the bill delta of 128572 pins the double count; the runner now asserts `billed − true == double_counted_tokens` instead of `billed ≥ true`.
- Q2: "gap, you did not miss one." DELEGATION-008 added: N children each within its slice, the sum over the parent budget → FAIL (008a: slices 350 × 3, spend 1015 of 1000); the sum within → PASS (008b: spend 915). A deliberate wrinkle: the slices are over-subscribed (1050 > 1000), named in the failure reason as the allocation-layer gap that mirrors LIP-3 §6's issuer-side point, which "neither family closes, the issuer does".
- On 005a's allowance-versus-counter distinction: "the cleanest statement of why the two sides differ there, and we agree with it ... same invariant, enforced at different boundaries."
- Runner green 23/23. The mirror table over our 17 vectors is still owed ("we lost three days to a scheduling gap").

**Verdict.** Both questions produced changes in the other project's conformance vectors, which is the first time a LAP contribution has changed a public test suite outside LAP. The new 008 shows the two layers on one input: under the slice rules both 008a and 008b are refused at issuance (1050 > 1000), while the roll-up fails 008a and passes 008b.

**Done 2026-10-26.** CROSSWALK.md updated for `1b7d4e38` (005a note; 008 family row; per-vector rows 008a agree, 008b differs; totals 23: 5 agree, 3 via the library, 2 differ, 1 different question, 12 out of scope; the "cannot see" bullet rewritten). SL-18 added with his numbers (three slices of 350 under 1000, refused), 18 vectors, Python 160/160. Reply drafted for the owner's approval.
