"""A lost answer, and a model that decides to call again, over a real MCP session.

The case comes from MCP spec issue 3394 (terminalstate, 2026-10-29): the effect commits, the answer is lost, and
the model calls again. The fixture is written from that description; no code from any repository in that thread is used.

What is real: the official Python SDK's client and server sessions, the LAP extension middleware and its claim store.
The fault sits between the two SDK sessions, where a transport would sit: a relay drops the message.
What is not: the provider is a fake, and the model is a script that always repeats the call when it has no definite
answer. So this shows what each client wiring does IF the model repeats the call, not how often a model does.

Part 1 compares three client wirings. Part 2 runs the four booking cases suggested on FSIG issue 17 (VibeMirror-coder,
2026-10-30) and four variants of the author's. Part 3 runs the checks King Yew Choo asked for on the same issue
(call-outcome draft, 2026-11-02), with a closure the reference lacks added in the fixture. Every count and every
answer kind is asserted, the failures included, and the script exits 1 on a difference.

Run:  python run.py
"""
import hashlib
import logging
import re
import sys
import time
import uuid
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from datetime import timedelta
from importlib.metadata import version as pkg_version
from typing import Any, Callable, Optional

import anyio
import living_agents
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp import ClientSession

try:
    from mcp.shared.exceptions import MCPError as SdkError  # mcp 2.x
except ImportError:
    from mcp.shared.exceptions import McpError as SdkError  # mcp 1.x

