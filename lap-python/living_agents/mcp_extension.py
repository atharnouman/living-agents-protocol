"""
MCP extension binding for LAP Micro-Core (LIP-4): ``io.github.atharnouman/lap-microcore``.

Specification draft: ``output/lip/LIP-4-mcp-extension-draft.md``. Wire format, all under one key:

- request  ``params._meta[EXTENSION_ID]`` = ``{passport, signature_base, signature[, idempotency_key]}``
- result   ``_meta[EXTENSION_ID]``        = ``{receipt_base, receipt_signature_b64url, server_did}``
- tool     ``_meta[EXTENSION_ID]``        = ``{action, resource[, amount_param, unit_param, mutating]}``
- server   ``capabilities.extensions[EXTENSION_ID]`` = ``{aud[, min_proof_class, receipts, server_did]}``

Two halves. The SDK-independent half (``sign_tool_call``, ``lap_auth_from_meta``, ``tool_meta``,
``signature_base_for_tool_call``) imports nothing from the MCP SDK. The SDK-aware half
(``lap_tool``, ``microcore_extension``) imports the official ``mcp`` package lazily and works
with FastMCP (mcp 1.x) and MCPServer (mcp 2.x) alike.
"""

import functools
import inspect
import json
from typing import Any, Callable, Dict, Mapping, Optional

from .crypto_util import b64url_encode, jcs, sha256_b64url, sha256_hex
from .mcp_middleware import verify_envelope
from .microcore import IdempotencyCache

EXTENSION_ID = "io.github.atharnouman/lap-microcore"
META_KEY = EXTENSION_ID  # the same key names the object in request _meta, result _meta and tool _meta


# --------------------------------------------------------------------------- SDK-independent

def signature_base_for_tool_call(
    arguments: Mapping[str, Any],
    resource: str,
    passport: str,
    agent_did: str,
    created: int,
    idempotency_key: Optional[str] = None,
) -> str:
    """The RFC 9421 signature base of one ``tools/call`` (extension draft section 5).

    ``@method`` is the MCP method, ``@target-uri`` the tool's declared resource, ``content-digest``
    the SHA-256 of the RFC 8785 canonical form of ``arguments`` (RFC 9530 form), and
    ``lap-passport-hash`` the SHA-256 of the passport string. ``idempotency-key`` is covered when
    present, so a key cannot be re-attached to another request.
    """
    body = jcs(dict(arguments))
    lines = [
        '"@method": tools/call',
        f'"@target-uri": {resource}',
        f'"content-digest": sha-256=:{sha256_b64url(body)}:',
        f'"lap-passport-hash": sha256:{sha256_hex(passport)}',
    ]
    components = ['"@method"', '"@target-uri"', '"content-digest"', '"lap-passport-hash"']
    if idempotency_key is not None:
        lines.append(f'"idempotency-key": {idempotency_key}')
        components.append('"idempotency-key"')
    lines.append(f'"@signature-params": ({" ".join(components)});created={created};keyid="{agent_did}#key-1"')
    return "\n".join(lines)


def sign_tool_call(
    arguments: Mapping[str, Any],
    resource: str,
    passport: str,
    agent_private_key: Any,
    agent_did: str,
    created: int,
    idempotency_key: Optional[str] = None,
) -> Dict[str, str]:
    """Client side: the object to send as ``_meta[EXTENSION_ID]`` on a ``tools/call`` request.

    ``agent_private_key`` is the AGENT's Ed25519 key (the passport's ``sub``), never the principal's.
    Send exactly the ``arguments`` you signed, every argument explicitly.
    """
    base = signature_base_for_tool_call(arguments, resource, passport, agent_did, created, idempotency_key)
    out = {
        "passport": passport,
        "signature_base": base,
        "signature": b64url_encode(agent_private_key.sign(base.encode("ascii"))),
    }
    if idempotency_key is not None:
        out["idempotency_key"] = idempotency_key
    return out


