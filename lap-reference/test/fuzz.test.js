// Property-based fuzzing of the LIP-3 Scope Algebra (self-contained: no fast-check, no deps).
//
// A deterministic xorshift32 generator — written identically in lap-python/tests/test_fuzz.py —
// drives the SAME random scopes through both ports. A committed digest of the decisions locks
// cross-port parity. Properties checked here:
//   1. reflexivity (a scope subsumes an identical scope one delegation hop down)
//   2. transitivity along attenuation chains, with a non-vacuous accept rate
//   3. instantiation (a pattern subsumes every concrete path it generates)
//   4. no widening (wildcard escalation and origin changes are always refused)
//   5. the two-dimensional cap rule agrees with an exact-integer oracle (BigInt)
//   6. budget conservation agrees with an exact-integer oracle
//   7. typed errors only: malformed input yields false / {ok:false} / LAP_ERR_*, never a TypeError
//   8. cross-port parity digest
//
//   LAP_FUZZ_SEED=123 node --test test/fuzz.test.js   # explore another seed (parity check skipped)
//   LAP_FUZZ_WRITE=1  node --test test/fuzz.test.js   # regenerate the parity digest after an
//                                                     # intentional algebra change, then run pytest
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  ACTION_REGISTRY_V0, capIsValid, capSubsumes, pathSubsumes, scopeSubsumes, verifyEnvelopeAttenuation,
} from "../src/algebra.js";

const isPlainObj = (x) => x !== null && typeof x === "object" && !Array.isArray(x);
const strList = (x) => Array.isArray(x) && x.every((s) => typeof s === "string");
const here = dirname(fileURLToPath(import.meta.url));
const DIGEST_PATH = join(here, "..", "..", "output", "lip", "test-vectors", "algebra-fuzz-digest.json");
const SEED = Number(process.env.LAP_FUZZ_SEED ?? 20260906);
const EXPLORING = process.env.LAP_FUZZ_SEED !== undefined;

// ---------- deterministic generator (mirror of the Python one; keep the call order identical) ----------
function xorshift32(seed) {
  let x = (seed >>> 0) || 1;
  return () => {
    x = (x ^ (x << 13)) >>> 0;
    x = (x ^ (x >>> 17)) >>> 0;
    x = (x ^ (x << 5)) >>> 0;
    return x / 4294967296;
  };
}

const NUMS_VALID = [0, 1, 5, 100, 4200, 5000, 6000, 10000, 123456, 99999999, 123456789012345, 342563965713392, 8707531655995247, 9007199254740991];
const ACTS_VALID = ["data:read", "data:read:public", "data:write", "finance:pay", "finance:pay:escrow", "finance:pay:release", "compute:exec", "compute:exec:sandboxed", "comm:send", "*"];
const V = {
  schemes: ["mcp", "https", "a2a", "MCP"],
  hosts: ["tools.example.com", "Tools.Example.com", "api.example.org", "[::1]", "[2001:db8::1]", "127.0.0.1", "tools.example.com:4107"],
  segs: ["a", "b", "billing", "pay", "admin", "keys", "x", "finance", "finance_admin", "A"],
  badSegs: [".", "..", "%2e", "%2F", "a?x=1", "a#f", "", "*", "**"],
  wildcards: [null, "*", "**"],
  actsValid: ACTS_VALID,
  actsAny: [...ACTS_VALID, "compute:exec:unconfined", "finance", "Finance:Pay", "", 42],
  units: ["USD", "EUR"],
  windowsValid: ["tx", "utc_hour", "utc_day", "epoch_total"],
  windowsAny: ["tx", "utc_hour", "utc_day", "epoch_total", "rolling_day", "", null],
  numsValid: NUMS_VALID,
  numsAny: [...NUMS_VALID, -1, 1.5, "100", 9007199254740992, true, null],
  dids: ["did:key:z6MkA", "did:key:z6MkB", "did:web:vendora.com", "DID:WEB:vendora.com", "did:web:Vendora.com", "did:web:other.example"],
  depths: [0, 1, 2, 5, 16],
  decays: [60, 300, 3600],
};

