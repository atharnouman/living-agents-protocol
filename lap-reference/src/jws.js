import { sign as cryptoSign } from "node:crypto";
import { b64urlDecode, b64urlEncode, jcs, normalizeDid, publicKeyFromDid, verifyEd25519 } from "./crypto-util.js";

// Produce a compact EdDSA JWS over the JCS canonical form of `payload`.
export function signJws(payload, privateKey, kid, typ = "lap-passport+jwt") {
  const header = { alg: "EdDSA", kid, typ };
  const input = b64urlEncode(Buffer.from(jcs(header))) + "." + b64urlEncode(Buffer.from(jcs(payload)));
  const sig = cryptoSign(null, Buffer.from(input), privateKey);
  return input + "." + b64urlEncode(sig);
}

export const SKEW_SECONDS = 60; // LIP-1 §2 default clock-skew tolerance

function parseJwsJson(b64, what) {
  // F7: a valid-base64url-but-invalid-JSON segment must be a typed protocol error, not a
  // raw language SyntaxError leaking out of a verifier.
  try { return JSON.parse(b64urlDecode(b64).toString()); }
  catch (e) { throw new Error(`LAP_ERR_SIG: malformed JWS ${what} (${e.message})`); }
}

export function decodeJws(token) {
  if (typeof token !== "string") throw new Error("LAP_ERR_SIG: token must be a string"); // F8
  const parts = token.split(".");
  if (parts.length !== 3) throw new Error("LAP_ERR_SIG: not a compact JWS");
  const [h, p, s] = parts;
  return {
    header: parseJwsJson(h, "header"),
    payload: parseJwsJson(p, "payload"),
    signature: b64urlDecode(s),
    signingInput: Buffer.from(h + "." + p),
  };
}

// Verify a compact EdDSA JWS whose signer is identified by `signerDid` (did:key).
export function verifyJws(token, signerDid) {
  const { header, payload, signature, signingInput } = decodeJws(token);
  if (header.alg !== "EdDSA") throw new Error(`LAP_ERR_SIG: alg ${header.alg}`);
  const key = publicKeyFromDid(signerDid);
  if (!verifyEd25519(key, signingInput, signature)) throw new Error("LAP_ERR_SIG: signature invalid");
  return { header, payload };
}

export function checkTimeWindow(payload, now = Math.floor(Date.now() / 1000)) {
  if (typeof payload.iat !== "number") throw new Error("LAP_ERR_EXPIRED: iat missing");
  if (typeof payload.exp !== "number") throw new Error("LAP_ERR_EXPIRED: exp missing");
  if (now < payload.iat - SKEW_SECONDS || now > payload.exp + SKEW_SECONDS) {
    throw new Error("LAP_ERR_EXPIRED");
  }
}

// LIP-1 §6 passport verification (the vector-testable subset: steps 1-5 of nine;
// proof-class credentials, revocation endpoints, and registration proofs need
// network context and live in the higher-level verifier).
export function verifyPassport(token, { now } = {}) {
  const { header, payload } = decodeJws(token);
  if (payload.v !== "lip1-v0") throw new Error("LAP_ERR_VERSION");
  if (header.alg !== "EdDSA") throw new Error(`LAP_ERR_SIG: alg ${header.alg}`);
  const principalDid = payload.principal?.id ? normalizeDid(payload.principal.id) : null;
  const agentDid = payload.id ? normalizeDid(payload.id) : null;
  if (!principalDid) throw new Error("LAP_ERR_SELF_OWNED: principal missing");
  if (principalDid === agentDid) throw new Error("LAP_ERR_SELF_OWNED");
  verifyJws(token, principalDid);
  checkTimeWindow(payload, now);
  return payload;
}
