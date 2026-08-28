# LAP — Bitcoin Anchors (OpenTimestamps)

*Stamped 2026-08-29 via 4 independent public calendar servers (a.pool.opentimestamps.org, b.pool.opentimestamps.org, a.pool.eternitywall.com, ots.btc.catallaxy.com). Each `.ots` file sits beside its artifact. This is the spec §19 pattern in miniature: Merkle aggregation by calendars → one Bitcoin transaction anchors thousands of digests, no per-file fees, no personal data on-chain.*

| SHA-256 | Artifact |
|---|---|
| `5e6fd275d1a30394c86c672456eb831d4f95ac233b69a6d93317b785dd2ab865` | LAP-founding-document.md (v0.4.2) |
| `27d88e7d315c1ef200f76f996036f6d63c3a6e36d961019bf064ffd4ea978406` | lip/LIP-1-agent-passport-draft.md |
| `9286af182704bde1de310552c10c47527dbcf1f301f2021361bf27d1325e15a1` | lip/LIP-2-meet-draft.md |
| `2b7f564a6f68dabf240d2d100136928341027da1985efd2fcdbc902e78c37ccb` | lip/LIP-3-scope-algebra-v0-draft.md |
| `e89823bd513d6d83801507bf53a7dfca47a7e0c90eee71d0f81009a8915d4905` | lip/LIP-4-micro-core-draft.md |
| `b389bf8335e928609c9cbdc7828d3e23c35486ece607527503cacc1adbf28fb5` | lip/test-vectors/vectors.json |
| `6e2817b74059ee537cd483889f7379525818f4407b13e34097099f09b0a84532` | LAP-position-paper.md |
| `5b50772f8ea3753450f10959c3b9edf604ced936eafa8016350f7b5ca8c760cf` | LAP-essay.md |

## Status and how to use

- **Now**: proofs are *pending attestations* — the calendars have the digests and will fold them into their next Bitcoin aggregation transaction (typically within hours).
- **Upgrade to full on-chain proof** (any time later, from any machine with the `ots` tool): `ots upgrade <file>.ots` then `ots verify <file>.ots` — verification then states the Bitcoin block that commits to the file's existence.
- **What this proves**: these exact bytes existed no later than the anchored Bitcoin block's time — priority/prior-art evidence for the spec, independent of any company, platform, or this machine.
- **Rule going forward** (per the adoption plan): every spec release gets stamped at release time; edit an artifact ⇒ its old proof still proves the old version; restamp the new one (`python output/anchors/lap_stamp.py <files>`).

*Note: the founding-document proof covers v0.4.2 as of stamping; the file is actively edited, so expect to restamp at the next version cut. The stable priority anchors are the LIPs, vectors, paper, and essay.*
