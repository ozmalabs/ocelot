#!/usr/bin/env python3
"""jabberwock_grounds_its_own_gap — GAP-DRIVEN KNOWLEDGE ACQUISITION, live (self-improvement #3).

The agent perceives a KNOWLEDGE GAP in itself — a thin/empty DIMENSION the concept-graph edge-learner
cannot ground — then does what a person does with a word it doesn't know: it READS a source, EXTRACTS
the region's concepts, TEACHES itself the microtheory (persisted, reboot-proof), and RE-DECODES. The
SAME shape the external developer produced by hand (seeds/*_microtheory.json), now AGENT-DRIVEN off a
gap the agent detected in its OWN coverage.

    GAP (thin/anchored dimension) -> READ (reference reader) -> EXTRACT (source-faithful)
        -> TEACH (microtheory + has_concept edges, persisted) -> RE-DECODE (coverage rises)

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_grounds_its_own_gap.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains import gap_driven_acquisition as gda   # noqa: E402
from domains import concept_graph as cg             # noqa: E402

# the demo writes its acquired seed here — an ISOLATED dir NOT globbed by load_all_seeds (which reads
# seeds/*.json + seeds/generated/*.json), so the demo never perturbs the boot graph or other tests.
ACQUIRED_DIR = os.path.join(ROOT, "seeds", "acquired")

# a fed reference document (real, factual) so the demo runs network-free; drop it to read the live
# wiki_local slab instead (source_title="Cryptography").
CRYPTO_DOC = (
    "In cryptography, the main primitives are: cipher, key, plaintext, ciphertext, hash function, "
    "digital signature, key exchange, and message authentication code. Other concepts include: nonce, "
    "salt, initialization vector, and block cipher. A cipher transforms plaintext into ciphertext.")


def _fmt(cov: dict) -> str:
    return (f"bag={cov['bag']:3d}  region-cosine={cov['best']:.3f}  "
            f"region={cov['region']}  source={cov['source']}  descent={'/'.join(cov['path'])}")


def main() -> None:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cg._CACHE.clear()

    # 1) THE GAP SIGNAL — read off concept_graph coverage (not a hand list).
    pool = ["cryptography", "machine_learning", "philosophy", "compilers"]
    gaps = gda.detect_knowledge_gaps(a, pool)
    print("PERCEIVED KNOWLEDGE GAPS (thin + ungrounded region, read off concept_graph coverage):")
    for g in gaps:
        print(f"   GAP  {g['domain']:16s}  {_fmt(g)}")
    if not gaps:
        print("   (no gaps in the pool)")
        return
    domain = gaps[0]["domain"]

    # 2-6) READ -> EXTRACT -> TEACH -> RE-DECODE, on the thinnest gap.
    print(f"\nAGENT-DRIVEN ACQUISITION of the gap '{domain}':")
    print(f"   BEFORE  {_fmt(gda.coverage(a, domain))}")
    r = gda.acquire_for_gap(a, domain, source_text=CRYPTO_DOC, seeds_dir=ACQUIRED_DIR)
    if not r["acquired"]:
        print(f"   HONEST NULL: {r['reason']}")
        return
    ex = r["extracted"]
    print(f"   READ    source='{ex['source']}'  title='{ex['source_title']}'")
    print(f"   EXTRACT {len(ex['concepts'])} concepts (each traces to source: {r['traced']}): "
          f"{', '.join(c['name'] for c in ex['concepts'][:10])}...")
    print(f"   TEACH   persisted -> {os.path.relpath(r['seed_path'], ROOT)}")
    print(f"   AFTER   {_fmt(r['after'])}")
    print(f"   DELTA   {r['delta']}   ({r['reason']})")

    # HONEST NULL demonstration — a gap with no readable source.
    n = gda.acquire_for_gap(a, "zzq_no_such_domain_qzz", seeds_dir=ACQUIRED_DIR)
    print(f"\nNO-SOURCE CONTROL ('zzq_no_such_domain_qzz'): acquired={n['acquired']} — {n['reason']}")


if __name__ == "__main__":
    main()
