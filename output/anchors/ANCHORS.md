# LAP — Bitcoin Anchors (OpenTimestamps)

*Current stamping: **2026-09-08, v0.4.10** (essay, README and the MCP extension draft re-stamped 2026-10-08; essay and README 2026-10-16; README, both LIP-4 drafts and the new cap vectors re-stamped 2026-10-17 for libraries 0.4.13, all confirmed 2026-10-21; README, both LIP-4 drafts and the new replay vectors re-stamped 2026-10-28 for libraries 0.4.14, confirmed the same day) — 4 independent OpenTimestamps calendars. **Confirmed on Bitcoin (every proof):** every proof carries block-header attestations, each verified against a public block explorer with `lap_upgrade.py`; the blocks are listed below. Superseded hashes remain valid for their own bytes in git history.*

| SHA-256 | Artifact |
|---|---|
| `50e64bdca86bdbc62ae3783f19804552608f51da6233bacad9aa6aad9f2fd50d` | LAP-founding-document.md (v0.4.10) |
| `90986f3e0f93d6276df44dda80f697568c828fa4d9cd20bb6b423b6254dbb140` | lip/LIP-1-agent-passport-draft.md (v0.4.8, canonical base64url MUST) |
| `81747e9475cc9c4125934dea4f2d9d83854f1fdfe997ea879d2abf5c172e88ac` | lip/LIP-2-meet-draft.md |
| `a0d34f0fc066af9447a287b60e31a55d0f6e36670fdc20d7925b48b1985e8ffd` | lip/LIP-3-scope-algebra-v0-draft.md (v0.4, review pass) |
| `827d752e6c6035c82cb415e20921d5dbc198c87d26d65a2dc2d80c0951858d05` | lip/LIP-4-micro-core-draft.md (v0.4.10 hardening; errata 2026-10-17 on the amount rule and 2026-10-28 on recognition before authority, §2 step 3; re-stamped 2026-10-28, confirmed) |
| `b389bf8335e928609c9cbdc7828d3e23c35486ece607527503cacc1adbf28fb5` | lip/test-vectors/vectors.json (unchanged since first stamp) |
| `85df4217bc1cd7c675308c284f6a286fc9b6c0dceebfde5ff8d89c8bbbcec106` | lip/test-vectors/microcore-cap-vectors.json (25 cap and amount vectors, first stamped 2026-10-17, confirmed) |
| `e83f7646ca2458e37bad85bd266e340881e7e06d78a66e8732600b10ed434ebf` | lip/test-vectors/microcore-replay-vectors.json (18 stateful replay vectors, first stamped 2026-10-28 and restamped the same day after the third review, confirmed) |
| `563deaa95bb6f4bef1fba1974abb6a36b6159026341a3d2c0404afd90485ab48` | LAP-position-paper.md (v1.2-draft) |
| `4bf89b8a5b1a188d52584a20721881113ab7d2610fa2d4c60d44a29bb7f652ef` | LAP-essay.md (October 2026 byline; corrected 2026-10-16 per the A2A review, re-stamped, confirmed) |
| `67714e645946e56be14540a2347b5aa8707b981bb47664d1170d54aa0794e1db` | ../README.md as released with 0.4.14 (v0.4.10 spec; libraries 0.4.14; Node 88/88, Python 199/199; the 28 October status sentence; re-stamped 2026-10-28 (second stamping of the day), confirmed) |
| `ee8db683fa6bb0ad7721f481cd1bffe2d69e7b8aab69936b8274ea16dffdb9cf` | lip/LIP-4-mcp-extension-draft.md (v0.4 draft, 2026-10-28: recognition before the envelope, tenant scope, request identity, two refusal codes, second pass after the third review; re-stamped 2026-10-28, confirmed) |

## Status and how to use

- **Status (2026-10-28)**: all confirmed. The four proofs stamped 2026-10-28 for libraries 0.4.14 (README, both LIP-4 drafts, the replay vectors) were upgraded and verified the same day (each attested 32 bytes equal the block's merkle root per blockstream.info): blocks 973452 and 973453, earliest 2026-10-27 20:51 UTC (the stamps were made in the first hours of 28 October Pakistan time, the evening of 27 October UTC). Three of the four calendars had published their attestations by then; the fourth (catallaxy) can be added later with the same command. Everything earlier was confirmed on 2026-10-21.
- **Status (2026-10-21)**: all confirmed. The five proofs left pending on 2026-10-16 and 2026-10-17 were upgraded and verified on 2026-10-21 (each attested 32 bytes equal the block's merkle root per blockstream.info): README.md, LIP-4 Micro-Core, the MCP extension draft and the cap vectors in blocks 971814, 971817, 971835, 971845 (earliest 2026-10-17 05:43 UTC); the essay in blocks 971625 and 971630 (earliest 2026-10-15 21:23 UTC). Everything earlier was confirmed on 2026-10-16.
- **Upgrade / verify yourself** (any machine, no Bitcoin node): `python output/anchors/lap_upgrade.py` upgrades every proof and checks each attestation against a public block explorer; `--verify-only` checks without writing. The stock `ots upgrade` / `ots verify` work too (the `ots` CLI is broken on Windows, which is why stamping uses `lap_stamp.py` and upgrading uses `lap_upgrade.py`).
- **What a proof establishes**: these exact bytes existed no later than the anchored block's time — priority evidence independent of any company, platform, or machine.
- **Prior generations**: the first stamping (2026-08-29, pre-freeze — v0.4.2-era spec, pre-round-3 LIPs) is preserved in **git history** (initial commit `bb77edf`): those `.ots` files still prove those exact prior versions. Superseded proofs are never invalid — they just prove older bytes.
- **Rule**: every release freeze gets restamped (`python output/anchors/lap_stamp.py <files>`); stamp *after* the last edit, never before.
