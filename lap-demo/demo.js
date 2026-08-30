// LAP overnight demo — two strangers' agents transact while both humans sleep.
// Real Ed25519 signatures throughout; simulated clock and in-process transport.
// Honest labels: registration is self-attested (no live transparency log in the demo);
// production runs use two machines and SCITT logs. Everything else is the real protocol.
import { generateKeyPairSync, randomBytes } from "node:crypto";
import { mkdirSync, writeFileSync } from "node:fs";
import { sign as cryptoSign } from "node:crypto";
import {
  jcs, sha256Hex, sha256B64url, b64urlEncode,
  didKeyFromRawPublicKey, rawPublicKeyFromKeyObject, publicKeyFromDid, verifyEd25519,
} from "../lap-reference/src/crypto-util.js";
import { signJws, verifyPassport } from "../lap-reference/src/jws.js";
import {
  verifyMicroCorePassport, verifyRequestSignature, checkInvocation, verifyReceipt,
} from "../lap-reference/src/microcore.js";
import { MerkleLog, verifyInclusion, saltedCommitment } from "../lap-reference/src/merkle-log.js";

// ---------- sim clock ----------
let T = 1787019000; // simulated unix seconds — the small hours UTC, both principals asleep
const tick = (s) => (T += s);
const fmt = (t = T) => new Date(t * 1000).toISOString().slice(11, 19) + "Z";
const say = (msg) => console.log(`  ${fmt()}  ${msg}`);

// ---------- keys & identities ----------
function keypair() {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  return { publicKey, privateKey, did: didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey)) };
}

function recorder(owner) {
  const entries = [];
  return {
    entries,
    head: () => (entries.length ? entries.at(-1).hash : "genesis"),
    add(act, payload) {
      const prev = this.head();
      const e = { seq: entries.length, ts: T, actor: owner, act, payload, payload_hash: sha256Hex(jcs(payload)), prev };
      e.hash = sha256Hex(jcs({ seq: e.seq, ts: e.ts, actor: e.actor, act: e.act, payload_hash: e.payload_hash, prev }));
      entries.push(e);
      return e;
    },
  };
}

function makeAgent(name, city, envelope) {
  const principal = keypair();
  const agent = keypair();
  const constitution = `Constitution of ${name}: act only within the signed envelope; escalate on ambiguity; honor FORCE_HALT.\n`;
  const passportClaims = {
    v: "lip1-v0", id: agent.did,
    principal: { id: principal.did, proof_class: "self-asserted", contact: `mailto:${name.toLowerCase()}@example.com` },
    lineage: { spawner: null, generation: 1 },
    constitution: { sha256: sha256Hex(constitution) },
    autonomy_level: 3,
    era: { track: "api-hosted", digest: sha256Hex(`provider:demo|model:demo-lm|${sha256Hex(constitution)}`) },
    presence_contact: `https://${name.toLowerCase()}.example.com/lap/pulse`,
    revocation: `https://${name.toLowerCase()}.example.com/lap/revocation`,
    iat: T, exp: T + 86400 * 365,
  };
  const passportJwt = signJws(passportClaims, principal.privateKey, principal.did + "#key-1");
  return { name, city, principal, agent, passportJwt, passportClaims, envelope, recorder: recorder(name), lastPulseFrom: {}, trust: {} };
}

const signObj = (obj, key) => b64urlEncode(cryptoSign(null, Buffer.from(jcs(obj)), key));
const verifyObj = (obj, sigB64, did) =>
  verifyEd25519(publicKeyFromDid(did), Buffer.from(jcs(obj)), Buffer.from(sigB64, "base64url"));

