// LAP networked demo — CONDUCTOR. Spawns the seller and buyer as two real OS
// processes, waits for the server, and performs a genuine process kill + restart
// driven by the buyer's actual progress. Run: node conductor.mjs
// The crash is a real SIGKILL; the recovery is a real re-listen; the buyer's
// "suspension" is caused by real connection failures, not a simulated flag.
import { spawn } from "node:child_process";
import readline from "node:readline";
import { rmSync } from "node:fs";

const PORT = 4107;
const PRESENT = process.argv.includes("--present");   // filmable ~70s pacing
const BUYER_ENV = PRESENT ? { ...process.env, LAP_PACE: "3400" } : process.env;
const RESTART_MS = PRESENT ? 3600 : 2000;
// fresh identity per full run; it persists only across the mid-run restart
try { rmSync(new URL("./out/seller-identity.json", import.meta.url)); } catch { /* first run */ }
const C = { buyer: "\x1b[36m", seller: "\x1b[35m", cond: "\x1b[33m", dim: "\x1b[90m", reset: "\x1b[0m" };
const banner = (m) => console.log(`\n${C.cond}=== ${m} ===${C.reset}\n`);
const note = (m) => console.log(`${C.cond}[conductor]  ${m}${C.reset}`);

function spawnSeller() {
  const p = spawn(process.execPath, ["seller.mjs", String(PORT)], { cwd: new URL(".", import.meta.url) });
  readline.createInterface({ input: p.stdout }).on("line", (l) => console.log(`${C.seller}${l}${C.reset}`));
  readline.createInterface({ input: p.stderr }).on("line", (l) => console.log(`${C.seller}[seller:err] ${l}${C.reset}`));
  return p;
}

async function waitReady() {
  for (let i = 0; i < 50; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/passport`); if (r.ok) return true; } catch { /* not up yet */ }
    await new Promise((r) => setTimeout(r, 120));
  }
  throw new Error("seller did not become ready");
}

async function main() {
  banner("LAP OVERNIGHT DEMO — two real processes, both humans asleep");
  let seller = spawnSeller();
  await waitReady();
  note("seller is live; starting buyer as a separate process\n");

  const buyer = spawn(process.execPath, ["buyer.mjs", String(PORT)], { cwd: new URL(".", import.meta.url), env: BUYER_ENV });
  readline.createInterface({ input: buyer.stderr }).on("line", (l) => console.log(`${C.buyer}[buyer:err] ${l}${C.reset}`));

  let killed = false;
  const rl = readline.createInterface({ input: buyer.stdout });
  for await (const line of rl) {
    if (line.includes("__MARK_PAID_A1__")) {
      await new Promise((r) => setTimeout(r, 500));
      note("*** killing the seller process now (real SIGKILL) — simulating a crash ***");
      seller.kill("SIGKILL");
      killed = true;
      continue;
    }
    if (line.includes("__MARK_HELD__")) {
      note("buyer safely held its order through the outage. Restarting the seller…");
      await new Promise((r) => setTimeout(r, RESTART_MS));
      seller = spawnSeller();
      await waitReady();
      note("*** seller process RESTARTED and listening again — a restart is a nap, not a death ***\n");
      continue;
    }
    if (line.includes("__MARK_DONE__")) break;
    console.log(`${C.buyer}${line}${C.reset}`);
  }

  seller.kill("SIGKILL");
  banner("Demo complete — run `node verify.mjs` for the independent morning replay");
  process.exit(0);
}

main().catch((e) => { console.error(`${C.cond}[conductor] FATAL ${e.message}${C.reset}`); process.exit(1); });