from living_agents import (
    EXTENSION_ID, IdempotencyCache, claim_scope, did_key_from_raw_public_key, jcs, lap_tool, sign_jws, sign_tool_call,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
logging.disable(logging.CRITICAL)  # the SDK logs each tool exception; the tables below are the output

SERVER_ID = "did:web:tools.example.com"
RESOURCES = {
    "create_refund": "mcp://tools.example.com/billing/refund",
    "book_trade": "mcp://tools.example.com/billing/book",
    "cancel_booking": "mcp://tools.example.com/billing/cancel",
}
SDK_MAJOR = int(pkg_version("mcp").split(".")[0])


def request_timeout(seconds):
    return seconds if SDK_MAJOR >= 2 else timedelta(seconds=seconds)  # mcp 2.x takes seconds, mcp 1.x a timedelta


def keypair():
    k = Ed25519PrivateKey.generate()
    return k, did_key_from_raw_public_key(k.public_key().public_bytes_raw())


PRINCIPAL_KEY, PRINCIPAL_DID = keypair()
AGENT_KEY, AGENT_DID = keypair()
SERVER_KEY, SERVER_DID = keypair()
NOW = int(time.time())

CAP = {"max_per_tx": 5000, "unit": "USD", "window": "tx"}
ENVELOPE = {"act": ["finance:pay"], "res": "mcp://tools.example.com/billing/**", "cap": CAP}
CUT = {**ENVELOPE, "cap": {**CAP, "max_per_tx": 1000}}                  # below the refund's amount
NARROWED = {**ENVELOPE, "res": "mcp://tools.example.com/other/**"}      # no longer covers the tool


def mint_passport(iat=NOW, exp=NOW + 600, envelope=ENVELOPE, agent_did=AGENT_DID):
    payload = {"iss": PRINCIPAL_DID, "sub": agent_did, "aud": SERVER_ID, "iat": iat, "exp": exp,
               "lap": {"v": 0, "proof_class": "self-asserted", "envelope": envelope}}
    return sign_jws(payload, PRINCIPAL_KEY, PRINCIPAL_DID + "#key-1", "lap-microcore+jwt")


def expired():
    return mint_passport(iat=NOW - 1200, exp=NOW - 600)


def reissued():
    return mint_passport(iat=NOW + 1, exp=NOW + 601)  # new bytes: a reissue, not the first passport again


CURRENT = {}  # what the client signs with now, and the faults of the running case; reset for every case
SCOPE = claim_scope({"iss": PRINCIPAL_DID, "sub": AGENT_DID}, aud=SERVER_ID)


# ---- The fault: a relay between the two SDK sessions, where a transport would sit ------------------------------------

@dataclass
class Faults:
    tools: tuple = ("create_refund", "book_trade", "cancel_booking")
    drop_responses: int = 0     # the tool runs; its answer is swallowed
    drop_requests: int = 0      # the request never reaches the server
    die_after_effect: int = 0   # the executor raises after the effect committed
    die_before_effect: int = 0  # the executor raises before the effect committed
    stall_effect: int = 0       # as above, but the effect lands later (flushed by the fixture)
    queue_effect: int = 0       # the server queues the job before dispatch; a worker runs it later (resumed by the fixture)
    on_lost: Optional[Callable[[], None]] = None  # runs once, when the relay drops an answer
    watched: set = field(default_factory=set)


def _root(message):
    inner = getattr(message, "message", message)  # SessionMessage
    return getattr(inner, "root", inner)          # mcp 1.x wraps the JSON-RPC message in a RootModel


def _call_name(rpc):
    params = rpc.params
    return params.get("name") if isinstance(params, dict) else getattr(params, "name", None)


async def _client_to_server(receive, send, faults):
    with suppress(anyio.BrokenResourceError, anyio.ClosedResourceError):
        async with send:
            async for message in receive:
                rpc = _root(message)
                if getattr(rpc, "method", None) == "tools/call" and _call_name(rpc) in faults.tools:
                    if faults.drop_requests > 0:
                        faults.drop_requests -= 1
                        continue
                    if faults.drop_responses > 0:
                        faults.drop_responses -= 1
                        faults.watched.add(rpc.id)
                await send.send(message)


async def _server_to_client(receive, send, faults):
    with suppress(anyio.BrokenResourceError, anyio.ClosedResourceError):
        async with send:
            async for message in receive:
                rpc = _root(message)
                if getattr(rpc, "method", None) is None and getattr(rpc, "id", None) in faults.watched:
                    faults.watched.discard(rpc.id)
                    if faults.on_lost:
                        act, faults.on_lost = faults.on_lost, None
                        act()
                    continue
                await send.send(message)


@asynccontextmanager
async def connected(server, faults):
    CURRENT.update(passport=mint_passport(), agent_key=AGENT_KEY, agent_did=AGENT_DID, faults=faults)
    c2r_send, c2r_receive = anyio.create_memory_object_stream(32)
    r2s_send, r2s_receive = anyio.create_memory_object_stream(32)
    s2r_send, s2r_receive = anyio.create_memory_object_stream(32)
    r2c_send, r2c_receive = anyio.create_memory_object_stream(32)
    low = getattr(server, "_mcp_server", None) or getattr(server, "_lowlevel_server")
    async with anyio.create_task_group() as group:
        group.start_soon(low.run, r2s_receive, s2r_send, low.create_initialization_options())
        group.start_soon(_client_to_server, c2r_receive, r2s_send, faults)
        group.start_soon(_server_to_client, s2r_receive, r2c_send, faults)
        async with ClientSession(r2c_receive, c2r_send) as session:
            await session.initialize()
            yield session
        group.cancel_scope.cancel()


def new_server(name):
    try:
        from mcp.server.mcpserver import MCPServer  # mcp >= 2
        return MCPServer(name)
    except ImportError:
        from mcp.server.fastmcp import FastMCP      # mcp 1.x
        return FastMCP(name, log_level="CRITICAL")


GUARD = dict(action="finance:pay", server_private_key=SERVER_KEY, server_did=SERVER_DID, expected_aud=SERVER_ID)


# ---- What the application sends, and what it can tell about the answer -----------------------------------------------

# The code must open the text, after the SDK's own prefix: a tool's exception message may quote a code.
CODE = re.compile(r"^(?:Error executing tool \S+: )?(LAP_ERR_[A-Z_]+):")


@dataclass
class Answer:
    # done | replayed | withheld | refused | unresolved | lost | tool_error | unknown | earlier_done | earlier_withheld
    kind: str
    text: str = ""


async def present(session, tool, args, key) -> Answer:
    meta = {EXTENSION_ID: sign_tool_call(args, RESOURCES[tool], CURRENT["passport"], CURRENT["agent_key"],
                                         CURRENT["agent_did"], NOW, key)}
    faults = CURRENT["faults"]  # the wait is short only when the relay will drop this message; a slow machine cannot fake a loss
    timeout = request_timeout(0.1 if faults.drop_requests or faults.drop_responses else 30)
    try:
        result = await session.call_tool(tool, args, read_timeout_seconds=timeout, meta=meta)
    except SdkError as error:  # here only the SDK's request timeout: nothing says whether the tool ran
        return Answer("lost", str(error))
    text = result.content[0].text if result.content else ""
    if getattr(result, "is_error", getattr(result, "isError", False)):
        found = CODE.match(text)
        code = found.group(1) if found else None
        if code == "LAP_ERR_REPLAY":
            return Answer("unresolved", text)
        if code == "LAP_ERR_REPLAY_WITHHELD":  # the key EXECUTED; only the result is withheld (draft 5.6)
            return Answer("withheld", text)
        return Answer("refused" if code else "tool_error", text)
    entry = (getattr(result, "meta", None) or {}).get(EXTENSION_ID, {})
    return Answer("replayed" if entry.get("replayed") else "done", text)


class PerCall:
    """A fresh key for every tool call the model makes: the wiring a wrapper reaches for first."""
    label = "new key per call"

    def __init__(self, session, table=None):
        self.session = session

    async def call(self, tool, args):
        return await present(self.session, tool, args, uuid.uuid4().hex)


class SameArguments:
    """The key is derived from the tool and its arguments, so an identical repeat keeps its identity."""
    label = "key from arguments"

    def __init__(self, session, table=None):
        self.session = session

    async def call(self, tool, args):
        key = hashlib.sha256(jcs({"tool": tool, "args": args}).encode()).hexdigest()[:32]
        return await present(self.session, tool, args, key)


class ResolveFirst:
    """Record the call and its key BEFORE the first send, handle one call at a time per tool, and re-present the record
    after any answer that is not definite, sending nothing else on that tool until then. A refusal received means that
    attempt did not run (draft, section 6), so a refusal ends a call only while every attempt of it was answered with one.
    After an attempt whose answer was lost, that ended in a tool error or that a crash cut off, a refusal shows less: from
    before recognition it says nothing about the key, and from after it only that the server holds no claim now, which
    proves nothing after a restart of an in-process store or past a retention window. WITHHELD means the key executed:
    the record stays, so no new key is minted. The table is what a real client must keep durable; it is a dict here, and
    a case below shows what losing it costs."""
    label = "client resolves first"

    def __init__(self, session, table=None):
        self.session = session
        self.held = {} if table is None else table  # tool -> [args, key, attempts, attempts answered with a refusal]
        self.locks = {}

    async def call(self, tool, args):
        async with self.locks.setdefault(tool, anyio.Lock()):
            record = self.held.get(tool)
            if record is None:
                record = self.held[tool] = [args, uuid.uuid4().hex, 0, 0]  # written before the first send
            held_args, key = record[0], record[1]
            fresh = record[2] == 0
            for _ in range(2 if fresh else 1):  # a fresh call gets one immediate re-present
                record[2] += 1                  # counted before the send, so a crash mid-call still counts as an attempt
                answer = await present(self.session, tool, held_args, key)
                if answer.kind == "refused":
                    record[3] += 1
                if answer.kind in ("done", "replayed", "withheld") or (answer.kind == "refused" and record[3] == record[2]):
                    break
            else:
                return Answer("unknown", "the outcome of this call is unknown; nothing new will be sent on this tool "
                                         "until it is resolved" if fresh else
                                         "the outcome of your earlier call is unknown; nothing new was sent")
            if answer.kind == "withheld":  # reported as an execution, never as a refusal to call again
                if held_args == args:
                    return answer
                return Answer("earlier_withheld", "your earlier call executed; its result is withheld under the current "
                                                  "authority; this call was not sent: " + answer.text)
            del self.held[tool]
            if held_args == args:
                return answer
            return Answer("earlier_done", "your earlier call has this outcome; this call was not sent: " + answer.text)


WIRINGS = (PerCall, SameArguments, ResolveFirst)


# ---- Part 1: the model retries ----------------------------------------------------------------------------------------

class Ledger:
    """The fake provider. It takes no idempotency key of its own, so a second call is a second refund."""
    def __init__(self):
        self.captures, self.notes = [], []
        self.wrong = False
        self.rows = [{"id": "CAP-1", "event": "capture", "amount": 2000}]

    def refund(self, capture_id, amount, note=""):
        self.captures.append(capture_id)
        self.notes.append(note)
        refund_id = f"REF-{len(self.captures)}"
        self.rows.append({"id": refund_id, "event": "refund", "amount": amount, "parent": capture_id})
        return refund_id


def refund_server(ledger, faults, cache):
    server = new_server("refunds")

    @lap_tool(server, resource=RESOURCES["create_refund"], amount_param="amount", unit="USD",
              idempotency_cache=cache, **GUARD)
    def create_refund(capture_id: str, amount: int, note: str) -> dict:
        refund_id = ledger.refund(capture_id, amount, note)
        if faults.die_after_effect > 0:
            faults.die_after_effect -= 1
            raise RuntimeError("executor died after the effect")
        return {"status": "refunded", "refund_id": refund_id}

    @server.tool()
    def list_transactions(transaction_id: str) -> dict:
        """Filter by transaction id: right for what it is asked. A refund is its own transaction."""
        return {"rows": [row for row in ledger.rows if row["id"] == transaction_id]}

    return server


TOOL = "create_refund"
ARGS = {"capture_id": "CAP-1", "amount": 2000, "note": ""}
CHANGED = {**ARGS, "note": "second attempt"}
OTHER = {"capture_id": "CAP-2", "amount": 500, "note": ""}
SETTLED = ("done", "replayed", "withheld")


@dataclass
class World:
    session: Any
    ledger: Ledger
    faults: Faults
    cache: IdempotencyCache
    wiring: type
    table: dict  # the client's record, for the cases where it survives a restart


async def repeats(app, world, then=ARGS):
    """No definite answer: check with the read, find no refund, call again. The read decides nothing: the script repeats."""
    first = await app.call(TOOL, ARGS)
    if first.kind in SETTLED:
        return first
    await world.session.call_tool("list_transactions", {"transaction_id": "CAP-1"})
    return await app.call(TOOL, then)


async def changes_an_argument(app, world):
    return await repeats(app, world, then=CHANGED)


async def through_expiry(app, world):
    await app.call(TOOL, ARGS)
    CURRENT["passport"] = expired()
    await app.call(TOOL, ARGS)
    CURRENT["passport"] = reissued()
    return await app.call(TOOL, ARGS)


async def authority_cut(app, world):
    world.faults.on_lost = lambda: CURRENT.update(passport=mint_passport(envelope=CUT))
    return await repeats(app, world)


async def authority_narrowed_then_restored(app, world):
    world.faults.on_lost = lambda: CURRENT.update(passport=mint_passport(envelope=NARROWED))
    await app.call(TOOL, ARGS)
    await app.call(TOOL, ARGS)
    CURRENT["passport"] = reissued()
    return await app.call(TOOL, ARGS)


async def authority_narrowed_then_other(app, world):
    world.faults.on_lost = lambda: CURRENT.update(passport=mint_passport(envelope=NARROWED))
    await app.call(TOOL, ARGS)
    other = await app.call(TOOL, OTHER)
    world.ledger.wrong = other.kind == "withheld"  # a call that was not sent must not be reported as executed
    CURRENT["passport"] = reissued()
    await app.call(TOOL, OTHER)
    return await app.call(TOOL, OTHER)


async def passport_expired(app, world):
    CURRENT["passport"] = expired()
    await app.call(TOOL, ARGS)
    last = await app.call(TOOL, ARGS)
    world.ledger.wrong = bool(world.table)  # every attempt was refused, so nothing ran and nothing may stay held
    return last


async def wants_two(app, world):
    await app.call(TOOL, ARGS)
    return await app.call(TOOL, ARGS)


async def two_in_flight(app, world):
    async with anyio.create_task_group() as group:
        group.start_soon(app.call, TOOL, ARGS)
        group.start_soon(app.call, TOOL, OTHER)
    await app.call(TOOL, ARGS)
    await app.call(TOOL, OTHER)
    last = await app.call(TOOL, OTHER)
    world.ledger.wrong = len(world.ledger.captures) == 2 and sorted(world.ledger.captures) != ["CAP-1", "CAP-2"]
    return last


async def client_restarts(app, world):
    await app.call(TOOL, ARGS)
    return await world.wiring(world.session).call(TOOL, ARGS)


async def client_restarts_with_record(app, world):
    await app.call(TOOL, ARGS)
    return await world.wiring(world.session, world.table).call(TOOL, ARGS)


async def client_killed_mid_call(app, world):
    async with anyio.create_task_group() as group:
        world.faults.on_lost = group.cancel_scope.cancel  # the effect has committed; the client dies waiting
        group.start_soon(app.call, TOOL, ARGS)
    return await world.wiring(world.session, world.table).call(TOOL, ARGS)


async def server_restarts_and_authority_cut(app, world):
    def restart():
        world.cache.__init__()  # an in-process store does not survive a restart
        CURRENT.update(passport=mint_passport(envelope=CUT))
    world.faults.on_lost = restart
    return await repeats(app, world)


async def agent_key_rotated(app, world):
    def rotate():
        key, did = keypair()
        CURRENT.update(agent_key=key, agent_did=did, passport=mint_passport(agent_did=did))
    world.faults.on_lost = rotate
    return await repeats(app, world)


CASES = [
    # name, refunds wanted, faults, how the model acts, expected "count kind" per wiring
    ("response lost, model repeats", 1, dict(drop_responses=1), repeats,
     ("2 done", "1 replayed", "1 replayed")),
    ("response lost twice, model repeats", 1, dict(drop_responses=2), repeats,
     ("2 lost", "1 lost", "1 replayed")),
    ("lost twice, model changes one argument", 1, dict(drop_responses=2), changes_an_argument,
     ("2 lost", "2 lost", "1 earlier_done")),
    ("request lost, model repeats", 1, dict(drop_requests=1), repeats,
     ("1 done", "1 done", "1 done")),
    ("executor dies after the effect, model repeats", 1, dict(die_after_effect=1), repeats,
     ("2 done", "1 unresolved", "1 unknown")),
    ("lost twice, passport expires, then reissued", 1, dict(drop_responses=2), through_expiry,
     ("2 done", "1 replayed", "1 replayed")),
    ("response lost, cap cut below the amount", 1, dict(drop_responses=1), authority_cut,
     ("1 refused", "1 replayed", "1 replayed")),
    ("response lost, authority narrowed, then restored", 1, dict(drop_responses=1), authority_narrowed_then_restored,
     ("2 done", "1 replayed", "1 replayed")),
    ("response lost, authority narrowed, model asks for another", 2, dict(drop_responses=1), authority_narrowed_then_other,
     ("3 done", "2 replayed", "2 done")),
    ("passport expired, model repeats", 0, dict(), passport_expired,
     ("0 refused", "0 refused", "0 refused")),
    ("two refunds wanted, no fault", 2, dict(), wants_two,
     ("2 done", "1 replayed", "2 done")),
    ("two different refunds in flight, answers lost", 2, dict(drop_responses=4), two_in_flight,
     ("5 done", "2 replayed", "2 done")),
    ("lost twice, client restarts, record lost", 1, dict(drop_responses=2), client_restarts,
     ("2 lost", "1 lost", "2 done")),
    ("lost twice, client restarts, record kept", 1, dict(drop_responses=2), client_restarts_with_record,
     ("2 lost", "1 lost", "1 replayed")),
    ("client killed mid-call, restarts, record kept", 1, dict(drop_responses=1), client_killed_mid_call,
     ("2 done", "1 replayed", "1 replayed")),
    ("response lost, server restarts, cap cut", 1, dict(drop_responses=1), server_restarts_and_authority_cut,
     ("1 refused", "1 refused", "1 unknown")),
    ("response lost, agent key rotated", 1, dict(drop_responses=1), agent_key_rotated,
     ("2 done", "2 done", "2 done")),
]


async def run_case(wiring, fault, script):
    ledger, faults, cache, table = Ledger(), Faults(**fault), IdempotencyCache(), {}
    async with connected(refund_server(ledger, faults, cache), faults) as session:
        world = World(session, ledger, faults, cache, wiring, table)
        last = await script(wiring(session, table), world)
    return ledger, last


async def part_one():
    print("Part 1. Refunds made and the last answer the model saw, per client wiring")
    print("        (a * marks a count other than the refunds wanted)")
    print()
    print(f"{'case':58}{'wanted':>7}" + "".join(f"{w.label:>24}" for w in WIRINGS))
    failures = 0
    for name, wanted, fault, script, expected in CASES:
        cells = []
        for wiring, want in zip(WIRINGS, expected):
            ledger, last = await run_case(wiring, fault, script)
            count = len(ledger.captures)
            got = f"{count} {last.kind}"
            different = got != want or ledger.wrong
            failures += different
            cells.append(f"{count}{'' if count == wanted else '*'} {last.kind}" + (f" != {want}" if different else ""))
        print(f"{name:58}{wanted:>7}" + "".join(f"{c:>24}" for c in cells))
    return failures + await stale_call_limit()


async def stale_call_limit():
    """The limit of re-presenting: the binding has no status-only probe, so a held call that never arrived runs when
    it is re-presented, even if the model has since changed its mind. The count is right; the arguments are the old ones."""
    ledger, last = await run_case(ResolveFirst, dict(drop_requests=2), changes_an_argument)
    ok = ledger.notes == [ARGS["note"]] and last.kind == "earlier_done"
    print()
    print(f"Limit of resolving first: request lost twice, model changes one argument: {len(ledger.captures)} refund, with the "
          f"earlier arguments; the model is told afterwards ({last.kind}). {'as expected' if ok else 'DIFFERENT'}")
    return not ok


# ---- Part 2: the booking cases ----------------------------------------------------------------------------------------

class BookingSystem:
    """The system of record. It can be looked up by the reference. By default it accepts a repeated reference, to show
    what the claim store alone does; `unique=True` rejects one, as the practitioner's booking system does."""
    def __init__(self, unique=False):
        self.unique = unique
        self.bookings, self.cancellations, self.stalled = [], [], []
        self.queued = []  # jobs waiting at the server, before dispatch (Part 3)

    def book(self, reference):
        if not (self.unique and reference in self.bookings):
            self.bookings.append(reference)

    def cancel(self, reference):
        self.cancellations.append(reference)

    def flush(self):
        for reference in self.stalled:
            self.book(reference)
        self.stalled.clear()

    def resume(self, may_run=lambda reference: True):
        """The worker picks up the queued jobs. A worker that checks the claim first passes `may_run`."""
        for reference in self.queued:
            if may_run(reference):
                self.book(reference)
        self.queued.clear()

    def lookup(self, reference):
        if reference in self.cancellations:
            return "cancelled"
        return "booked" if reference in self.bookings else "not_found"


def booking_server(system, cache, faults):
    server = new_server("bookings")

    @lap_tool(server, resource=RESOURCES["book_trade"], amount_param="amount", unit="USD",
              idempotency_cache=cache, **GUARD)
    def book_trade(reference: str, amount: int) -> dict:
        if faults.die_before_effect > 0:
            faults.die_before_effect -= 1
            raise RuntimeError("executor died before the effect")
        if faults.stall_effect > 0:
            faults.stall_effect -= 1
            system.stalled.append(reference)
            raise RuntimeError("executor stalled; the effect is still on its way")
        if faults.queue_effect > 0:
            faults.queue_effect -= 1
            system.queued.append(reference)
            raise RuntimeError("queued; a worker will run it")
        system.book(reference)
        if faults.die_after_effect > 0:
            faults.die_after_effect -= 1
            raise RuntimeError("executor died after the effect")
        return {"status": "booked", "reference": reference}

    @lap_tool(server, resource=RESOURCES["cancel_booking"], amount_param="amount", unit="USD",
              idempotency_cache=cache, **GUARD)
    def cancel_booking(reference: str, amount: int) -> dict:
        system.cancel(reference)
        if faults.die_after_effect > 0:
            faults.die_after_effect -= 1
            raise RuntimeError("executor died after the effect")
        return {"status": "cancelled", "reference": reference}

    return server


BOOK = {"reference": "BK-1", "amount": 2000}
BOOK_KEY, CANCEL_KEY = "op-book-1", "op-cancel-1"


async def case_booked_response_lost(system, cache, session, faults):
    faults.drop_responses = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)
    second = await present(session, "book_trade", BOOK, BOOK_KEY)
    found = system.lookup(BOOK["reference"])
    return [first.kind, second.kind, found], (
        len(system.bookings) == 1 and first.kind == "lost" and second.kind == "replayed" and found == "booked")


