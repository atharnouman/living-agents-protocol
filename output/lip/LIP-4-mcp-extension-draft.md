# MCP extension `io.github.atharnouman/lap-microcore`: LAP Micro-Core over the Model Context Protocol

*Status: DRAFT v0.1, 2026-10-08. Extension identifier: `io.github.atharnouman/lap-microcore`. Targets MCP protocol revision 2026-07-28 (per-request metadata) and the handshake-based revisions 2025-11-25 and 2025-06-18. Requires: [LIP-4 Micro-Core](LIP-4-micro-core-draft.md) (the server invariant), [LIP-1](LIP-1-agent-passport-draft.md) (the passport), the [LIP-3](LIP-3-scope-algebra-v0-draft.md) subset (the envelope grammar). Reference implementation: `lap-python/living_agents/mcp_extension.py` on the official Python SDK, 1.x and 2.x lines, with the runnable example in [`examples/mcp-server/`](../../examples/mcp-server/). Written in the form the MCP project uses for extension specifications (SEP-2133). The key words MUST, MUST NOT, REQUIRED, SHALL, SHOULD, SHOULD NOT, RECOMMENDED, MAY and OPTIONAL are to be interpreted as described in BCP 14 (RFC 2119, RFC 8174) when, and only when, they appear in all capitals. This draft has not been submitted anywhere; it exists so that the discussion with the MCP interest groups can be about a concrete text.*

## 1. Introduction

### 1.1 Purpose and scope

The core protocol and the authorization extensions answer *who is calling* an MCP server. This extension answers three further questions for one `tools/call` request, without a round trip to any third party:

1. **On whose authority** does the calling agent act? A compact passport, signed by the responsible principal, names the agent's key, this server as its audience, and a short validity window.
2. **Within what bounds?** The passport carries a bounded envelope: registered actions, resource patterns, a per-call cap in a declared unit. The server checks the invoked tool against it before the tool runs.
3. **What happened?** The server returns a receipt it signed over the request and the response, which both parties can keep and a third party can verify.

The extension binds the LIP-4 Micro-Core profile, which was specified over two HTTP headers, to MCP's request and result metadata so that it works on every MCP transport, including stdio, and composes with MCP's own authorization rather than replacing it. The server-side work is the LIP-4 verification invariant (section 4 below), about a hundred lines in the reference implementation.

Out of scope, by design (LIP-4 section 4): cumulative budgets across calls, revocation infrastructure (the short `exp` is the revocation), agent-to-agent handshakes, liveness, registries. A server MAY implement any of them on top; this extension does not require them.

### 1.2 Extension requirements

This extension is **OPTIONAL** for MCP implementations. When adopted:

- Implementations **MUST** conform to all requirements in this document and to the LIP-4 server verification invariant it binds.
- Implementations **MUST** follow the `_meta` key naming rules of the core specification; every key this extension defines is the extension identifier itself.
- The extension applies to `tools/call` requests and their results. It is transport-agnostic: it works unchanged over stdio and over Streamable HTTP.
- Servers **MUST** continue to serve tools that do not declare the extension exactly as before (section 2.5). Nothing in this document changes the behaviour of a tool that does not opt in.

### 1.3 Standards compliance

This extension is based on the following specifications:

