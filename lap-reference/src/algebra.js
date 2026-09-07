// LIP-3 v0.3 — LAP-Core Scope Algebra reference checker.
// Sound-but-incomplete by design (greedy first-match in canonical order; see LIP-3 §6).
import { jcs, normalizeUri, normalizeDid } from "./crypto-util.js";

const normId = (s) => (/^did:/i.test(s) ? normalizeDid(s) : normalizeUri(s));

// Seed Action Registry DAG (LIP-3 §2): only registry-declared edges subsume.
// String prefixing confers NOTHING: e.g. compute:exec:unconfined is deliberately absent.
export const ACTION_REGISTRY_V0 = {
  "data:read": ["data:read:public"],
  "data:write": [],
  "finance:pay": ["finance:pay:escrow", "finance:pay:release"],
  "compute:exec": ["compute:exec:sandboxed"],
  "comm:send": [],
  "identity:present": [],
  "governance:revoke": [],
};

const WINDOW_SECONDS = { utc_hour: 3600, utc_day: 86400 };
const VALID_WINDOWS = new Set(["tx", "utc_hour", "utc_day", "epoch_total"]);
const MAX_DEPTH = 16;

// LIP-3 §2 (v0.4): closed resource-scheme set. did/urn are identifiers (used in `cp`), not
// resources; `git` is reserved for the experimental lap-git commit binding. Every other scheme
// (http, file, gopher, ...) is refused — the algebra never default-allows an unknown scheme.
const RES_SCHEMES = new Set(["mcp", "a2a", "ap2", "https", "git"]);

const isPlainObject = (x) => x !== null && typeof x === "object" && !Array.isArray(x);
const isStringList = (x) => Array.isArray(x) && x.every((s) => typeof s === "string");
const show = (x) => { try { return jcs(x); } catch { return JSON.stringify(x) ?? String(x); } };

export function isRegisteredVerb(act, registry = ACTION_REGISTRY_V0) {
  if (act === "*") return true;
  if (typeof act !== "string") return false;
  if (Object.prototype.hasOwnProperty.call(registry, act)) return true;
  return Object.values(registry).some((children) => children.includes(act));
}

// LIP-3 §2. Handles both a bare verb string and a verb array (envelope `act[]`),
// in exact parity with the Python port. Uses value-equality throughout — an array
// argument must never be compared by reference (round-3 audit F-extra).
export function dagSubsumes(parentAct, childAct, registry = ACTION_REGISTRY_V0) {
  const pList = Array.isArray(parentAct) ? parentAct : [parentAct];
  const cList = Array.isArray(childAct) ? childAct : [childAct];
  if (![...pList, ...cList].every((a) => isRegisteredVerb(a, registry))) return false;
  if (pList.includes("*")) return true;
  const expand = (verb) => {
    const out = new Set([verb]);
    for (const ch of registry[verb] ?? []) for (const e of expand(ch)) out.add(e);
    return out;
  };
  const allowed = new Set();
  for (const p of pList) for (const e of expand(p)) allowed.add(e);
  return cList.every((c) => allowed.has(c));
}

function parseRes(res) {
  if (typeof res !== "string" || res.length === 0) throw new Error("LAP_ERR_RES: resource must be a non-empty string");
  const norm = normalizeUri(res);
  // Closed syntax (v0.3): the algebra defines scheme, authority and path — nothing else.
  // A query, a fragment or an empty interior segment is an unknown construct; never
  // default-allow an unknown construct (LIP-3 §2).
  if (/[?#]/.test(norm)) throw new Error("LAP_ERR_RES: query and fragment are not allowed in resource patterns");
  const m = norm.match(/^([a-z0-9+.-]+):\/\/([^/]+)(\/.*)?$/);
  if (!m) throw new Error(`LAP_ERR_RES: invalid resource URI: ${res}`);
  const [, scheme, host, path = ""] = m;
  if (!RES_SCHEMES.has(scheme)) throw new Error(`LAP_ERR_RES: scheme not in the closed set: ${scheme}`); // F3
  if (path.includes("//")) throw new Error("LAP_ERR_RES: empty path segment");
  // F2/F10 (v0.4.10): a resource pattern is decoded, canonical text. Percent-encoding and
  // backslashes are exactly the forms a downstream proxy resolves AFTER authorization
  // (`/safe/..\\admin`, `/safe/%252e%252e/admin`), so a pattern MUST contain neither, nor any
  // control character; with the dot-segment check below this closes the traversal class.
  if (/[\\%]/.test(path)) throw new Error("LAP_ERR_RES: backslashes and percent-encoding are not allowed in resource patterns");
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u001f\u007f]/.test(path)) throw new Error("LAP_ERR_RES: control characters are not allowed in resource patterns");
  const segments = path.split("/").filter((s) => s.length > 0);
  if (segments.includes(".") || segments.includes("..")) {
    throw new Error("LAP_ERR_RES: dot-segments not allowed");
  }
  let wildcard = null;
  if (segments.at(-1) === "**") { wildcard = "**"; segments.pop(); }
  else if (segments.at(-1) === "*") { wildcard = "*"; segments.pop(); }
  if (segments.includes("*") || segments.includes("**")) {
    throw new Error("LAP_ERR_RES: wildcards are terminal-only");
  }
  return { scheme, host, segments, wildcard };
}

