// Repository integrity canaries. Three external-tool corruption incidents taught us
// that silent character-substitution damage (e->"." , *->"D", digits 2/3->"1") and
// raw control bytes can land in files between sessions. This test makes every known
// corruption class a loud CI failure. Patterns are built by concatenation so this
// file never matches itself.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const TEXT_EXT = [".md", ".js", ".mjs", ".py", ".html", ".svg", ".json", ".txt"];
const SKIP_DIRS = new Set([".git", "node_modules", "out", "inbox", "test-vectors"]);
const SELF = "integrity.test.js";

const CANARIES = [
  ["digit-swap", new RegExp("101" + "6-0\\d")],                 // 2026 -> 1016 dates
  ["digit-swap", new RegExp("Ed1" + "5519")],                   // Ed25519 -> Ed15519
  ["digit-swap", new RegExp("RFC 941" + "1|RFC 696" + "1\\b")], // 9421/6962 -> 9411/6961
  ["digit-swap", new RegExp("Gemini 1" + "\\.7")],              // 3.7 -> 1.7
  ["e-swap", new RegExp("Past" + "\\. this|Sp" + "\\.c Hygi")], // e -> .
  ["star-swap", new RegExp("DD" + "Athar|D" + "existenceD")],   // * -> D
];

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) {
      if (!SKIP_DIRS.has(name)) yield* walk(p);
    } else if (TEXT_EXT.some((e) => name.endsWith(e)) && name !== SELF) {
      yield p;
    }
  }
}

test("no known corruption signatures anywhere in the repository", () => {
  const hits = [];
  for (const file of walk(ROOT)) {
    const text = readFileSync(file, "utf8");
    for (const [kind, re] of CANARIES) {
      if (re.test(text)) hits.push(`${kind}: ${file}`);
    }
  }
  assert.deepEqual(hits, [], `corruption canaries tripped:\n${hits.join("\n")}`);
});

test("no raw NUL bytes in any text file", () => {
  const hits = [];
  for (const file of walk(ROOT)) {
    if (readFileSync(file).includes(0)) hits.push(file);
  }
  assert.deepEqual(hits, [], `NUL bytes found in:\n${hits.join("\n")}`);
});
