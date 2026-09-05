// Sigstore Rekor binding — offline tests against a REAL public-log entry (fixture
// captured from rekor.sigstore.dev), plus a live round-trip gated behind LAP_REKOR_LIVE=1.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { randomBytes, generateKeyPairSync } from "node:crypto";
import { MerkleLog } from "../src/merkle-log.js";
import { didKeyFromRawPublicKey, rawPublicKeyFromKeyObject, sha256Hex, jcs } from "../src/crypto-util.js";
import {
  rootFromInclusionProof, verifyEntry, buildGenesisEntry, submitEntry, fetchEntry, fetchRekorPublicKey,
} from "../src/rekor.js";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/rekor-genesis.json", import.meta.url), "utf8"));

test("rekor: root reconstruction agrees with LAP's own Merkle proofs for every (index, size), sizes 1..48", () => {
  let checks = 0;
  for (let size = 1; size <= 48; size++) {
    const log = new MerkleLog("t");
    for (let i = 0; i < size; i++) log.append(randomBytes(8));
    for (let idx = 0; idx < size; idx++) {
      const p = log.inclusionProof(idx);
      const root = rootFromInclusionProof(log.leaves[idx], idx, size, p.path.map((s) => s.hash)).toString("hex");
      assert.equal(root, p.root, `mismatch at index ${idx} of ${size}`);
      checks++;
    }
  }
  assert.ok(checks > 1000);
});

test("rekor: a real public-log entry verifies offline — inclusion, substance, and Rekor's signed timestamp", () => {
  const v = verifyEntry(fixture.entry, {
    expectedPrincipalDid: fixture.principalDid,
    expectedGenesis: fixture.genesis,
    rekorPublicKeyPem: fixture.rekorPublicKeyPem,
  });
  assert.equal(v.ok, true);
  assert.equal(v.principalDid, fixture.principalDid);
  assert.equal(v.signatureVerified, true);
  assert.equal(v.setVerified, true);
  assert.ok(v.treeSize > 1_000_000, "the fixture came from the real multi-billion-leaf log");
  assert.equal(v.loggedHash, sha256Hex(Buffer.from(jcs(fixture.genesis))), "the log holds exactly this genesis record's hash");
  assert.match(v.url, /logIndex=\d+$/);
});

test("rekor: tampered proof, wrong principal, and wrong genesis all fail loudly", () => {
  const bad = structuredClone(fixture.entry);
  bad.verification.inclusionProof.hashes[0] = "00".repeat(32);
  assert.throws(() => verifyEntry(bad), /LAP_ERR_REKOR_INCLUSION/);

  const { publicKey } = generateKeyPairSync("ed25519");
  const stranger = didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey));
  assert.throws(() => verifyEntry(fixture.entry, { expectedPrincipalDid: stranger }), /LAP_ERR_REKOR_KEY/);

  assert.throws(() => verifyEntry(fixture.entry, { expectedGenesis: { ...fixture.genesis, generation: 99 } }), /LAP_ERR_REKOR_CONTENT/);

  const badSet = structuredClone(fixture.entry);
  badSet.integratedTime += 1;
  assert.throws(() => verifyEntry(badSet, { rekorPublicKeyPem: fixture.rekorPublicKeyPem }), /LAP_ERR_REKOR_SET/);
});

test("rekor: buildGenesisEntry produces a rekord/x509 entry Rekor can verify (structure)", () => {
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  const genesis = { v: "lap-genesis-v0", agent: "did:key:zTest", principal: didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey)), generation: 1 };
  const e = buildGenesisEntry(genesis, privateKey);
  assert.equal(e.kind, "rekord");
  assert.equal(e.spec.signature.format, "x509");
  assert.equal(Buffer.from(e.spec.data.content, "base64").toString(), jcs(genesis));
  assert.match(Buffer.from(e.spec.signature.publicKey.content, "base64").toString(), /BEGIN PUBLIC KEY/);
});

test("rekor: live round-trip against rekor.sigstore.dev (set LAP_REKOR_LIVE=1)", { skip: !process.env.LAP_REKOR_LIVE }, async () => {
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  const principal = didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey));
  const genesis = { v: "lap-genesis-v0", agent: "did:key:zLiveTest", principal, generation: 1, created_at: Math.floor(Date.now() / 1000), purpose: "lap-reference-test" };
  let e = await submitEntry(buildGenesisEntry(genesis, privateKey));
  if (!e.verification?.inclusionProof) e = await fetchEntry(e.uuid);
  const v = verifyEntry(e, { expectedPrincipalDid: principal, expectedGenesis: genesis, rekorPublicKeyPem: await fetchRekorPublicKey() });
  assert.equal(v.ok && v.setVerified && v.signatureVerified, true);
});