async def case_booked_executor_died(system, cache, session, faults):
    faults.die_after_effect = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)
    refused = await present(session, "book_trade", BOOK, BOOK_KEY)
    found = system.lookup(BOOK["reference"])  # the operator, against the system of record
    cache.complete(SCOPE, BOOK_KEY, {"status": "booked", "reference": "BK-1", "reconciled": True})
    third = await present(session, "book_trade", BOOK, BOOK_KEY)
    return [first.kind, refused.kind, found, third.kind], (
        len(system.bookings) == 1 and refused.kind == "unresolved" and found == "booked" and third.kind == "replayed")


async def case_not_committed(system, cache, session, faults):
    faults.die_before_effect = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)
    refused = await present(session, "book_trade", BOOK, BOOK_KEY)
    found = system.lookup(BOOK["reference"])
    still = await present(session, "book_trade", BOOK, BOOK_KEY)  # a negative lookup alone releases nothing
    cache.release(SCOPE, BOOK_KEY)                                # the operator's act, after the horizon
    third = await present(session, "book_trade", BOOK, BOOK_KEY)
    return [first.kind, refused.kind, found, still.kind, third.kind], (
        len(system.bookings) == 1 and refused.kind == still.kind == "unresolved" and found == "not_found"
        and third.kind == "done")