// ---------- the two parties ----------
const alice = makeAgent("Alice", "Karachi", {
  act: ["finance:pay"], res: "ap2://demo-rails/bob-store/**",
  cap: { max_per_tx: 50, max_cumulative: 100, unit: "USD", window: "utc_day" },
});
const bob = makeAgent("Bob", "Berlin", {
  act: ["finance:pay:release"], res: "ap2://demo-rails/bob-store/fulfil/**",
  cap: { max_per_tx: 100, max_cumulative: 500, unit: "USD", window: "utc_day" },
});
let aliceDailySpent = 0; // Alice-principal's spend authorizer (LIP-4: authorizer-side counter)
const witnessNode = { name: "Witness-1", ...keypair(), lastPulseFrom: {} }; // independent 3rd-party witness (≥2 rule)

// Reservation tickets (LIP-2 §7): authorizer-signed, counterparty-bound, single-use, enforced at settlement.
const consumedTickets = new Set();
function mintTicket(amount, counterparty) {
  const core = { nonce: randomBytes(8).toString("hex"), amount, unit: "USD", expiry: T + 3600, counterparty };
  return { ...core, sig: signObj(core, alice.principal.privateKey) };
}
function redeemTicket(ticket, amount, expectedCounterparty) {
  const { sig, ...core } = ticket;
  if (!verifyObj(core, sig, alice.principal.did)) throw new Error("LAP_ERR_TICKET: signature");
  if (core.counterparty !== expectedCounterparty) throw new Error("LAP_ERR_TICKET: counterparty");
  if (T > core.expiry) throw new Error("LAP_ERR_TICKET: expired");
  if (amount > core.amount) throw new Error("LAP_ERR_TICKET: amount exceeds reservation");
  if (consumedTickets.has(core.nonce)) throw new Error("LAP_ERR_TICKET: already consumed");
  consumedTickets.add(core.nonce);
  return core.nonce;
}

// ---------- registration: a real (local, single-operator) Agent Transparency Log ----------
// Honest label: production requires >=2 UNRELATED operators (spec §14.5); this demo runs one,
// RFC 6962 hashing, salted GDPR-safe principal commitments, real Merkle inclusion proofs.
const atl = new MerkleLog("demo-atl-1");
function register(party) {
  const pc = saltedCommitment(party.principal.did); // salt stays with the principal, off-log
  const genesis = jcs({
    v: "lip1-genesis-v0", agent: party.agent.did,
    passport_sha256: sha256Hex(jcs(party.passportClaims)),
    principal_commitment: pc.commitment, created_at: T,
  });
  const index = atl.append(Buffer.from(genesis));
  return { genesis, index, saltHex: pc.saltHex, commitment: pc.commitment };
}
const regAlice = register(alice);
const regBob = register(bob);

// ---------- MEET (LIP-2, transcript-hashed, all messages signed) ----------
const meetMessages = [];
const sid = sha256Hex(jcs({ a: alice.agent.did, b: bob.agent.did, t: T })).slice(0, 16);
function meetSend(from, step, body) {
  const transcript_hash = sha256Hex(meetMessages.map((m) => jcs(m)).join("\n"));
  const core = { sid, seq: meetMessages.length, step, transcript_hash, sender: from.agent.did, body };
  const msg = { ...core, sig: signObj(core, from.agent.privateKey) };
  meetMessages.push(msg);
  alice.recorder.add(`meet:${step}`, { seq: msg.seq, transcript_hash, body_hash: sha256Hex(jcs(body)) });
  bob.recorder.add(`meet:${step}`, { seq: msg.seq, transcript_hash, body_hash: sha256Hex(jcs(body)) });
  return msg;
}

console.log("\n=== LAP OVERNIGHT DEMO — both humans asleep ===\n");
say(`Alice's agent (${alice.city}) ${alice.agent.did.slice(0, 24)}…  |  Bob's agent (${bob.city}) ${bob.agent.did.slice(0, 24)}…`);

say("MEET step 1 — HAIL: passports exchanged");
meetSend(alice, "HAIL", { passport: alice.passportJwt });
meetSend(bob, "HAIL", { passport: bob.passportJwt });