function makeGen(rng, valid) {
  const rint = (n) => Math.floor(rng() * n);
  const pick = (arr) => arr[rint(arr.length)];
  const res = (clean) => {
    const scheme = pick(V.schemes), host = pick(V.hosts), n = rint(4), segs = [];
    for (let i = 0; i < n; i++) { const r = rng(); segs.push(!clean && r < 0.06 ? pick(V.badSegs) : pick(V.segs)); }
    const wc = pick(V.wildcards);
    return `${scheme}://${host}/${segs.join("/")}${wc ? (segs.length ? "/" : "") + wc : ""}`;
  };
  const act = () => {
    const r = rng(), pool = valid ? V.actsValid : V.actsAny;
    if (r < 0.6) return pick(pool);
    const n = 1 + rint(2), out = [];
    for (let i = 0; i < n; i++) out.push(pick(pool));
    return out;
  };
  const cap = () => {
    const r = rng();
    if (r < 0.25) return undefined;
    const unit = pick(V.units), window = pick(valid ? V.windowsValid : V.windowsAny);
    let tx = pick(valid ? V.numsValid : V.numsAny), cum = pick(valid ? V.numsValid : V.numsAny);
    if (valid && tx > cum) [tx, cum] = [cum, tx];
    return { max_per_tx: tx, max_cumulative: cum, unit, window };
  };
  const cp = () => {
    const r = rng();
    if (r < 0.4) return undefined;
    const na = rint(3), nd = rint(2), allow = [], deny = [];
    for (let i = 0; i < na; i++) allow.push(pick(V.dids));
    for (let i = 0; i < nd; i++) deny.push(pick(V.dids));
    if (!valid && rng() < 0.08) return { allow: "did:key:z6MkA" };
    return { allow, deny };
  };
  const scope = () => {
    const s = { v: "lap-scope-v0" };
    if (!valid && rng() < 0.05) { const alt = pick(["lap-scope-v1", 7, undefined]); if (alt === undefined) delete s.v; else s.v = alt; }
    s.act = act();
    s.res = res(valid);
    if (!valid && rng() < 0.05) { const alt = pick([undefined, null, 42, "not a uri"]); if (alt === undefined) delete s.res; else s.res = alt; }
    const c = cap(); if (c !== undefined) s.cap = c;
    const p = cp(); if (p !== undefined) s.cp = p;
    if (rng() < 0.5) s.depth = pick(V.depths);
    if (rng() < 0.5) s.decay_max_sec = pick(V.decays);
    if (!valid && rng() < 0.03) return pick([null, "junk", 42]);
    return s;
  };
  const descendants = (verb) => { const out = [verb]; for (const ch of ACTION_REGISTRY_V0[verb] ?? []) out.push(...descendants(ch)); return out; };
  const splitRes = (r) => {
    const m = r.match(/^(.*?:\/\/[^/]+)\/(.*)$/);
    let segs = m[2].length ? m[2].split("/") : [];
    let wc = null;
    if (segs.at(-1) === "**") { wc = "**"; segs.pop(); } else if (segs.at(-1) === "*") { wc = "*"; segs.pop(); }
    return { origin: m[1], segs, wc };
  };
  const isSafe = (v) => Number.isSafeInteger(v) && v >= 0;
  const usableCap = (cap) => isPlainObj(cap) && isSafe(cap.max_per_tx) && isSafe(cap.max_cumulative) && typeof cap.window === "string" && typeof cap.unit === "string";
  const canAttenuate = (p) => isPlainObj(p) && typeof p.res === "string" && /^[^:]+:\/\/[^/]+\//.test(p.res) && (typeof p.act === "string" || (Array.isArray(p.act) && p.act.length > 0));
  // A child that SHOULD be subsumed by `parent` (when parent is valid) — with deliberate, rare overshoots.
  // Malformed parent parts are copied verbatim so "any"-mode pairs stay identical across ports.
  const attenuate = (parent) => {
    const c = { v: "lap-scope-v0" };
    const pActs = Array.isArray(parent.act) ? parent.act : [parent.act];
    const base = pick(pActs);
    c.act = base === "*" ? pick(V.actsValid.filter((a) => a !== "*")) : pick(descendants(base));
    const { origin, segs, wc } = splitRes(parent.res);
    if (wc === "**") {
      const extra = rint(3);
      for (let i = 0; i < extra; i++) segs.push(pick(V.segs));
      const k = pick([null, "*", "**"]); if (k) segs.push(k);
    } else if (wc === "*") {
      segs.push(rng() < 0.5 ? pick(V.segs) : "*");
    }
    c.res = `${origin}/${segs.join("/")}`;
    if (usableCap(parent.cap)) {
      const p = parent.cap;
      let window = p.window, scale = 1n;
      if (p.window === "utc_day" && rng() < 0.5) { window = "utc_hour"; scale = 24n; }
      const cumMax = BigInt(p.max_cumulative) / scale, txMax = BigInt(p.max_per_tx);
      const k = rint(1001);
      let cum = Number((cumMax * BigInt(k)) / 1000n);
      if (rng() < 0.15) cum = Number(cumMax) + 1;        // deliberately over the scaled budget
      let tx = Number(txMax); if (tx > cum) tx = cum;
      if (rng() < 0.1) tx = Number(txMax) + 1;            // deliberately over per-tx
      c.cap = { max_per_tx: tx, max_cumulative: cum, unit: p.unit, window };
    } else if (parent.cap !== undefined) {
      c.cap = parent.cap;
    } else if (rng() < 0.3) {
      c.cap = { max_per_tx: 1, max_cumulative: 5, unit: "USD", window: "tx" };
    }
    if (parent.cp !== undefined && !(isPlainObj(parent.cp) && strList(parent.cp.allow ?? []) && strList(parent.cp.deny ?? []))) {
      c.cp = parent.cp;
    } else if (parent.cp) {
      const pAllow = parent.cp.allow ?? [];
      let allow = pAllow.filter(() => rng() < 0.7);
      if (allow.length === 0 && pAllow.length > 0) allow = [pAllow[0]];
      const deny = [...(parent.cp.deny ?? [])];
      if (rng() < 0.3) deny.push(pick(V.dids));
      c.cp = { allow, deny };
    }
    if (parent.depth !== undefined) c.depth = Math.max(0, parent.depth - 1);
    if (parent.decay_max_sec !== undefined) c.decay_max_sec = parent.decay_max_sec;
    return c;
  };
  const concrete = (pattern) => {
    const { origin, segs, wc } = splitRes(pattern);
    if (wc === "*") segs.push(pick(V.segs));
    if (wc === "**") { const extra = rint(3); for (let i = 0; i < extra; i++) segs.push(pick(V.segs)); }
    return `${origin}/${segs.join("/")}`;
  };
  return { rng, rint, pick, res, act, cap, cp, scope, attenuate, concrete, splitRes, canAttenuate };
}