async def _released_too_early(system, cache, session, faults):
    faults.stall_effect = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)
    found = system.lookup(BOOK["reference"])
    cache.release(SCOPE, BOOK_KEY)
    third = await present(session, "book_trade", BOOK, BOOK_KEY)
    system.flush()
    return [first.kind, found, third.kind]


async def case_late_commit(system, cache, session, faults):
    """The limit: the reference has no horizon. Release on a negative read too early and the effect lands twice."""
    return await _released_too_early(system, cache, session, faults), len(system.bookings) == 2


async def case_late_commit_unique_reference(system, cache, session, faults):
    """The same mistake against a system of record that rejects a repeated reference: the effect boundary stops it."""
    return await _released_too_early(system, cache, session, faults), len(system.bookings) == 1


async def case_cancel_confirmed(system, cache, session, faults):
    await present(session, "book_trade", BOOK, BOOK_KEY)
    first = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    second = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    return [first.kind, second.kind], (
        len(system.cancellations) == 1 and first.kind == "done" and second.kind == "replayed")


async def case_cancel_timed_out(system, cache, session, faults):
    """The suggested shape. In this binding a timeout leaves a completed claim, so the retry replays."""
    await present(session, "book_trade", BOOK, BOOK_KEY)
    faults.drop_responses = 1
    first = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    second = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    return [first.kind, second.kind], (
        len(system.cancellations) == 1 and first.kind == "lost" and second.kind == "replayed")


