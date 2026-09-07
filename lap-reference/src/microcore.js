// LIP-4 — Micro-Core server-side verification invariant (§2), transport-agnostic core.
import { timingSafeEqual } from "node:crypto";
import { publicKeyFromDid, verifyEd25519, b64urlDecode, sha256Hex, sha256B64url, normalizeUri, normalizeDid } from "./crypto-util.js";
import { decodeJws, verifyJws, checkTimeWindow } from "./jws.js";
import { pathSubsumes } from "./algebra.js";

const PROOF_CLASS_ORDER = ["self-asserted", "domain-validated", "org-validated", "gov-validated"];

// Step 1: verify the principal-signed passport JWT, audience, and time window.
// F4: `expectedAud` is MANDATORY — a missing audience is fail-open cross-server replay.
// F1: `allowedIssuers` / `minProofClass` let a server refuse self-asserted or unknown
// principals. A valid passport proves identity + envelope integrity; it is NOT by itself
// authority over a server-owned resource — the server MUST apply its own trust policy.
export function verifyMicroCorePassport(passportJwt, { expectedAud, allowedIssuers, minProofClass, now } = {}) {
  if (!expectedAud) throw new Error("LAP_ERR_AUDIENCE: expectedAud (this server's identity) is required");
  const iss = decodeJws(passportJwt).payload.iss; // F7: typed LAP_ERR_SIG on a malformed token, never a raw SyntaxError
  if (!iss) throw new Error("LAP_ERR_PASSPORT: iss missing");
  const { payload } = verifyJws(passportJwt, iss); // proves the presenter controls iss's key
  if (!payload.aud) throw new Error("LAP_ERR_AUDIENCE: aud missing");
  if (normalizeUri(payload.aud) !== normalizeUri(expectedAud)) throw new Error("LAP_ERR_AUDIENCE");
  checkTimeWindow(payload, now);
  if (!payload.lap?.envelope) throw new Error("LAP_ERR_PASSPORT_SIG: envelope missing");
  if (allowedIssuers && !allowedIssuers.map(normalizeDid).includes(normalizeDid(iss))) {
    throw new Error("LAP_ERR_ISSUER: issuer not in server allow-list");
  }
  if (minProofClass) {
    const have = PROOF_CLASS_ORDER.indexOf(payload.lap.proof_class);
    if (have < 0 || have < PROOF_CLASS_ORDER.indexOf(minProofClass)) {
      throw new Error("LAP_ERR_PROOF_CLASS: below required floor");
    }
  }
  return payload;
}

// Step 2: verify the AGENT's request signature. F2: the verification key is derived
// from the verified passport's `sub` (holder-of-key) — never from a caller-supplied
// DID, or a captured passport plus any attacker keypair would pass. F3: the mandatory
// RFC 9421 covered components must be present, and are compared to the server-observed
// method/target when those are supplied.
export function verifyRequestSignature({ passportJwt, sub, signatureBase, signatureB64url, requestBody, expectedMethod, expectedTarget }) {
  if (!sub) throw new Error("LAP_ERR_REQ_SIG: sub (verified passport subject) required");
  const key = publicKeyFromDid(sub);
  if (!verifyEd25519(key, Buffer.from(signatureBase), b64urlDecode(signatureB64url))) {
    throw new Error("LAP_ERR_REQ_SIG");
  }
  const lines = signatureBase.split("\n");
  const findLine = (prefix) => lines.find((l) => l.startsWith(prefix));
  for (const comp of ['"@method":', '"@target-uri":', '"content-digest":', '"lap-passport-hash":', '"@signature-params":']) {
    if (!findLine(comp)) throw new Error(`LAP_ERR_SIG_PARAMS: missing covered component ${comp}`);
  }
  const expectedDigest = `"content-digest": sha-256=:${sha256B64url(requestBody)}:`;
  if (!lines.includes(expectedDigest)) throw new Error("LAP_ERR_DIGEST");
  const expectedPassportLine = `"lap-passport-hash": sha256:${sha256Hex(passportJwt)}`;
  if (!lines.includes(expectedPassportLine)) throw new Error("LAP_ERR_DIGEST: passport hash");
  if (expectedMethod !== undefined && findLine('"@method":') !== `"@method": ${expectedMethod}`) {
    throw new Error("LAP_ERR_METHOD: signed method does not match transport");
  }
  if (expectedTarget !== undefined && findLine('"@target-uri":') !== `"@target-uri": ${expectedTarget}`) {
    throw new Error("LAP_ERR_TARGET: signed target does not match transport");
  }
  return true;
}