tick(2);
say("MEET step 2 — PROVE: mutual verification");
const pa = verifyPassport(alice.passportJwt, { now: T });
const pb = verifyPassport(bob.passportJwt, { now: T });
const proofAlice = atl.inclusionProof(regAlice.index);
const proofBob = atl.inclusionProof(regBob.index);
if (!verifyInclusion(Buffer.from(regBob.genesis), proofBob)) throw new Error("Bob registration proof failed");
if (!verifyInclusion(Buffer.from(regAlice.genesis), proofAlice)) throw new Error("Alice registration proof failed");
alice.trust[bob.agent.did] = "VERIFIED";
bob.trust[alice.agent.did] = "VERIFIED";
meetSend(alice, "PROVE", { verified: bob.agent.did, registration: { log: proofAlice.log, index: proofAlice.index, root: proofAlice.root }, trust: "VERIFIED" });
meetSend(bob, "PROVE", { verified: alice.agent.did, registration: { log: proofBob.log, index: proofBob.index, root: proofBob.root }, trust: "VERIFIED" });
say(`  passports verified; Merkle inclusion proofs checked against ${atl.name} (root ${atl.root().slice(0, 12)}…) → both VERIFIED`);

tick(2);
say("MEET step 3 — CHARTER: commitment + reservation ticket (limits before disclosure)");
const ticket1 = mintTicket(50, bob.agent.did);
meetSend(alice, "CHARTER", { commitment: sha256Hex(jcs(alice.envelope)), reservation_ticket: ticket1 });
meetSend(bob, "CHARTER", { commitment: sha256Hex(jcs(bob.envelope)) });
say(`  Bob verified Alice's authorizer-signed reservation: $${ticket1.amount} locked, bound to Bob, expires ${fmt(ticket1.expiry)} — enforced at settlement, not just shown`);

tick(1);
say("MEET step 4 — TUNE: transport agreed (lap-microcore-sim/1)");
meetSend(alice, "TUNE", { profiles: ["lap-microcore-sim/1"] });
meetSend(bob, "TUNE", { accepted: "lap-microcore-sim/1" });

tick(2);
say("MEET step 5 — BIND: interaction contract signed, full charters disclosed");
const contractCore = {
  sid, parties: [sha256Hex(alice.passportJwt), sha256Hex(bob.passportJwt)],
  purpose: "overnight procurement of compute units",
  charters: { alice: alice.envelope, bob: bob.envelope },
  escalation: { alice: alice.passportClaims.principal.contact, bob: bob.passportClaims.principal.contact, bounded_hours: 12 },
  dispute: "lap-evidence-v0:demo", logging: "dual-entry",
};
const aliceSig = signObj(contractCore, alice.agent.privateKey);
const bobSig = signObj({ contract: contractCore, countersigning: aliceSig }, bob.agent.privateKey);
const contract = { core: contractCore, aliceSig, bobSig };
meetSend(alice, "BIND", { contract_hash: sha256Hex(jcs(contractCore)), sig: aliceSig });
meetSend(bob, "BIND", { contract_hash: sha256Hex(jcs(contractCore)), countersig: bobSig });

tick(1);
say("MEET step 6 — PULSE: presence contract (cadence 30s, witnesses: counterparty + independent Witness-1, per the ≥2 rule) → session ACTIVE\n");
meetSend(alice, "PULSE", { cadence: 30, witness: [bob.agent.did, witnessNode.did] });
meetSend(bob, "PULSE", { cadence: 30, witness: [alice.agent.did, witnessNode.did] });

// ---------- pulses & transactions ----------
function pulse(from, to, status = "active") {
  const core = { t: T, status, head: from.recorder.head(), from: from.agent.did };
  to.lastPulseFrom[from.agent.did] = T;
  witnessNode.lastPulseFrom[from.agent.did] = T; // independent witness observes every pulse
  to.recorder.add("pulse:received", core);
  from.recorder.add("pulse:sent", { ...core, sig: signObj(core, from.agent.privateKey) });
}

