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

// A cap-comparable amount: a non-negative safe integer (LIP-3 §4 interop bound, 2^53-1).
// `-500 <= cap` is true, NaN compares false both ways, and a string compares as a number,
// so anything else is refused BEFORE the comparison (cold-start test, 2026-10-17: both
// ports ran -500000 under a 1000 cap).
export function isExactAmount(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

// LIP-4 cap schema, checked before any comparison: max_per_tx a non-negative safe integer,
// unit a non-empty string. max_cumulative and window are informational in Micro-Core
// (LIP-4 §2 step 4), so they are not validated here; the full LIP-3 shape is capIsValid.
export function microCoreCapIsValid(cap) {
  return typeof cap === "object" && cap !== null && !Array.isArray(cap)
    && isExactAmount(cap.max_per_tx) && typeof cap.unit === "string" && cap.unit !== "";
}

// Steps 4-5: the invoked operation must match the envelope (registered-verb equality,
// segment-wise resource match, per-transaction cap in the exact unit). `enforceMagnitude: false`
// is the disclosure check of a replay (LIP-4 §2 step 3, 0.4.14): action, resource, cap schema, the
// amount's presence and type and the unit are still checked against the envelope presented now,
// but `amount <= max_per_tx` is not compared, because a replay spends nothing.
export function checkInvocation(envelope, { act, resource, amount, unit, enforceMagnitude = true }) {
  if (envelope.act.includes("*")) throw new Error("LAP_ERR_ACT: wildcard not allowed in Micro-Core envelopes");
  if (!envelope.act.includes(act)) throw new Error("LAP_ERR_ACT");
  if (!pathSubsumes(envelope.res, resource)) throw new Error("LAP_ERR_RES");
  if (envelope.cap !== undefined && envelope.cap !== null) { // a present-but-empty cap is malformed, not "no cap"
    // Schema before arithmetic (LIP-3 §4 F8): a malformed cap never reaches a comparison.
    if (!microCoreCapIsValid(envelope.cap)) throw new Error("LAP_ERR_CAP: malformed cap");
    // F5 parity: a capped tool with an indeterminable amount MUST fail closed.
    if (amount === undefined || amount === null) throw new Error("LAP_ERR_CAP: capped operation requires an amount");
    if (!isExactAmount(amount)) throw new Error("LAP_ERR_CAP: amount must be a non-negative exact integer");
    if (unit !== envelope.cap.unit) throw new Error("LAP_ERR_CAP: unit");
    if (enforceMagnitude && amount > envelope.cap.max_per_tx) throw new Error("LAP_ERR_CAP");
  }
  return true;
}

// Step 3 (0.4.14): the identity of a request for idempotency purposes: the signed `@method`,
// `@target-uri` and `content-digest` lines of a VERIFIED signature base. Not the passport hash (a
// retry under a replaced passport is the same request), not the key itself.
export function requestIdentity(signatureBase) {
  const lines = signatureBase.split("\n");
  const find = (prefix) => lines.find((line) => line.startsWith(prefix));
  const method = find('"@method":'), target = find('"@target-uri":'), digest = find('"content-digest":');
  if (method === undefined || target === undefined || digest === undefined) {
    throw new Error("LAP_ERR_SIG_PARAMS: request identity needs the @method, @target-uri and content-digest lines");
  }
  return [method, target, digest];
}

// The scope an idempotency claim lives in: [tenant, sub] from a VERIFIED passport payload. The
// tenant is the server's F1 mapping of the verified issuer (`tenantOf(payload)`), by default the
// normalised `iss` itself, so two principals never share a claim even through one agent key. A
// `tenantOf` that returns nothing is an unknown principal (LAP_ERR_ISSUER). Never the passport
// hash, the envelope or the audience: a claim survives authority replacement.
export function claimScope(passportPayload, tenantOf) {
  const sub = passportPayload.sub;
  if (!sub) throw new Error("LAP_ERR_PASSPORT: sub missing");
  const tenant = tenantOf ? tenantOf(passportPayload) : normalizeDid(passportPayload.iss ?? "");
  if (typeof tenant !== "string" || tenant === "") throw new Error("LAP_ERR_ISSUER: no tenant for this issuer");
  return [tenant, sub];
}

// Step 6 helper: idempotency cache keyed by scope [tenant, agent] and key. NUL separators prevent
// key-splicing collisions. F6: `claim()` reserves atomically within one process, closing the
// check-then-await-then-store race. NOT distributed — production deployments MUST back this with a
// shared store (a unique constraint on (tenant, agent, key) whose row also holds the identity, or
// Redis SET NX with a value) or a load balancer replays a signed key once per replica.
// Request identity (0.4.14): a reservation records the identity of the request it was made for
// (`requestIdentity`); a later request with the same key and a different identity is `key_reuse`
// in every state, never a replay and never a second execution. `lookup()` reads without
// reserving, so a server can recognise an existing claim before it consults the envelope (LIP-4
// §2 step 3) and refuse without creating anything.
// Recovery rule (LIP-4, 2026-10-21; raised on A2A #2323): the reservation is written before the
// external effect, the completion after it. A claim whose executor died between the two is
// INDETERMINATE: the effect may or may not have happened. It is refused on retry, never
// re-executed, never released by time alone, and resolves only by reconciliation against the
// effect's system of record: complete() with the reconciled result if the effect happened,
// release() if it verifiably did not. This in-process map cannot observe its own death; a
// durable backend detects dead executors (for example through a lease) and marks their claims.
// Retention is a published server policy, independent of passport lifetime.
export function makeIdempotencyCache() {
  const seen = new Map();
  const k = (scope, idempotencyKey) => {
    const [tenant, sub] = typeof scope === "string" ? ["", scope] : [scope[0] ?? "", scope[1]];
    return `${tenant}\u0000${sub}\u0000${idempotencyKey}`;
  };
  const sameIdentity = (a, b) => a.length === b.length && a.every((line, i) => line === b[i]);
  const status = (entry, identity) => {
    if (identity && entry.identity && !sameIdentity([...identity], entry.identity)) return { status: "key_reuse" };
    if (entry.state === "reserved") return { status: "in_flight" };
    if (entry.state === "indeterminate") return { status: "indeterminate" };
    return { status: "completed", receipt: entry.result };
  };
  return {
    // Recognise without reserving: absent | key_reuse | in_flight | indeterminate | completed.
    lookup(scope, idempotencyKey, identity) {
      const entry = seen.get(k(scope, idempotencyKey));
      return entry === undefined ? { status: "absent" } : status(entry, identity);
    },
    // F1 (v0.4.10): atomic reservation. A binary null return could not tell a FRESH reservation
    // from an IN-FLIGHT one, so two concurrent mutating requests both saw "free" and both
    // executed. Callers proceed ONLY on {status:"reserved"}; {status:"in_flight"} is a duplicate
    // to reject (HTTP 409); {status:"indeterminate"} is a duplicate to reject until
    // reconciliation; {status:"completed"} returns the stored result; {status:"key_reuse"}
    // (0.4.14) is the same key for a different request, refused in every state (HTTP 422).
    // `meta` (the executing passport hash, the reservation time) stays with the reservation.
    claim(scope, idempotencyKey, identity, meta) {
      const key = k(scope, idempotencyKey);
      const entry = seen.get(key);
      if (entry === undefined) {
        seen.set(key, { state: "reserved", identity: identity ? [...identity] : null, result: null, meta: { ...(meta ?? {}) } });
        return { status: "reserved" };
      }
      return status(entry, identity);
    },
    // Store the result for a reserved claim, or for an indeterminate one once reconciliation
    // found that the effect happened.
    complete(scope, idempotencyKey, receipt) {
      const key = k(scope, idempotencyKey);
      const entry = seen.get(key) ?? { state: "reserved", identity: null, result: null, meta: {} };
      entry.state = "completed";
      entry.result = receipt;
      seen.set(key, entry);
    },
    // The executor holding this in-flight claim died (or threw) before storing its completion.
    markIndeterminate(scope, idempotencyKey) {
      const entry = seen.get(k(scope, idempotencyKey));
      if (entry === undefined || entry.state !== "reserved") throw new Error("LAP_ERR_REPLAY: only an in-flight claim can become indeterminate");
      entry.state = "indeterminate";
    },
    // Reconciliation found that the effect did not happen: the next request with this key
    // executes fresh. An in-flight claim cannot be released; its executor may still be running.
    release(scope, idempotencyKey) {
      const key = k(scope, idempotencyKey);
      const entry = seen.get(key);
      if (entry === undefined || entry.state !== "indeterminate") throw new Error("LAP_ERR_REPLAY: only an indeterminate claim can be released, after reconciliation");
      seen.delete(key);
    },
    // The executor that holds this reservation reports that the effect never began: forget it.
    // Only the reserving executor may say so, and only for an in-flight claim.
    abandon(scope, idempotencyKey) {
      const key = k(scope, idempotencyKey);
      const entry = seen.get(key);
      if (entry === undefined || entry.state !== "reserved") throw new Error("LAP_ERR_REPLAY: only the in-flight claim of a tool that reported no effect can be abandoned");
      seen.delete(key);
    },
    // What the reservation recorded (identity, executing passport hash, time), for reconciliation.
    meta(scope, idempotencyKey) {
      const entry = seen.get(k(scope, idempotencyKey));
      return entry === undefined ? null : { state: entry.state, identity: entry.identity, ...entry.meta };
    },
    // Legacy read (pre-0.4.10): the stored result of a completed claim; undefined for no claim,
    // null for one that is in flight or indeterminate (no result yet).
    check(scope, idempotencyKey) {
      const entry = seen.get(k(scope, idempotencyKey));
      if (entry === undefined) return undefined;
      return entry.state === "completed" ? entry.result : null;
    },
    // Legacy write (pre-0.4.10): complete without a prior reservation. Prefer claim() then complete().
    store(scope, idempotencyKey, receipt, identity) {
      this.complete(scope, idempotencyKey, receipt);
      if (identity) seen.get(k(scope, idempotencyKey)).identity = [...identity];
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
