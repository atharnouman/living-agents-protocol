// Strict-canonical base64url (self-found 2026-09-06 via a flaky lap-git self-test).
// A lenient decoder gives one signature many textual forms: the final character of an
// Ed25519 signature carries only two data bits, so 'A'->'B' changes padding bits alone
// and the bytes still verify. Anything keyed by the TEXT (lap-passport-hash, dedup keys,
// denylists, log entries) could then be evaded by re-encoding. Decoders MUST reject.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { b64urlDecode, b64urlEncode, sha256Hex } from "../src/crypto-util.js";
import { verifyRequestSignature, verifyMicroCorePassport } from "../src/microcore.js";
import { decodeJws } from "../src/jws.js";

const here = dirname(fileURLToPath(import.meta.url));
const v = JSON.parse(readFileSync(join(here, "..", "..", "output", "lip", "test-vectors", "vectors.json"), "utf8"));
const ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
const NOW = 1787000000;
// Change padding-only bits in the final character: same bytes under a lenient decoder.
const nonCanonical = (s) => s.slice(0, -1) + ALPHA[ALPHA.indexOf(s.at(-1)) + 1];

test("b64urlDecode is strict: canonical only (no padding, no foreign chars, zero trailing bits)", () => {
  const sig = v.micro_core.request_signature_b64url;
  assert.equal(sig.length, 86);
  assert.equal(b64urlEncode(b64urlDecode(sig)), sig);                       // canonical round-trip
  const sig2 = nonCanonical(sig);
  assert.ok(Buffer.from(sig2, "base64url").equals(Buffer.from(sig, "base64url")), "premise: lenient decoding conflates the two forms");
  assert.throws(() => b64urlDecode(sig2), /LAP_ERR_ENCODING: non-canonical/);
  assert.throws(() => b64urlDecode(sig + "=="), /LAP_ERR_ENCODING/);       // padding
  assert.throws(() => b64urlDecode(sig.slice(0, 10) + "$" + sig.slice(10)), /LAP_ERR_ENCODING/); // foreign char
  assert.throws(() => b64urlDecode(sig.replace("-", "+").replace("_", "/") + "+"), /LAP_ERR_ENCODING/); // std alphabet
  assert.throws(() => b64urlDecode(sig + "AAA"), /LAP_ERR_ENCODING/);      // length % 4 === 1
  assert.throws(() => b64urlDecode(null), /LAP_ERR_ENCODING/);
  assert.equal(b64urlDecode("").length, 0);
});

test("malleated signature text is rejected end to end (request signature and passport JWS)", () => {
  const mc = v.micro_core;
  const sig2 = nonCanonical(mc.request_signature_b64url);
  assert.throws(() => verifyRequestSignature({
    passportJwt: mc.passport_jwt, sub: v.keys.agent.did, signatureBase: mc.rfc9421_signature_base,
    signatureB64url: sig2, requestBody: mc.request_body,
  }), /LAP_ERR_ENCODING/);
  const [h, p, s] = mc.passport_jwt.split(".");
  const jwt2 = `${h}.${p}.${nonCanonical(s)}`;
  assert.notEqual(sha256Hex(mc.passport_jwt), sha256Hex(jwt2), "the two forms hash differently: a hash-keyed denylist would miss the re-encoded token");
  assert.throws(() => verifyMicroCorePassport(jwt2, { expectedAud: "did:web:tools.example.com", now: NOW }), /LAP_ERR_ENCODING/);
  // and the canonical originals still verify
  assert.equal(verifyMicroCorePassport(mc.passport_jwt, { expectedAud: "did:web:tools.example.com", now: NOW }).sub, v.keys.agent.did);
});

// ---- v0.4 external hostile-review round (Gemini, 2026-09-08): malformed tokens are typed ----
test("F7/F8: malformed tokens yield typed LAP_ERR_SIG, never a raw language error", () => {
  assert.throws(() => decodeJws(null), /LAP_ERR_SIG: token must be a string/);        // F8
  assert.throws(() => decodeJws(42), /LAP_ERR_SIG: token must be a string/);
  assert.throws(() => decodeJws("eyJhbGciOiJFZERTQSJ9.bm90X2pzb24.sig"), /LAP_ERR_SIG: malformed JWS/); // F7
  // the passport verifier extracts iss BEFORE JWS verification; it used to leak a raw SyntaxError
  assert.throws(() => verifyMicroCorePassport("eyJhbGciOiJFZERTQSJ9.bm90X2pzb24.sig", { expectedAud: "did:web:x" }), /LAP_ERR_SIG/);
});
