import { createHash, createPublicKey, verify as cryptoVerify } from "node:crypto";

const B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
// DER SPKI header for a raw Ed25519 public key (RFC 8410)
const ED25519_SPKI_PREFIX = Buffer.from("302a300506032b6570032100", "hex");

export function b64urlDecode(s) {
  return Buffer.from(s, "base64url");
}

export function b64urlEncode(buf) {
  return Buffer.from(buf).toString("base64url");
}

export function sha256Hex(data) {
  return createHash("sha256").update(data).digest("hex");
}

export function sha256B64url(data) {
  return b64urlEncode(createHash("sha256").update(data).digest());
}

export function b58Encode(buf) {
  let n = BigInt("0x" + (Buffer.from(buf).toString("hex") || "0"));
  let s = "";
  while (n > 0n) {
    const r = n % 58n;
    n /= 58n;
    s = B58[Number(r)] + s;
  }
  let pad = 0;
  for (const byte of buf) {
    if (byte === 0) pad++;
    else break;
  }
  return "1".repeat(pad) + s;
}

export function b58Decode(s) {
  if (!s || s.length === 0) return Buffer.alloc(0);
  let n = 0n;
  for (const ch of s) {
    const v = B58.indexOf(ch);
    if (v < 0) throw new Error(`invalid base58 character: ${ch}`);
    n = n * 58n + BigInt(v);
  }
  let pad = 0;
  for (const ch of s) {
    if (ch === "1") pad++;
    else break;
  }
  if (n === 0n) return Buffer.alloc(pad);
  let hex = n.toString(16);
  if (hex.length % 2) hex = "0" + hex;
  const out = Buffer.from(hex, "hex");
  return pad ? Buffer.concat([Buffer.alloc(pad), out]) : out;
}

// did:key:z6Mk... -> 32-byte raw Ed25519 public key
export function didKeyToRawPublicKey(did) {
  if (!did.startsWith("did:key:z")) throw new Error(`unsupported DID method: ${did}`);
  const multibase = did.slice("did:key:z".length);
  // F12: bound input BEFORE base58 decoding — an ed25519 did:key multibase is ~46-48
  // chars; `iss`/`agentDid` are attacker-controlled and decoded pre-auth, so an
  // unbounded string would drive O(n^2) BigInt work (CPU-exhaustion DoS).
  if (multibase.length > 48) throw new Error("LAP_ERR_DID: multibase too long for ed25519 did:key");
  const decoded = b58Decode(multibase);
  if (decoded[0] !== 0xed || decoded[1] !== 0x01) throw new Error("not an ed25519-pub did:key");
  const raw = decoded.subarray(2);
  if (raw.length !== 32) throw new Error(`bad key length: ${raw.length}`);
  return raw;
}

export function publicKeyFromRaw(raw32) {
  return createPublicKey({
    key: Buffer.concat([ED25519_SPKI_PREFIX, raw32]),
    format: "der",
    type: "spki",
  });
}

export function publicKeyFromDid(did) {
  return publicKeyFromRaw(didKeyToRawPublicKey(did));
}

// 32-byte raw Ed25519 public key -> did:key:z6Mk...
export function didKeyFromRawPublicKey(raw32) {
  return "did:key:z" + b58Encode(Buffer.concat([Buffer.from([0xed, 0x01]), raw32]));
}

export function rawPublicKeyFromKeyObject(publicKey) {
  const der = publicKey.export({ format: "der", type: "spki" });
  return der.subarray(der.length - 32);
}

export function verifyEd25519(publicKey, data, signature) {
  return cryptoVerify(null, Buffer.from(data), publicKey, signature);
}

// DID-safe normalization: NFC + lowercase the "did:method:" prefix ONLY.
// The method-specific id is case-sensitive (base58 in did:key) and MUST NOT be
// case-folded — lowercasing it would corrupt the key. (Round-3 triage note: the
// reviewer's proposed fix of running DIDs through normalizeUri would do exactly that.)
export function normalizeDid(did) {
  const s = did.normalize("NFC");
  const m = s.match(/^did:([A-Za-z0-9]+):(.+)$/);
  if (!m) return s;
  return "did:" + m[1].toLowerCase() + ":" + m[2];
}

// LIP-1 §3 string normalization for resource URIs: NFC + lowercase scheme/host.
// Do NOT use on DIDs — use normalizeDid (host-lowercasing corrupts did:key ids).
export function normalizeUri(uri) {
  const s = uri.normalize("NFC");
  const m = s.match(/^([a-zA-Z][a-zA-Z0-9+.-]*):(\/\/)?([^/]*)(.*)$/);
  if (!m) return s;
  const [, scheme, slashes = "", host, rest] = m;
  return scheme.toLowerCase() + ":" + slashes + host.toLowerCase() + rest;
}

// JCS-compatible canonical JSON for the LAP data subset (ASCII strings, integers,
// objects, arrays, null, booleans). Matches Python json.dumps(sort_keys=True,
// separators=(",",":")) for this subset.
export function jcs(value) {
  if (value === null || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isInteger(value)) throw new Error("JCS subset: integers only");
    return String(value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(jcs).join(",") + "]";
  if (typeof value === "object") {
    const keys = Object.keys(value).sort();
    return "{" + keys.map((k) => JSON.stringify(k) + ":" + jcs(value[k])).join(",") + "}";
  }
  throw new Error(`JCS subset: unsupported type ${typeof value}`);
}
