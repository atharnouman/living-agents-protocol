# LAP — Bitcoin Anchors (OpenTimestamps)

*Current stamping: **2026-09-08, v0.4.10** (essay, README and the MCP extension draft re-stamped 2026-10-08) — 4 independent OpenTimestamps calendars. **Confirmed on Bitcoin (all ten proofs; the three stamped on 2026-10-08 confirmed on upgrade, 2026-10-16):** every proof now carries block-header attestations, each verified against a public block explorer with `lap_upgrade.py`; the blocks are listed below. Superseded hashes remain valid for their own bytes in git history.*

| SHA-256 | Artifact |
|---|---|
| `50e64bdca86bdbc62ae3783f19804552608f51da6233bacad9aa6aad9f2fd50d` | LAP-founding-document.md (v0.4.10) |
| `90986f3e0f93d6276df44dda80f697568c828fa4d9cd20bb6b423b6254dbb140` | lip/LIP-1-agent-passport-draft.md (v0.4.8, canonical base64url MUST) |
| `81747e9475cc9c4125934dea4f2d9d83854f1fdfe997ea879d2abf5c172e88ac` | lip/LIP-2-meet-draft.md |
| `a0d34f0fc066af9447a287b60e31a55d0f6e36670fdc20d7925b48b1985e8ffd` | lip/LIP-3-scope-algebra-v0-draft.md (v0.4, review pass) |
| `1d022cb5ce84af88c6e07769a0893744e5772362035c3f8155a5edab362d03cd` | lip/LIP-4-micro-core-draft.md (v0.4.10 hardening) |
| `b389bf8335e928609c9cbdc7828d3e23c35486ece607527503cacc1adbf28fb5` | lip/test-vectors/vectors.json (unchanged since first stamp) |
| `563deaa95bb6f4bef1fba1974abb6a36b6159026341a3d2c0404afd90485ab48` | LAP-position-paper.md (v1.2-draft) |
| `4bf89b8a5b1a188d52584a20721881113ab7d2610fa2d4c60d44a29bb7f652ef` | LAP-essay.md (October 2026 byline; corrected 2026-10-16 per the A2A review, re-stamped, pending) |
| `3b47a1c2709aef142c97cffa25c239093e28933ab5834566a7c2d82c6ab547b6` | ../README.md (v0.4.10 spec; packages npm 0.4.11, PyPI 0.4.12; Python 108/108 after the audit-record interop test; re-stamped 2026-10-16, pending) |
| `c7f67a4e2734e33f63242ccd45530e663030202257aaf33c28d121620814c6f6` | lip/LIP-4-mcp-extension-draft.md (v0.1 draft, 2026-10-08; confirmed) |

## Status and how to use

- **Status (2026-10-16)**: all confirmed. Each `.ots` was upgraded from the calendars' pending markers to Bitcoin block-header attestations and verified (the attested 32 bytes equal the block's merkle root per blockstream.info):
  - founding document, LIP-3, LIP-4 (and the September README proof, now superseded) — blocks 965977, 965979, 966021, 966041 (earliest 2026-09-07 21:53 UTC)
  - position paper — blocks 965968, 965969, 965971, 965974 (earliest 2026-09-07 20:07 UTC)
  - LIP-1 — blocks 965661, 965689, 965708 (earliest 2026-09-05 20:14 UTC)
  - LIP-2, test vectors — blocks 964477, 964488, 964496, 964513 (earliest 2026-08-28 20:15 UTC)
  - README.md (final 2026-10-08 edit) and the MCP extension draft v0.1 — blocks 970409, 970411, 970412, 970415; essay (October byline) — blocks 970383, 970387, 970412, 970415 (earliest 2026-10-07 20:00 UTC; upgraded and verified 2026-10-16; the README and essay proofs among these are kept in git history, superseded by the 2026-10-16 re-stamps, which are pending)
  A freshly stamped proof is a *pending calendar attestation* until the calendars fold it into a Bitcoin transaction (typically within a day); until then the honest claim for that file is "OpenTimestamps-stamped, pending Bitcoin confirmation."
- **Upgrade / verify yourself** (any machine, no Bitcoin node): `python output/anchors/lap_upgrade.py` upgrades every proof and checks each attestation against a public block explorer; `--verify-only` checks without writing. The stock `ots upgrade` / `ots verify` work too (the `ots` CLI is broken on Windows, which is why stamping uses `lap_stamp.py` and upgrading uses `lap_upgrade.py`).
- **What a proof establishes**: these exact bytes existed no later than the anchored block's time — priority evidence independent of any company, platform, or machine.
- **Prior generations**: the first stamping (2026-08-29, pre-freeze — v0.4.2-era spec, pre-round-3 LIPs) is preserved in **git history** (initial commit `bb77edf`): those `.ots` files still prove those exact prior versions. Superseded proofs are never invalid — they just prove older bytes.
- **Rule**: every release freeze gets restamped (`python output/anchors/lap_stamp.py <files>`); stamp *after* the last edit, never before.
