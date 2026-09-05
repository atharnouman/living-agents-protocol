#!/usr/bin/env node
// lap-git — "Micro-Core for commits" (experimental LAP binding).
// An agent passport for commits, an envelope of permitted paths enforced BEFORE the
// commit exists, and a signature over the resulting tree that anyone can verify from
// the commit alone. Reuses the LAP reference library unchanged.
//
//   node lap-git.mjs init --agent <name> --scope <glob> [--scope <glob>...] [--days 90]
//   node lap-git.mjs check                 # are the staged paths inside the envelope?
//   node lap-git.mjs commit -m "<message>" # check, sign the tree, commit with LAP trailers
//   node lap-git.mjs verify [<rev-range>]  # verify passport, scope, and signature per commit
//   node lap-git.mjs selftest              # end-to-end demonstration in a temp repo
import { execSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync, mkdirSync, appendFileSync, rmSync } from "node:fs";
import { generateKeyPairSync, sign, createPrivateKey, createPublicKey, randomBytes } from "node:crypto";
import { basename, join } from "node:path";
import { tmpdir } from "node:os";
import {
  didKeyFromRawPublicKey, rawPublicKeyFromKeyObject, jcs, sha256Hex, b64urlEncode, b64urlDecode,
  publicKeyFromDid, verifyEd25519,
} from "../lap-reference/src/crypto-util.js";
import { signJws } from "../lap-reference/src/jws.js";
import { verifyMicroCorePassport } from "../lap-reference/src/microcore.js";
import { pathSubsumes } from "../lap-reference/src/algebra.js";

const git = (args, opts = {}) => execSync(`git ${args}`, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], ...opts }).trim();
const nowSec = () => Math.floor(Date.now() / 1000);
const repoRoot = () => git("rev-parse --show-toplevel");
const stateDir = () => join(repoRoot(), ".lap-git");
const repoAud = () => "git://" + basename(repoRoot());
const resourceFor = (path) => `${repoAud()}/${path}`;

// ---------- identity persistence (private keys stay out of git) ----------
function keypair() {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  return { publicKey, privateKey, did: didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey)) };
}
function rebuild(pkcs8Hex) {
  const privateKey = createPrivateKey({ key: Buffer.from(pkcs8Hex, "hex"), format: "der", type: "pkcs8" });
  const publicKey = createPublicKey(privateKey);
  return { publicKey, privateKey, did: didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey)) };
}
function loadIdentity() {
  const f = join(stateDir(), "keys.json");
  if (!existsSync(f)) throw new Error("not initialised — run: lap-git init --agent <name> --scope <glob>");
  const j = JSON.parse(readFileSync(f, "utf8"));
  return { principal: rebuild(j.principal), agent: rebuild(j.agent), passportJwt: readFileSync(join(stateDir(), "passport.jwt"), "utf8").trim() };
}
function ensureIgnored() {
  const gi = join(repoRoot(), ".gitignore");
  const line = ".lap-git/keys.json";
  const cur = existsSync(gi) ? readFileSync(gi, "utf8") : "";
  if (!cur.split(/\r?\n/).includes(line)) appendFileSync(gi, (cur.endsWith("\n") || cur === "" ? "" : "\n") + line + "\n");
}

// ---------- the signing base: what a LAP commit signature covers ----------
function signingBase({ tree, parent, passportJwt, paths }) {
  return [
    `"@tree": ${tree}`,
    `"@parent": ${parent}`,
    `"lap-passport-hash": sha256:${sha256Hex(passportJwt)}`,
    `"paths": ${jcs(paths)}`,
  ].join("\n");
}
const stagedPaths = () => git("diff --cached --name-only --diff-filter=ACMRD").split(/\r?\n/).filter(Boolean).sort();
const commitPaths = (c) => git(`diff-tree --root -r --name-only --no-commit-id ${c}`).split(/\r?\n/).filter(Boolean).sort();

function scopeCheck(envelope, paths) {
  if (!envelope.act.includes("data:write")) throw new Error("LAP_ERR_ACT: envelope lacks data:write");
  const res = Array.isArray(envelope.res) ? envelope.res : [envelope.res];
  return paths.map((p) => ({ path: p, ok: res.some((r) => { try { return pathSubsumes(r, resourceFor(p)); } catch { return false; } }) }));
}