const receipts = [];
function buy(order, qty, unitPrice, ticket) {
  const amount = qty * unitPrice;
  if (aliceDailySpent + amount > alice.envelope.cap.max_cumulative) throw new Error("authorizer refuses: daily cap");
  const reservationNonce = redeemTicket(ticket, amount, bob.agent.did); // Bob-side: reservation enforced, single-use
  const mcClaims = {
    iss: alice.principal.did, sub: alice.agent.did, aud: bob.agent.did, iat: T, exp: T + 600,
    lap: { v: 0, proof_class: "self-asserted", constitution_hash: alice.passportClaims.constitution.sha256, envelope: alice.envelope },
  };
  const mcJwt = signJws(mcClaims, alice.principal.privateKey, alice.principal.did + "#key-1", "lap-microcore+jwt");
  const body = jcs({ order, qty, unit_price: unitPrice, amount, unit: "USD" });
  const base = [
    '"@method": POST',
    '"@target-uri": ap2://demo-rails/bob-store/pay',
    `"content-digest": sha-256=:${sha256B64url(body)}:`,
    `"lap-passport-hash": sha256:${sha256Hex(mcJwt)}`,
    `"lap-reservation-nonce": ${reservationNonce}`,
    `"@signature-params": ("@method" "@target-uri" "content-digest" "lap-passport-hash" "lap-reservation-nonce");created=${T};keyid="${alice.agent.did}#key-1"`,
  ].join("\n");
  const reqSig = b64urlEncode(cryptoSign(null, Buffer.from(base), alice.agent.privateKey));
  // ---- Bob's server-side LIP-4 invariant ----
  const claims = verifyMicroCorePassport(mcJwt, { expectedAud: bob.agent.did, now: T });
  verifyRequestSignature({ passportJwt: mcJwt, sub: claims.sub, signatureBase: base, signatureB64url: reqSig, requestBody: body });
  checkInvocation(claims.lap.envelope, { act: "finance:pay", resource: "ap2://demo-rails/bob-store/pay", amount, unit: "USD" });
  const responseBody = jcs({ status: "paid", order, fulfilment: `F-${order}` });
  const receiptBase = `sha256:${sha256Hex(body)}:sha256:${sha256Hex(responseBody)}`;
  const receipt = { order, amount, receiptBase, sig: b64urlEncode(cryptoSign(null, Buffer.from(receiptBase), bob.agent.privateKey)), body, responseBody };
  verifyReceipt({ receiptBase, receiptSignatureB64url: receipt.sig, serverDid: bob.agent.did, requestBody: body, responseBody });
  aliceDailySpent += amount;
  receipts.push(receipt);
  alice.recorder.add("tx:paid", { order, amount, receipt_base: receiptBase, receipt_sig: receipt.sig });
  bob.recorder.add("tx:received", { order, amount, receipt_base: receiptBase });
  say(`ORDER ${order}: ${qty} units @ $${unitPrice} = $${amount} — passport✓ aud✓ signature✓ cap✓ reservation✓(${reservationNonce.slice(0, 8)}, consumed) → paid, dual receipts ($${aliceDailySpent}/$${alice.envelope.cap.max_cumulative} daily)`);
}

tick(30); pulse(alice, bob); pulse(bob, alice);
buy("A-001", 3, 12, ticket1);
tick(30); pulse(alice, bob); pulse(bob, alice);