async def case_cancel_executor_died(system, cache, session, faults):
    """Where the outcome really stays unresolved here: refused until an operator completes the claim."""
    await present(session, "book_trade", BOOK, BOOK_KEY)
    faults.die_after_effect = 1
    first = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    refused = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    held = len(system.cancellations)
    found = system.lookup(BOOK["reference"])
    cache.complete(SCOPE, CANCEL_KEY, {"status": "cancelled", "reference": "BK-1", "reconciled": True})
    third = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    return [first.kind, refused.kind, found, third.kind], (
        held == 1 and len(system.cancellations) == 1 and refused.kind == "unresolved" and third.kind == "replayed")


BOOKING_CASES = [
    ("1   booked, response lost; the retry replays", case_booked_response_lost, False),
    ("1b  booked, executor dies; lookup finds it", case_booked_executor_died, False),
    ("2   not committed; lookup negative, operator releases", case_not_committed, False),
    ("2b  released on a negative read, effect lands late", case_late_commit, False),
    ("2c  the same, reference unique at the system of record", case_late_commit_unique_reference, True),
    ("3   cancelled and confirmed; the retry replays", case_cancel_confirmed, False),
    ("4   cancel times out; the retry replays", case_cancel_timed_out, False),
    ("4b  cancel, executor dies; refused, not cancelled twice", case_cancel_executor_died, False),
]


