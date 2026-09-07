import { test } from "node:test";
import assert from "node:assert/strict";
import { dagSubsumes, pathSubsumes, capSubsumes, counterpartySubsumes, scopeSubsumes, scopeIsValid, verifyEnvelopeAttenuation } from "../src/algebra.js";

const S = (over = {}) => ({ v: "lap-scope-v0", act: "finance:pay", res: "ap2://rails/stripe/**", ...over });

// LAP never inspects the network layer, so IPv4/IPv6 is transparent to the protocol.
// The only place the address surfaces is inside resource URIs, where IPv6 literals are
// bracketed (RFC 3986 §3.2.2). Host lowercasing already matches RFC 5952 canonical form.
test("IPv6 literal resources: bracketed authority, case-folded, distinct from IPv4", () => {
  assert.equal(pathSubsumes("mcp://[2001:db8::1]:4107/billing/**", "mcp://[2001:DB8::1]:4107/billing/pay"), true);
  assert.equal(pathSubsumes("mcp://[2001:db8::1]:4107/billing/**", "mcp://[2001:db8::2]:4107/billing/pay"), false);
  assert.equal(pathSubsumes("mcp://[::1]:4107/billing/**", "mcp://127.0.0.1:4107/billing/pay"), false);
  assert.equal(pathSubsumes("http://[::1]:4107/pay", "http://[::1]:4107/pay"), true);
  // Documented interop hazard: matching is TEXTUAL, so the expanded and compressed
  // forms of the same address do not match. Scopes MUST use RFC 5952 canonical form.
  assert.equal(pathSubsumes("mcp://[2001:db8:0:0:0:0:0:1]/x/**", "mcp://[2001:db8::1]/x/y"), false);
});

test("REJECT: sub-verb escalation via unregistered edge (compute:exec → :unconfined)", () => {
  assert.equal(dagSubsumes("compute:exec", "compute:exec:unconfined"), false);
  assert.equal(dagSubsumes("compute:exec", "compute:exec:sandboxed"), true); // registered edge
});

test("REJECT: character-prefix path escape (finance vs finance_admin)", () => {
  assert.equal(pathSubsumes("mcp://t/finance/**", "mcp://t/finance_admin/x"), false);
  assert.equal(pathSubsumes("mcp://t/finance/**", "mcp://t/finance/x/y"), true);
});

test("REJECT: window inversion — bare tx cannot attenuate a windowed parent", () => {
  const parent = { max_per_tx: 50, max_cumulative: 100, unit: "USD", window: "utc_hour" };
  const child = { max_per_tx: 50, max_cumulative: 50, unit: "USD", window: "tx" };
  assert.equal(capSubsumes(parent, child), false);
});

test("ACCEPT: timed subdivision with proportional cumulative", () => {
  const parent = { max_per_tx: 50, max_cumulative: 2400, unit: "USD", window: "utc_day" };
  const okChild = { max_per_tx: 50, max_cumulative: 100, unit: "USD", window: "utc_hour" }; // 2400/24
  const badChild = { max_per_tx: 50, max_cumulative: 200, unit: "USD", window: "utc_hour" };
  assert.equal(capSubsumes(parent, okChild), true);
  assert.equal(capSubsumes(parent, badChild), false);
});

test("REJECT: cross-currency attenuation", () => {
  const parent = { max_per_tx: 100, max_cumulative: 100, unit: "USD", window: "tx" };
  const child = { max_per_tx: 90, max_cumulative: 90, unit: "EUR", window: "tx" };
  assert.equal(capSubsumes(parent, child), false);
});

test("REJECT: empty-allow-list deny bypass (effective sets)", () => {
  const parent = { allow: [], deny: ["did:web:competitor.com"] };
  const child = { allow: ["did:web:competitor.com"], deny: [] };
  assert.equal(counterpartySubsumes(parent, child), false);
  const honestChild = { allow: ["did:web:vendora.com"], deny: ["did:web:competitor.com"] };
  assert.equal(counterpartySubsumes(parent, honestChild), true);
});

test("REJECT: budget replication across sibling child scopes (conservation)", () => {
  const parent = [S({ cap: { max_per_tx: 500, max_cumulative: 500, unit: "USD", window: "utc_day" } })];
  const children = [
    S({ res: "ap2://rails/stripe/a/**", cap: { max_per_tx: 500, max_cumulative: 500, unit: "USD", window: "utc_day" } }),
    S({ res: "ap2://rails/stripe/b/**", cap: { max_per_tx: 500, max_cumulative: 500, unit: "USD", window: "utc_day" } }),
  ];
  assert.equal(verifyEnvelopeAttenuation(parent, children).ok, false);
  const conserving = [
    S({ res: "ap2://rails/stripe/a/**", cap: { max_per_tx: 300, max_cumulative: 300, unit: "USD", window: "utc_day" } }),
    S({ res: "ap2://rails/stripe/b/**", cap: { max_per_tx: 200, max_cumulative: 200, unit: "USD", window: "utc_day" } }),
  ];
  assert.equal(verifyEnvelopeAttenuation(parent, conserving).ok, true);
});

test("REJECT: delegation depth exhaustion and decay loosening", () => {
  assert.equal(scopeSubsumes(S({ depth: 0 }), S({ depth: 0 })), false);
  assert.equal(scopeSubsumes(S({ depth: 3 }), S({ depth: 2 })), true);
  assert.equal(scopeSubsumes(S({ decay_max_sec: 300 }), S({ decay_max_sec: 3600 })), false);
});

test("normalization: case and NFC differences do not bypass matching", () => {
  assert.equal(pathSubsumes("MCP://Tools.Example.com/billing/**", "mcp://tools.example.com/billing/pay"), true);
});

