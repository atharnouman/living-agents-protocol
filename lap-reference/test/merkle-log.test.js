import { test } from "node:test";
import assert from "node:assert/strict";
import { MerkleLog, verifyInclusion, saltedCommitment, verifyCommitment } from "../src/merkle-log.js";

test("inclusion proofs verify for every leaf, at several sizes", () => {
  for (const n of [1, 2, 3, 7, 8, 13]) {
    const log = new MerkleLog("t");
    const data = Array.from({ length: n }, (_, i) => Buffer.from(`entry-${i}`));
    data.forEach((d) => log.append(d));
    for (let i = 0; i < n; i++) {
      assert.ok(verifyInclusion(data[i], log.inclusionProof(i)), `n=${n} i=${i}`);
    }
  }
});

test("proof fails for tampered data and forged root", () => {
  const log = new MerkleLog("t");
  const a = Buffer.from("genesis-A"); const b = Buffer.from("genesis-B");
  log.append(a); log.append(b);
  const proof = log.inclusionProof(0);
  assert.equal(verifyInclusion(Buffer.from("genesis-X"), proof), false);
  assert.equal(verifyInclusion(a, { ...proof, root: "00".repeat(32) }), false);
});

test("append-only: old proofs verify against old root; root advances", () => {
  const log = new MerkleLog("t");
  log.append(Buffer.from("e0"));
  const r1 = log.root();
  const p0 = log.inclusionProof(0);
  log.append(Buffer.from("e1"));
  assert.notEqual(log.root(), r1);
  assert.ok(verifyInclusion(Buffer.from("e0"), p0)); // proof pinned to its root snapshot
  assert.ok(verifyInclusion(Buffer.from("e0"), log.inclusionProof(0))); // and re-provable now
});

test("salted commitments: verifiable with salt, unlinkable without, erasable by salt destruction", () => {
  const { commitment, saltHex } = saltedCommitment("did:key:z6MkExamplePrincipal");
  assert.ok(verifyCommitment(commitment, saltHex, "did:key:z6MkExamplePrincipal"));
  assert.equal(verifyCommitment(commitment, saltHex, "did:key:z6MkSomeoneElse"), false);
  const again = saltedCommitment("did:key:z6MkExamplePrincipal");
  assert.notEqual(again.commitment, commitment); // fresh salt => unlinkable across entries
});