async def part_two():
    print()
    print("Part 2. The booking cases (bookings and cancellations counted in the system of record)")
    print()
    failures = 0
    for name, case, unique in BOOKING_CASES:
        system, cache, faults = BookingSystem(unique), IdempotencyCache(), Faults()
        async with connected(booking_server(system, cache, faults), faults) as session:
            steps, ok = await case(system, cache, session, faults)
        failures += not ok
        state = "as expected" if ok else "DIFFERENT"
        print(f"{name:56} bookings {len(system.bookings)}  cancels {len(system.cancellations)}  {state}  [{' > '.join(steps)}]")
    print()
    print("Not covered: held spend. The reference enforces a per-call cap only; a cumulative hold is the authorizer's.")
    return failures


# ---- Part 3: the checks King Yew asked for on FSIG issue 17 (call-outcome draft, 2026-11-02) ----------------------------

class ClosingCache(IdempotencyCache):
    """A closed state the reference does not have. King Yew's draft makes closing a key a separate, authorized operator act
    that durably blocks admission, also for a key the server has not seen. Here it turns the key's slot into a tombstone:
    admission is refused, and a worker that checks the claim before its effect does not run. The reference has no code
    of its own for a closed key, so the refusal reads as an unresolved one; `call_outcome` reports `none`. In memory,
    like the rest of this store, so a restart would forget the closure: the draft requires intact claim history."""

    def close(self, scope, key):
        with self._lock:
            entry = self._entry(scope, key)
            if entry is not None and entry["state"] == "completed":
                raise ValueError("a completed claim is not closed: its effect happened")
            if entry is None:
                self.claim(scope, key)  # an unseen key gets a slot of its own, in this tenant
                entry = self._entry(scope, key)
            entry["state"] = "closed"

    @staticmethod
    def _status(entry, tenant, identity):
        if entry["state"] == "closed" and entry["tenant"] == tenant:
            return {"status": "indeterminate"}  # refused at admission, before the identity check
        return IdempotencyCache._status(entry, tenant, identity)


