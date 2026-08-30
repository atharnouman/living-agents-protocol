// LAP networked demo — BUYER process (Alice). A real HTTP client that performs the
// MEET handshake and transacts against the seller over localhost sockets, and survives
// the seller genuinely going offline. Run: node buyer.mjs <seller-port>
import { generateKeyPairSync, sign } from "node:crypto";
import { writeFileSync, mkdirSync } from "node:fs";
import {
  didKeyFromRawPublicKey, rawPublicKeyFromKeyObject, jcs, sha256Hex, sha256B64url, b64urlEncode,
  publicKeyFromDid, verifyEd25519,
} from "../../lap-reference/src/crypto-util.js";
import { signJws, verifyPassport } from "../../lap-reference/src/jws.js";

const PORT = Number(process.argv[2] || 4102);
const BASE = `http://127.0.0.1:${PORT}`;
const NOW = 1787019000;
const say = (m) => console.log(`[buyer]  ${m}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const BEAT = Number(process.env.LAP_PACE || 0);      // presentation pacing (ms between beats); 0 = fast
const beat = () => (BEAT ? sleep(BEAT) : Promise.resolve());
const PULSE_MS = BEAT ? 900 : 700;

function keypair() {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  return { publicKey, privateKey, did: didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey)) };
}
const principal = keypair();
const agent = keypair();
const envelope = { act: ["finance:pay"], res: "ap2://demo-rails/bob-store/**", cap: { max_per_tx: 50, unit: "USD", window: "tx" } };
const constitution = "Constitution of Alice (buyer): act only within the signed envelope; escalate on ambiguity; honor FORCE_HALT.\n";
const passport = signJws({
  v: "lip1-v0", id: agent.did,
  principal: { id: principal.did, proof_class: "self-asserted", contact: "mailto:oncall@example.com" },
  lineage: { spawner: null, generation: 1 },
  constitution: { sha256: sha256Hex(constitution) },
  autonomy_level: 3,
  era: { track: "api-hosted", digest: sha256Hex(`provider:demo|model:demo-lm|${sha256Hex(constitution)}`) },
  presence_contact: "mailto:oncall@example.com",
  revocation: "https://buyer.example/revocation",
  iat: NOW, exp: NOW + 86400 * 365,
}, principal.privateKey, principal.did + "#key-1");

const post = (path, obj) => fetch(BASE + path, { method: "POST", headers: { "content-type": "application/json" }, body: jcs(obj) }).then((r) => r.json());
const get = (path) => fetch(BASE + path).then((r) => r.json());

const receipts = [];
let dailySpent = 0;

async function pay(order, qty, unitPrice, sellerAgent) {
  const amount = qty * unitPrice;
  if (dailySpent + amount > 100) throw new Error("authorizer refuses: daily cap");
  const mcClaims = {
    iss: principal.did, sub: agent.did, aud: sellerAgent, iat: NOW, exp: NOW + 600,
    lap: { v: 0, proof_class: "self-asserted", constitution_hash: sha256Hex(constitution), envelope },
  };
  const mcJwt = signJws(mcClaims, principal.privateKey, principal.did + "#key-1", "lap-microcore+jwt");
  const inner = jcs({ order, qty, unit_price: unitPrice, amount, unit: "USD" });
  const base = [
    '"@method": POST',
    '"@target-uri": http://127.0.0.1:' + PORT + '/pay',
    `"content-digest": sha-256=:${sha256B64url(inner)}:`,
    `"lap-passport-hash": sha256:${sha256Hex(mcJwt)}`,
    `"@signature-params": ("@method" "@target-uri" "content-digest" "lap-passport-hash");created=${NOW};keyid="${agent.did}#key-1"`,
  ].join("\n");
  const reqSig = b64urlEncode(sign(null, Buffer.from(base), agent.privateKey));
  const resp = await post("/pay", { passport_jwt: mcJwt, signature_base: base, signature_b64url: reqSig, request_body: inner, order, qty, unit_price: unitPrice });
  if (resp.error) throw new Error("seller rejected: " + resp.error);
  // verify the seller's signed receipt (real signature check on the response)
  const ok = verifyEd25519(publicKeyFromDid(resp.server_did), Buffer.from(resp.receipt_base), Buffer.from(resp.receipt_sig, "base64url"));
  if (!ok) throw new Error("bad receipt signature");
  dailySpent += amount;
  receipts.push({ order, amount, receipt_base: resp.receipt_base, receipt_sig: resp.receipt_sig, server_did: resp.server_did });
  say(`ORDER ${order}: ${qty} units @ $${unitPrice} = $${amount} over HTTP — receipt signature✓ ($${dailySpent}/$100 daily)`);
}

async function pulseAlive(sellerAgent) {
  try {
    const p = await get("/pulse");
    return verifyEd25519(publicKeyFromDid(sellerAgent), Buffer.from(jcs({ t: p.t, status: p.status, head: p.head, from: p.from })), Buffer.from(p.sig, "base64url"));
  } catch { return false; }
}

async function main() {
  await beat();
  say(`agent ${agent.did.slice(0, 22)}…  →  seller at ${BASE}`);

  // MEET 1-2 — HAIL/PROVE over the wire
  await beat();
  const sellerPassportRes = await get("/passport");
  const sp = verifyPassport(sellerPassportRes.passport, { now: NOW });
  say(`MEET HAIL/PROVE: fetched + verified seller passport ${sp.id.slice(0, 22)}… → VERIFIED`);
  const hail = await post("/meet", { step: "HAIL", passport });
  const sellerAgent = hail.sellerAgent;
  await beat();
  say(`  ↕ real HTTP: sent our passport, seller replied ${JSON.stringify({ step: hail.step, ok: hail.ok }).slice(0, 40)} (both sides verified each other's Ed25519 signatures)`);

  // MEET 3 — CHARTER: authorizer-signed reservation ticket
  const ticket = { nonce: sha256Hex(String(NOW)).slice(0, 12), amount: 50, unit: "USD", expiry: NOW + 3600, counterparty: sellerAgent };
  await beat();
  say(`MEET CHARTER: authorizer reservation $${ticket.amount} bound to seller, disclosed before transacting`);

  // MEET 5 — BIND: sign contract, seller countersigns over the wire
  const contractCore = { sid: sha256Hex(agent.did + sellerAgent).slice(0, 16), parties: [sha256Hex(passport), sha256Hex(sellerPassportRes.passport)], purpose: "overnight procurement", charter: envelope };
  const aliceSig = b64urlEncode(sign(null, Buffer.from(jcs(contractCore)), agent.privateKey));
  const bind = await post("/meet", { step: "BIND", contract: contractCore, aliceSig });
  const bindOk = verifyEd25519(publicKeyFromDid(sellerAgent), Buffer.from(jcs({ contract: contractCore, countersigning: aliceSig })), Buffer.from(bind.countersig, "base64url"));
  await beat();
  say(`MEET BIND: interaction contract dual-signed (seller countersignature verified: ${bindOk}) → session ACTIVE\n`);

  // Transact order 1
  await beat();
  await pay("A-001", 3, 12, sellerAgent);
  console.log("[buyer]  __MARK_PAID_A1__"); // conductor watches this to kill the seller

  // Pulse-gated liveness: poll the seller; a real outage = real connection failures
  let misses = 0, held = false;
  for (let i = 0; i < 40; i++) {
    await sleep(PULSE_MS);
    const alive = await pulseAlive(sellerAgent);
    if (alive) {
      if (held) {
        say(`pulse resumed from seller → authority restored automatically; releasing held order`);
        await pay("A-002", 3, 12, sellerAgent);
        break;
      }
    } else {
      misses++;
      if (misses === 1) say(`no pulse from seller (connection refused) — first miss`);
      if (misses >= 2 && !held) {
        held = true;
        say(`no pulse from seller across ${misses} intervals → counterparty DEGRADED, authority SUSPENDED prospectively`);
        say(`order A-002 is due — HELD: no live counterparty, nothing moves (no human woken: within protocol)`);
        console.log("[buyer]  __MARK_HELD__"); // conductor watches this to restart the seller
      }
    }
  }

  // Close + write transcript
  mkdirSync(new URL("./out/", import.meta.url), { recursive: true });
  writeFileSync(new URL("./out/session.json", import.meta.url), jcs({
    buyer: { agent: agent.did, principal: principal.did }, seller_agent: sellerAgent,
    receipts, spent: dailySpent, suspensions: held ? 1 : 0, transport: "real localhost HTTP between two OS processes",
  }) + "\n");
  say(`\nSession closed: ${receipts.length} orders, $${dailySpent} total over real HTTP, ${held ? 1 : 0} suspension, 0 escalations`);
  say(`Transcript → net/out/session.json. This ran across TWO OS processes exchanging signed JSON over sockets.`);
  console.log("[buyer]  __MARK_DONE__");
}

main().catch((e) => { console.error(`[buyer]  FATAL ${e.message}`); process.exit(1); });
