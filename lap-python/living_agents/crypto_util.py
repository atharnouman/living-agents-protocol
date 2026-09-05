"""
LIP-1 / LIP-4 Cryptographic utilities: Base58, JCS canonicalization, Ed25519 did:key parsing.
"""

import base64
import hashlib
import json
import re
from typing import Any, Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


_B64URL_ALPHABET = re.compile(r"^[A-Za-z0-9_-]*$")


def b64url_decode(s: str) -> bytes:
    """Decode unpadded base64url STRICTLY (RFC 4648 §5; §3.5 canonical trailing bits).

    Lenient decoding lets one signature have many textual forms — 'A'->'B' as the final
    character of an Ed25519 signature changes padding bits only and still verifies — so
    anything keyed by the TEXT (passport hashes, dedup, denylists, transparency-log entries)
    could be evaded by re-encoding. Reject padding, foreign characters, and non-zero
    trailing bits instead; the check is "re-encode and compare".
    """
    if not isinstance(s, str) or not _B64URL_ALPHABET.match(s) or len(s) % 4 == 1:
        raise ValueError("LAP_ERR_ENCODING: invalid base64url")
    raw = base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
    if b64url_encode(raw) != s:
        raise ValueError("LAP_ERR_ENCODING: non-canonical base64url")
    return raw

def b64url_encode(buf: bytes) -> str:
    """Encode bytes to unpadded base64url string."""
    return base64.urlsafe_b64encode(buf).decode("ascii").rstrip("=")


def sha256_hex(data: Union[bytes, str]) -> str:
    """Return hex-encoded SHA-256 digest."""
    buf = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(buf).hexdigest()


def sha256_b64url(data: Union[bytes, str]) -> str:
    """Return base64url-encoded SHA-256 digest."""
    buf = data.encode("utf-8") if isinstance(data, str) else data
    return b64url_encode(hashlib.sha256(buf).digest())


def b58encode(buf: bytes) -> str:
    """Encode bytes to Bitcoin Base58 string with zero-byte preservation."""
    if not buf:
        return ""
    n = int.from_bytes(buf, byteorder="big")
    chars = []
    while n > 0:
        n, r = divmod(n, 58)
        chars.append(B58_ALPHABET[r])
    chars.reverse()
    
    pad = 0
    for byte in buf:
        if byte == 0:
            pad += 1
        else:
            break
    return ("1" * pad) + "".join(chars)


def b58decode(s: str) -> bytes:
    """Decode Bitcoin Base58 string to bytes with zero-byte preservation."""
    if not s:
        return b""
    n = 0
    for ch in s:
        v = B58_ALPHABET.find(ch)
        if v < 0:
            raise ValueError(f"invalid base58 character: {ch}")
        n = n * 58 + v

    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break

    if n == 0:
        return b"\x00" * pad

    hex_str = hex(n)[2:]
    if len(hex_str) % 2:
        hex_str = "0" + hex_str
    out = bytes.fromhex(hex_str)
    return (b"\x00" * pad) + out if pad else out


def did_key_to_raw_public_key(did: str) -> bytes:
    """Parse did:key:z6Mk... to 32-byte raw Ed25519 public key."""
    if not did.startswith("did:key:z"):
        raise ValueError(f"unsupported DID method: {did}")
    multibase = did[len("did:key:z"):]
    # F12: bound input BEFORE base58 decoding — an ed25519 did:key multibase is ~46-48
    # chars; iss/agent_did are attacker-controlled and decoded pre-auth, so an unbounded
    # string would drive O(n^2) big-int work (CPU-exhaustion DoS).
    if len(multibase) > 48:
        raise ValueError("LAP_ERR_DID: multibase too long for ed25519 did:key")
    decoded = b58decode(multibase)
    if len(decoded) < 2 or decoded[0] != 0xED or decoded[1] != 0x01:
        raise ValueError("not an ed25519-pub did:key (expected multicodec prefix 0xed, 0x01)")
    raw = decoded[2:]
    if len(raw) != 32:
        raise ValueError(f"bad key length: {len(raw)} (expected 32 bytes)")
    return raw


def public_key_from_raw(raw32: bytes) -> Ed25519PublicKey:
    """Create Ed25519PublicKey from raw 32 bytes."""
    return Ed25519PublicKey.from_public_bytes(raw32)


def public_key_from_did(did: str) -> Ed25519PublicKey:
    """Resolve did:key to Ed25519PublicKey."""
    return public_key_from_raw(did_key_to_raw_public_key(did))


def did_key_from_raw_public_key(raw32: bytes) -> str:
    """Convert raw 32-byte Ed25519 public key to did:key:z6Mk..."""
    multicodec = b"\xed\x01" + raw32
    return "did:key:z" + b58encode(multicodec)


def verify_ed25519(public_key: Ed25519PublicKey, data: bytes, signature: bytes) -> bool:
    """Verify Ed25519 signature over data bytes."""
    try:
        public_key.verify(signature, data)
        return True
    except InvalidSignature:
        return False


def normalize_did(did: str) -> str:
    """
    DID-safe normalization: NFC + lowercase the 'did:method:' prefix ONLY.
    Preserves case of the method-specific identifier.
    """
    import unicodedata
    s = unicodedata.normalize("NFC", did)
    m = re.match(r"^did:([A-Za-z0-9]+):(.+)$", s, re.IGNORECASE)
    if not m:
        return s
    return f"did:{m.group(1).lower()}:{m.group(2)}"


def normalize_uri(uri: str) -> str:
    """
    LIP-1 §3 string normalization for resource URIs: NFC + lowercase scheme and host.
    """
    import unicodedata
    s = unicodedata.normalize("NFC", uri)
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):(//)?([^/]*)(.*)$", s)
    if not m:
        return s
    scheme, slashes, host, rest = m.group(1), m.group(2) or "", m.group(3), m.group(4)
    return f"{scheme.lower()}:{slashes}{host.lower()}{rest}"


def jcs(value: Any) -> str:
    """
    JCS (RFC 8785) canonical JSON serialization for the LAP data subset.
    Produces byte-identical output to Node.js reference implementation.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError("JCS subset: integers only")
        return str(int(value))
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(jcs(x) for x in value) + "]"
    if isinstance(value, dict):
        sorted_keys = sorted(value.keys())
        items = [json.dumps(k, ensure_ascii=False) + ":" + jcs(value[k]) for k in sorted_keys]
        return "{" + ",".join(items) + "}"
    raise TypeError(f"JCS subset: unsupported type {type(value)}")