// ---------- exact-integer oracles (BigInt) ----------
const SECS = { utc_hour: 3600n, utc_day: 86400n };
function oracleCapSubsumes(p, c) {
  if (c.unit !== p.unit || c.max_per_tx > p.max_per_tx) return false;
  if (p.window === "tx" || p.window === "epoch_total") return c.window === p.window && c.max_cumulative <= p.max_cumulative;
  if (!(c.window in SECS)) return false;
  const pS = SECS[p.window], cS = SECS[c.window];
  if (cS > pS || pS % cS !== 0n) return false;
  return BigInt(c.max_cumulative) <= (BigInt(p.max_cumulative) * cS) / pS;
}
function oracleDebit(p, c) {
  const pS = SECS[p.window], cS = SECS[c.window];
  return pS && cS ? (BigInt(c.max_cumulative) * pS) / cS : BigInt(c.max_cumulative);
}
function decide(f) {
  try {
    const r = f();
    if (r === true || r === false) return r ? "T" : "F";
    return r && r.ok === true ? "T" : "F";
  } catch (e) {
    const m = String(e && e.message);
    return m.startsWith("LAP_ERR_") ? "E:" + m.split(":")[0] : "X:" + (e && e.constructor ? e.constructor.name : "Error");
  }
}
const j = (x) => JSON.stringify(x);
// "any"-mode cases: a third of the pairs and half of the children are attenuations, so the accept path is exercised too.
function anyPair(g) { const p = g.scope(); const c = (g.rng() < 0.35 && g.canAttenuate(p)) ? g.attenuate(p) : g.scope(); return [p, c]; }
function anyEnvelope(g) {
  const np = 1 + g.rint(2), nc = 1 + g.rint(3), P = [], C = [];
  for (let k = 0; k < np; k++) P.push(g.scope());
  for (let k = 0; k < nc; k++) { const r = g.rng(); C.push(r < 0.5 && g.canAttenuate(P[0]) ? g.attenuate(P[0]) : g.scope()); }
  return [P, C];
}

// ---------- properties ----------
test("fuzz 1: reflexivity — a valid scope subsumes an identical scope one hop down", () => {
  const g = makeGen(xorshift32(SEED ^ 1), true);
  for (let i = 0; i < 400; i++) {
    const s = g.scope();
    const same = { ...s };
    if (s.depth !== undefined) same.depth = s.depth - 1;
    const want = s.depth === undefined || s.depth >= 1;
    assert.equal(scopeSubsumes(s, same), want, `reflexivity: ${j(s)}`);
  }
});

