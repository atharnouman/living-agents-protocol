// Round-3 review tests (Gemini findings, triaged). Test 1 is ADAPTED from the
// contributed version: LIP-4 §2(3) mandates registered-verb EQUALITY in Micro-Core
// (no wildcard/DAG), so the spec-conformant expectation is rejection, not support.
import { test } from "node:test";
import assert from "node:assert/strict";
import { b58Decode, b58Encode, didKeyToRawPublicKey, normalizeDid } from "../src/crypto-util.js";
import { capSubsumes } from "../src/algebra.js";
import { checkInvocation, makeIdempotencyCache } from "../src/microcore.js";

test("INVOCATION: Micro-Core is equality-only — wildcard rejected loudly, DAG children not implied", () => {
  const wildcardEnv = { act: ["*"], res: "mcp://tools/**" };
  assert.throws(() => checkInvocation(wildcardEnv, { act: "data:read", resource: "mcp://tools/db" }), /wildcard/);
  const parentEnv = { act: ["finance:pay"], res: "ap2://rails/**", cap: { max_per_tx: 100, unit: "USD" } };
  assert.throws(() => checkInvocation(parentEnv, { act: "finance:pay:escrow", resource: "ap2://rails/pay" }), /LAP_ERR_ACT/);
  assert.ok(checkInvocation(parentEnv, { act: "finance:pay", resource: "ap2://rails/pay", amount: 50, unit: "USD" }));
});

test("IDEMPOTENCY: cache prevents duplicate execution, keyed per agent", () => {
  const cache = makeIdempotencyCache();
  const agentDid = "did:key:z6MksMrZDkhaiLzXQo4kRmKLcU8qbVerEv4j1Jqon9CPPHEC";
  const receipt = { status: "paid", receipt_base: "sha256:abc:sha256:def" };
  assert.equal(cache.check(agentDid, "req-1"), undefined);
  cache.store(agentDid, "req-1", receipt);
  assert.deepEqual(cache.check(agentDid, "req-1"), receipt);
  assert.equal(cache.check("did:key:z6MkOther", "req-1"), undefined);
});

test("CRYPTO: b58Decode boundary invariants (leading zeros, empty, round-trip)", () => {
  assert.equal(b58Decode("").length, 0);
  assert.deepEqual(b58Decode("1"), Buffer.from([0x00]));
  assert.deepEqual(b58Decode("11"), Buffer.from([0x00, 0x00]));
  assert.deepEqual(b58Decode("111"), Buffer.from([0x00, 0x00, 0x00]));
  const raw32WithZero = Buffer.concat([Buffer.from([0x00]), Buffer.alloc(31, 0xff)]);
  assert.deepEqual(b58Decode(b58Encode(raw32WithZero)), raw32WithZero);
});

test("ALGEBRA: epoch_total attenuates only to epoch_total, cumulative reduced", () => {
  const parent = { max_per_tx: 500, max_cumulative: 5000, unit: "USD", window: "epoch_total" };
  assert.equal(capSubsumes(parent, { max_per_tx: 100, max_cumulative: 1000, unit: "USD", window: "epoch_total" }), true);
  assert.equal(capSubsumes(parent, { max_per_tx: 100, max_cumulative: 1000, unit: "USD", window: "utc_day" }), false);
  assert.equal(capSubsumes(parent, { max_per_tx: 100, max_cumulative: 6000, unit: "USD", window: "epoch_total" }), false);
});

test("CRYPTO: didKeyToRawPublicKey rejects unsupported methods and malformed input", () => {
  assert.throws(() => didKeyToRawPublicKey("did:web:example.com"), /unsupported DID method/);
  assert.throws(() => didKeyToRawPublicKey("did:key:"), /unsupported DID method/);
  assert.throws(() => didKeyToRawPublicKey("did:key:z6Ls..."), /invalid base58 character|not an ed25519-pub|bad key length/);
});

test("NORMALIZATION: normalizeDid lowercases method prefix but PRESERVES case-sensitive id", () => {
  const did = "did:KEY:z6MksMrZDkhaiLzXQo4kRmKLcU8qbVerEv4j1Jqon9CPPHEC";
  const n = normalizeDid(did);
  assert.equal(n, "did:key:z6MksMrZDkhaiLzXQo4kRmKLcU8qbVerEv4j1Jqon9CPPHEC");
  // the reviewer's proposed normalizeUri approach would have destroyed the key:
  assert.notEqual(n, n.toLowerCase());
});
