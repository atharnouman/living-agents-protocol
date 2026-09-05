# LAP — Bitcoin Anchors (OpenTimestamps)

*Current stamping: **2026-09-05, v0.4.7** — 4 independent OpenTimestamps calendars. Superseded hashes remain valid for their own bytes in git history.*

| SHA-256 | Artifact |
|---|---|
| `c920cc71c7d9f48f94e6ed55522b091299fd4d63e8753190b2f1c5bd0b9c8f20` | LAP-founding-document.md (v0.4.7, Rekor registration) |
| `acbc13ecfe9926bdbfb94d1db8a458dcd2e88c6b7f2e311017625fed041d2dca` | lip/LIP-1-agent-passport-draft.md |
| `81747e9475cc9c4125934dea4f2d9d83854f1fdfe997ea879d2abf5c172e88ac` | lip/LIP-2-meet-draft.md |
| `98e49cf19b988673723c3a7d051cefcd3c7dc0d94b90dfd492da72d990226f1f` | lip/LIP-3-scope-algebra-v0-draft.md (v0.2, F7/F8/F9/F10 hardened) |
| `71506b659e94593c418699cb0011ec04a77f5049a3835af3d84406a4cb34da0d` | lip/LIP-4-micro-core-draft.md (F1/F2/F3/F4/F5/F6 hardened) |
| `b389bf8335e928609c9cbdc7828d3e23c35486ece607527503cacc1adbf28fb5` | lip/test-vectors/vectors.json (unchanged since first stamp) |
| `dc90f5425825829de5d2d3a746b045a3f94771ce5e7a2393a1d75d32ad07c0b2` | LAP-position-paper.md (v1.0-draft) |
| `f4ba5d94d8e183b1e212fa2d82e19dfab628558f1f33c8c11a764487dedc6501` | LAP-essay.md (post-ready, live demo link) |
| `5a283accb31243910b40449848bc64f5c101d04dfcecca6f482ecee7d9339426` | ../README.md (v0.4.7, Rekor + Codespaces) |

## Status and how to use

- **Now**: proofs are *pending calendar attestations* — the calendars fold these digests into their next Bitcoin aggregation transaction (typically within hours). Until then the honest claim is "OpenTimestamps-stamped, pending Bitcoin confirmation."
- **Upgrade to full on-chain proof** (any later time, any machine with an OTS tool): `ots upgrade <file>.ots` then `ots verify <file>.ots` — verification then names the Bitcoin block committing to the file's existence. (The stock `ots` CLI is broken on Windows; stamping here uses `lap_stamp.py`.)
- **What a proof establishes**: these exact bytes existed no later than the anchored block's time — priority evidence independent of any company, platform, or machine.
- **Prior generations**: the first stamping (2026-08-29, pre-freeze — v0.4.2-era spec, pre-round-3 LIPs) is preserved in **git history** (initial commit `bb77edf`): those `.ots` files still prove those exact prior versions. Superseded proofs are never invalid — they just prove older bytes.
- **Rule**: every release freeze gets restamped (`python output/anchors/lap_stamp.py <files>`); stamp *after* the last edit, never before.
