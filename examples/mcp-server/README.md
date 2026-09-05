# Add LAP to your MCP server in 15 minutes

By the end you will have an MCP server whose sensitive tool **refuses to run** unless the calling agent presents a valid passport, a signature over the exact arguments, and an envelope that permits the action — and whose every successful call returns a **server-signed receipt**. Three lines of code on the server; a small helper on the client.

```
examples/mcp-server/
  server.py   # FastMCP server; one tool protected by @verify_envelope
  client.py   # LAP-aware client: mints a passport, signs calls, verifies receipts
```

## 0. What you get (and what you don't)

**Enforced before your tool code runs:**
1. A principal-signed **passport** is presented, addressed to *this* server (audience check — a passport minted for another server is refused).
2. The call is **signed by the agent named in the passport** (holder-of-key — a stolen passport is useless without the agent's key).
3. The signature covers the **exact arguments the server bound** (canonical JSON) — a signature can't be replayed with different arguments.
4. The **action and resource** are inside the passport's envelope.
5. The **amount** is within the envelope's per-transaction cap, in the declared unit.

**Not provided by this example** (stated plainly): transport-level binding over stdio (over HTTP, put the passport and signature in the `LAP-Passport` / `LAP-Signature` headers and have your transport layer populate `lap_auth`); idempotency for retried mutating calls (see LIP-4 §2(5)); and principal *proofing* — the demo passport is `self-asserted`, which is why the decorator offers `min_proof_class`.

## 1. Install (2 min)

```bash
pip install -e ../../lap-python        # the LAP Python library (one dependency: cryptography)
pip install "mcp>=1.2,<2"              # the official MCP Python SDK
```

## 2. Protect a tool (3 lines) — `server.py`

```python
from living_agents import verify_envelope, did_key_from_raw_public_key

@mcp.tool()
@verify_envelope(
    action="finance:pay",
    resource="mcp://tools.example.com/billing/pay",
    amount_param="amount", unit_param="unit",
    server_private_key=SERVER_KEY, server_did=SERVER_DID,   # for signing receipts
    expected_aud=SERVER_ID,                                 # the audience every passport must name
)
def pay_invoice(invoice: str, amount: int, unit: str = "USD", lap_auth: dict | None = None) -> dict:
    return {"status": "paid", "invoice": invoice, "amount": amount, "unit": unit}
```

Two details that matter:
- **`lap_auth: dict | None = None`** must be a parameter of the tool so it appears in the MCP tool schema (the client sends it as an argument over stdio). The decorator removes it before your function runs and never includes it in the signed body.
- **`expected_aud` is mandatory.** Without an audience a passport would be valid for every server — the spec calls that fail-open, and the decorator refuses to run that way.

Optional server policy — because *a valid passport is identity, not authorization*:
```python
    allowed_issuers=["did:key:z6Mk…"],   # only these principals may call this tool
    min_proof_class="org-validated",     # refuse self-asserted passports
```

## 3. The client mints a passport and signs each call — `client.py`

Two keys: the **principal** (who is responsible) issues the passport; the **agent** (the software) signs calls. The passport says: *this agent, for this principal, may do these things (`envelope`), when talking to this server (`aud`), until this time (`exp`).*

```python
ENVELOPE = {"act": ["finance:pay"], "res": "mcp://tools.example.com/billing/**",
            "cap": {"max_per_tx": 5000, "unit": "USD", "window": "tx"}}
PASSPORT = sign_jws({"iss": principal_did, "sub": agent_did, "aud": SERVER_ID, "iat": NOW, "exp": NOW + 600,
                     "lap": {"v": 0, "proof_class": "self-asserted", "envelope": ENVELOPE, ...}},
                    principal_key, principal_did + "#key-1", "lap-microcore+jwt")
```

Each call signs an RFC 9421-style base over the canonical JSON of the arguments plus the passport hash, with the **agent** key, and sends `{**args, "lap_auth": {...}}`. See `lap_auth_for()` in `client.py` — about ten lines.

## 4. Run it (1 min)

```bash
python client.py
```

You should see one paid call with a **verified receipt** and four refusals, each with its reason:

```
  PAID     in-scope: $4200 (cap $5000)      -> paid INV-1001 $4200  receipt verified ✓
  REFUSED  over cap: $6000                  -> LAP_ERR_CAP: amount 6000 exceeds max_per_tx 5000
  REFUSED  tampered: signed $100, sent $4200 -> LAP_ERR_DIGEST: content-digest line mismatch
  REFUSED  wrong unit: EUR                  -> LAP_ERR_CAP: unit mismatch (EUR vs USD)
  REFUSED  no passport at all               -> LAP_ERR_AUTH_MISSING: lap_auth context required
```

Every refusal happens **before** `pay_invoice` runs. The receipt (`_lap_receipt` on the result) is a tripartite line — request hash, response hash, server signature — that both sides can log; the client verifies it against the server's DID with `verify_receipt`.

## 5. Take it to production

- **HTTP transport:** carry the passport and signature in the `LAP-Passport` / `LAP-Signature` headers (LIP-4) and let your transport layer build `lap_auth` — including `request_body` as the raw bytes and the observed method/target — so the signature is bound to the wire, not just to arguments.
- **Persist the server key** and publish its DID, so receipts remain verifiable across restarts (a restart is a nap, not a death).
- **Set policy:** `allowed_issuers` and `min_proof_class` for anything touching money or PII.
- **Idempotency:** claim `(agent, Idempotency-Key)` atomically before executing a mutating tool (LIP-4 §2(5)); the library ships a single-process helper and documents the distributed requirement.
- **Register births:** `lap-demo/register-genesis.mjs` shows how to put an agent's genesis in Sigstore's public Rekor log — birth witnessed, not self-asserted.

Spec references: [LIP-4 Micro-Core](../../output/lip/LIP-4-micro-core-draft.md) (the server invariant), [LIP-3 Scope Algebra](../../output/lip/LIP-3-scope-algebra-v0-draft.md) (what `act`/`res`/`cap` mean), [LIP-1 Passport](../../output/lip/LIP-1-agent-passport-draft.md).
