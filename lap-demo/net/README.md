# LAP networked demo — two real processes

The single-process demo (`../demo.js`) tells the story in one script. **This version proves it across two real OS processes exchanging signed JSON over real localhost sockets** — which is what a protocol actually is.

```bash
cd lap-demo/net && node conductor.mjs      # then: node verify.mjs
```

What it does, and why each part is credible:

| Beat | What's real |
|---|---|
| **Two processes** | `seller.mjs` (an HTTP server) and `buyer.mjs` (a client) are separate OS processes with no shared memory — the conductor spawns both. |
| **MEET over the wire** | The buyer fetches and verifies the seller's passport; both sides verify each other's **real Ed25519 signatures**; the interaction contract is signed by the buyer and **countersigned by the seller** over HTTP. |
| **Micro-Core enforcement** | Every `/pay` runs the LIP-4 server-side invariant on the **actual request bytes**: audience, holder-of-key request signature, envelope act/resource/cap. |
| **The crash** | The conductor sends the seller a **real `SIGKILL`**. The buyer's "suspension" is caused by **real `ECONNREFUSED`** on its pulse polls — not a simulated flag. |
| **The recovery** | The seller **reloads its persisted identity** (same `did:key` across the restart — L4: a session is bound to the passport, not the process), the buyer's pulse verifies again, authority restores automatically, and the held order completes. |
| **The proof** | `verify.mjs` re-checks the seller-signed receipts with no access to either process's memory. |

Honest labels (same as the single-process demo): registration is self-attested (production needs ≥2 independent transparency logs), the payment rail is mocked, and the clock is fixed for stable output. Everything else — identities, signatures, request binding, the crash, the recovery — is real.

`net/out/` (transcripts and the seller's private-key identity file) is git-ignored and regenerated each run.
