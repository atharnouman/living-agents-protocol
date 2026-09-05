// Register an agent's Genesis Record in the PUBLIC Sigstore Rekor transparency log,
// then verify the result with LAP's own RFC 6962 code — turning "registration is
// self-attested" into "registered in an append-only public log anyone can audit."
//
//   node register-genesis.mjs                 # mint a demo agent, register it, verify, print the public URL
//   node register-genesis.mjs --verify <idx>  # re-verify any Rekor entry's inclusion proof + Rekor signature
//
// Entries are permanent and public. This demo logs only DIDs, hashes, and timestamps —
// never personal data (spec §14.5: principal references belong behind salted commitments).
import { generateKeyPairSync } from "node:crypto";
import { writeFileSync, mkdirSync } from "node:fs";
import { didKeyFromRawPublicKey, rawPublicKeyFromKeyObject, sha256Hex, jcs } from "../lap-reference/src/crypto-util.js";
import { buildGenesisEntry, submitEntry, fetchEntry, fetchRekorPublicKey, verifyEntry, searchUrl } from "../lap-reference/src/rekor.js";

const say = (m) => console.log(m);
const kp = () => { const { publicKey, privateKey } = generateKeyPairSync("ed25519"); return { publicKey, privateKey, did: didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey)) }; };

if (process.argv[2] === "--verify") {
  const idx = process.argv[3];
  if (!idx) { console.error("usage: node register-genesis.mjs --verify <logIndex|uuid>"); process.exit(1); }
  const e = await fetchEntry(idx);
  const v = verifyEntry(e, { rekorPublicKeyPem: await fetchRekorPublicKey() });
  say(`\nRekor entry ${e.logIndex}: inclusion proof ✓ (tree size ${v.treeSize.toLocaleString()}), Rekor signed timestamp ✓`);
  say(`  logged principal: ${v.principalDid}\n  logged genesis hash: sha256:${v.loggedHash}\n  ${v.url}`);
  say(`  (substance — that the hash is a specific genesis record — is verified when the expected record is supplied)`);
  process.exit(0);
}

say("\n=== LAP GENESIS REGISTRATION — public transparency log (Sigstore Rekor) ===\n");
const principal = kp(), agent = kp();
const constitution = "Constitution of a LAP reference demo agent: act only within the signed envelope; escalate on ambiguity.\n";
const genesis = {
  v: "lap-genesis-v0", agent: agent.did, principal: principal.did, spawner: null, generation: 1,
  constitution_sha256: sha256Hex(constitution), created_at: Math.floor(Date.now() / 1000), purpose: "lap-reference-demo",
};
say(`  agent      ${agent.did}`);
say(`  principal  ${principal.did}`);
say(`  genesis    sha256:${sha256Hex(jcs(genesis))}  (canonical JSON, principal-signed)\n`);

say("  submitting to https://rekor.sigstore.dev …");
let entry = await submitEntry(buildGenesisEntry(genesis, principal.privateKey));
if (!entry.verification?.inclusionProof) { await new Promise((r) => setTimeout(r, 3000)); entry = await fetchEntry(entry.uuid); }
say(`  LOGGED  index ${entry.logIndex}  integrated ${new Date(entry.integratedTime * 1000).toISOString()}`);
say(`  public record: ${searchUrl(entry.logIndex)}\n`);

say("  verifying with LAP's own code (no trust in the log's answer):");
const rekorKey = await fetchRekorPublicKey();
const v = verifyEntry(entry, { expectedPrincipalDid: principal.did, expectedGenesis: genesis, rekorPublicKeyPem: rekorKey });
say(`    inclusion proof   ✓  leaf → root over ${entry.verification.inclusionProof.hashes.length} hashes, tree size ${v.treeSize.toLocaleString()} (RFC 6962)`);
say(`    substance         ✓  logged hash = this genesis; logged key = this principal; signature verifies`);
say(`    Rekor timestamp   ✓  signed entry timestamp verifies under Rekor's published key`);

mkdirSync(new URL("./out/", import.meta.url), { recursive: true });
writeFileSync(new URL("./out/rekor-entry.json", import.meta.url), JSON.stringify({ genesis, principalDid: principal.did, entry, rekorPublicKeyPem: rekorKey }, null, 2) + "\n");
say(`\n  Birth witnessed, not self-asserted. Saved to lap-demo/out/rekor-entry.json.`);
say(`  Re-verify anytime, from any machine:  node register-genesis.mjs --verify ${entry.logIndex}\n`);
