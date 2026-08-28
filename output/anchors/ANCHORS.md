# LAP — Bitcoin Anchors (OpenTimestamps)

*Current stamping: **2026-08-29, release freeze v0.4.3** — submitted to 4 independent public calendar servers (a.pool.opentimestamps.org, b.pool.opentimestamps.org, a.pool.eternitywall.com, ots.btc.catallaxy.com). Each `.ots` proof sits beside its artifact. This is spec §19's pattern in miniature: calendars Merkle-aggregate thousands of digests into one Bitcoin transaction — no per-file fees, no personal data on-chain.*

| SHA-256 | Artifact |
|---|---|
| `2bf1c2ee8701eb3ac6a26aa9fc3c04b8e5f6463a8da4ae5a4595ccba5ccf84f4` | LAP-founding-document.md (v0.4.3) |
| `acbc13ecfe9926bdbfb94d1db8a458dcd2e88c6b7f2e311017625fed041d2dca` | lip/LIP-1-agent-passport-draft.md |
| `81747e9475cc9c4125934dea4f2d9d83854f1fdfe997ea879d2abf5c172e88ac` | lip/LIP-2-meet-draft.md |
| `2b7f564a6f68dabf240d2d100136928341027da1985efd2fcdbc902e78c37ccb` | lip/LIP-3-scope-algebra-v0-draft.md (unchanged since first stamp) |
| `205060cb70efbebdea6fc75baa7db621027f96d1cb355926fff8bbe59be24fa5` | lip/LIP-4-micro-core-draft.md |
| `b389bf8335e928609c9cbdc7828d3e23c35486ece607527503cacc1adbf28fb5` | lip/test-vectors/vectors.json (unchanged since first stamp) |
| `dc90f5425825829de5d2d3a746b045a3f94771ce5e7a2393a1d75d32ad07c0b2` | LAP-position-paper.md (v1.0-draft) |
| `ec1312916569715dd020ac1f749870f5860a0d7e230f477e314dbad78692f124` | LAP-essay.md |
| `4c258ddf265784865c410fd6227f92ebb83e43950724fa8cfe3d4903594cc00d` | ../README.md |

## Status and how to use

- **Now**: proofs are *pending calendar attestations* — the calendars fold these digests into their next Bitcoin aggregation transaction (typically within hours). Until then the honest claim is "OpenTimestamps-stamped, pending Bitcoin confirmation."
- **Upgrade to full on-chain proof** (any later time, any machine with an OTS tool): `ots upgrade <file>.ots` then `ots verify <file>.ots` — verification then names the Bitcoin block committing to the file's existence. (The stock `ots` CLI is broken on Windows; stamping here uses `lap_stamp.py`.)
- **What a proof establishes**: these exact bytes existed no later than the anchored block's time — priority evidence independent of any company, platform, or machine.
- **Prior generations**: the first stamping (2026-08-29, pre-freeze — v0.4.2-era spec, pre-round-3 LIPs) is preserved in **git history** (initial commit `bb77edf`): those `.ots` files still prove those exact prior versions. Superseded proofs are never invalid — they just prove older bytes.
- **Rule**: every release freeze gets restamped (`python output/anchors/lap_stamp.py <files>`); stamp *after* the last edit, never before.