def tool_meta(
    action: str,
    resource: str,
    amount_param: Optional[str] = None,
    unit_param: Optional[str] = None,
    mutating: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """Server side: the ``_meta`` entry a tool carries in ``tools/list`` to say it requires the extension."""
    entry: Dict[str, Any] = {"action": action, "resource": resource}
    if amount_param:
        entry["amount_param"] = amount_param
    if unit_param:
        entry["unit_param"] = unit_param
    if mutating:
        entry["mutating"] = True
    return {META_KEY: entry}


def _meta_entry(meta: Any) -> Optional[Dict[str, Any]]:
    """The extension object inside a request ``_meta``: a plain dict (mcp 2.x) or a pydantic
    ``Meta`` model whose unknown keys live in ``model_extra`` (mcp 1.x)."""
    if meta is None:
        return None
    if isinstance(meta, Mapping):
        entry = meta.get(META_KEY)
    else:
        extra = getattr(meta, "model_extra", None) or {}
        entry = extra.get(META_KEY)
        if entry is None:
            entry = getattr(meta, META_KEY, None)
    return entry if isinstance(entry, Mapping) else None


def lap_auth_from_meta(meta: Any, raw_arguments: Optional[Mapping[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Server side: translate the request ``_meta`` into the ``lap_auth`` dict ``verify_envelope`` expects.

    Returns ``None`` when the extension object is absent (the caller decides how to refuse). When the
    SDK exposes the request's raw ``arguments`` (mcp 2.x), pass them: the signed body is then the
    canonical form of the arguments AS SENT, which is what the extension draft specifies. Without
    them the middleware derives the body from its own bound arguments (defaults applied), so a
    client must send every argument explicitly (mcp 1.x hides the raw request from tools).
    """
    entry = _meta_entry(meta)
    if entry is None:
        return None
    auth: Dict[str, Any] = {
        "passport_jwt": entry.get("passport"),
        "signature_base": entry.get("signature_base"),
        "signature_b64url": entry.get("signature"),
    }
    if entry.get("idempotency_key") is not None:
        auth["idempotency_key"] = str(entry["idempotency_key"])
    if raw_arguments is not None:
        auth["request_body"] = jcs(dict(raw_arguments))
    return auth


# --------------------------------------------------------------------------- SDK-aware (lazy imports)

def _sdk():
    """The pieces that differ between SDK majors, resolved once at decoration time."""
    try:
        from mcp.server.mcpserver import Context  # mcp >= 2
    except ImportError:
        from mcp.server.fastmcp import Context  # mcp 1.x
    try:
        from mcp.server.mcpserver.exceptions import ToolError  # mcp >= 2
    except ImportError:
        from mcp.server.fastmcp.exceptions import ToolError  # mcp 1.x
    import mcp.types as types
    return Context, ToolError, types


def _raw_arguments(request_context: Any) -> Optional[Mapping[str, Any]]:
    """mcp 2.x exposes the request's params on the context; mcp 1.x does not (None)."""
    params = getattr(request_context, "params", None)
    if params is None:
        return None
    arguments = params.get("arguments") if isinstance(params, Mapping) else getattr(params, "arguments", None)
    return arguments if isinstance(arguments, Mapping) else None


def _call_tool_result(types: Any, result: Any, receipt: Optional[Dict[str, str]]) -> Any:
    """A CallToolResult for either SDK major: text content, structured content for a dict result,
    and the receipt under ``_meta[META_KEY]``."""
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
    fields = types.CallToolResult.model_fields
    structured = "structuredContent" if "structuredContent" in fields else "structured_content"
    body: Dict[str, Any] = {"content": [types.TextContent(type="text", text=text)]}
    if isinstance(result, dict):
        body[structured] = result
    if not receipt:
        return types.CallToolResult(**body)
    try:
        return types.CallToolResult(**body, **{"_meta": {META_KEY: receipt}})
    except Exception:  # a model that accepts only the field name, not the wire alias
        return types.CallToolResult(**body, meta={META_KEY: receipt})


def lap_tool(
    server: Any,
    action: str,
    resource: str,
    *,
    amount_param: Optional[str] = None,
    unit_param: Optional[str] = None,
    server_private_key: Any = None,
    server_did: Optional[str] = None,
    expected_aud: Optional[str] = None,
    allowed_issuers: Optional[list] = None,
    min_proof_class: Optional[str] = None,
    idempotency_cache: Optional[IdempotencyCache] = None,
    tool_kwargs: Optional[Dict[str, Any]] = None,
) -> Callable:
    """Register a tool that REQUIRES the extension on a FastMCP (mcp 1.x) or MCPServer (mcp 2.x) instance.

    Replaces ``@server.tool()``. In ``tools/list`` the tool keeps its own parameters (no auth argument,
    no context argument) and carries ``tool_meta(...)``. On every call the extension object is read
    from the request ``_meta`` through the SDK's context, the LIP-4 invariant runs via
    ``verify_envelope`` before the function executes, a refusal reaches the caller as a ``ToolError``
    carrying its ``LAP_ERR_*`` reason, and a success returns a ``CallToolResult`` whose ``_meta``
    carries the server-signed receipt. Pass ``idempotency_cache`` for a mutating tool. Synchronous
    functions only. ``tool_kwargs`` are forwarded to ``server.tool()`` (title, description, ...).
    """
    Context, ToolError, types = _sdk()
    options = dict(tool_kwargs or {})
    options["meta"] = {**options.get("meta", {}),
                       **tool_meta(action, resource, amount_param, unit_param, mutating=idempotency_cache is not None)}

    def decorator(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):
            raise TypeError("lap_tool supports synchronous tool functions only")
        signature = inspect.signature(fn)
        if "ctx" in signature.parameters:
            raise TypeError("lap_tool adds its own ctx parameter; rename the tool's ctx argument")
        guarded = verify_envelope(
            action=action, resource=resource, amount_param=amount_param, unit_param=unit_param,
            server_private_key=server_private_key, server_did=server_did, expected_aud=expected_aud,
            allowed_issuers=allowed_issuers, min_proof_class=min_proof_class,
            idempotency_cache=idempotency_cache,
        )(fn)
        with_ctx = list(signature.parameters.values()) + [
            inspect.Parameter("ctx", inspect.Parameter.KEYWORD_ONLY, annotation=Context)
        ]

        @functools.wraps(fn)
        def wrapper(*args: Any, ctx: Any, **kwargs: Any) -> Any:
            request_context = ctx.request_context
            lap_auth = lap_auth_from_meta(getattr(request_context, "meta", None), _raw_arguments(request_context))
            if lap_auth is None:
                raise ToolError(f"LAP_ERR_AUTH_MISSING: request _meta lacks {META_KEY}")
            try:
                result = guarded(*args, lap_auth=lap_auth, **kwargs)
            except ValueError as e:  # a typed LAP_ERR_* refusal; nothing else about the server leaks
                raise ToolError(str(e)) from e
            receipt = result.pop("_lap_receipt", None) if isinstance(result, dict) else None
            return _call_tool_result(types, result, receipt)

        # What the SDK inspects: the tool's own parameters plus the context, returning a CallToolResult.
        wrapper.__signature__ = signature.replace(parameters=with_ctx, return_annotation=types.CallToolResult)
        wrapper.__annotations__ = {**getattr(fn, "__annotations__", {}), "ctx": Context, "return": types.CallToolResult}
        server.tool(**options)(wrapper)
        return wrapper

    return decorator


def microcore_extension(
    aud: str,
    *,
    server_did: Optional[str] = None,
    min_proof_class: Optional[str] = None,
    receipts: bool = True,
) -> Any:
    """mcp 2.x only: an ``Extension`` for ``MCPServer(extensions=[...])`` that advertises
    ``capabilities.extensions[EXTENSION_ID]`` with this server's settings (extension draft section 4).
    mcp 1.x has no server-side extension registry; its tools still enforce the extension per call."""
    from mcp.server.extension import Extension  # mcp >= 2

    advertised: Dict[str, Any] = {"aud": aud, "receipts": bool(receipts)}
    if min_proof_class:
        advertised["min_proof_class"] = min_proof_class
    if server_did:
        advertised["server_did"] = server_did

    class LapMicroCoreExtension(Extension):
        identifier = EXTENSION_ID

        def settings(self) -> Dict[str, Any]:
            return dict(advertised)

    return LapMicroCoreExtension()
