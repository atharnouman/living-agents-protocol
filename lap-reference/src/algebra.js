// LIP-3 v0.2 — LAP-Core Scope Algebra reference checker.
// Sound-but-incomplete by design (greedy first-match in canonical order; see LIP-3 §6).
import { jcs, normalizeUri, normalizeDid } from "./crypto-util.js";

const normId = (s) => (s.startsWith("did:") ? normalizeDid(s) : normalizeUri(s));

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

export function isRegisteredVerb(act, registry = ACTION_REGISTRY_V0) {
  if (act === "*") return true;
  if (act in registry) return true;
  return Object.values(registry).some((children) => children.includes(act));
}

export function dagSubsumes(parentAct, childAct, registry = ACTION_REGISTRY_V0) {
  if (!isRegisteredVerb(parentAct, registry) || !isRegisteredVerb(childAct, registry)) return false;
  if (parentAct === "*") return true;
  if (parentAct === childAct) return true;
  const direct = registry[parentAct] ?? [];
  if (direct.includes(childAct)) return true;
  return direct.some((mid) => dagSubsumes(mid, childAct, registry));
}

function parseRes(res) {
  const norm = normalizeUri(res);
  const m = norm.match(/^([a-z0-9+.-]+):\/\/([^/]+)(\/.*)?$/);
  if (!m) throw new Error(`invalid resource URI: ${res}`);
  const [, scheme, host, path = ""] = m;
  const segments = path.split("/").filter((s) => s.length > 0);
  let wildcard = null;
  if (segments.at(-1) === "**") { wildcard = "**"; segments.pop(); }
  else if (segments.at(-1) === "*") { wildcard = "*"; segments.pop(); }
  if (segments.includes("*") || segments.includes("**")) {
    throw new Error("wildcards are terminal-only");
  }
  return { scheme, host, segments, wildcard };
}

export function pathSubsumes(parentRes, childRes) {
  const p = parseRes(parentRes);
  const c = parseRes(childRes);
  if (p.scheme !== c.scheme || p.host !== c.host) return false;
  const prefixMatches = p.segments.every((seg, i) => c.segments[i] === seg);
  if (p.wildcard === "**") {
    // child must live at or below parent's prefix, segment-wise
    return c.segments.length >= p.segments.length && prefixMatches;
  }
  if (p.wildcard === "*") {
    // exactly one extra segment, and the child must not widen with its own wildcard
    return c.segments.length === p.segments.length + 1 && prefixMatches && c.wildcard === null;
  }
  // exact resource: child must be identical and add no wildcard
  return c.wildcard === null && c.segments.length === p.segments.length && prefixMatches;
}

const UNIVERSE = Symbol("universe");

function effectiveSet(cp = {}) {
  const allow = (cp.allow ?? []).map(normId);
  const deny = new Set((cp.deny ?? []).map(normId));
  return { base: allow.length > 0 ? new Set(allow) : UNIVERSE, deny };
}

export function counterpartySubsumes(parentCp, childCp) {
  const p = effectiveSet(parentCp);
  const c = effectiveSet(childCp);
  // p.deny ⊆ c.deny (a child may never un-deny)
  for (const d of p.deny) if (!c.deny.has(d)) return false;
  if (p.base === UNIVERSE) return true; // E(c) ⊆ Universe\p.deny given deny inheritance above
  if (c.base === UNIVERSE) return false; // universe-sized child can't fit a finite parent
  for (const member of c.base) {
    if (c.deny.has(member)) continue; // not effectively included
    if (!p.base.has(member) || p.deny.has(member)) return false;
  }
  return true;
}

// LIP-3 §4: two-dimensional cap rule (replaces the withdrawn v0.1 window lattice).
export function capSubsumes(parentCap, childCap) {
  if (!parentCap) return true; // unconstrained parent: constraining child is fine
  if (!childCap) return false;
  if (childCap.unit !== parentCap.unit) return false;
  if (childCap.max_per_tx > parentCap.max_per_tx) return false;
  const pw = parentCap.window;
  const cw = childCap.window;
  if (pw === "tx") {
    // parent carries no time-rate constraint; any child window only constrains further
    return childCap.max_cumulative <= parentCap.max_cumulative;
  }
  if (pw === "epoch_total") {
    // conservative v0: epoch_total attenuates only to epoch_total (LIP-3 §10 open item)
    return cw === "epoch_total" && childCap.max_cumulative <= parentCap.max_cumulative;
  }
  // timed parent: child MUST be timed; equal or integer subdivision; proportional cumulative
  if (cw === "tx" || cw === "epoch_total") return false;
  const pSec = WINDOW_SECONDS[pw];
  const cSec = WINDOW_SECONDS[cw];
  if (!pSec || !cSec || cSec > pSec || pSec % cSec !== 0) return false;
  // integer floor arithmetic: identical verdicts across language ports (no float jitter)
  return childCap.max_cumulative <= Math.floor((parentCap.max_cumulative * cSec) / pSec);
}

export function scopeSubsumes(parent, child, registry = ACTION_REGISTRY_V0) {
  return (
    parent.v === "lap-scope-v0" &&
    child.v === "lap-scope-v0" &&
    dagSubsumes(parent.act, child.act, registry) &&
    pathSubsumes(parent.res, child.res) &&
    counterpartySubsumes(parent.cp, child.cp) &&
    (parent.depth === undefined || (child.depth !== undefined && child.depth <= parent.depth - 1)) &&
    (parent.decay_max_sec === undefined || (child.decay_max_sec !== undefined && child.decay_max_sec <= parent.decay_max_sec))
  );
}

// LIP-3 §6: envelope-level verification with budget conservation.
// Deterministic: children and parents evaluated in canonical (JCS) sorted order.
export function verifyEnvelopeAttenuation(parentScopes, childScopes, registry = ACTION_REGISTRY_V0) {
  const canonical = (arr) => [...arr].sort((a, b) => (jcs(a) < jcs(b) ? -1 : 1));
  const parents = canonical(parentScopes);
  const children = canonical(childScopes);
  const remaining = parents.map((p) => p.cap?.max_cumulative ?? Infinity);
  for (const c of children) {
    let matched = false;
    for (let i = 0; i < parents.length; i++) {
      const p = parents[i];
      if (!scopeSubsumes(p, c, registry)) continue;
      if (p.cap && !capSubsumes(p.cap, c.cap)) continue;
      if (p.cap) {
        if ((c.cap?.max_cumulative ?? Infinity) > remaining[i]) continue;
        remaining[i] -= c.cap.max_cumulative;
      }
      matched = true;
      break;
    }
    if (!matched) return { ok: false, rejected: c };
  }
  return { ok: true };
}