// Steps 3-4: the invoked operation must match the envelope (registered-verb equality,
// segment-wise resource match, per-transaction cap in the exact unit).
export function checkInvocation(envelope, { act, resource, amount, unit }) {
  if (envelope.act.includes("*")) throw new Error("LAP_ERR_ACT: wildcard not allowed in Micro-Core envelopes");
  if (!envelope.act.includes(act)) throw new Error("LAP_ERR_ACT");
  if (!pathSubsumes(envelope.res, resource)) throw new Error("LAP_ERR_RES");
  if (envelope.cap) {
    // F5 parity: a capped tool with an indeterminable amount MUST fail closed.
    if (amount === undefined || amount === null) throw new Error("LAP_ERR_CAP: capped operation requires an amount");
    if (unit !== envelope.cap.unit) throw new Error("LAP_ERR_CAP: unit");
    if (amount > envelope.cap.max_per_tx) throw new Error("LAP_ERR_CAP");
  }
  return true;
}

// Step 5 helper: idempotency cache keyed by (agent, key). NUL separator prevents
// key-splicing collisions. F6: `claim()` reserves atomically within one process,
// closing the check-then-await-then-store race. NOT distributed — production
// deployments MUST back this with a shared store (Redis SET NX / DB unique
// constraint) or a load balancer replays a signed key once per replica.
export function makeIdempotencyCache() {
  const seen = new Map();
  const k = (agentDid, idempotencyKey) => `${agentDid}\u0000${idempotencyKey}`;
  return {
    // F1 (v0.4.10): three-state atomic reservation. A binary null return could not tell a
    // FRESH reservation from an IN-FLIGHT one, so two concurrent mutating requests both saw
    // "free" and both executed. Callers proceed ONLY on {status:"reserved"}; {status:"in_flight"}
    // is a duplicate to reject (e.g. HTTP 409); {status:"completed"} returns the cached receipt.
    claim(agentDid, idempotencyKey) {
      const key = k(agentDid, idempotencyKey);
      if (!seen.has(key)) { seen.set(key, null); return { status: "reserved" }; }
      const receipt = seen.get(key);
      return receipt === null ? { status: "in_flight" } : { status: "completed", receipt };
    },
    complete(agentDid, idempotencyKey, receipt) {
      seen.set(k(agentDid, idempotencyKey), receipt);
    },
    check(agentDid, idempotencyKey) {
      return seen.get(k(agentDid, idempotencyKey));
    },
    store(agentDid, idempotencyKey, receipt) {
      seen.set(k(agentDid, idempotencyKey), receipt);
    },
  };
}

// LIP-4 §3: verify a tripartite receipt line against the tool server's key.
export function verifyReceipt({ receiptBase, receiptSignatureB64url, serverDid, requestBody, responseBody }) {
  const key = publicKeyFromDid(serverDid);
  if (!verifyEd25519(key, Buffer.from(receiptBase), b64urlDecode(receiptSignatureB64url))) {
    throw new Error("LAP_ERR_RECEIPT_SIG");
  }
  const [reqPart, respPart] = [receiptBase.split(":").slice(0, 2).join(":"), receiptBase.split(":").slice(2).join(":")];
  const tse = (a, b) => a.length === b.length && timingSafeEqual(Buffer.from(a), Buffer.from(b));
  if (requestBody !== undefined && !tse(reqPart, `sha256:${sha256Hex(requestBody)}`)) {
    throw new Error("LAP_ERR_RECEIPT: request hash mismatch");
  }
  if (responseBody !== undefined && !tse(respPart, `sha256:${sha256Hex(responseBody)}`)) {
    throw new Error("LAP_ERR_RECEIPT: response hash mismatch");
  }
  return true;
}
