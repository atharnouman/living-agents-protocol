// Sigstore Rekor binding — registers a LAP Genesis Record in the PUBLIC Rekor
// transparency log and verifies the result with LAP's own RFC 6962 code.
//
// This turns "registration is self-attested" (the demo's honest caveat) into
// "registered in an append-only public log anyone can audit" (spec §14.5 / §19:
// the Agent Transparency Log pattern, here instantiated on an existing neutral log).
//
// What gets logged: the canonical genesis JSON, the principal's Ed25519 signature
// over it, and the principal's public key (PEM). Rekor verifies the signature before
// admitting the entry, then returns an inclusion proof against its Merkle root and a
// Signed Entry Timestamp (SET) under Rekor's own key. We verify all three locally.
import { createHash, createPublicKey, createVerify, sign, verify } from "node:crypto";
import { jcs, sha256Hex, didKeyFromRawPublicKey, rawPublicKeyFromKeyObject } from "./crypto-util.js";
import { leafHash } from "./merkle-log.js";

export const REKOR_PUBLIC = "https://rekor.sigstore.dev";
export const searchUrl = (logIndex) => `https://search.sigstore.dev/?logIndex=${logIndex}`;

// ---------- building the entry ----------
// `rekord` (x509 signature format) carries the full content, so Rekor can verify a
// pure-Ed25519 signature over it (hashedrekord cannot, since Ed25519 signs messages,
// not digests).
export function buildGenesisEntry(genesisRecord, principalPrivateKey) {
  const content = Buffer.from(jcs(genesisRecord));
  const signature = sign(null, content, principalPrivateKey);
  const pem = createPublicKey(principalPrivateKey).export({ type: "spki", format: "pem" });
  return {
    apiVersion: "0.0.1",
    kind: "rekord",
    spec: {
      data: { content: content.toString("base64") },
      signature: {
        format: "x509",
        content: signature.toString("base64"),
        publicKey: { content: Buffer.from(pem).toString("base64") },
      },
    },
  };
}

// ---------- talking to the log ----------
const normalize = (map) => { const [uuid, e] = Object.entries(map)[0]; return { uuid, ...e }; };

export async function submitEntry(entry, base = REKOR_PUBLIC) {
  const r = await fetch(`${base}/api/v1/log/entries`, {
    method: "POST", headers: { "content-type": "application/json", accept: "application/json" }, body: JSON.stringify(entry),
  });
  if (r.status === 409) { // identical entry already logged: idempotent — fetch it
    const loc = r.headers.get("location") || "";
    return fetchEntry(loc.split("/").pop(), base);
  }
  const text = await r.text();
  if (r.status !== 201) throw new Error(`LAP_ERR_REKOR_SUBMIT: HTTP ${r.status}: ${text.slice(0, 300)}`);
  return normalize(JSON.parse(text));
}

export async function fetchEntry(uuidOrIndex, base = REKOR_PUBLIC) {
  const byIndex = /^\d+$/.test(String(uuidOrIndex));
  const url = byIndex ? `${base}/api/v1/log/entries?logIndex=${uuidOrIndex}` : `${base}/api/v1/log/entries/${uuidOrIndex}`;
  const r = await fetch(url, { headers: { accept: "application/json" } });
  if (!r.ok) throw new Error(`LAP_ERR_REKOR_FETCH: HTTP ${r.status}`);
  return normalize(await r.json());
}

export async function fetchRekorPublicKey(base = REKOR_PUBLIC) {
  const r = await fetch(`${base}/api/v1/log/publicKey`);
  if (!r.ok) throw new Error(`LAP_ERR_REKOR_KEY: HTTP ${r.status}`);
  return await r.text(); // PEM (ECDSA P-256)
}

// ---------- RFC 6962 verification, LAP-side ----------
const nodeHash = (l, r) => createHash("sha256").update(Buffer.from([0x01])).update(l).update(r).digest();
const bitLen = (x) => (x === 0n ? 0 : x.toString(2).length);
const popcount = (x) => x.toString(2).split("1").length - 1;

