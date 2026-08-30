// Records a real asciinema v2 .cast of the paced networked demo — genuine output,
// genuine timings, ANSI colours preserved. Run: node record-cast.mjs
// Output: ../../output/lap-overnight.cast  (play: `asciinema play …`, or upload to asciinema.org)
import { spawn } from "node:child_process";
import readline from "node:readline";
import { writeFileSync, mkdirSync } from "node:fs";

const start = Date.now();
const events = [];
const child = spawn(process.execPath, ["conductor.mjs", "--present"], { cwd: new URL(".", import.meta.url) });

readline.createInterface({ input: child.stdout }).on("line", (line) => {
  events.push([(Date.now() - start) / 1000, "o", line + "\r\n"]);
});
readline.createInterface({ input: child.stderr }).on("line", (line) => {
  events.push([(Date.now() - start) / 1000, "o", line + "\r\n"]);
});

child.on("exit", () => {
  const header = {
    version: 2, width: 118, height: 34, timestamp: Math.floor(start / 1000),
    env: { TERM: "xterm-256color", SHELL: "/bin/bash" },
    title: "Living Agents Protocol — overnight demo (two processes, real HTTP)",
  };
  const out = new URL("../../output/lap-overnight.cast", import.meta.url);
  mkdirSync(new URL("../../output/", import.meta.url), { recursive: true });
  writeFileSync(out, [JSON.stringify(header), ...events.map((e) => JSON.stringify(e))].join("\n") + "\n");
  console.log(`\nwrote output/lap-overnight.cast — ${events.length} frames, ${((Date.now() - start) / 1000).toFixed(1)}s`);
});
