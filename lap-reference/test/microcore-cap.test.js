// LIP-4 Micro-Core cap vectors (output/lip/test-vectors/microcore-cap-vectors.json), shared with
// the Python port: the per-transaction cap check refuses every amount that is not a non-negative
// exact integer, and every malformed cap, BEFORE comparing. Found by the cold-start usability test
// of 2026-10-17: both ports evaluated `-500000 <= 1000` as true and executed the payment.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { checkInvocation, isExactAmount, microCoreCapIsValid } from "../src/microcore.js";

const V = JSON.parse(
  readFileSync(new URL("../../output/lip/test-vectors/microcore-cap-vectors.json", import.meta.url), "utf8"),
);

const verdict = (envelope, amount, unit) => {
  try {
    checkInvocation(envelope, { ...V.invocation, amount, unit });
    return "ok";
  } catch (e) {
    return e.message.split(":")[0];
  }
};

test("CAP VECTORS: every amount that is not a non-negative exact integer is refused before comparison", () => {
  for (const v of V.amount_vectors) assert.equal(verdict(V.envelope, v.amount, v.unit), v.expect, `${v.id}: ${v.note}`);
});

test("CAP VECTORS: a malformed cap never reaches a comparison; null is no cap, {} is malformed", () => {
  for (const v of V.cap_vectors) {
    const envelope = { ...V.envelope, cap: v.cap };
    assert.equal(verdict(envelope, V.probe.amount, V.probe.unit), v.expect, `${v.id}: ${v.note}`);
  }
});

test("CAP: values JSON cannot carry (NaN, infinities) and JavaScript coercions are refused", () => {
  for (const bad of [NaN, Infinity, -Infinity, "abc", "500", [], {}, true, -0.5, 1n]) {
    assert.equal(verdict(V.envelope, bad, "USD"), "LAP_ERR_CAP", String(bad));
  }
  assert.ok(isExactAmount(0) && isExactAmount(Number.MAX_SAFE_INTEGER));
  assert.ok(!isExactAmount(Number.MAX_SAFE_INTEGER + 1) && !isExactAmount(true) && !isExactAmount(-1));
  assert.ok(microCoreCapIsValid({ max_per_tx: 0, unit: "USD" }));
  assert.ok(!microCoreCapIsValid([1000, "USD"]) && !microCoreCapIsValid({ max_per_tx: NaN, unit: "USD" }));
});
