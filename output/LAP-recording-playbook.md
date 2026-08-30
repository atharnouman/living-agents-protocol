# LAP Demo — Recording Playbook

Everything you need to record a professional 60–75s demo, in three formats. You press record; the pieces below make the take land on the first try.

---

## The three assets (pick one or all)

| Asset | What to record | Best for |
|---|---|---|
| **A. Terminal MP4** | `node conductor.mjs --present` in a styled terminal | developer audiences, GitHub, HN — reads as "real system" |
| **B. Visual MP4** | the browser visualization playing | LinkedIn, investors, a landing hero |
| **C. asciinema cast** | already generated: `output/lap-overnight.cast` | embeddable, developer-native, no video hosting |

---

## A. Terminal recording (the credibility take)

### 1. Style the terminal (Windows Terminal — one-time)

Open **Windows Terminal → Settings → “Open JSON file”** and merge this. It sets a clean dark background, a crisp mono font, generous padding, and colors tuned to the demo's output (yellow = conductor, cyan = buyer, magenta = seller):

```json
{
  "profiles": {
    "defaults": {
      "colorScheme": "LAP Dark",
      "font": { "face": "Cascadia Mono", "size": 15, "weight": "medium" },
      "padding": "18",
      "cursorShape": "filledBox",
      "useAcrylic": false,
      "opacity": 100,
      "scrollbarState": "hidden"
    }
  },
  "schemes": [
    {
      "name": "LAP Dark",
      "background": "#080B13", "foreground": "#E4EBF8",
      "black": "#0D1220", "red": "#F06D6D", "green": "#43D9A3", "yellow": "#F2B44B",
      "blue": "#5F9BFF", "purple": "#B98BE0", "cyan": "#63B6E6", "white": "#E4EBF8",
      "brightBlack": "#7E8BAB", "brightRed": "#F06D6D", "brightGreen": "#43D9A3", "brightYellow": "#F2B44B",
      "brightBlue": "#5F9BFF", "brightPurple": "#B98BE0", "brightCyan": "#63B6E6", "brightWhite": "#FFFFFF",
      "cursorColor": "#43D9A3", "selectionBackground": "#233048"
    }
  ]
}
```

### 2. Size the window
- **Font size 15–18** (bump to 18 if recording at 1080p — bigger reads better on video).
- **Window ~118 columns × 34 rows.** Drag the window wide enough that the long lines don't wrap (the demo lines are up to ~115 chars). Quick check: the header rule `=== LAP OVERNIGHT DEMO … ===` should sit on one line.
- **Maximize, then clear**: run `cls` (PowerShell) / `clear` so the screen is empty before you start recording.

### 3. Record

**Option 1 — Snipping Tool (built into Windows 11):** open Snipping Tool → click the **camcorder / Record** icon → drag a box around the terminal → **Start** → run the command → **Stop** → Save as MP4.

**Option 2 — Xbox Game Bar (fastest):** click the terminal to focus it → **`Win + Alt + R`** to start → run the command → **`Win + Alt + R`** to stop. The MP4 lands in `Videos\Captures`.

### 4. The command
```
cd E:\LivingAIAgents\lap-demo\net
node conductor.mjs --present
```
(≈70 seconds paced. Drop `--present` for the fast version. Then optionally `node verify.mjs` for the morning-replay beat.)

### 5. Shot list (what happens, ~70s)

| ~time | On screen | The point |
|---|---|---|
| 0–5s | `=== two real processes …` + `[seller] listening…` | two separate OS processes start |
| 5–20s | `[buyer]` MEET HAIL/PROVE, both DIDs, "verified each other's Ed25519 signatures" | strangers verify each other over a real socket |
| 20–30s | CHARTER (reservation), BIND (seller countersignature verified: true) → ACTIVE | limits disclosed, contract dual-signed |
| 30–38s | `ORDER A-001 … receipt signature✓` | a real signed payment over HTTP |
| 38–44s | **`*** killing the seller process now (real SIGKILL) ***`** | the crash — a genuine process kill |
| 44–52s | `no pulse (connection refused)` → **`SUSPENDED`** → **`HELD`** | authority freezes automatically; nothing moves |
| 52–62s | `seller RESTARTED … same DID` → `authority restored` → `ORDER A-002 … ✓` | recovery; a restart is a nap, not a death |
| 62–70s | `Session closed … 0 escalations` (+ `verify.mjs`: all receipts ✓) | the morning proof |

**The money moment to make sure you capture:** the SIGKILL line, immediately followed by SUSPENDED/HELD, immediately followed by the automatic restore. That 20-second stretch is the entire pitch.

---

## B. Visual recording (the polished take)

Open the visualization (published artifact, or `output/lap-demo-visual.html` locally). It auto-plays in ~35s; the **Replay** button restarts it and **Speed** cycles 1× / 1.6× / 2.4×.

- Record the **browser tab region only** (Snipping Tool box or Game Bar on the browser window).
- Put the browser in a clean window (hide bookmarks bar; `F11` full-screen is ideal), light-off room-tone not needed — it's silent.
- Hit **Replay**, then start recording so the run begins clean.
- The choreography mirrors the shot list above: watch for Bob's panel going **OFFLINE red** and the wire breaking, Alice flipping to **DEGRADED amber**, the A-002 chip going **HELD**, then everything returning green with the **budget meter** climbing to $72 and the **✓ Morning replay** badge.

---

## C. asciinema cast (embeddable, zero video)

Already generated at `output/lap-overnight.cast` (a real recording — real output, real timings, colors preserved).

- **Play locally:** `asciinema play output/lap-overnight.cast` (install: `pip install asciinema`).
- **Share:** `asciinema upload output/lap-overnight.cast` → gives an embeddable player URL for the README or a blog post.
- **Regenerate** anytime (e.g., after tuning pace): `cd lap-demo/net && node record-cast.mjs`.

---

## Export & polish (any format)

- Target **1920×1080, 30fps, MP4 (H.264)**. Both Snipping Tool and Game Bar already output this.
- Trim dead air at the head/tail (any video editor, or the free **Clipchamp** built into Windows 11).
- If you want captions, add three: *"Two agents. One crashes. No human wakes up."* at the SIGKILL, and *"Authority restored automatically"* at the recovery, and *"Every receipt verified"* at the end.
- Keep it **silent or lightly scored** — the on-screen text carries it; a voiceover isn't needed for the technical audience.

Honest framing to keep with any post: real Ed25519 signatures, real sockets, a real crash and recovery; registration is self-attested and the payment rail mocked for the demo — stated plainly, because the project's whole brand is verified honesty.
