// LIP-4 Micro-Core replay vectors (output/lip/test-vectors/microcore-replay-vectors.json), shared
// with the Python suite: the idempotency claim under authority replacement and key reuse (LIP-4
// section 2 step 3 and step 6, 0.4.14). Each vector is a sequence of steps against one fresh cache
// and the envelope check; the two ports must give the same outcome at every step.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { checkInvocation, makeIdempotencyCache } from "../src/microcore.js";

const V = JSON.parse(
  readFileSync(new URL("../../output/lip/test-vectors/microcore-replay-vectors.json", import.meta.url), "utf8"),
);

const scopeOf = (scope) => (typeof scope === "string" ? scope : [...scope]);
const identityOf = (name) => (name === undefined || name === null ? undefined : V.identities[name]);
const method = { complete: "complete", mark_indeterminate: "markIndeterminate", release: "release", abandon: "abandon" };

function run(vector) {
  const cache = makeIdempotencyCache();
  vector.steps.forEach((step, i) => {
    const where = `${vector.id} step ${i + 1} (${step.op})`;
    if (step.op === "claim" || step.op === "lookup") {
      const out = cache[step.op](scopeOf(step.scope), step.key, identityOf(step.identity));
      assert.equal(out.status, step.expect, where);
      if (step.expect_result !== undefined) assert.deepEqual(out.receipt, step.expect_result, where);
    } else if (step.op === "store") {
      cache.store(scopeOf(step.scope), step.key, step.result, identityOf(step.identity));
    } else if (step.op in method) {
      let got;
      try {
        if (step.op === "complete") cache.complete(scopeOf(step.scope), step.key, step.result);
        else cache[method[step.op]](scopeOf(step.scope), step.key);
        got = "ok";
      } catch { got = "error"; }
      assert.equal(got, step.expect ?? "ok", where);
    } else if (step.op === "check_invocation") {
      let got;
      try {
        checkInvocation(V.envelopes[step.envelope], {
          act: step.act, resource: step.resource, amount: step.amount ?? undefined, unit: step.unit,
          enforceMagnitude: step.enforce_magnitude ?? true,
        });
        got = "ok";
      } catch (e) { got = e.message.split(":")[0]; }
      assert.equal(got, step.expect, where);
    } else {
      assert.fail(`${where}: unknown op`);
    }
  });
}

for (const vector of V.vectors) {
  test(`REPLAY VECTORS ${vector.id}: ${vector.name}`, () => run(vector));
}

test("REPLAY VECTORS: the file covers the faults the reviews found", () => {
  const names = V.vectors.map((v) => v.name).join(" ");
  for (const phrase of ["cap was cut", "another request", "two principals", "without an identity", "never overwritten", "audiences"]) {
    assert.ok(names.includes(phrase), phrase);
  }
  assert.ok(V.vectors.length >= 18);
});
