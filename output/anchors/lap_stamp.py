"""Minimal OpenTimestamps stamper for LAP artifacts (bypasses the Windows-broken CLI import).

Ports the core of otsclient's `stamp` command using only the `opentimestamps` library:
sha256(file) -> append per-file random nonce -> sha256 -> submit to public calendars
-> serialize pending proof as <file>.ots. Proofs upgrade to full Bitcoin attestations
once the calendars' next aggregation lands on-chain (verify/upgrade later with any OTS tool).
"""
import sys, os, hashlib
from opentimestamps.core.timestamp import Timestamp, DetachedTimestampFile
from opentimestamps.core.op import OpAppend, OpSHA256
from opentimestamps.core.serialize import StreamSerializationContext
from opentimestamps.calendar import RemoteCalendar

CALENDARS = [
    "https://a.pool.opentimestamps.org",
    "https://b.pool.opentimestamps.org",
    "https://a.pool.eternitywall.com",
    "https://ots.btc.catallaxy.com",
]

def stamp(path):
    data = open(path, "rb").read()
    digest = hashlib.sha256(data).digest()
    file_ts = DetachedTimestampFile(OpSHA256(), Timestamp(digest))
    nonce = os.urandom(16)
    t = file_ts.timestamp.ops.add(OpAppend(nonce))
    merkle_tip = t.ops.add(OpSHA256())
    ok = 0
    for url in CALENDARS:
        try:
            resp = RemoteCalendar(url).submit(merkle_tip.msg, timeout=15)
            merkle_tip.merge(resp)
            ok += 1
            print(f"  calendar ok: {url}")
        except Exception as e:
            print(f"  calendar FAILED: {url} ({type(e).__name__}: {e})")
    if ok == 0:
        return None
    out = path + ".ots"
    with open(out, "wb") as f:
        file_ts.serialize(StreamSerializationContext(f))
    return out, hashlib.sha256(data).hexdigest(), ok

if __name__ == "__main__":
    results = []
    for p in sys.argv[1:]:
        print(f"stamping {p}")
        r = stamp(p)
        if r:
            out, hexd, ok = r
            results.append((p, hexd, out, ok))
            print(f"  -> {out} ({ok} calendars)")
        else:
            print("  -> FAILED (no calendar reachable)")
    print("\nSUMMARY")
    for p, hexd, out, ok in results:
        print(f"{hexd}  {os.path.basename(p)}  [{ok} cal]")
