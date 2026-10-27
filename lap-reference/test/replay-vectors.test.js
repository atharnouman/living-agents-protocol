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

const scopeOf = (scope) => (typeof scope === "string" ? scope : [scope[0], scope[1]]);
const identityOf = (name) => (name === undefined || name === null ? undefined : V.identities[name]);
const snake = { mark_indeterminate: "markIndeterminate", release: "release", abandon: "abandon" };

function run(vector) {
  const cache = makeIdempotencyCache();
  vector.steps.forEach((step, i) => {
    const where = `${vector.id} step ${i + 1} (${step.op})`;
    if (step.op === "claim" || step.op === "lookup") {
      const out = cache[step.op](scopeOf(step.scope), step.key, identityOf(step.identity));
      assert.equal(out.status, step.expect, where);
      if (step.expect_result !== undefined) assert.deepEqual(out.receipt, step.expect_result, where);
    } else if (step.op === "complete") {
      cache.complete(scopeOf(step.scope), step.key, step.result);
    } else if (step.op in snake) {
      let got;
      try { cache[snake[step.op]](scopeOf(step.scope), step.key); got = "ok"; } catch { got = "error"; }
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

test("REPLAY VECTORS: the file covers the three faults the reviews found", () => {
  const names = V.vectors.map((v) => v.name).join(" ");
  assert.ok(names.includes("cap was cut") && names.includes("another request") && names.includes("two principals"));
  assert.ok(V.vectors.length >= 15);
});
