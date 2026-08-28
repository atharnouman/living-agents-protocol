"""LIP-1 / LIP-4 test-vector generator (deterministic).

Reproducible: keys derive from fixed seed strings, so running this script
always yields byte-identical vectors.json. Requires: cryptography>=42.
"""
import json, hashlib, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big"); s = ""
    while n:
        n, r = divmod(n, 58); s = B58[r] + s
    pad = 0
    for byte in b:
        if byte == 0: pad += 1
        else: break
    return "1" * pad + s

def did_key(pub32: bytes) -> str:
    # multicodec ed25519-pub = 0xed 0x01, then base58btc with 'z' prefix
    return "did:key:z" + b58encode(b"\xed\x01" + pub32)

def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def jcs(obj) -> str:
    # Sufficient JCS (RFC 8785) subset for these vectors: ASCII strings + ints only.
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def key_from(label: str) -> Ed25519PrivateKey:
    seed = hashlib.sha256(label.encode()).digest()
    return Ed25519PrivateKey.from_private_bytes(seed)

def pub_bytes(k: Ed25519PrivateKey) -> bytes:
    return k.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)

def jws_eddsa(payload: dict, key: Ed25519PrivateKey, kid: str) -> str:
    header = {"alg": "EdDSA", "typ": "lap-passport+jwt", "kid": kid}
    signing_input = (b64url(jcs(header).encode()) + "." + b64url(jcs(payload).encode())).encode()
    return signing_input.decode() + "." + b64url(key.sign(signing_input))

principal_key = key_from("LAP LIP-1 test vector principal seed 001")
agent_key = key_from("LAP LIP-1 test vector agent seed 001")
principal_did = did_key(pub_bytes(principal_key))
agent_did = did_key(pub_bytes(agent_key))

constitution_text = "LAP test constitution v1: act only within the signed envelope; escalate on ambiguity; honor FORCE_HALT.\n"
constitution_hash = hashlib.sha256(constitution_text.encode()).hexdigest()

passport = {
    "v": "lip1-v0",
    "id": agent_did,
    "principal": {"id": principal_did, "proof_class": "self-asserted", "contact": "mailto:escalation@example.com"},
    "lineage": {"spawner": None, "generation": 1},
    "constitution": {"sha256": constitution_hash},
    "autonomy_level": 3,
    "era": {"track": "api-hosted", "digest": hashlib.sha256(
        ("provider:example|model:example-lm-1|" + constitution_hash).encode()).hexdigest()},
    "presence_contact": "https://agent.example.com/lap/pulse",
    "revocation": "https://agent.example.com/lap/revocation",
    "iat": 1787000000,
    "exp": 1818536000,
}
passport_canonical = jcs(passport)
passport_jws = jws_eddsa(passport, principal_key, principal_did + "#key-1")

genesis = {
    "v": "lip1-genesis-v0",
    "agent": agent_did,
    "passport_sha256": hashlib.sha256(passport_canonical.encode()).hexdigest(),
    "created_at": 1787000000,
}
genesis_canonical = jcs(genesis)

micro_core_claims = {
    "iss": principal_did,
    "sub": agent_did,
    "aud": "did:web:tools.example.com",
    "iat": 1787000000,
    "exp": 1787000600,
    "lap": {
        "v": 0,
        "proof_class": "self-asserted",
        "constitution_hash": constitution_hash,
        "envelope": {
            "act": ["finance:pay"],
            "res": "mcp://tools.example.com/billing/**",
            "cap": {"max_per_tx": 5000, "unit": "USD", "window": "tx"},
        },
    },
}
micro_core_jwt = jws_eddsa(micro_core_claims, principal_key, principal_did + "#key-1")

request_body = b'{"invoice":"INV-1001","amount":4200,"unit":"USD"}'
signature_base = "\n".join([
    '"@method": POST',
    '"@target-uri": https://tools.example.com/billing/pay',
    '"content-digest": sha-256=:' + b64url(hashlib.sha256(request_body).digest()) + ":",
    '"lap-passport-hash": sha256:' + hashlib.sha256(micro_core_jwt.encode()).hexdigest(),
    '"@signature-params": ("@method" "@target-uri" "content-digest" "lap-passport-hash");created=1787000060;keyid="' + agent_did + '#key-1"',
])
request_signature = b64url(agent_key.sign(signature_base.encode()))

tool_server_key = key_from("LAP LIP-4 test vector tool-server seed 001")
receipt_base = "sha256:" + hashlib.sha256(request_body).hexdigest() + ":" + \
    "sha256:" + hashlib.sha256(b'{"status":"paid","receipt":"R-77"}').hexdigest()
receipt_sig = b64url(tool_server_key.sign(receipt_base.encode()))

vectors = {
    "_note": "Deterministic LIP-1/LIP-4 test vectors. Regenerate with generate_vectors.py; output is byte-stable.",
    "keys": {
        "principal": {"seed_label": "LAP LIP-1 test vector principal seed 001",
                       "public_key_hex": pub_bytes(principal_key).hex(), "did": principal_did},
        "agent": {"seed_label": "LAP LIP-1 test vector agent seed 001",
                   "public_key_hex": pub_bytes(agent_key).hex(), "did": agent_did},
        "tool_server": {"seed_label": "LAP LIP-4 test vector tool-server seed 001",
                         "public_key_hex": pub_bytes(tool_server_key).hex(),
                         "did": did_key(pub_bytes(tool_server_key))},
    },
    "constitution": {"text": constitution_text, "sha256": constitution_hash},
    "passport": {"claims": passport, "canonical_jcs": passport_canonical, "jws": passport_jws},
    "genesis": {"claims": genesis, "canonical_jcs": genesis_canonical,
                 "sha256": hashlib.sha256(genesis_canonical.encode()).hexdigest()},
    "micro_core": {"passport_jwt": micro_core_jwt,
                    "request_body": request_body.decode(),
                    "rfc9421_signature_base": signature_base,
                    "request_signature_b64url": request_signature,
                    "receipt_base": receipt_base, "receipt_signature_b64url": receipt_sig},
}

out = json.dumps(vectors, indent=2)
open(__file__.replace("generate_vectors.py", "vectors.json"), "w", newline="\n").write(out + "\n")
print("principal did:", principal_did)
print("agent did:    ", agent_did)
print("passport jws (first 90):", passport_jws[:90])
print("micro-core jwt (first 90):", micro_core_jwt[:90])
print("vectors.json written,", len(out), "bytes")