test("fuzz 2: attenuation chains are transitive, and the accept rate is not vacuous", () => {
  const g = makeGen(xorshift32(SEED ^ 11), true);
  let held = 0;
  for (let i = 0; i < 600; i++) {
    const a = g.scope(), b = g.attenuate(a), c = g.attenuate(b);
    if (scopeSubsumes(a, b) && scopeSubsumes(b, c)) {
      held++;
      assert.equal(scopeSubsumes(a, c), true, `transitivity broken: ${j({ a, b, c })}`);
    }
  }
  assert.ok(held >= 120, `premise held only ${held}/600 times — chains too weak to test anything`);
});

test("fuzz 3: a pattern subsumes every concrete path it generates", () => {
  const g = makeGen(xorshift32(SEED ^ 3), true);
  for (let i = 0; i < 400; i++) {
    const p = g.res(true), c = g.concrete(p);
    assert.equal(pathSubsumes(p, c), true, `instantiation: ${p} should cover ${c}`);
  }
});

test("fuzz 4: no widening — wildcard escalation and origin changes are always refused", () => {
  const g = makeGen(xorshift32(SEED ^ 4), true);
  for (let i = 0; i < 400; i++) {
    const p = g.res(true);
    const { origin, segs, wc } = g.splitRes(p);
    if (wc !== "**") {
      const wider = `${origin}/${[...segs, wc === "*" ? "**" : segs.length ? "*" : "*"].join("/")}`;
      assert.equal(pathSubsumes(p, wider), false, `widened: ${p} must not cover ${wider}`);
    }
    const otherHost = p.replace(/:\/\/[^/]+/, "://not-the-same.example");
    assert.equal(pathSubsumes(p, otherHost), false, `origin: ${p} must not cover ${otherHost}`);
  }
});

test("fuzz 5: the two-dimensional cap rule agrees with an exact-integer oracle", () => {
  const g = makeGen(xorshift32(SEED ^ 5), true);
  const dflt = { max_per_tx: 100, max_cumulative: 100000, unit: "USD", window: "utc_day" };
  let trues = 0;
  for (let i = 0; i < 1500; i++) {
    const p = g.cap() ?? dflt, c = g.cap() ?? dflt;
    const want = oracleCapSubsumes(p, c);
    assert.equal(capSubsumes(p, c), want, `cap oracle: ${j({ p, c })}`);
    if (want) trues++;
  }
  for (let i = 0; i < 600; i++) {
    const s = g.scope(); if (!s.cap) s.cap = dflt;
    const c = g.attenuate(s).cap;
    const want = capIsValid(c) && oracleCapSubsumes(s.cap, c);
    assert.equal(capSubsumes(s.cap, c), want, `cap oracle (attenuated): ${j({ p: s.cap, c })}`);
    if (want) trues++;
  }
  assert.ok(trues > 200, `oracle accepted only ${trues} pairs — generator too hostile`);
});

test("fuzz 6: budget conservation agrees with an exact-integer oracle (single parent)", () => {
  const g = makeGen(xorshift32(SEED ^ 9), true);
  let accepted = 0;
  for (let i = 0; i < 400; i++) {
    const parent = g.scope();
    if (!parent.cap) parent.cap = { max_per_tx: 100, max_cumulative: 100000, unit: "USD", window: "utc_day" };
    const n = 1 + g.rint(4), children = [];
    for (let k = 0; k < n; k++) children.push(g.attenuate(parent));
    let got;
    try { got = verifyEnvelopeAttenuation([parent], children).ok; } catch (e) { got = "E:" + String(e.message).split(":")[0]; }
    if (children.some((c) => !capIsValid(c.cap))) { assert.equal(got, "E:LAP_ERR_CAP_SCHEMA", j({ parent, children })); continue; }
    const allSub = children.every((c) => scopeSubsumes(parent, c));
    let sum = 0n; for (const c of children) sum += oracleDebit(parent.cap, c.cap);
    const want = allSub && sum <= BigInt(parent.cap.max_cumulative);
    assert.equal(got, want, `conservation: ${j({ parent, children })}`);
    if (want) accepted++;
  }
  assert.ok(accepted > 40, `conservation oracle accepted only ${accepted}/400 — generator too hostile`);
});

