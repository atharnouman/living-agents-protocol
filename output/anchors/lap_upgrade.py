"""Upgrade and verify OpenTimestamps proofs without the `ots` CLI (which is broken on Windows).

    python output/anchors/lap_upgrade.py                 # upgrade + verify every *.ots in the repo
    python output/anchors/lap_upgrade.py --verify-only   # verify without writing anything
    python output/anchors/lap_upgrade.py README.md.ots   # specific files

Upgrade: for every pending calendar attestation, fetch the calendar's completed path and merge it;
once a Bitcoin block-header attestation is present below a node, the pending marker is dropped
(the same result as `ots upgrade`).
Verify: a Bitcoin block-header attestation claims the attested 32-byte value IS the merkle root of
block N. That is checked against a public block explorer (blockstream.info) — no local node needed.
What a verified proof establishes: the file's exact bytes existed no later than that block's time.
"""
import glob
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

from opentimestamps.calendar import RemoteCalendar
from opentimestamps.core.notary import BitcoinBlockHeaderAttestation, PendingAttestation
from opentimestamps.core.serialize import StreamDeserializationContext, StreamSerializationContext
from opentimestamps.core.timestamp import DetachedTimestampFile

EXPLORER = "https://blockstream.info/api"


def explorer_block(height):
    h = urllib.request.urlopen(f"{EXPLORER}/block-height/{height}", timeout=20).read().decode()
    b = json.loads(urllib.request.urlopen(f"{EXPLORER}/block/{h}", timeout=20).read().decode())
    return b["merkle_root"], b["timestamp"]


def nodes(ts):
    """Every Timestamp node in the tree (pre-order)."""
    stack = [ts]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(n.ops.values())


def upgrade(ts):
    changed = False
    for node in list(nodes(ts)):
        for att in list(node.attestations):
            if not isinstance(att, PendingAttestation):
                continue
            try:
                completed = RemoteCalendar(att.uri).get_timestamp(node.msg)
            except Exception as e:  # calendar not ready or unreachable: keep the pending marker
                print(f"      {att.uri}: not available ({type(e).__name__})")
                continue
            node.merge(completed)
            changed = True
            if any(isinstance(a, BitcoinBlockHeaderAttestation) for n in nodes(node) for a in n.attestations):
                node.attestations.discard(att)  # superseded by the Bitcoin attestation below it
    return changed


def verify(ts):
    """Returns (ok, [(height, block_time)]) for every Bitcoin attestation; ok=False on any mismatch."""
    results, ok = [], True
    for node in nodes(ts):
        for att in node.attestations:
            if isinstance(att, BitcoinBlockHeaderAttestation):
                mr, when = explorer_block(att.height)
                match = node.msg[::-1].hex() == mr
                ok &= match
                results.append((att.height, when, match))
    return ok, results


def main(argv):
    verify_only = "--verify-only" in argv
    files = [a for a in argv if a != "--verify-only"] or sorted(
        f for f in glob.glob("**/*.ots", recursive=True) if ".git" not in f.replace("\\", "/").split("/"))
    all_ok, pending = True, []
    for f in files:
        with open(f, "rb") as fh:
            dts = DetachedTimestampFile.deserialize(StreamDeserializationContext(fh))
        changed = False if verify_only else upgrade(dts.timestamp)
        ok, results = verify(dts.timestamp)
        all_ok &= ok
        if changed:
            with open(f, "wb") as fh:
                dts.serialize(StreamSerializationContext(fh))
        if results:
            earliest = min(w for _, w, _ in results)
            heights = ", ".join(f"{h}{'' if m else ' MISMATCH'}" for h, _, m in sorted(results))
            print(f"{'CONFIRMED' if ok else 'INVALID  '} {f}\n           Bitcoin blocks {heights}; earliest {datetime.fromtimestamp(earliest, timezone.utc):%Y-%m-%d %H:%M UTC}"
                  + ("  [upgraded, written]" if changed else ""))
        else:
            pending.append(f)
            print(f"PENDING   {f}  (calendars have not aggregated it into Bitcoin yet; re-run later)")
    print(f"\n{len(files)} proofs: {len(files) - len(pending)} confirmed, {len(pending)} pending" + ("" if all_ok else "; VERIFICATION FAILURES above"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