// Root reconstruction from a side-less audit path (RFC 6962 §2.1.1). This is the
// compact "inner + border" formulation used by Trillian and Rekor's own verifier;
// orientation at each level is derived from (index, size) rather than carried.
export function rootFromInclusionProof(leaf, index, size, hashes) {
  if (index >= size) throw new Error("LAP_ERR_REKOR_PROOF: index >= treeSize");
  const inner = bitLen(BigInt(index) ^ BigInt(size - 1));
  const border = popcount(BigInt(index) >> BigInt(inner));
  if (hashes.length !== inner + border) throw new Error(`LAP_ERR_REKOR_PROOF: expected ${inner + border} hashes, got ${hashes.length}`);
  let seed = leaf;
  for (let i = 0; i < inner; i++) {
    const h = Buffer.from(hashes[i], "hex");
    seed = ((BigInt(index) >> BigInt(i)) & 1n) === 0n ? nodeHash(seed, h) : nodeHash(h, seed);
  }
  for (let i = inner; i < hashes.length; i++) seed = nodeHash(Buffer.from(hashes[i], "hex"), seed);
  return seed;
}

// Verify a Rekor entry end to end:
//  1. inclusion — SHA256(0x00||body) chains to the log's root through the audit path;
//  2. substance — the logged key is the expected principal, the logged content is the
//     expected genesis, and the logged signature verifies (Rekor is not trusted for this);
//  3. SET — Rekor's ECDSA-P256 signature over {body, integratedTime, logID, logIndex}.
export function verifyEntry(entry, { expectedPrincipalDid, expectedGenesis, rekorPublicKeyPem } = {}) {
  const body = Buffer.from(entry.body, "base64");
  const leaf = leafHash(body);
  const p = entry.verification?.inclusionProof;
  if (!p) throw new Error("LAP_ERR_REKOR_PROOF: entry carries no inclusion proof (not yet integrated?)");
  const root = rootFromInclusionProof(leaf, p.logIndex, p.treeSize, p.hashes).toString("hex");
  if (root !== p.rootHash) throw new Error("LAP_ERR_REKOR_INCLUSION: reconstructed root does not match the log root");

  const spec = JSON.parse(body.toString()).spec;
  const key = createPublicKey(Buffer.from(spec.signature.publicKey.content, "base64").toString());
  const principalDid = didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(key));
  if (expectedPrincipalDid && principalDid !== expectedPrincipalDid) throw new Error("LAP_ERR_REKOR_KEY: logged key is not the expected principal");
  // Rekor's canonical body keeps only the content's HASH (spec.data.hash) plus the
  // signature and key — the content itself is not stored. Substance is therefore
  // re-verified against the caller's expected genesis, never taken from the log.
  const loggedHash = spec.data?.hash?.value ?? (spec.data?.content ? sha256Hex(Buffer.from(spec.data.content, "base64")) : null);
  if (!loggedHash) throw new Error("LAP_ERR_REKOR_CONTENT: entry carries neither a data hash nor content");
  let signatureVerified = null;
  if (expectedGenesis) {
    const content = Buffer.from(jcs(expectedGenesis));
    if (sha256Hex(content) !== loggedHash) throw new Error("LAP_ERR_REKOR_CONTENT: logged hash is not the expected genesis record");
    signatureVerified = verify(null, content, key, Buffer.from(spec.signature.content, "base64"));
    if (!signatureVerified) throw new Error("LAP_ERR_REKOR_SIG: logged signature does not verify over the expected genesis");
  }

  let setVerified = null;
  if (rekorPublicKeyPem) {
    const payload = jcs({ body: entry.body, integratedTime: entry.integratedTime, logID: entry.logID, logIndex: entry.logIndex });
    setVerified = createVerify("sha256").update(payload).verify(rekorPublicKeyPem, Buffer.from(entry.verification.signedEntryTimestamp, "base64"));
    if (!setVerified) throw new Error("LAP_ERR_REKOR_SET: signed entry timestamp does not verify under Rekor's key");
  }
  return {
    ok: true, logIndex: entry.logIndex, integratedTime: entry.integratedTime, treeSize: p.treeSize,
    leafHash: leaf.toString("hex"), root, principalDid, loggedHash, signatureVerified, setVerified, url: searchUrl(entry.logIndex),
  };
}