export function pathSubsumes(parentRes, childRes) {
  const p = parseRes(parentRes);
  const c = parseRes(childRes);
  if (p.scheme !== c.scheme || p.host !== c.host) return false;
  const prefixMatches = p.segments.every((seg, i) => c.segments[i] === seg);
  if (p.wildcard === "**") {
    return c.segments.length >= p.segments.length && prefixMatches;
  }
  if (p.wildcard === "*") {
    if (c.wildcard === "**") return false;                                          // never widen
    if (c.wildcard === "*") return c.segments.length === p.segments.length && prefixMatches; // the same set (v0.3: reflexive)
    return c.segments.length === p.segments.length + 1 && prefixMatches;
  }
  return c.wildcard === null && c.segments.length === p.segments.length && prefixMatches;
}

const UNIVERSE = Symbol("universe");

export function cpIsValid(cp) {
  if (cp === undefined || cp === null) return true;
  if (!isPlainObject(cp)) return false;
  return (cp.allow === undefined || isStringList(cp.allow)) && (cp.deny === undefined || isStringList(cp.deny));
}

function effectiveSet(cp = {}) {
  const allow = (cp.allow ?? []).map(normId);
  const deny = new Set((cp.deny ?? []).map(normId));
  return { base: allow.length > 0 ? new Set(allow) : UNIVERSE, deny };
}

export function counterpartySubsumes(parentCp, childCp) {
  if (!cpIsValid(parentCp) || !cpIsValid(childCp)) return false;
  const p = effectiveSet(parentCp ?? {});
  const c = effectiveSet(childCp ?? {});
  for (const d of p.deny) if (!c.deny.has(d)) return false;
  if (p.base === UNIVERSE) return true;
  if (c.base === UNIVERSE) return false;
  for (const member of c.base) {
    if (c.deny.has(member)) continue;
    if (!p.base.has(member) || p.deny.has(member)) return false;
  }
  return true;
}

// F8: caps must be non-negative safe integers with max_per_tx <= max_cumulative,
// a real unit, and a known window. Returns false (never throws) so direct callers
// of capSubsumes/scopeSubsumes fail closed; verifyEnvelopeAttenuation throws early.
export function capIsValid(cap) {
  if (cap === undefined || cap === null) return true;
  if (!isPlainObject(cap)) return false;
  for (const f of ["max_per_tx", "max_cumulative"]) {
    const v = cap[f];
    if (!Number.isSafeInteger(v) || v < 0) return false;
  }
  if (cap.max_per_tx > cap.max_cumulative) return false;
  if (typeof cap.unit !== "string" || cap.unit.length === 0) return false;
  if (!VALID_WINDOWS.has(cap.window)) return false;
  return true;
}

// v0.3: window scaling is exact-integer arithmetic. Double arithmetic (value × 3600 / 86400)
// rounds above ~1e11 and diverged from the Python port by one unit in ~5% of large-value
// cases — found by the differential fuzzer. Inputs are safe integers (F8), so BigInt is exact.
const scaleFloor = (value, num, den) => (BigInt(value) * BigInt(num)) / BigInt(den);

// LIP-3 §4: two-dimensional cap rule. Fails closed on any invalid cap (F8).
export function capSubsumes(parentCap, childCap) {
  if (parentCap === undefined || parentCap === null) return true;
  if (childCap === undefined || childCap === null) return false;
  if (!capIsValid(parentCap) || !capIsValid(childCap)) return false;
  if (childCap.unit !== parentCap.unit) return false;
  if (childCap.max_per_tx > parentCap.max_per_tx) return false;
  const pw = parentCap.window;
  const cw = childCap.window;
  if (pw === "tx") {
    // tightened (audit F7): a tx parent admits only a tx child — a differently-based
    // child window would rate-expand the parent's per-transaction budget.
    return cw === "tx" && childCap.max_cumulative <= parentCap.max_cumulative;
  }
  if (pw === "epoch_total") {
    return cw === "epoch_total" && childCap.max_cumulative <= parentCap.max_cumulative;
  }
  if (cw === "tx" || cw === "epoch_total") return false;
  const pSec = WINDOW_SECONDS[pw];
  const cSec = WINDOW_SECONDS[cw];
  if (!pSec || !cSec || cSec > pSec || pSec % cSec !== 0) return false;
  return BigInt(childCap.max_cumulative) <= scaleFloor(parentCap.max_cumulative, cSec, pSec);
}

