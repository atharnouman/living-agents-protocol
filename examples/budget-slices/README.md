# Budget slices: a runnable check for "a child gets a slice, not a view of the whole"

When an agent delegates work and passes a budget down, the number it passes can be read two ways. As a **view** ("the remainder is $500"), every child sees the same number, and n children in parallel can spend n times the remainder before any report comes back. As a **slice** ("your allocation is $200 of my $500"), the parent checks at delegation time that the slices it issues never total more than it holds, and each child is bounded by its own number.

This folder is the slice rule as seventeen test vectors and a dependency-free checker of about 170 lines:

```bash
python slice_check.py vectors.json       # one line per vector; exit 1 if any verdict differs from `expect`
python slice_check.py vectors.json -v    # with the per-child trace (what each child debits, what remains)
```

The rules are LIP-3 sections 4 and 6 of the [Living Agents Protocol](../../output/lip/LIP-3-scope-algebra-v0-draft.md), restated in the checker's docstring:

1. caps are well-formed (non-negative exact integers in minor units, a non-empty unit, a known window);
2. a child's unit and per-call ceiling cannot differ from or exceed the parent's;
3. a child's window cannot be wider than the parent's, and a per-call parent admits only per-call children;
4. a child's allocation is debited in the **parent's window units**: an hourly child of a daily parent debits 24 × its hourly allowance;
5. slices are debited in canonical order, and the remainder never goes negative;
6. optionally, slices carry provenance (`{"parent": id, "ordinal": k, "of": n}`), so a child learns it holds "k of n" rather than "the whole remainder"; if any slice carries it, all must, with one parent, `of` equal to the number of slices, and ordinals exactly 1..n.

Rule 6 was added on 21 October 2026 after a reply on the A2A thread: three slices each labelled "1 of 1" pass the arithmetic (SL-17) and fail on their labels, which pins "the budget was small" against "I was told my share wrongly". Provenance reveals the fan-out width to every child, so whether that observability is worth the loss of sibling privacy is the draft's decision, not the checker's; the vectors show both forms (SL-16, SL-17).

Rule 4 is the one most implementations miss, so the vectors spend four cases on it (SL-05 to SL-08). The trap: a daily parent of 100,000 hands 24 hourly children 4,166 each. Every child is under 1/24 of the parent and passes a per-child check; together they may spend 24 × 24 × 4,166 ≈ 2.4 million a day. Debiting in the parent's units (4,166 × 24 = 99,984 per child) makes the first child consume the parent and refuses the second.

**What this is not.** A static check at delegation time, not a ledger at spend time. Children drawing concurrently on one shared pool need reserve-then-settle accounting against a single ledger (shape (b) in the A2A #2121 thread), and a static check cannot see slices that were issued separately. The algebra makes each issuance sound; the issuer still accounts across everything it signs.

**Consistency.** The two LAP reference libraries (Node and Python) reach the same verdict as this checker on every vector's arithmetic (rules 1 to 5); provenance is the checker's alone. `lap-python/tests/test_budget_slices.py` checks all three agree. Both libraries also share a property-based fuzz digest for the full algebra (actions, resources, counterparties, caps).

**Money.** Amounts are exact integers in the unit's minor denomination; a decimal string such as `"12.50"` USD is `1250`. No floats, no cross-currency arithmetic: a unit mismatch is a refusal, never a conversion.