// ---------- commands ----------
function init(argv) {
  const agentName = opt(argv, "--agent") || "agent";
  const scopes = optAll(argv, "--scope");
  if (scopes.length === 0) throw new Error("at least one --scope <glob> is required (e.g. --scope src/**)");
  const days = Number(opt(argv, "--days") || 90);
  mkdirSync(stateDir(), { recursive: true });
  const principal = keypair(), agent = keypair();
  const envelope = { act: ["data:write"], res: scopes.map((s) => resourceFor(s.replace(/^\/+/, ""))) };
  const t = nowSec();
  const passportJwt = signJws({
    iss: principal.did, sub: agent.did, aud: repoAud(), iat: t, exp: t + days * 86400,
    lap: { v: 0, proof_class: "self-asserted", agent_name: agentName, envelope },
  }, principal.privateKey, principal.did + "#key-1", "lap-microcore+jwt");
  writeFileSync(join(stateDir(), "keys.json"), JSON.stringify({
    principal: principal.privateKey.export({ format: "der", type: "pkcs8" }).toString("hex"),
    agent: agent.privateKey.export({ format: "der", type: "pkcs8" }).toString("hex"),
  }));
  writeFileSync(join(stateDir(), "passport.jwt"), passportJwt + "\n");
  ensureIgnored();
  console.log(`lap-git initialised for ${repoAud()}`);
  console.log(`  agent      ${agentName}  ${agent.did}`);
  console.log(`  principal  ${principal.did}`);
  console.log(`  envelope   act=data:write  res=${envelope.res.join(", ")}  (valid ${days} days)`);
  console.log(`  keys       .lap-git/keys.json (git-ignored — private)`);
}

function check({ quiet = false } = {}) {
  const { passportJwt } = loadIdentity();
  const payload = verifyMicroCorePassport(passportJwt, { expectedAud: repoAud(), now: nowSec() });
  const results = scopeCheck(payload.lap.envelope, stagedPaths());
  if (!quiet) for (const r of results) console.log(`  ${r.ok ? "✓" : "✗ OUT OF SCOPE"}  ${r.path}`);
  const bad = results.filter((r) => !r.ok);
  if (results.length === 0 && !quiet) console.log("  (nothing staged)");
  return { ok: bad.length === 0, results, payload };
}

function commit(argv) {
  const msg = opt(argv, "-m");
  if (!msg) throw new Error("commit requires -m \"<message>\"");
  const { agent, passportJwt } = loadIdentity();
  const { ok, results, payload } = check();
  if (results.length === 0) throw new Error("nothing staged");
  if (!ok) throw new Error("LAP_ERR_RES: refusing to commit — staged paths outside the agent's envelope");
  const tree = git("write-tree");
  let parent = "none"; try { parent = git("rev-parse --verify -q HEAD"); } catch { /* root commit */ }
  const paths = results.map((r) => r.path);
  const base = signingBase({ tree, parent, passportJwt, paths });
  const sig = b64urlEncode(sign(null, Buffer.from(base), agent.privateKey));
  const trailers = [`LAP-Agent: ${payload.sub}`, `LAP-Passport: ${passportJwt}`, `LAP-Signature: ${sig}`].join("\n");
  // Join into an existing trailer paragraph (e.g. Co-Authored-By) only when the message
  // already has one; a lone "feat: …" subject is NOT a trailer paragraph.
  const paras = msg.trimEnd().split(/\r?\n\s*\r?\n/);
  const last = paras[paras.length - 1].split(/\r?\n/);
  const endsWithTrailers = paras.length > 1 && last.every((l) => /^[A-Za-z-]+: /.test(l));
  const full = msg.trimEnd() + (endsWithTrailers ? "\n" : "\n\n") + trailers + "\n";
  const f = join(tmpdir(), `lap-git-msg-${randomBytes(4).toString("hex")}.txt`);
  writeFileSync(f, full);
  git(`commit -q -F "${f}"`);
  rmSync(f, { force: true });
  const head = git("rev-parse HEAD");
  // hash-chained local receipt
  const recPath = join(stateDir(), "recorder.jsonl");
  const prev = existsSync(recPath) ? (readFileSync(recPath, "utf8").trim().split("\n").pop() ?? "") : "";
  const prevHash = prev ? JSON.parse(prev).hash : "genesis";
  const entry = { ts: nowSec(), commit: head, tree, parent, paths, passport_hash: sha256Hex(passportJwt), sig, prev: prevHash };
  entry.hash = sha256Hex(jcs(entry));
  appendFileSync(recPath, JSON.stringify(entry) + "\n");
  console.log(`committed ${head.slice(0, 10)} — ${paths.length} path(s) in scope, tree signed by ${payload.sub.slice(0, 24)}…`);
}