test("ACCEPT: full valid attenuation", () => {
  const parent = [S({ act: "finance:pay", cap: { max_per_tx: 10000, max_cumulative: 50000, unit: "USD", window: "utc_day" }, cp: { allow: ["did:web:vendora.com", "did:web:vendorb.com"], deny: [] }, depth: 3, decay_max_sec: 600 })];
  const child = [S({ act: "finance:pay:escrow", res: "ap2://rails/stripe/invoices/**", cap: { max_per_tx: 2000, max_cumulative: 10000, unit: "USD", window: "utc_day" }, cp: { allow: ["did:web:vendora.com"], deny: [] }, depth: 2, decay_max_sec: 300 })];
  assert.equal(verifyEnvelopeAttenuation(parent, child).ok, true);
});

// ---- v0.3 fuzz-round findings (2026-09-08; see llm-collab/IMPROVEMENTS-LOG.md) ----
test("v0.3: a '*' pattern subsumes itself one hop down; the URI syntax is closed; malformed scopes fail closed with typed errors", () => {
  assert.equal(pathSubsumes("mcp://h/a/*", "mcp://h/a/*"), true);      // the same set (was false: an identical delegation was refused)
  assert.equal(pathSubsumes("mcp://h/a/*", "mcp://h/a/**"), false);     // still never widen
  assert.equal(pathSubsumes("mcp://h/a/*", "mcp://h/a/b/*"), false);
  assert.equal(pathSubsumes("mcp://h/a/*", "mcp://h/b/*"), false);
  for (const bad of ["mcp://h/a?x=1", "mcp://h/a#f", "mcp://h//a", "mcp://h/a//b", "mcp://h?x/a", "not a uri", "", 42, null]) {
    assert.throws(() => pathSubsumes("mcp://h/**", bad), /LAP_ERR_RES/, `should refuse ${JSON.stringify(bad)}`);
  }
  assert.equal(pathSubsumes("mcp://h/a/", "mcp://h/a"), true);          // one trailing slash is tolerated
  const ok = S({ res: "mcp://h/**" });
  const malformed = [null, "junk", 42, [], S({ res: undefined }), S({ res: null }), S({ act: 7 }), S({ act: [7] }), S({ act: undefined }),
    S({ cp: { allow: "did:key:z6MkA" } }), S({ cp: { deny: [1] } }), S({ depth: -1 }), S({ depth: 17 }), S({ depth: "2" }), S({ decay_max_sec: null }), S({ v: 7 }), S({ v: undefined })];
  for (const bad of malformed) {
    assert.equal(scopeIsValid(bad), false, `should be invalid: ${JSON.stringify(bad)}`);
    assert.equal(scopeSubsumes(ok, bad), false);
    assert.equal(scopeSubsumes(bad, ok), false);
    assert.throws(() => verifyEnvelopeAttenuation([ok], [bad]), /LAP_ERR_SCOPE_SCHEMA/);
    assert.throws(() => verifyEnvelopeAttenuation([bad], [ok]), /LAP_ERR_SCOPE_SCHEMA/);
  }
  assert.throws(() => verifyEnvelopeAttenuation(ok, [ok]), /LAP_ERR_SCOPE_SCHEMA/);
  assert.equal(scopeIsValid(ok), true);
  assert.equal(counterpartySubsumes({ allow: "x" }, {}), false);
  // a missing act must not compare as "grants nothing is a subset of grants nothing" (one port did)
  assert.equal(scopeSubsumes(S({ act: undefined }), S({ act: undefined })), false);
  // parity trap from the differential fuzzer: an uppercase DID prefix normalizes identically in both ports
  assert.equal(counterpartySubsumes({ allow: ["did:web:vendora.com"] }, { allow: ["DID:WEB:vendora.com"] }), true);
  assert.equal(counterpartySubsumes({ allow: ["did:key:z6MkA"] }, { allow: ["did:key:Z6MKA"] }), false); // did:key ids are case-sensitive
  // effective sets: a member the child itself denies does not count against it (the Python port lacked this skip — found by the fuzzer)
  const AB = { allow: ["did:key:z6MkA", "did:key:z6MkB"], deny: ["did:key:z6MkA"] };
  assert.equal(counterpartySubsumes(AB, { allow: ["did:key:z6MkA", "did:key:z6MkB"], deny: ["did:key:z6MkA"] }), true);
  assert.equal(counterpartySubsumes(AB, { allow: ["did:key:z6MkA"], deny: [] }), false);
});

test("v0.3: exact integer arithmetic for window scaling and debits (no double rounding at large caps)", () => {
  const P = { unit: "USD", window: "utc_day", max_per_tx: 1, max_cumulative: 8707531655995247 };
  assert.equal(capSubsumes(P, { unit: "USD", window: "utc_hour", max_per_tx: 1, max_cumulative: 362813818999801 }), true);  // exact floor(P/24)
  assert.equal(capSubsumes(P, { unit: "USD", window: "utc_hour", max_per_tx: 1, max_cumulative: 362813818999802 }), false); // Math.floor said yes
  const parent = S({ res: "mcp://h/**", cap: { unit: "USD", window: "utc_day", max_per_tx: 1, max_cumulative: 8221535177121408 } });
  const child = S({ res: "mcp://h/x", cap: { unit: "USD", window: "utc_hour", max_per_tx: 1, max_cumulative: 342563965713392 } });
  assert.equal(verifyEnvelopeAttenuation([parent], [child]).ok, true);   // debit 342563965713392 x 24 = 8221535177121408, exactly the budget
  const twoChildren = [child, S({ res: "mcp://h/y", cap: { unit: "USD", window: "utc_hour", max_per_tx: 1, max_cumulative: 1 } })];
  assert.equal(verifyEnvelopeAttenuation([parent], twoChildren).ok, false); // one unit over
});
