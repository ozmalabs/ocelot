"""RUNG 2 — build the `normal` arm's stimulus cache from the REAL source.

Attempt 10's video arm used Sesame Street over Jellyfin and cached nothing, so the
BUILT result had no re-runnable stimulus. This script decodes a small, pinned frame
cache and commits it, so a third party reproduces rung 2 WITHOUT a live server.

THE PIN (everything a re-decode needs, in the file, not in a memory):

    series    a6152b4a3b12f70779d1cb6364fa97e6   "Sesame Street" (78 episodes)
    episodes  the 10 ids in EPISODES below
    start_s   300     (past the title sequence)
    every     6       (every 6th decoded frame)
    size      16      (the resolution the rung actually uses)
    frames    600 per episode  -> 6000 x 16 x 16 float32 (~6 MB, npz-compressed)

`--verify` re-decodes from the live server and checks the committed cache still
hashes identically. That is the difference between a cache and a rumour.

THE READ ERROR THIS FILE EXISTS TO PREVENT (VISION_PROTOCOL.md §12):
`catalog()` returns dicts keyed lowercase `name`/`type`/`id`. A previous absence
check read `Name` (capital); `.get('Name','')` returns `''` and CANNOT raise, so a
stocked 137-item library silently read as empty and the corpus was declared gone.
`_positive_control()` below re-proves the reader can SEE a thing known present
before this script trusts any lookup. An absence claim off a soft accessor is
evidence of a LOOKUP, not of ABSENCE.

Python here is a world adapter: it decodes bytes and writes an array. No decisions.
"""
from __future__ import annotations

import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

SERIES_ID = "a6152b4a3b12f70779d1cb6364fa97e6"

# Pinned by id, not by list order: the server's ordering is not a contract.
EPISODES = [
    ("ae7cbce94109558b544bb6194930f50e", "Can They Be Friends?"),
    ("05e375f5a7be453e66eae92429dc5fa4", "The Oct-Dough-Pus"),
    ("e7e1f1ecc5b7035404c73a5cbd28ba3b", "Proud of My Name"),
    ("d2926777a4e652289e8f94d82c451488", "Abby's Magical Sleepover"),
    ("12263123c101e166da7ed6fe75c9c4a2", "Sesame Street Self-Portraits"),
    ("0c06a46840fefa33435f4328477c8c78", "Scootin' on Sesame Street"),
    ("13a77f1a266761671c6fb95f53cb86e6", "Worms Want To Play"),
    ("66d90b3a59460967b8e0e7c1560a40b2", "Elmo's Morning Routine"),
    ("41d00e9c9a02149b36e7142a416a8792", "Are You Ready For School?"),
    ("d4ac9387c834ff9e8fa8db56fd9fa9ca", "Supermarket Games"),
]

START_S = 300
EVERY = 6
SIZE = 16
PER_EP = 600

CACHE = os.path.join(ROOT, "tests", "fixtures", "vision_rung2", "sesame_16x16.npz")


def frames_hash(a: np.ndarray) -> str:
    """Content hash of the decoded frames. float32 bytes, C-order, shape-tagged."""
    a = np.ascontiguousarray(a, dtype=np.float32)
    h = hashlib.sha256()
    h.update(repr(a.shape).encode())
    h.update(a.tobytes())
    return h.hexdigest()[:16]


def _positive_control(jf) -> None:
    """Prove the READER can see a thing known to be present, before trusting it."""
    cat = jf.catalog()
    good = [i for i in cat if "sesame" in i.get("name", "").lower()]
    bad = [i for i in cat if "sesame" in i.get("Name", "").lower()]
    print(f"  catalogue: {len(cat)} items | lowercase 'name' -> {len(good)} Sesame hits"
          f" | capital 'Name' -> {len(bad)} (the dead instrument)")
    if not good:
        raise SystemExit("READER FAILED ITS POSITIVE CONTROL — do not trust any "
                         "absence claim from this probe.")


def build() -> np.ndarray:
    from domains.vision_corpus import _jellyfin, episode_frames
    jf = _jellyfin()
    _positive_control(jf)
    out = []
    for eid, name in EPISODES:
        f = episode_frames(jf, eid, n=PER_EP, every=EVERY,
                           start_s=START_S, size=SIZE)
        if len(f) < PER_EP:
            raise SystemExit(f"{name}: got {len(f)} frames, need {PER_EP}")
        print(f"  {name[:34]:34s} {f.shape} "
              f"range {f.min():.3f}-{f.max():.3f}")
        out.append(f)
    return np.stack(out).astype(np.float32)      # (10, 600, 16, 16)


def load() -> np.ndarray:
    """The committed cache. The runner's ONLY stimulus source."""
    if not os.path.exists(CACHE):
        raise SystemExit(f"stimulus cache missing: {CACHE}\n"
                         f"build it with:  python scripts/rung2_cache_stimulus.py")
    return np.load(CACHE)["frames"].astype(np.float32)


if __name__ == "__main__":
    verify = "--verify" in sys.argv
    if verify:
        print("VERIFY — re-decoding from the live server and comparing hashes")
        live = build()
        have = load()
        hl, hh = frames_hash(live), frames_hash(have)
        print(f"  live   {live.shape} sha256[:16]={hl}")
        print(f"  cached {have.shape} sha256[:16]={hh}")
        print("  MATCH" if hl == hh else "  *** MISMATCH ***")
        sys.exit(0 if hl == hh else 1)

    print("BUILD — decoding the rung-2 `normal` stimulus from Jellyfin")
    a = build()
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    np.savez_compressed(CACHE, frames=a)
    print(f"\n  wrote {CACHE}")
    print(f"  shape {a.shape}  sha256[:16]={frames_hash(a)}  "
          f"{os.path.getsize(CACHE)/1e6:.1f} MB on disk")
