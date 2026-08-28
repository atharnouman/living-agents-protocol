// Minimal append-only Merkle transparency log (RFC 6962 hashing convention) —
// the local building block of a LAP Agent Transparency Log (SCITT-profile, spec §14.5/§19).
// Plus salted blinded principal commitments (GDPR rule, spec §14.5): the salt stays
// off-log with the principal; erasure = salt destruction.
import { createHash, randomBytes, timingSafeEqual } from "node:crypto";

const h = (...bufs) => {
  const c = createHash("sha256");
  for (const b of bufs) c.update(b);
  return c.digest();
};
const LEAF = Buffer.from([0x00]);
const NODE = Buffer.from([0x01]);

export function leafHash(dataBuf) {
  return h(LEAF, dataBuf);
}

export function saltedCommitment(principalDid, saltHex = randomBytes(16).toString("hex")) {
  if (saltHex.length < 32) throw new Error("salt must be >=128 bits");
  const commitment = h(Buffer.from(saltHex, "hex"), Buffer.from(principalDid)).toString("hex");
  return { commitment, saltHex }; // saltHex is held OFF-log by the principal
}

export function verifyCommitment(commitmentHex, saltHex, principalDid) {
  const a = Buffer.from(saltedCommitment(principalDid, saltHex).commitment, "hex");
  const b = Buffer.from(commitmentHex, "hex");
  return a.length === b.length && timingSafeEqual(a, b);
}

export class MerkleLog {
  constructor(name) {
    this.name = name;
    this.leaves = []; // leaf hashes (Buffers)
  }
  get size() { return this.leaves.length; }

  append(dataBuf) {
    this.leaves.push(leafHash(dataBuf));
    return this.size - 1;
  }

  // RFC 6962 Merkle Tree Hash over leaves[lo, hi)
  #mth(lo, hi) {
    const n = hi - lo;
    if (n === 0) return h();
    if (n === 1) return this.leaves[lo];
    let k = 1;
    while (k * 2 < n) k *= 2;
    return h(NODE, this.#mth(lo, lo + k), this.#mth(lo + k, hi));
  }
  root() { return this.#mth(0, this.size).toString("hex"); }

  // RFC 6962 audit path for leaf at index m within leaves[lo, hi)
  #path(m, lo, hi) {
    const n = hi - lo;
    if (n <= 1) return [];
    let k = 1;
    while (k * 2 < n) k *= 2;
    if (m - lo < k) {
      return [...this.#path(m, lo, lo + k), { side: "right", hash: this.#mth(lo + k, hi).toString("hex") }];
    }
    return [...this.#path(m, lo + k, hi), { side: "left", hash: this.#mth(lo, lo + k).toString("hex") }];
  }
  inclusionProof(index) {
    if (index < 0 || index >= this.size) throw new Error("index out of range");
    return { log: this.name, index, size: this.size, root: this.root(), path: this.#path(index, 0, this.size) };
  }
}

export function verifyInclusion(dataBuf, proof) {
  let cur = leafHash(dataBuf);
  for (const step of proof.path) {
    const sib = Buffer.from(step.hash, "hex");
    cur = step.side === "left" ? h(NODE, sib, cur) : h(NODE, cur, sib);
  }
  return cur.toString("hex") === proof.root;
}
