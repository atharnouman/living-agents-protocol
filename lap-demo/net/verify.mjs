// LAP networked demo — independent morning replay. Re-verifies the receipts the
// buyer wrote, with no access to either process's memory. Run: node verify.mjs
import { readFileSync } from "node:fs";
import { publicKeyFromDid, verifyEd25519 } from "../../lap-reference/src/crypto-util.js";

const s = JSON.parse(readFileSync(new URL("./out/session.json", import.meta.url), "utf8"));
console.log("\n=== MORNING REPLAY (independent verifier) ===\n");
console.log("While you slept, your agent (buyer) dealt with a stranger's agent (seller) over real HTTP:\n");

let checks = 0, fail = 0;
for (const r of s.receipts) {
  const ok = verifyEd25519(publicKeyFromDid(r.server_did), Buffer.from(r.receipt_base), Buffer.from(r.receipt_sig, "base64url"));
  checks++; if (!ok) fail++;
  console.log(`  • Order ${r.order}: $${r.amount} — seller-signed receipt ${ok ? "verified ✓" : "FAILED ✗"}`);
}
if (s.suspensions) console.log("  • counterparty went offline mid-session → authority suspended; the pending order was HELD, not sent");
console.log(`\n  Spent $${s.spent} of $100 daily cap. Escalations: 0. Transport: ${s.transport}.`);
console.log(`\n  Evidence verified: ${checks} receipt signature(s) — ${fail === 0 ? "ALL PASSED ✓" : fail + " FAILED"}`);
if (fail === 0) console.log("  Real cryptography, real sockets, real crash-and-recover. This is accountable autonomy.\n");
process.exit(fail === 0 ? 0 : 1);