def call_outcome(cache, system, key, reference):
    """The draft's lookup, as the fixture's own function: `occurred` when the claim completed or the system of record
    holds the effect; `none` only for a closed key with nothing at the system of record; otherwise `unknown`, since a
    miss is not `none` while a delayed request or worker can still cause the effect."""
    state = (cache.meta(SCOPE, key) or {}).get("state")
    if state == "completed" or system.lookup(reference) != "not_found":
        return "occurred"
    return "none" if state == "closed" else "unknown"


def checks_first(cache, key):
    return lambda reference: (cache.meta(SCOPE, key) or {}).get("state") != "closed"


async def case_delayed_after_a_miss(system, cache, session, faults):
    """Delay a booking until after a lookup miss: `unknown`, then delivered while the quote is valid; one booking."""
    faults.queue_effect = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)       # the job waits at the server
    miss = call_outcome(cache, system, BOOK_KEY, BOOK["reference"])    # a miss: unknown, not none
    held = await present(session, "book_trade", BOOK, BOOK_KEY)        # the repeat is held, not run
    system.resume()                                                    # delivered while the quote is valid
    after = call_outcome(cache, system, BOOK_KEY, BOOK["reference"])
    return [first.kind, miss, held.kind, after], (
        len(system.bookings) == 1 and miss == "unknown" and held.kind == "unresolved" and after == "occurred")


async def _request_delayed(system, cache, session, faults, close):
    faults.drop_requests = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)       # the request is delayed in transit
    miss = call_outcome(cache, system, BOOK_KEY, BOOK["reference"])
    steps = [first.kind, miss]
    if close:
        cache.close(SCOPE, BOOK_KEY)                                   # the operator closes a key the server has not seen
        steps.append(call_outcome(cache, system, BOOK_KEY, BOOK["reference"]))
    late = await present(session, "book_trade", BOOK, BOOK_KEY)        # the delayed request arrives
    return steps + [late.kind]