// ---------- the stress beat: Bob crashes ----------
tick(30); pulse(alice, bob); // Bob misses his beat
say("Bob's agent crashes (simulated) — first pulse missed");
tick(30); pulse(alice, bob); // Bob misses again
const gap = T - (alice.lastPulseFrom[bob.agent.did] ?? 0);
const gapW = T - (witnessNode.lastPulseFrom[bob.agent.did] ?? 0);
if (gap < 2 * 30 || gapW < 2 * 30) throw new Error(`demo bug: suspension beat must fire (gaps=${gap},${gapW})`);
alice.trust[bob.agent.did] = "DEGRADED";
alice.recorder.add("decay:suspend", { counterparty: bob.agent.did, missed_seconds: gap, witnesses_agreeing: 2, rule: "pulse-gated suspension (prospective only)" });
say(`ALICE: no pulse from Bob for ${gap}s — confirmed by 2 independent observers (Alice + Witness-1, ≥2 rule) → DEGRADED, authority suspended prospectively`);
say("ALICE: order A-002 is due — HELD: counterparty authority suspended (no human woken: within protocol)");
alice.recorder.add("tx:held", { order: "A-002", reason: "counterparty pulse-gated suspension" });

tick(45);
say("Bob's agent restarts — a restart is a nap, not a death (session resumes on passport, not process)");
pulse(bob, alice, "active");
alice.trust[bob.agent.did] = "VERIFIED";
alice.recorder.add("decay:recovered", { counterparty: bob.agent.did, rule: "automatic on pulse resumption — re-blessing is for expiry, not blips" });
say("ALICE: pulse resumed → authority restored automatically, releasing held order");
tick(5);
const ticket2 = mintTicket(50, bob.agent.did);
say("ALICE's authorizer issues a fresh reservation for the held order (ticket1 was single-use)");
buy("A-002", 3, 12, ticket2);

// ---------- teardown ----------
tick(30); pulse(alice, bob); pulse(bob, alice);
const closingCore = {
  sid, orders: receipts.map((r) => ({ order: r.order, amount: r.amount })),
  total: receipts.reduce((s, r) => s + r.amount, 0),
  era_stamps: { alice: alice.passportClaims.era.digest, bob: bob.passportClaims.era.digest },
  suspensions: 1, escalations: 0,
};
const closing = { core: closingCore, aliceSig: signObj(closingCore, alice.agent.privateKey), bobSig: signObj(closingCore, bob.agent.privateKey) };
alice.recorder.add("session:closed", { closing_hash: sha256Hex(jcs(closingCore)) });
bob.recorder.add("session:closed", { closing_hash: sha256Hex(jcs(closingCore)) });
say(`Session closed with dual-signed, era-stamped receipt: ${receipts.length} orders, $${closingCore.total} total, 1 suspension, 0 escalations\n`);

// ---------- persist for the morning replay ----------
mkdirSync(new URL("./out/", import.meta.url), { recursive: true });
const out = (f, data) => writeFileSync(new URL(`./out/${f}`, import.meta.url), JSON.stringify(data, null, 1) + "\n");
out("session.json", {
  sid, sim_now: T,
  parties: {
    alice: { agent: alice.agent.did, principal: alice.principal.did, passport: alice.passportJwt, city: alice.city },
    bob: { agent: bob.agent.did, principal: bob.principal.did, passport: bob.passportJwt, city: bob.city },
  },
  contract, closing, receipts, daily_cap: alice.envelope.cap.max_cumulative, spent: aliceDailySpent,
  witness: witnessNode.did,
  registration: {
    log: atl.name, root: atl.root(),
    note: "single-operator demo log; production requires >=2 unrelated operators; salts shown here would stay off-log with each principal",
    alice: { genesis: regAlice.genesis, proof: atl.inclusionProof(regAlice.index), commitment: regAlice.commitment, saltHex: regAlice.saltHex },
    bob: { genesis: regBob.genesis, proof: atl.inclusionProof(regBob.index), commitment: regBob.commitment, saltHex: regBob.saltHex },
  },
});
out("meet-messages.json", meetMessages);
out("recorder-alice.json", alice.recorder.entries);
out("recorder-bob.json", bob.recorder.entries);
console.log("Transcripts written to lap-demo/out/ — run `node replay.js` for the morning report.\n");