- JSON Web Signature (JWS), compact serialization, with `EdDSA` over Ed25519 ([RFC 7515](https://www.rfc-editor.org/rfc/rfc7515), [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032), [RFC 8037](https://www.rfc-editor.org/rfc/rfc8037)); canonical base64url without padding ([RFC 4648 section 5](https://www.rfc-editor.org/rfc/rfc4648#section-5)).
- JSON Canonicalization Scheme ([RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)) for every hashed JSON value.
- HTTP Message Signatures ([RFC 9421](https://www.rfc-editor.org/rfc/rfc9421)) for the shape of the per-call signature base, and Digest Fields ([RFC 9530](https://www.rfc-editor.org/rfc/rfc9530)) for the content-digest component.
- The `did:key` method ([W3C CCG](https://w3c-ccg.github.io/did-key-spec/)) for principal, agent and server identifiers; `did:web` MAY name a server.
- The Model Context Protocol specification, revision 2026-07-28, including its extension negotiation and `_meta` rules, and SEP-2133 (Extensions).
- The Living Agents Protocol drafts LIP-1, LIP-3 (v0.4) and LIP-4, and their shared test vectors in [`test-vectors/`](test-vectors/).

### 1.4 Terminology

- **Principal**: the human or organisation responsible for an agent. Signs the passport.
- **Agent**: the software that calls tools. Holds the key named by the passport's `sub` and signs each call.
- **Passport**: a compact JWS, issued by the principal, that names the agent, the audience and the envelope (LIP-4 section 1).
- **Envelope**: the bounded authority inside the passport: `act` (registered actions), `res` (a resource pattern), `cap` (a per-call cap in a unit), in the LIP-3 subset LIP-4 allows.
- **Tool resource**: the URI a server assigns to a tool for envelope matching and signature binding, for example `mcp://tools.example.com/billing/pay`. It is a name, not an address.
- **Mutating tool**: a tool whose execution has side effects the server does not want repeated on a retry. Declared by the server (section 2.4).
- **Receipt**: the server-signed line over the request hash and the response hash (LIP-4 section 3).
- **Proof class**: the passport's label for how the principal's identity was established (`self-asserted`, `domain-validated`, `org-validated`, `gov-validated`; LIP-1).
- **Client**: the MCP client application that holds the agent key and builds requests. The language model never sees or produces the extension's request object.

## 2. Extension identifier and negotiation

### 2.1 Identifier

The extension identifier is `io.github.atharnouman/lap-microcore`. The prefix is the reversed form of `atharnouman.github.io`, the domain the author controls, as SEP-2133 asks of third-party extensions. The same string is the `_meta` key under which this extension places its request object, its result object and its per-tool declaration. A breaking change to any of them **MUST** be published under a new identifier.

### 2.2 Client declaration

A client that supports this extension declares it with an empty settings object:

- On protocol revision 2026-07-28 and later, in the `io.modelcontextprotocol/clientCapabilities` field of each request's `_meta` (that field is required on every request in those revisions):

```json
{
  "_meta": {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {
      "extensions": { "io.github.atharnouman/lap-microcore": {} }
    }
  }
}
```

- On earlier revisions, in `params.capabilities.extensions` of the `initialize` request.

This version defines no client settings. Servers **MUST** ignore unknown members of the client settings object.

### 2.3 Server advertisement

A server that supports this extension advertises it under `capabilities.extensions`, in the `server/discover` result (2026-07-28 and later) or the `initialize` result (earlier revisions), with the settings object below:

```json
{
  "capabilities": {
    "tools": {},
    "extensions": {
      "io.github.atharnouman/lap-microcore": {
        "aud": "did:web:tools.example.com",
        "min_proof_class": "self-asserted",
        "receipts": true,
        "server_did": "did:key:z6Mk..."
      }
    }
  }
}
```

| Member | Type | Required | Meaning |
|---|---|---|---|
| `aud` | string | Yes | The audience every passport presented to this server **MUST** name (a DID or a canonical origin). |
| `min_proof_class` | string | No | The lowest proof class the server accepts for tools that declare the extension. Default `self-asserted`. A server MAY apply a higher floor per tool. |
| `receipts` | boolean | No | Whether successful calls carry a receipt (section 5). Default `true`. |
| `server_did` | string | No | The `did:key` the server signs receipts with. Informative: a client **MUST** obtain or pin the server's receipt key out of band or on first use; an in-band value only helps it find the right pinned key. |

Clients **MUST** ignore unknown members. A server **MAY** advertise the extension and still expose tools that do not require it.

### 2.4 Tool declaration

A tool that requires the extension carries the following object in its `_meta` in `tools/list`:

```json
{
  "name": "pay_invoice",
  "inputSchema": { "type": "object", "properties": { "invoice": {"type": "string"}, "amount": {"type": "integer"}, "unit": {"type": "string", "default": "USD"} }, "required": ["invoice", "amount"] },
  "_meta": {
    "io.github.atharnouman/lap-microcore": {
      "action": "finance:pay",
      "resource": "mcp://tools.example.com/billing/pay",
      "amount_param": "amount",
      "unit_param": "unit",
      "mutating": true
    }
  }
}
```

| Member | Type | Required | Meaning |
|---|---|---|---|
| `action` | string | Yes | The registered action (LIP-3 registry) that the passport's `envelope.act` **MUST** contain for this tool. |
| `resource` | string | Yes | The tool resource. The passport's `envelope.res` **MUST** cover it, and the per-call signature **MUST** name it as `@target-uri`. |
| `amount_param` | string | No | The argument that carries the amount the envelope's `cap` applies to. Absent for uncapped tools. |
| `unit_param` | string | No | The argument that carries the unit of that amount. |
| `mutating` | boolean | No | `true` when the request **MUST** carry an `idempotency_key` (section 3.2). Default `false`. |

The presence of this object means the tool requires the extension; there is no separate `required` flag. The tool's `inputSchema` is unchanged: the extension adds no tool arguments. (The earlier LAP prototype passed the authorization context as a tool argument named `lap_auth`; this extension replaces that with `_meta`, and the argument no longer exists.)

### 2.5 Graceful degradation

- A tool without the declaration is unaffected by this extension in every respect.
- A `tools/call` to a tool with the declaration whose request carries no extension object **MUST NOT** execute the tool. The server **MUST** report the refusal as described in section 4.2 with the code `LAP_ERR_AUTH_MISSING`. On revision 2026-07-28 and later, a server **MAY** instead respond with `MissingRequiredClientCapabilityError` (`-32021`) naming this extension in `requiredCapabilities.extensions` when the client did not declare the extension at all.
- A client that does not support the extension will see the tool's declaration in `tools/list`; it **SHOULD** either hide such tools from the model or surface the refusal verbatim, which is a typed, human-readable reason.
- A client that supports the extension and meets a server that does not advertise it **MAY** still send the extension object; a server that does not understand it ignores the `_meta` key, as the core specification requires of unknown keys, and the client **MUST** treat the absence of a receipt as "unproven", never as "verified".

## 3. Request: the extension object on `tools/call`

### 3.1 Placement

The client places one JSON object at `params._meta["io.github.atharnouman/lap-microcore"]` of the `tools/call` request. Tool `arguments` are untouched.

### 3.2 Members

| Member | Type | Required | Meaning |
|---|---|---|---|
| `passport` | string | Yes | The LAP passport: a compact JWS exactly as LIP-4 section 1 defines the `LAP-Passport` header value (`alg` `EdDSA`, `typ` `lap-microcore+jwt` or `lap-passport+jwt`, signed by the principal). |
| `signature_base` | string | Yes | The RFC 9421 signature base of this call (section 3.4), as the exact bytes that were signed. |
| `signature` | string | Yes | The agent's Ed25519 signature over the ASCII bytes of `signature_base`, as canonical base64url without padding. |
| `idempotency_key` | string | When the tool is mutating | A client-chosen key, unique per intended execution. **MUST** be a covered component of `signature_base` when present. |

A server **MUST** reject an object missing a required member with `LAP_ERR_HEADERS`, and **MUST** validate every member as untrusted input before use (SEP-2133 asks this of all extension data): a malformed JWS is `LAP_ERR_SIG`, non-canonical base64url anywhere is `LAP_ERR_ENCODING`.

### 3.3 The passport

The passport is the LIP-4 Micro-Core passport without change. In this binding:

- `aud` **MUST** equal the server's advertised `aud` (section 2.3). A passport without an audience, or for a different audience, is refused (`LAP_ERR_AUDIENCE`): this is what stops a passport captured on one server from working on another.
- `sub` is the agent's `did:key`. The server derives the signature verification key from it after verifying the passport, never from anything in the request (LIP-4 F2).
- `exp` SHOULD be minutes to hours after `iat`; servers apply a skew tolerance of 60 seconds (`LAP_ERR_EXPIRED` otherwise).
- `lap.envelope.act` **MUST** list literal registered actions; `*` is invalid in Micro-Core (`LAP_ERR_ACT`). `lap.envelope.res` is a LIP-3 resource pattern; `lap.envelope.cap` is `{max_per_tx, unit, window: "tx"}`.
- `lap.proof_class` is compared with the server's floor (`LAP_ERR_PROOF_CLASS`).

### 3.4 The signature base

The signature base binds the passport to this call, this tool, and these arguments. Its lines, in this order, separated by a single line feed, with no trailing line feed:

```
"@method": tools/call
"@target-uri": <the tool's resource, exactly as declared in its _meta>
"content-digest": sha-256=:<base64url(SHA-256(JCS(arguments)))>:
"lap-passport-hash": sha256:<lowercase hex SHA-256 of the passport string>
"idempotency-key": <the idempotency key>                         (mutating tools only)
"@signature-params": ("@method" "@target-uri" "content-digest" "lap-passport-hash" "idempotency-key");created=<unix seconds>;keyid="<agent DID>#key-1"
```

- `@method` is the MCP method name, `tools/call`. (LIP-4 over HTTP uses the HTTP method there; the two bindings share the grammar, not the values, so a base signed for one cannot verify under the other.)
- `@target-uri` is the tool resource, not a transport address. The server **MUST** compare it to the resource it declared for the invoked tool (`LAP_ERR_TARGET`), so a signature made for one tool cannot be replayed against another tool under the same envelope.
- `content-digest` is the SHA-256 of the RFC 8785 canonical form of the request's `arguments` member exactly as sent; an absent `arguments` is the empty object. The digest is encoded as canonical base64url without padding, as LIP-4's test vectors do (see the open question in section 9 on RFC 9530's standard base64).
- `lap-passport-hash` is the SHA-256 of the `passport` string, lowercase hex.
- `idempotency-key` is present exactly when `idempotency_key` is present in the object, with the same value, and is then listed in `@signature-params`.
- `created` is the agent's clock in seconds. Servers **MAY** reject a `created` outside the passport's validity window. `keyid` is informative; verifiers **MUST** take the key from the verified passport's `sub`.

The client signs the ASCII bytes of the base with the agent key (the key the passport's `sub` names), never with the principal key.

### 3.5 Example request

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "pay_invoice",
    "arguments": { "invoice": "INV-1001", "amount": 4200, "unit": "USD" },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": { "extensions": { "io.github.atharnouman/lap-microcore": {} } },
      "io.github.atharnouman/lap-microcore": {
        "passport": "eyJhbGciOiJFZERTQSIsImtpZCI6ImRpZDprZXk6ejZNa2VrUkxXSC4uLiNrZXktMSIsInR5cCI6ImxhcC1taWNyb2NvcmUrand0In0.eyJpc3MiOiJkaWQ6a2V5Ono2TWtla1JMV0guLi4iLCJzdWIiOiJkaWQ6a2V5Ono2TWtzTXJaRGsuLi4iLCJhdWQiOiJkaWQ6d2ViOnRvb2xzLmV4YW1wbGUuY29tIiwiaWF0IjoxNzg3MDAwMDAwLCJleHAiOjE3ODcwMDA2MDAsImxhcCI6eyJ2IjowLCJwcm9vZl9jbGFzcyI6InNlbGYtYXNzZXJ0ZWQiLCJlbnZlbG9wZSI6eyJhY3QiOlsiZmluYW5jZTpwYXkiXSwicmVzIjoibWNwOi8vdG9vbHMuZXhhbXBsZS5jb20vYmlsbGluZy8qKiIsImNhcCI6eyJtYXhfcGVyX3R4Ijo1MDAwLCJ1bml0IjoiVVNEIiwid2luZG93IjoidHgifX19fQ.<principal signature>",
        "signature_base": "\"@method\": tools/call\n\"@target-uri\": mcp://tools.example.com/billing/pay\n\"content-digest\": sha-256=:<digest>:\n\"lap-passport-hash\": sha256:<hex>\n\"idempotency-key\": pay-1001\n\"@signature-params\": (\"@method\" \"@target-uri\" \"content-digest\" \"lap-passport-hash\" \"idempotency-key\");created=1787000000;keyid=\"did:key:z6MksMrZDk...#key-1\"",
        "signature": "<agent signature, base64url>",
        "idempotency_key": "pay-1001"
      }
    }
  }
}
```

The passport above decodes to the LIP-4 section 1 example: `iss` the principal, `sub` the agent, `aud` this server, a ten-minute window, and an envelope allowing `finance:pay` under `mcp://tools.example.com/billing/**` up to 5000 USD per call.

## 4. Server processing

### 4.1 The invariant

On each `tools/call` to a tool that declares the extension, the server **MUST** perform the following steps in this order, and **MUST NOT** execute the tool unless every step succeeds. A failure at any step stops processing: no receipt is minted and, for a mutating tool, no idempotency claim is consumed.

1. **Read** the extension object from `params._meta`. Absent: `LAP_ERR_AUTH_MISSING`. A required member missing: `LAP_ERR_HEADERS`.
2. **Verify the passport.** A compact JWS with `alg` `EdDSA` whose signature verifies under the key of its `iss` (`LAP_ERR_SIG` when malformed or invalid; `LAP_ERR_PASSPORT` when `iss` is missing; `LAP_ERR_PASSPORT_SIG` when the envelope is missing). `aud` equals the server's configured audience (`LAP_ERR_AUDIENCE`); a server with no configured audience **MUST** fail closed (LIP-4 F4). `iat` and `exp` present and the current time inside them with 60 seconds of skew (`LAP_ERR_EXPIRED`). Then policy: the issuer allow-list if configured (`LAP_ERR_ISSUER`) and the proof-class floor (`LAP_ERR_PROOF_CLASS`).
3. **Verify the call signature.** The verification key is derived from the verified passport's `sub`, never from the request (LIP-4 F2). The signature **MUST** verify over the ASCII bytes of `signature_base` (`LAP_ERR_REQ_SIG`). The base **MUST** contain the components `@method`, `@target-uri`, `content-digest`, `lap-passport-hash` and `@signature-params` (`LAP_ERR_SIG_PARAMS`; LIP-4 F3). The server recomputes the content digest from the canonical form of the `arguments` it received and the passport hash from the `passport` it received, and compares the two lines byte for byte (`LAP_ERR_DIGEST`). The `@target-uri` line **MUST** equal the invoked tool's declared resource (`LAP_ERR_TARGET`).
4. **Check the envelope.** The tool's `action` is in `envelope.act` by string equality, and `*` is refused (`LAP_ERR_ACT`); `envelope.res` covers the tool's resource segment-wise under the LIP-3 rules (`LAP_ERR_RES`).
5. **Check the cap.** If the envelope has a `cap`, bind the arguments the tool will execute with (defaults applied), take the amount from `amount_param` and the unit from `unit_param`. An amount that cannot be determined is refused (`LAP_ERR_CAP`; LIP-4 F5); the unit **MUST** equal `cap.unit`; the amount **MUST NOT** exceed `cap.max_per_tx`.
6. **Claim the idempotency key** (mutating tools). `idempotency_key` **MUST** be present (`LAP_ERR_IDEMPOTENCY`) and covered by the signature (`LAP_ERR_SIG_PARAMS`). The server claims `(sub, key)` atomically: a fresh claim continues; a completed claim returns the stored result and its receipt without executing the tool; an in-flight claim is refused (`LAP_ERR_REPLAY`; LIP-4 F6, three-state).
7. **Execute** the tool, mint the receipt (section 5) and, for a mutating tool, store the result with its receipt under the claim.

### 4.2 Reporting a refusal

A refusal is a tool result, not a protocol error: `isError` is `true`, `structuredContent` is absent, there is no receipt, and the first content block is text that begins with the error code followed by a colon and a human-readable reason, for example `LAP_ERR_CAP: amount 6000 exceeds max_per_tx 5000`. This follows the core specification's rule that errors originating from a tool are reported in the result so that the model can see them and self-correct, and it gives client code a typed reason it can act on. The reason **MUST NOT** reveal anything about the server beyond the code and the condition. On revision 2026-07-28 and later a server **MAY** respond to an undeclared extension with `MissingRequiredClientCapabilityError` instead (section 2.5).

### 4.3 Error codes

| Code | Step | Condition |
|---|---|---|
| `LAP_ERR_AUTH_MISSING` | 1 | No extension object in the request `_meta`. |
| `LAP_ERR_HEADERS` | 1 | A required member is missing. |
| `LAP_ERR_SIG` | 2 | The passport is not a compact JWS, uses another `alg`, carries malformed JSON, or its signature is invalid. |
| `LAP_ERR_ENCODING` | 2, 3 | A base64url field is not canonical (padding, trailing bits, non-URL alphabet). |
| `LAP_ERR_PASSPORT` | 2 | `iss` is missing. |
| `LAP_ERR_PASSPORT_SIG` | 2 | The passport carries no envelope. |
| `LAP_ERR_AUDIENCE` | 2 | `aud` is missing or is not this server, or the server has no configured audience. |
| `LAP_ERR_EXPIRED` | 2 | `iat` or `exp` missing or not numeric, expired, or issued in the future beyond the skew. |
| `LAP_ERR_ISSUER` | 2 | The issuer is not in the server's allow-list. |
| `LAP_ERR_PROOF_CLASS` | 2 | The proof class is below the server's floor. |
| `LAP_ERR_REQ_SIG` | 3 | The call signature does not verify under the passport's `sub`. |
| `LAP_ERR_SIG_PARAMS` | 3, 6 | A required covered component is missing (including `idempotency-key` when a key is present). |
| `LAP_ERR_DIGEST` | 3 | The content-digest or passport-hash line does not match what the server computed. |
| `LAP_ERR_TARGET` | 3 | The signed `@target-uri` is not the invoked tool's resource. |
| `LAP_ERR_ACT` | 4 | The action is not in `envelope.act`, or the envelope uses `*`. |
| `LAP_ERR_RES` | 4 | `envelope.res` does not cover the tool's resource. |
| `LAP_ERR_CAP` | 5 | The amount cannot be determined, the unit differs, or the amount exceeds `max_per_tx`. |
| `LAP_ERR_IDEMPOTENCY` | 6 | A mutating tool was called without an idempotency key. |
| `LAP_ERR_REPLAY` | 6 | The same key is already in flight. |

The codes are the LIP-4 section 2 codes plus the three this binding adds (`AUTH_MISSING`, `HEADERS`, `IDEMPOTENCY`); `METHOD` from the HTTP binding does not occur here because `@method` is constant.

## 5. Result: the receipt

### 5.1 Placement

On success, and when the server advertises `receipts` (the default), the `tools/call` result carries one JSON object at `_meta["io.github.atharnouman/lap-microcore"]`. `content` and `structuredContent` are the tool's own output, unchanged.

### 5.2 Members

| Member | Type | Meaning |
|---|---|---|
| `receipt_base` | string | `sha256:<request hash>:sha256:<response hash>`, both lowercase hex. The request hash is the SHA-256 of the canonical form of the `arguments` as received, the same bytes the content digest covered. The response hash is the SHA-256 of the canonical form of `structuredContent` when the result has one, otherwise of the `text` of the first content block. |
| `receipt_signature_b64url` | string | The server's Ed25519 signature over the ASCII bytes of `receipt_base`, canonical base64url without padding. |
| `server_did` | string | The `did:key` of the signing key. |

This is the LIP-4 section 3 receipt line, `sha256:<req>:sha256:<resp>:<signature>`, split into its members so that a client need not parse it.

### 5.3 Verification by the client

The client **MUST** verify the signature with the server key it has pinned (section 2.3), recompute both hashes from what it sent and what it received, and compare them in constant time. A receipt that verifies under an unknown key is "unproven", not "verified". The reference verifier is `verify_receipt` in both ports; it is CONFORMANCE check 10.

### 5.4 Example result

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "content": [ { "type": "text", "text": "{\"status\": \"paid\", \"invoice\": \"INV-1001\", \"amount\": 4200, \"unit\": \"USD\"}" } ],
    "structuredContent": { "status": "paid", "invoice": "INV-1001", "amount": 4200, "unit": "USD" },
    "_meta": {
      "io.github.atharnouman/lap-microcore": {
        "receipt_base": "sha256:dc8d36b1...:sha256:9f1c0a2e...",
        "receipt_signature_b64url": "5kX5Gn7Y...",
        "server_did": "did:key:z6Mkm4189n1V4GNw..."
      }
    }
  }
}
```

### 5.5 Logging

Both parties **MUST** append `(timestamp, tool name, resource, passport hash, receipt)` to a local append-only log (LIP-4 section 3). The receipt is the portable, dual-held proof that *this request produced this response*, which is what a billing dispute needs; the log is the seed of the Flight Recorder described in the founding document.

### 5.6 Replays

For a replayed idempotency key the server returns the stored result with the same receipt and `isError` `false`; the client sees exactly what the first execution produced. A client that receives a receipt it already holds knows the retry did not execute again.

## 6. Backward compatibility and versioning

- The extension is purely additive. It changes no core message; a peer that does not implement it ignores the `_meta` keys, as the core specification requires of unknown keys, and tools without the declaration behave as before.
- It works on both eras of the protocol. Only the place where capabilities are declared differs: per-request `_meta` from revision 2026-07-28, the `initialize` handshake before it (section 2).
- It is a binding of LIP-4, not a fork of it. The passport, the envelope grammar, the receipt and the signature base grammar are the LIP-4 ones. One passport serves a server on both bindings (same audience); one signature never does, because `@method` and `@target-uri` differ. A server MAY expose the same tool over HTTP headers and over MCP metadata.
- This document is versioned. Compatible additions (new optional members in the three objects) keep the identifier; implementations **MUST** ignore unknown optional members. A change to the signature base, to a required member or to the error contract **MUST** use a new identifier.

## 7. Security considerations

Implementations adopting this extension **MUST** follow the LIP-4 hardening rules (F1 to F6 and canonical encoding) and SHOULD read the project's [threat model](../../THREAT-MODEL.md), whose rows 1 to 10 apply to this binding directly. Points specific to MCP:

- **Untrusted input.** The extension object arrives from the client. Servers **MUST** validate it before any cryptographic operation, **SHOULD** bound the size of the passport and the signature base, and **MUST** refuse non-canonical encodings (`LAP_ERR_ENCODING`): a lenient decoder gives one signature several textual forms and makes text-keyed state (passport hashes, idempotency keys, deny lists) evadable.
- **Transport authentication is separate.** This extension does not authenticate the connection. Over Streamable HTTP, servers SHOULD combine it with the core authorization framework or an `ext-auth` flow, which answer who the client is; this extension answers what the agent is permitted to do and proves what happened. Over stdio, the client process is the trust boundary, and the extension still gives the server a verifiable principal and bounds.
- **Identity is not authorization (F1).** A valid passport proves who the agent is and that its envelope is intact. It does not grant authority over server-owned resources. A server acting on its own accounts **MUST** map the verified `iss` and its proof class to a locally recognised tenant, and **MUST** refuse `self-asserted` passports for money or personal data unless explicitly configured to accept them.
- **Replay.** The audience, the expiry, the target binding, the content digest and the idempotency claim together make a captured request object useless anywhere else and harmless when re-sent: a replay with the same key returns the cached receipt, a replay with a different key is a new request the client signed, and nothing can be re-signed without the agent key.
- **Concurrency.** The idempotency claim is three-state, so a concurrent duplicate is refused rather than executed twice. A server with several replicas **MUST** back the claim with a shared store (a unique constraint, `SET NX`); the in-process cache of the reference is single-process only. Entries older than the longest passport lifetime the server accepts can be evicted: a replay after that fails on `exp`.
- **Arguments.** Servers **MUST** canonicalize the `arguments` as received, before their own defaulting or validation, and **MUST** enforce caps on the amount they actually bind (F5); a capped tool whose amount cannot be determined fails closed.
- **Model exposure.** The request object is produced by the client application that holds the agent key; the model never sees or produces it. The receipt in the result is visible to the model, which is harmless (hashes and a signature). Clients **SHOULD NOT** place passports into model-visible content.
- **Privacy.** A passport reveals the principal's DID and the envelope to the server. Envelopes **SHOULD NOT** carry personal data beyond what the server needs to decide.
- **Key custody.** Agent keys live in the client process; a compromise is bounded by the passport's expiry and envelope. A principal key compromise is handled by issuing new passports with new agent keys (LIP-1); there is no revocation list in Micro-Core.
- **Clocks.** Verification applies a skew tolerance of 60 seconds. A server with a wrong clock refuses everything, visibly, rather than accepting expired passports.

## 8. Reference implementation and conformance

**Python** (`living_agents.mcp_extension`, part of the `living-agents` package from 0.4.12): `sign_tool_call` builds the request object on the client; `lap_tool` registers a tool that requires the extension on a FastMCP (mcp 1.x) or MCPServer (mcp 2.x) instance, runs the LIP-4 invariant through `verify_envelope` before the function executes, reports refusals as the SDK's `ToolError` with the `LAP_ERR_*` reason, and returns the receipt in the result `_meta`; `tool_meta` and `lap_auth_from_meta` are the SDK-independent pieces; `microcore_extension` advertises the server settings on mcp 2.x. The tutorial in `examples/mcp-server/` runs in CI on both SDK lines over stdio: two paid calls (the second a cached replay with the same receipt) and five typed refusals, every one before the tool ran.

Known limits of the reference, stated rather than hidden: synchronous tool functions only; the `-32021` path of section 2.5 is not emitted (refusals are tool results); mcp 1.x has no server-side extension registry, so a 1.x server enforces the extension per tool but does not advertise it; on mcp 1.x the SDK hides the raw request from tools, so the signed body is derived from the bound arguments and a client must send every argument explicitly (the tutorial does); no TypeScript middleware yet.

**Conformance.** The ten checks of [CONFORMANCE.md](../../CONFORMANCE.md) apply unchanged to the passport, signature and receipt. This binding adds five: (1) the request object is read from `_meta`, never from tool arguments; (2) a tool that requires the extension declares it in its `_meta` and adds no arguments; (3) a refusal is a tool result with `isError: true` whose first text block begins with the `LAP_ERR_` code, and the tool did not execute; (4) a success carries the receipt in the result `_meta`, and the receipt verifies over the canonical arguments and the canonical structured content; (5) a mutating tool returns the stored result and receipt on a replayed key and refuses a concurrent duplicate.

**Test vectors.** The `micro_core` section of `test-vectors/vectors.json` covers the HTTP form of the signature base. Vectors for the MCP form (same keys, `@method` `tools/call`, the tool resource as target) are planned for the next vector release; `vectors.json` is Bitcoin-anchored, so adding them is a restamped release, not a quiet edit.

## 9. Open questions for the interest-group discussion

1. Whether to carry the signature in RFC 9421's wire form (`Signature-Input` and `Signature` structured fields) rather than the signature base itself. The base is simpler to implement and to audit; the structured form is smaller and matches the HTTP binding byte for byte.
2. Whether the content digest should use RFC 9530's standard base64 instead of the base64url that LIP-4's vectors use. A change here is a new identifier.
3. Whether the receipt should be a JWS rather than three members, so that generic JOSE tooling verifies it.
4. Whether the receipt key should be discoverable through the server's protected-resource metadata when the server also implements MCP authorization over HTTP.
5. How long-running calls under the Tasks extension should carry the receipt: at completion, in the final result, is the natural answer, but the signature base would then need the task identifier as a covered component.
6. Which interest group should own the extension (Security, for caller governance and auditability, or Financial Services, for tamper-evident records of what a tool call did under whose authority), and whether an `experimental-ext-` repository is the right home.

## 10. Change log

- **v0.1 (2026-10-08).** Initial draft. Reference implementation on the official Python SDK 1.29 and 2.3; the tutorial moved from a `lap_auth` tool argument to request `_meta`; idempotency claiming added to the reference middleware.
