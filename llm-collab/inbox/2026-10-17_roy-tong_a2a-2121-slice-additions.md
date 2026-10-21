# Reply on A2A #2121: two additions to the slice vectors (roy-tong, 2026-10-17)

**Source.** https://github.com/a2aproject/A2A/issues/2121#issuecomment-6233966461, three hours after the slice-checker comment of 2026-10-17. Roy Tong maintains AgentMeasure (metering and delegation-boundary conformance vectors; 218 stars on 2026-10-17), author association NONE on the A2A repository, an identifiable project owner. Not seen until 2026-10-21 because the Monday scheduled run stalled.

**The reply, in substance.** "Exactly the right shape for the rule: runnable vectors plus a dependency-free checker beats prose", and the five rules "are the same invariants we pin in the metering family". Two additions offered for the vector set:

1. **Sibling-split observability.** With shape (a), a child given a slice cannot tell from the slice alone whether it got the whole remainder or 1/n of it. A vector where the slice carries provenance (parent id plus ordinal) against one where it does not "pins the difference between 'budget was small' and 'I was lied to about my share'".
2. **The n-times-remainder window as a named vector.** B fans out the same $0.50 to C1..Cn; each child check passes locally; total spend reaches n × $0.50. "The delegation twin of retry double-counting, and it is the failure that looks like correct behavior in every per-child log."

Offer: if the checker stays dependency-free, "the fifteen vectors plus these two would slot cleanly into a CI gate later", and a cross-walk against AgentMeasure's delegation-boundary vectors either way.

**Verdict.** Both accepted. The second already existed as SL-02 and is now named for it. The first is a genuine addition, with one trade-off to state: provenance reveals the fan-out width to every child, which elang2 had chosen to hide (a child "cannot tell whether it got the whole budget or 1/n" was a privacy property in the 2026-10-16 synthesis). So provenance is optional in the checker, with both forms as vectors, and the choice is left to the draft.

**Done 2026-10-21.** Rule 6 (optional provenance) in `slice_check.py`: if any slice carries `{"parent", "ordinal", "of"}`, all must, with one parent, `of` equal to the number of slices, and ordinals exactly 1..n. SL-16 (consistent provenance, ok) and SL-17 (three slices each labelled "1 of 1": the arithmetic passes at 90,000 of 100,000, the labels fail). SL-02 retitled "the n-times-remainder window". The parity test separates the arithmetic (shared with the library) from the labels (the checker's alone). Reply drafted for the owner's approval, with the cross-walk accepted.
