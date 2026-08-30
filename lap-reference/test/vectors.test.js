import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { jcs, didKeyToRawPublicKey, sha256Hex, b58Decode, b58Encode } from "../src/crypto-util.js";
import { verifyPassport, verifyJws } from "../src/jws.js";
import { verifyMicroCorePassport, verifyRequestSignature, checkInvocation, verifyReceipt, makeIdempotencyCache } from "../src/microcore.js";

const vectors = JSON.parse(
  readFileSync(new URL("../../output/lip/test-vectors/vectors.json", import.meta.url), "utf8"),
);
const NOW = 1787000100; // inside the vectors' validity windows

test("did:key decoding matches published public keys", () => {
  for (const who of ["principal", "agent", "tool_server"]) {
    const { did, public_key_hex } = vectors.keys[who];
    assert.equal(didKeyToRawPublicKey(did).toString("hex"), public_key_hex);
  }
});

test("JCS canonicalization matches Python byte-for-byte", () => {
  assert.equal(jcs(vectors.passport.claims), vectors.passport.canonical_jcs);
  assert.equal(jcs(vectors.genesis.claims), vectors.genesis.canonical_jcs);
});

test("constitution hash reproduces", () => {
  assert.equal(sha256Hex(vectors.constitution.text), vectors.constitution.sha256);
});

test("passport JWS verifies under LIP-1 rules", () => {
  const payload = verifyPassport(vectors.passport.jws, { now: NOW });
  assert.equal(payload.id, vectors.keys.agent.did);
  assert.equal(payload.principal.id, vectors.keys.principal.did);
});

test("passport rejects a tampered payload", () => {
  const [h, p, s] = vectors.passport.jws.split(".");
  const tampered = JSON.parse(Buffer.from(p, "base64url").toString());
  tampered.autonomy_level = 5;
  const p2 = Buffer.from(JSON.stringify(tampered)).toString("base64url");
  assert.throws(() => verifyPassport([h, p2, s].join("."), { now: NOW }), /LAP_ERR/);
});

test("genesis hash chain reproduces", () => {
  assert.equal(sha256Hex(vectors.passport.canonical_jcs), vectors.genesis.claims.passport_sha256);
  assert.equal(sha256Hex(vectors.genesis.canonical_jcs), vectors.genesis.sha256);
});

test("micro-core passport JWT verifies with audience binding", () => {
  const payload = verifyMicroCorePassport(vectors.micro_core.passport_jwt, {
    expectedAud: "did:web:tools.example.com",
    now: NOW,
  });
  assert.equal(payload.sub, vectors.keys.agent.did);
  assert.throws(
    () => verifyMicroCorePassport(vectors.micro_core.passport_jwt, { expectedAud: "did:web:other.example.com", now: NOW }),
    /LAP_ERR_AUDIENCE/,
  );
});

test("micro-core request signature binds body and passport", () => {
  const mc = vectors.micro_core;
  assert.ok(
    verifyRequestSignature({
      passportJwt: mc.passport_jwt,
      agentDid: vectors.keys.agent.did,
      signatureBase: mc.rfc9421_signature_base,
      signatureB64url: mc.request_signature_b64url,
      requestBody: mc.request_body,
    }),
  );
  assert.throws(
    () =>
      verifyRequestSignature({
        passportJwt: mc.passport_jwt,
        agentDid: vectors.keys.agent.did,
        signatureBase: mc.rfc9421_signature_base,
        signatureB64url: mc.request_signature_b64url,
        requestBody: mc.request_body.replace("4200", "9900"),
      }),
    /LAP_ERR_DIGEST/,
  );
});

test("micro-core invocation checks act/res/cap", () => {
  const payload = verifyMicroCorePassport(vectors.micro_core.passport_jwt, { now: NOW });
  const env = payload.lap.envelope;
  assert.ok(checkInvocation(env, { act: "finance:pay", resource: "mcp://tools.example.com/billing/pay", amount: 4200, unit: "USD" }));
  assert.throws(() => checkInvocation(env, { act: "data:read", resource: "mcp://tools.example.com/billing/pay" }), /LAP_ERR_ACT/);
  assert.throws(() => checkInvocation(env, { act: "finance:pay", resource: "mcp://tools.example.com/admin/keys" }), /LAP_ERR_RES/);
  assert.throws(() => checkInvocation(env, { act: "finance:pay", resource: "mcp://tools.example.com/billing/pay", amount: 6000, unit: "USD" }), /LAP_ERR_CAP/);
});

test("receipt verifies against tool-server key and both body hashes", () => {
  const mc = vectors.micro_core;
  assert.ok(
    verifyReceipt({
      receiptBase: mc.receipt_base,
      receiptSignatureB64url: mc.receipt_signature_b64url,
      serverDid: vectors.keys.tool_server.did,
      requestBody: mc.request_body,
      responseBody: '{"status":"paid","receipt":"R-77"}',
    }),
  );
});

test("passport JWS rejects wrong signer", () => {
  assert.throws(() => verifyJws(vectors.passport.jws, vectors.keys.agent.did), /LAP_ERR_SIG/);
});

test("b58Decode handles leading zeros, empty strings, and roundtrips raw keys", () => {
  assert.equal(b58Decode("").length, 0);
  assert.deepEqual(b58Decode("1"), Buffer.from([0x00]));
  assert.deepEqual(b58Decode("11"), Buffer.from([0x00, 0x00]));
  assert.deepEqual(b58Decode("111"), Buffer.from([0x00, 0x00, 0x00]));

  const rawKeyWithZero = Buffer.concat([Buffer.from([0x00]), Buffer.alloc(31, 0xFF)]);
  const encoded = b58Encode(rawKeyWithZero);
  assert.deepEqual(b58Decode(encoded), rawKeyWithZero);
});

test("makeIdempotencyCache stores and retrieves cached receipts by agent and key", () => {
  const cache = makeIdempotencyCache();
  const agentDid = vectors.keys.agent.did;
  const key = "idem-key-12345";
  const receipt = { status: "paid", receipt_base: "sha256:req:sha256:resp" };

  assert.equal(cache.check(agentDid, key), undefined);
  cache.store(agentDid, key, receipt);
  assert.deepEqual(cache.check(agentDid, key), receipt);
  assert.equal(cache.check("did:key:z6MkOtherAgent...", key), undefined);
});