function verify(argv) {
  const range = argv.find((a) => !a.startsWith("-")) || "HEAD";
  const max = range === "HEAD" ? "--max-count=25" : "";
  const commits = git(`rev-list ${max} ${range}`).split(/\r?\n/).filter(Boolean);
  let okN = 0, badN = 0, unsignedN = 0;
  for (const c of commits) {
    const body = git(`log -1 --format=%B ${c}`);
    const tr = (k) => (body.match(new RegExp(`^${k}: (.+)$`, "m")) || [])[1];
    const agentDid = tr("LAP-Agent"), jwt = tr("LAP-Passport"), sig = tr("LAP-Signature");
    const short = c.slice(0, 10), subject = git(`log -1 --format=%s ${c}`);
    if (!jwt || !sig) { unsignedN++; console.log(`  –  ${short}  ${subject}\n       no LAP trailer (human, or an unattributed agent)`); continue; }
    try {
      const authorTime = Number(git(`log -1 --format=%at ${c}`));
      const payload = verifyMicroCorePassport(jwt, { expectedAud: repoAud(), now: authorTime });
      if (agentDid !== payload.sub) throw new Error("LAP_ERR_AGENT: trailer agent ≠ passport subject");
      const tree = git(`log -1 --format=%T ${c}`);
      const parent = (git(`log -1 --format=%P ${c}`).split(" ")[0]) || "none";
      const paths = commitPaths(c);
      const base = signingBase({ tree, parent, passportJwt: jwt, paths });
      if (!verifyEd25519(publicKeyFromDid(payload.sub), Buffer.from(base), b64urlDecode(sig))) throw new Error("LAP_ERR_COMMIT_SIG: tree signature invalid");
      const out = scopeCheck(payload.lap.envelope, paths).filter((r) => !r.ok);
      if (out.length) throw new Error(`LAP_ERR_RES: ${out.length} path(s) outside envelope: ${out.map((r) => r.path).join(", ")}`);
      okN++;
      console.log(`  ✓  ${short}  ${subject}\n       agent ${payload.sub.slice(0, 24)}… (${payload.lap.agent_name ?? "agent"}) · principal-signed passport · ${paths.length} path(s) in scope · tree signature ✓`);
    } catch (e) { badN++; console.log(`  ✗  ${short}  ${subject}\n       ${e.message}`); }
  }
  console.log(`\n${okN} verified · ${badN} FAILED · ${unsignedN} unsigned`);
  if (badN) process.exitCode = 1;
}

function selftest() {
  const dir = join(tmpdir(), `lap-git-selftest-${randomBytes(4).toString("hex")}`);
  mkdirSync(join(dir, "src"), { recursive: true }); mkdirSync(join(dir, "docs"), { recursive: true });
  process.chdir(dir);
  git("init -q -b main"); git('config user.name "LAP selftest"'); git('config user.email "selftest@example.com"');
  console.log(`\n=== lap-git self-test in ${dir} ===\n`);
  console.log("1) init: agent may write src/** only");
  init(["--agent", "demo-coder", "--scope", "src/**"]);
  writeFileSync(join(dir, "src", "a.txt"), "hello\n"); git("add src/a.txt");
  console.log("\n2) in-scope commit (src/a.txt) — should succeed");
  commit(["-m", "feat: add src/a.txt"]);
  writeFileSync(join(dir, "docs", "b.md"), "# out of scope\n"); git("add docs/b.md");
  console.log("\n3) out-of-scope commit attempt (docs/b.md) — should be REFUSED before the commit exists");
  let refused = false;
  try { commit(["-m", "docs: sneak a change outside scope"]); } catch (e) { refused = true; console.log(`  refused: ${e.message}`); }
  git("reset -q docs/b.md");
  console.log("\n4) a plain unattributed commit (no LAP trailer) — should show as unsigned");
  git('commit -q --allow-empty -m "chore: an unattributed commit"');
  console.log("\n5) tamper: flip one character of the signature in the signed commit — should FAIL verification");
  writeFileSync(join(dir, "src", "c.txt"), "more\n"); git("add src/c.txt"); commit(["-m", "feat: add src/c.txt"]);
  const body = git("log -1 --format=%B");
  // Flip the FIRST signature character: it carries six data bits, so the decoded bytes always
  // change. (Flipping the last character made this test flaky: the final base64url character
  // carries only two data bits, and 'A'->'B' touched padding bits alone.)
  const tampered = body.replace(/^(LAP-Signature: )([A-Za-z0-9_-])/m, (m, a, ch) => a + (ch === "A" ? "B" : "A"));
  const sigText = (b) => /^LAP-Signature: (\S+)/m.exec(b)[1];
  if (tampered === body || b64urlDecode(sigText(tampered)).equals(b64urlDecode(sigText(body)))) throw new Error("selftest: tamper did not change the signature bytes");
  const f = join(tmpdir(), "lap-git-tamper.txt"); writeFileSync(f, tampered); git(`commit -q --amend -F "${f}"`); rmSync(f, { force: true });
  console.log("\n6) verify the history\n");
  verify(["HEAD"]);
  const pass = refused && process.exitCode === 1;
  console.log(`\nSELF-TEST ${pass ? "PASSED" : "FAILED"}: in-scope commit signed ✓, out-of-scope refused ${refused ? "✓" : "✗"}, unattributed commit flagged, tampered signature caught ${process.exitCode === 1 ? "✓" : "✗"}`);
  process.exitCode = pass ? 0 : 1;
}

// ---------- tiny arg helpers ----------
function opt(argv, k) { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; }
function optAll(argv, k) { return argv.map((a, i) => (a === k ? argv[i + 1] : null)).filter(Boolean); }

const COMMANDS = { init, check, commit, verify, selftest };
const [cmd, ...rest] = process.argv.slice(2);
try {
  if (cmd in COMMANDS) COMMANDS[cmd](rest);
  else console.log("usage: lap-git <init|check|commit|verify|selftest> …");
} catch (e) { console.error(`lap-git: ${e.message}`); process.exit(1); }