// LIP-3 §5 (v0.3): shape validation precedes every comparison. Returns false (never throws)
// so a direct caller fails closed; verifyEnvelopeAttenuation throws LAP_ERR_SCOPE_SCHEMA.
// Found by the fuzzer: malformed scopes used to surface TypeErrors from deep inside the
// comparison, and a missing `act` compared as "grants nothing ⊆ grants nothing" in one port.
export function scopeIsValid(scope) {
  if (!isPlainObject(scope)) return false;
  if (typeof scope.v !== "string") return false;
  if (!(typeof scope.act === "string" || isStringList(scope.act))) return false;
  if (typeof scope.res !== "string") return false;
  if (!cpIsValid(scope.cp) || !capIsValid(scope.cap)) return false;
  for (const f of ["depth", "decay_max_sec"]) {
    const v = scope[f];
    if (v !== undefined && !(Number.isSafeInteger(v) && v >= 0)) return false;
  }
  if (scope.depth !== undefined && scope.depth > MAX_DEPTH) return false;
  return true;
}

// F9: caps are a conjunct of the subset relation — a direct caller (a policy engine)
// must never get a cap-blind "true". scopeSubsumes now includes capSubsumes.
export function scopeSubsumes(parent, child, registry = ACTION_REGISTRY_V0) {
  if (!scopeIsValid(parent) || !scopeIsValid(child)) return false;
  return (
    parent.v === "lap-scope-v0" &&
    child.v === "lap-scope-v0" &&
    dagSubsumes(parent.act, child.act, registry) &&
    pathSubsumes(parent.res, child.res) &&
    counterpartySubsumes(parent.cp, child.cp) &&
    capSubsumes(parent.cap, child.cap) &&
    (parent.depth === undefined || (child.depth !== undefined && child.depth <= parent.depth - 1)) &&
    (parent.decay_max_sec === undefined || (child.decay_max_sec !== undefined && child.decay_max_sec <= parent.decay_max_sec))
  );
}

// F7: debit the child's allocation expressed in the PARENT window's units, so a
// smaller-window child cannot multiply the parent's budget across sub-buckets.
// A utc_hour child of a utc_day parent debits max_cumulative × 24, not × 1. (BigInt: exact.)
function windowDebit(parentCap, childCap) {
  const pSec = WINDOW_SECONDS[parentCap.window];
  const cSec = WINDOW_SECONDS[childCap.window];
  if (pSec && cSec) return scaleFloor(childCap.max_cumulative, pSec, cSec);
  return BigInt(childCap.max_cumulative); // same-basis (tx/epoch_total): no scaling
}

// LIP-3 §6: envelope-level verification with budget conservation.
// Deterministic: children and parents evaluated in canonical (JCS) sorted order.
export function verifyEnvelopeAttenuation(parentScopes, childScopes, registry = ACTION_REGISTRY_V0) {
  if (!Array.isArray(parentScopes) || !Array.isArray(childScopes)) {
    throw new Error("LAP_ERR_SCOPE_SCHEMA: scope sets must be arrays");
  }
  for (const s of [...parentScopes, ...childScopes]) {
    if (!capIsValid(isPlainObject(s) ? s.cap : undefined)) throw new Error(`LAP_ERR_CAP_SCHEMA: invalid cap in ${show(s)}`);
    if (!scopeIsValid(s)) throw new Error(`LAP_ERR_SCOPE_SCHEMA: malformed scope ${show(s)}`);
  }
  const canonical = (arr) => [...arr].sort((a, b) => (jcs(a) < jcs(b) ? -1 : 1));
  const parents = canonical(parentScopes);
  const children = canonical(childScopes);
  const remaining = parents.map((p) => (p.cap ? BigInt(p.cap.max_cumulative) : null));
  for (const c of children) {
    let matched = false;
    for (let i = 0; i < parents.length; i++) {
      const p = parents[i];
      if (!scopeSubsumes(p, c, registry)) continue;
      if (p.cap) {
        const debit = windowDebit(p.cap, c.cap);
        if (debit > remaining[i]) continue;
        remaining[i] -= debit;
      }
      matched = true;
      break;
    }
    if (!matched) return { ok: false, rejected: c };
  }
  return { ok: true };
}
