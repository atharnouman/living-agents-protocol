# LAP — Bitcoin Anchors (OpenTimestamps)

*Current stamping: **2026-09-08, v0.4.9** — 4 independent OpenTimestamps calendars. Superseded hashes remain valid for their own bytes in git history.*

| SHA-256 | Artifact |
|---|---|
| `dde439517c0d0b61007f3ed4bc4230b1f5f2086bc70d0b7f4b124138037cb7e6` | LAP-founding-document.md (v0.4.9, fuzzing round) |
| `90986f3e0f93d6276df44dda80f697568c828fa4d9cd20bb6b423b6254dbb140` | lip/LIP-1-agent-passport-draft.md (v0.4.8, canonical base64url MUST) |
| `81747e9475cc9c4125934dea4f2d9d83854f1fdfe997ea879d2abf5c172e88ac` | lip/LIP-2-meet-draft.md |
| `0ba1d48d3062b67c4537d85ece0121e02652c7abd8a71644f6db92c1f9bb97e1` | lip/LIP-3-scope-algebra-v0-draft.md (v0.3, fuzzed) |
| `77d78441a3a4d7aec15a443659b03edd0925b71e987ff121c09f8b664779e210` | lip/LIP-4-micro-core-draft.md (F1-F6 hardened; v0.4.8 canonical encoding) |
| `b389bf8335e928609c9cbdc7828d3e23c35486ece607527503cacc1adbf28fb5` | lip/test-vectors/vectors.json (unchanged since first stamp) |
| `563deaa95bb6f4bef1fba1974abb6a36b6159026341a3d2c0404afd90485ab48` | LAP-position-paper.md (v1.2-draft) |
| `9b41bf73e0d6ad92da34a4d9b65404fdf11cd4e7f1ea246eef917f53449d78bf` | LAP-essay.md (September 2026, Rekor sentence) |
| `bdf47455735673636bf1c8e9f2ede8d2b58a9fabb2a3ebd0d0afdd26bc8c591c` | ../README.md (v0.4.9, fuzzing round + threat model) |

## Status and how to use

- **Now**: proofs are *pending calendar attestations* — the calendars fold these digests into their next Bitcoin aggregation transaction (typically within hours). Until then the honest claim is "OpenTimestamps-stamped, pending Bitcoin confirmation."
- **Upgrade to full on-chain proof** (any later time, any machine with an OTS tool): `ots upgrade <file>.ots` then `ots verify <file>.ots` — verification then names the Bitcoin block committing to the file's existence. (The stock `ots` CLI is broken on Windows; stamping here uses `lap_stamp.py`.)
- **What a proof establishes**: these exact bytes existed no later than the anchored block's time — priority evidence independent of any company, platform, or machine.
- **Prior generations**: the first stamping (2026-08-29, pre-freeze — v0.4.2-era spec, pre-round-3 LIPs) is preserved in **git history** (initial commit `bb77edf`): those `.ots` files still prove those exact prior versions. Superseded proofs are never invalid — they just prove older bytes.
- **Rule**: every release freeze gets restamped (`python output/anchors/lap_stamp.py <files>`); stamp *after* the last edit, never before.
