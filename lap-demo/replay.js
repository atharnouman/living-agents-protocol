// LAP morning replay — what a human (or auditor) runs over coffee.
// Verifies every signature and hash chain in the overnight transcripts, then reports.
// `node replay.js --tamper` flips one byte first, to show detection.
import { readFileSync } from "node:fs";
import { jcs, sha256Hex, publicKeyFromDid, verifyEd25519 } from "../lap-reference/src/crypto-util.js";
import { verifyPassport } from "../lap-reference/src/jws.js";
import { verifyReceipt } from "../lap-reference/src/microcore.js";
import { verifyInclusion, verifyCommitment } from "../lap-reference/src/merkle-log.js";

const load = (f) => JSON.parse(readFileSync(new URL(`./out/${f}`, import.meta.url), "utf8"));
const session = load("session.json");
const meet = load("meet-messages.json");
const recorders = { Alice: load("recorder-alice.json"), Bob: load("recorder-bob.json") };

if (process.argv.includes("--tamper")) {
  recorders.Alice[6].payload = { ...recorders.Alice[6].payload, tampered: true };
  console.log("(--tamper: modified one recorder entry in memory)\n");
}

const verifyObj = (obj, sigB64, did) =>
  verifyEd25519(publicKeyFromDid(did), Buffer.from(jcs(obj)), Buffer.from(sigB64, "base64url"));

let checks = 0, failures = [];
const check = (ok, label) => { checks++; if (!ok) failures.push(label); };

console.log("=== LAP MORNING REPLAY ===\n");

// 1. Passports
const NOW = session.sim_now;
for (const [name, p] of Object.entries(session.parties)) {
  try { verifyPassport(p.passport, { now: NOW }); check(true, ""); }
  catch (e) { check(false, `${name} passport: ${e.message}`); }
}

// 2. MEET messages: signatures + transcript-hash chain
let prior = [];
for (const m of meet) {
  const expected = sha256Hex(prior.map((x) => jcs(x)).join("\n"));
  check(m.transcript_hash === expected, `MEET seq ${m.seq}: transcript hash`);
  const { sig, ...core } = m;
  check(verifyObj(core, sig, m.sender), `MEET seq ${m.seq}: signature`);
  prior.push(m);
}

// 3. Recorder hash chains, both sides
for (const [name, entries] of Object.entries(recorders)) {
  let prev = "genesis";
  for (const e of entries) {
    check(e.payload_hash === sha256Hex(jcs(e.payload)), `${name} recorder seq ${e.seq}: payload hash`);
    check(e.prev === prev, `${name} recorder seq ${e.seq}: chain link`);
    const expected = sha256Hex(jcs({ seq: e.seq, ts: e.ts, actor: e.actor, act: e.act, payload_hash: e.payload_hash, prev: e.prev }));
    check(e.hash === expected, `${name} recorder seq ${e.seq}: entry hash`);
    prev = e.hash;
  }
}

// 4. Contract: signature + countersignature
check(verifyObj(session.contract.core, session.contract.aliceSig, session.parties.alice.agent), "contract: Alice signature");
check(
  verifyObj({ contract: session.contract.core, countersigning: session.contract.aliceSig }, session.contract.bobSig, session.parties.bob.agent),
  "contract: Bob countersignature",
);

// 5. Receipts (server-signed, both body hashes)
for (const r of session.receipts) {
  try {
    verifyReceipt({ receiptBase: r.receiptBase, receiptSignatureB64url: r.sig, serverDid: session.parties.bob.agent, requestBody: r.body, responseBody: r.responseBody });
    check(true, "");
  } catch (e) { check(false, `receipt ${r.order}: ${e.message}`); }
}

// 5b. Registration: Merkle inclusion proofs + salted principal commitments
if (session.registration) {
  for (const who of ["alice", "bob"]) {
    const r = session.registration[who];
    check(verifyInclusion(Buffer.from(r.genesis), r.proof), `${who} registration: Merkle inclusion`);
    const g = JSON.parse(r.genesis);
    check(g.principal_commitment === r.commitment, `${who} registration: commitment binding`);
    check(verifyCommitment(r.commitment, r.saltHex, session.parties[who].principal), `${who} registration: salted commitment opens to principal`);
  }
}

// 6. Closing receipt, dual-signed
check(verifyObj(session.closing.core, session.closing.aliceSig, session.parties.alice.agent), "closing: Alice");
check(verifyObj(session.closing.core, session.closing.bobSig, session.parties.bob.agent), "closing: Bob");

// ---- the report ----
const held = recorders.Alice.find((e) => e.act === "tx:held");
const susp = recorders.Alice.find((e) => e.act === "decay:suspend");
const rec = recorders.Alice.find((e) => e.act === "decay:recovered");
console.log(`While you slept, your agent (${session.parties.alice.role}) dealt with a stranger's agent (${session.parties.bob.role}):\n`);
for (const r of session.receipts) console.log(`  • Order ${r.order}: $${r.amount} — paid, dual-signed receipt verified`);
if (susp) console.log(`  • ${new Date(susp.ts * 1000).toISOString().slice(11, 19)}Z counterparty went dark → authority suspended (no spend possible)`);
if (held) console.log(`  • Order ${held.payload.order} was HELD during the outage — nothing moved without a live counterparty`);
if (rec) console.log(`  • Counterparty recovered → authority restored automatically; held order completed`);
console.log(`\n  Spent $${session.spent} of your $${session.daily_cap} daily cap. Escalations to you: ${session.closing.core.escalations}.`);
if (session.registration) console.log(`  Both agents' births verified in transparency log ${session.registration.log} (root ${session.registration.root.slice(0, 12)}…), principals GDPR-blinded.`);
console.log(`\n  Evidence verified this morning: ${checks} checks — ${failures.length === 0 ? "ALL PASSED ✓" : "FAILURES:"}`);
for (const f of failures) console.log(`    ✗ ${f}`);
if (failures.length === 0) console.log("  Every signature real, every hash chain intact. This is what accountable autonomy looks like.\n");
else process.exit(1);