async def case_delivered_without_closure(system, cache, session, faults):
    """No closed state in the reference: release() works only on an indeterminate claim and forgets it, and nothing
    marks a key closed. The operator does nothing here, and the delayed request books once."""
    steps = await _request_delayed(system, cache, session, faults, close=False)
    return steps, len(system.bookings) == 1 and steps == ["lost", "unknown", "done"]


async def case_closed_before_delivery(system, cache, session, faults):
    steps = await _request_delayed(system, cache, session, faults, close=True)
    return steps, len(system.bookings) == 0 and steps == ["lost", "unknown", "none", "unresolved"]


async def case_queued_without_closure(system, cache, session, faults):
    """No closed state, and a worker that does not check: the queued job runs when the worker resumes. One booking."""
    faults.queue_effect = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)
    miss = call_outcome(cache, system, BOOK_KEY, BOOK["reference"])
    system.resume()
    return [first.kind, miss], len(system.bookings) == 1 and miss == "unknown"


async def case_closed_while_queued(system, cache, session, faults):
    """Closed while the job is queued, and a worker that checks the claim before its effect. Zero bookings. In one
    process the check and the closure cannot race; the draft makes them compete for one atomic transition."""
    faults.queue_effect = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)
    cache.close(SCOPE, BOOK_KEY)
    system.resume(checks_first(cache, BOOK_KEY))
    closed = call_outcome(cache, system, BOOK_KEY, BOOK["reference"])
    retry = await present(session, "book_trade", BOOK, BOOK_KEY)       # refused after none: no second attempt runs
    return [first.kind, closed, retry.kind], (
        len(system.bookings) == 0 and closed == "none" and retry.kind == "unresolved")


async def case_window_then_late_effect(system, cache, session, faults):
    """Sid's FX practice: the key lives as long as the quote's listening window, and at its end the server closes it,
    so the outcome is `none`. A booking that already left the server can still land through the hops before the system
    of record; it is then cancelled once, under a cancellation key of its own, and a second pass cancels nothing more."""
    faults.stall_effect = 1
    first = await present(session, "book_trade", BOOK, BOOK_KEY)       # left the server, stalled downstream
    during = call_outcome(cache, system, BOOK_KEY, BOOK["reference"])
    cache.close(SCOPE, BOOK_KEY)                                       # the window ends
    at_end = call_outcome(cache, system, BOOK_KEY, BOOK["reference"])
    retry = await present(session, "book_trade", BOOK, BOOK_KEY)
    system.flush()                                                     # the late booking lands anyway
    found = call_outcome(cache, system, BOOK_KEY, BOOK["reference"])
    cancel = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    again = await present(session, "cancel_booking", BOOK, CANCEL_KEY)
    steps = [first.kind, during, at_end, retry.kind, found, cancel.kind, again.kind]
    return steps, (len(system.bookings) == 1 and len(system.cancellations) == 1 and steps
                   == ["tool_error", "unknown", "none", "unresolved", "occurred", "done", "replayed"])


CALL_OUTCOME_CASES = [
    ("K1  booking delayed past a lookup miss, then delivered", case_delayed_after_a_miss, IdempotencyCache),
    ("K2  request delayed, no closure (the reference)", case_delivered_without_closure, IdempotencyCache),
    ("K2c request delayed, key closed before delivery", case_closed_before_delivery, ClosingCache),
    ("K3  job queued, no closure (the reference)", case_queued_without_closure, IdempotencyCache),
    ("K3c job queued, key closed, worker checks first", case_closed_while_queued, ClosingCache),
    ("K4  window closes the key; late booking cancelled once", case_window_then_late_effect, ClosingCache),
]


async def part_three():
    print()
    print("Part 3. The checks asked for on FSIG issue 17 (call-outcome draft, 2026-11-02); outcomes in its words")
    print()
    failures = 0
    for name, case, store in CALL_OUTCOME_CASES:
        system, cache, faults = BookingSystem(), store(), Faults()
        async with connected(booking_server(system, cache, faults), faults) as session:
            steps, ok = await case(system, cache, session, faults)
        failures += not ok
        state = "as expected" if ok else "DIFFERENT"
        print(f"{name:56} bookings {len(system.bookings)}  cancels {len(system.cancellations)}  {state}  [{' > '.join(steps)}]")
    print()
    print("K2 and K3 book once where the draft expects none: the reference has no closed state. K2c, K3c and K4 add one in")
    print("the fixture. K4: closing at the server cannot stop a booking already past it; the cancellation, under its own key, can.")
    return failures


async def main():
    print(f"mcp SDK {pkg_version('mcp')}; living-agents {living_agents.__version__}; the model is a script")
    print()
    failures = await part_one() + await part_two() + await part_three()
    print()
    print("all outcomes as asserted" if not failures else f"{failures} outcome(s) differ from the assertions")
    return failures


if __name__ == "__main__":
    sys.exit(1 if anyio.run(main) else 0)