test("fuzz 7: typed errors only — malformed scopes never surface a TypeError", () => {
  const g = makeGen(xorshift32(SEED ^ 13), false);
  const seen = { T: 0, F: 0, E: 0 }, untyped = new Set();
  const tally = (d) => { if (d[0] === "X") untyped.add(d); else seen[d[0]]++; };
  for (let i = 0; i < 2000; i++) { const [p, c] = anyPair(g); tally(decide(() => scopeSubsumes(p, c))); }
  for (let i = 0; i < 400; i++) { const [P, C] = anyEnvelope(g); tally(decide(() => verifyEnvelopeAttenuation(P, C))); }
  assert.equal(untyped.size, 0, `untyped errors: ${[...untyped].join(" ")}`);
  assert.ok(seen.T > 0 && seen.E > 0, `non-vacuity: ${j(seen)}`);
});

test("fuzz 8: cross-port parity — same seed, same decisions in Node and Python", () => {
  const g = makeGen(xorshift32(SEED ^ 7), false);
  const out = [];
  for (let i = 0; i < 1500; i++) { const [p, c] = anyPair(g); out.push(decide(() => scopeSubsumes(p, c))); }
  for (let i = 0; i < 300; i++) { const [P, C] = anyEnvelope(g); out.push(decide(() => verifyEnvelopeAttenuation(P, C))); }
  const digest = createHash("sha256").update(out.join(",")).digest("hex");
  const counts = { T: 0, F: 0, E: 0, X: 0 };
  for (const d of out) counts[d[0]]++;
  assert.equal(counts.X, 0, "untyped errors would make the digest meaningless");
  if (process.env.LAP_FUZZ_WRITE) {
    writeFileSync(DIGEST_PATH, JSON.stringify({ generator: "xorshift32/v1", seed: SEED, pairs: 1500, envelopes: 300, decisions: counts, digest }, null, 2) + "\n");
    return;
  }
  if (EXPLORING) return;
  const expected = JSON.parse(readFileSync(DIGEST_PATH, "utf8"));
  assert.equal(digest, expected.digest, "decision digest differs from the committed one: a port diverged, or the algebra changed on purpose (LAP_FUZZ_WRITE=1 to regenerate, then run pytest)");
});

test("fuzz 6b: budget conservation is SOUND across MULTIPLE overlapping parents (brute-force oracle) [F5]", () => {
  const g = makeGen(xorshift32(SEED ^ 23), true);
  // Does SOME full assignment of children -> subsuming parents fit every per-parent budget (in
  // parent-window units)? Greedy's own accept is one such assignment, so ok ⟹ feasible; a failure
  // here would be a real soundness bug. F5: property 6 only ever exercised a single parent.
  const feasible = (parents, children) => {
    const budget = parents.map((p) => (p.cap ? BigInt(p.cap.max_cumulative) : null));
    const go = (i) => {
      if (i === children.length) return true;
      const c = children[i];
      for (let jx = 0; jx < parents.length; jx++) {
        if (!scopeSubsumes(parents[jx], c)) continue;
        if (budget[jx] === null) { if (go(i + 1)) return true; continue; }
        const d = oracleDebit(parents[jx].cap, c.cap);
        if (d > budget[jx]) continue;
        budget[jx] -= d; if (go(i + 1)) return true; budget[jx] += d;
      }
      return false;
    };
    return go(0);
  };
  let accepted = 0;
  for (let i = 0; i < 500; i++) {
    const np = 2 + g.rint(2);                                  // 2-3 parents sharing a resource family (overlap on purpose)
    const parents = [];
    for (let kx = 0; kx < np; kx++) {
      const s = g.scope();
      s.res = "mcp://h/pay/**";
      if (!s.cap) s.cap = { max_per_tx: 100, max_cumulative: 100000, unit: "USD", window: "utc_day" };
      s.depth = 5; delete s.cp; delete s.decay_max_sec;
      parents.push(s);
    }
    const nc = 1 + g.rint(4);
    const children = [];
    for (let kx = 0; kx < nc; kx++) children.push(g.attenuate(parents[g.rint(np)]));
    if (children.some((c) => !capIsValid(c.cap))) continue;
    let got;
    try { got = verifyEnvelopeAttenuation(parents, children).ok; } catch { continue; }
    assert.ok(!got || feasible(parents, children), `unsound multi-parent accept: ${j({ parents, children })}`);
    if (got) accepted++;
  }
  assert.ok(accepted > 30, `multi-parent accept rate too low (${accepted}/500) to test soundness`);
});
