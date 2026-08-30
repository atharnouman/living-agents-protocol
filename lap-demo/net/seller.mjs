// LAP networked demo — SELLER process (Bob). A real HTTP server that enforces the
// LIP-4 Micro-Core invariant on every request. Run: node seller.mjs <port>
// Talks to the buyer over real sockets; there is no shared memory between them.
import http from "node:http";
import { generateKeyPairSync, sign, createPrivateKey, createPublicKey } from "node:crypto";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import {
  didKeyFromRawPublicKey, rawPublicKeyFromKeyObject, jcs, sha256Hex, b64urlEncode,
} from "../../lap-reference/src/crypto-util.js";
import { signJws, verifyPassport } from "../../lap-reference/src/jws.js";
import {
  verifyMicroCorePassport, verifyRequestSignature, checkInvocation,
} from "../../lap-reference/src/microcore.js";

const PORT = Number(process.argv[2] || 4102);
const NOW = () => 1787019000; // fixed sim clock shared with the buyer, for stable vectors
const log = (m) => console.log(m);

// Identity persists across process restarts (L4: a session is bound to the passport,
// not the OS process — "a restart is a nap, not a death"). The keys are written on
// first start and reloaded on restart, so the restarted seller keeps the SAME did:key.
const KEY_FILE = new URL("./out/seller-identity.json", import.meta.url);
function rebuild(pkcs8Hex) {
  const privateKey = createPrivateKey({ key: Buffer.from(pkcs8Hex, "hex"), format: "der", type: "pkcs8" });
  const publicKey = createPublicKey(privateKey);
  return { publicKey, privateKey, did: didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey)) };
}
function loadOrCreateKeys() {
  if (existsSync(KEY_FILE)) {
    const j = JSON.parse(readFileSync(KEY_FILE, "utf8"));
    return { principal: rebuild(j.principal), agent: rebuild(j.agent), reused: true };
  }
  const mk = () => { const { publicKey, privateKey } = generateKeyPairSync("ed25519"); return { publicKey, privateKey, did: didKeyFromRawPublicKey(rawPublicKeyFromKeyObject(publicKey)) }; };
  const principal = mk(), agent = mk();
  mkdirSync(new URL("./out/", import.meta.url), { recursive: true });
  writeFileSync(KEY_FILE, JSON.stringify({
    principal: principal.privateKey.export({ format: "der", type: "pkcs8" }).toString("hex"),
    agent: agent.privateKey.export({ format: "der", type: "pkcs8" }).toString("hex"),
  }));
  return { principal, agent, reused: false };
}
const { principal, agent, reused } = loadOrCreateKeys();
const constitution = "Constitution of Bob (seller): fulfil only within the signed envelope; escalate on ambiguity; honor FORCE_HALT.\n";
const passport = signJws({
  v: "lip1-v0", id: agent.did,
  principal: { id: principal.did, proof_class: "self-asserted", contact: "mailto:oncall@example.com" },
  lineage: { spawner: null, generation: 1 },
  constitution: { sha256: sha256Hex(constitution) },
  autonomy_level: 3,
  era: { track: "api-hosted", digest: sha256Hex(`provider:demo|model:demo-lm|${sha256Hex(constitution)}`) },
  presence_contact: `http://127.0.0.1:${PORT}/pulse`,
  revocation: `http://127.0.0.1:${PORT}/revocation`,
  iat: NOW(), exp: NOW() + 86400 * 365,
}, principal.privateKey, principal.did + "#key-1");

const contracts = new Map();
const recorder = [];
const seq = () => recorder.length;

function readBody(req) {
  return new Promise((res) => { let b = ""; req.on("data", (c) => (b += c)); req.on("end", () => res(b)); });
}
const sendJson = (res, code, obj) => { res.writeHead(code, { "content-type": "application/json" }); res.end(jcs(obj)); };

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/passport") return sendJson(res, 200, { passport });

    if (req.method === "GET" && req.url === "/pulse") {
      const core = { t: NOW(), status: "active", head: recorder.at(-1)?.hash ?? "genesis", from: agent.did };
      return sendJson(res, 200, { ...core, sig: b64urlEncode(sign(null, Buffer.from(jcs(core)), agent.privateKey)) });
    }

    if (req.method === "POST" && req.url === "/meet") {
      const msg = JSON.parse(await readBody(req));
      if (msg.step === "HAIL") {
        const p = verifyPassport(msg.passport, { now: NOW() }); // REAL signature verification over the wire
        log(`[seller] HAIL: verified buyer passport ${p.id.slice(0, 22)}… (principal ${p.principal.id.slice(0, 18)}…) → VERIFIED`);
        return sendJson(res, 200, { step: "HAIL", ok: true, sellerAgent: agent.did });
      }
      if (msg.step === "BIND") {
        // countersign the buyer-signed interaction contract
        const countersig = b64urlEncode(sign(null, Buffer.from(jcs({ contract: msg.contract, countersigning: msg.aliceSig })), agent.privateKey));
        contracts.set(msg.contract.sid, { contract: msg.contract, aliceSig: msg.aliceSig, bobSig: countersig });
        log(`[seller] BIND: countersigned interaction contract ${msg.contract.sid.slice(0, 10)}…`);
        return sendJson(res, 200, { step: "BIND", countersig });
      }
      return sendJson(res, 400, { error: "unknown step" });
    }

    if (req.method === "POST" && req.url === "/pay") {
      const body = await readBody(req);
      const { passport_jwt, signature_base, signature_b64url, order, qty, unit_price } = JSON.parse(body);
      const inner = JSON.parse(body).request_body; // the exact signed bytes
      // ---- LIP-4 Micro-Core server-side invariant, on real request bytes ----
      const claims = verifyMicroCorePassport(passport_jwt, { expectedAud: agent.did, now: NOW() });   // F4 aud, F1 policy hook
      verifyRequestSignature({ passportJwt: passport_jwt, sub: claims.sub, signatureBase: signature_base, signatureB64url: signature_b64url, requestBody: inner }); // F2 holder-of-key, F3 components
      const amount = qty * unit_price;
      checkInvocation(claims.lap.envelope, { act: "finance:pay", resource: "ap2://demo-rails/bob-store/pay", amount, unit: "USD" });
      const responseBody = jcs({ status: "paid", order, fulfilment: `F-${order}` });
      const receiptBase = `sha256:${sha256Hex(inner)}:sha256:${sha256Hex(responseBody)}`;
      const receiptSig = b64urlEncode(sign(null, Buffer.from(receiptBase), agent.privateKey));
      recorder.push({ seq: seq(), act: "tx:received", order, amount, hash: sha256Hex(receiptBase) });
      log(`[seller] /pay ${order}: passport✓ aud✓ signature✓ cap✓ ($${amount}) → signed receipt returned`);
      return sendJson(res, 200, { status: "paid", order, receipt_base: receiptBase, receipt_sig: receiptSig, response_body: responseBody, server_did: agent.did });
    }

    sendJson(res, 404, { error: "not found" });
  } catch (e) {
    log(`[seller] REJECTED: ${e.message}`);
    sendJson(res, 403, { error: e.message });
  }
});

server.listen(PORT, "127.0.0.1", () => log(`[seller] listening on http://127.0.0.1:${PORT}  agent ${agent.did.slice(0, 22)}…  (identity ${reused ? "RELOADED — same DID across restart" : "created"})`));
