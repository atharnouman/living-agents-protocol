// Recovery of an in-flight idempotency claim after a crash (LIP-4 recovery rule, 2026-10-21, raised
// by an external review on A2A #2323): an external effect completes, then the process dies before
// storing its completion. The claim is INDETERMINATE: refused on retry, never re-executed, never
// released by time alone, resolved only by reconciliation.
import { test } from "node:test";
import assert from "node:assert/strict";
import { makeIdempotencyCache } from "../src/microcore.js";

test("RECOVERY: an indeterminate claim is refused until reconciliation completes it", () => {
  const cache = makeIdempotencyCache();
  assert.deepEqual(cache.claim("did:key:a", "k"), { status: "reserved" });
  cache.markIndeterminate("did:key:a", "k");                       // the executor died after reserving
  assert.deepEqual(cache.claim("did:key:a", "k"), { status: "indeterminate" }); // a retry is refused, not run
  assert.equal(cache.check("did:key:a", "k"), null);               // no receipt exists yet
  assert.throws(() => cache.markIndeterminate("did:key:a", "never-claimed"), /only an in-flight claim/);
  cache.complete("did:key:a", "k", { paid: true, reconciled: true }); // the effect had happened
  assert.deepEqual(cache.claim("did:key:a", "k"), { status: "completed", receipt: { paid: true, reconciled: true } });
});

test("RECOVERY: release after reconciliation found no effect lets the same key run fresh", () => {
  const cache = makeIdempotencyCache();
  cache.claim("did:key:a", "k");
  assert.throws(() => cache.release("did:key:a", "k"), /only an indeterminate claim/); // in flight: may be running
  cache.markIndeterminate("did:key:a", "k");
  cache.release("did:key:a", "k");                                 // reconciliation: nothing happened
  assert.deepEqual(cache.claim("did:key:a", "k"), { status: "reserved" });
});
