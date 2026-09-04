import { test } from "node:test";
import assert from "node:assert/strict";
import { dagSubsumes, pathSubsumes, capSubsumes, counterpartySubsumes, scopeSubsumes, verifyEnvelopeAttenuation } from "../src/algebra.js";

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
