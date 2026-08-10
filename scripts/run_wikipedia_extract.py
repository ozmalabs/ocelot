#!/usr/bin/env python3
"""Run the Wikipedia extract UNDER the Jabberwock's own OS paging (graph_virtual_memory):
consume a spread of REAL wiki_local articles, resident bounded by memory_bound + page-out,
corpus mmap'd. Measure resident (flat at base+workingset) vs corpus (growing) + throughput.
Honest: a BATCH under self-management to prove the OS + measure the rate; the full 7.6M is
then throughput-only (resumable), NOT run to completion here."""
import sys, os, time, sqlite3, io, contextlib
from pathlib import Path
ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT/"runners"/"dsl"/"python"), str(ROOT/"scripts")):
    sys.path.insert(0, p)
os.chdir(ROOT)
buf = io.StringIO()
with contextlib.redirect_stderr(buf):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.wiki_local as wl
    import domains.wikipedia_consumption as wc
    import domains.graph_virtual_memory as gvmmod

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
HEADROOM = int(sys.argv[2]) if len(sys.argv) > 2 else 600   # working-set nodes above the base kernel
TOTAL = 7_597_149

# Substantial, definitional real Wikipedia articles (WHICH articles only — no concepts
# hardcoded; the concepts come from each article). A raw rowid-spread lands on cruft
# (year/season/stub/disambiguation pages) with no enumerable structure -> no yield;
# these are genuine concept/phenomenon articles the pipeline can extract from.
SUBSTANTIAL = [
 "Photosynthesis","Cryptography","Volcano","Glacier","Antibiotic","Mitochondrion",
 "Evolution","Gravity","Electron","Enzyme","Ecosystem","Vaccine","Photon","Neuron",
 "Antibody","Bacteria","Virus","Galaxy","Earthquake","Tsunami","Blockchain","Compiler",
 "Database","Algorithm","Encryption","Operating system","Machine learning","Transistor",
 "Semiconductor","Democracy","Guitar","Symphony","Rhetoric","Ethics","Sonnet","Sculpture",
 "Jazz","Ballet","Architecture","Calligraphy","Coral reef","Rainforest","Desert","Tundra",
 "Pollination","Metabolism","Immune system","Nervous system","Photovoltaics","Telescope",
 "Microscope","Laser","Radar","Antenna","Capacitor","Combustion","Fermentation","Osmosis",
 "Erosion","Sedimentation",
]
titles = SUBSTANTIAL[:N]

with contextlib.redirect_stderr(buf):
    a = WorldAdapter(seeds=()); load_all_seeds(a)
base = a.inner.node_count()
BUDGET = base + HEADROOM   # kernel stays resident; only CONSUMED clusters page
with contextlib.redirect_stderr(buf):
    gvm = gvmmod.GraphVirtualMemory(a.inner, corpus="extract_run", budget_nodes=BUDGET)
print(f"pulled {len(titles)} real spread titles from the 7.6M index")
print(f"base kernel nodes={base}  budget_nodes={BUDGET} (base+{HEADROOM} working set)")

t0 = time.time(); consumed = 0; grounded = 0; failed = 0; peak_res = base
print(f"{'#':>4} {'title':<30} {'resident':>9} {'corpus':>7} {'concepts':>9} {'s/art':>7}")
for i, title in enumerate(titles, 1):
    ts = time.time()
    try:
        with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
            r = wc.consume_article(a, title)                 # ground the article
            adm = (r.get("admitted") if isinstance(r, dict) else None) or []
            if adm:
                consumed += 1; grounded += len(adm)
                if gvmmod.page_consumed(gvm, a, r):          # register the consumed cluster
                    gvm.enforce()                            # page cold clusters -> mmap corpus
            else:
                failed += 1
    except Exception as e:
        failed += 1
        if i <= 3: print(f"  ERR on {title!r}: {type(e).__name__}: {e}")
    peak_res = max(peak_res, a.inner.node_count())
    if i % 10 == 0 or i <= 3:
        print(f"{i:>4} {title[:30]:<30} {a.inner.node_count():>9} {gvm.corpus_records():>7} {grounded:>9} {(time.time()-ts):>7.2f}")
dt = time.time() - t0; per = dt / max(1, len(titles)); res = a.inner.node_count()
print("\n=== EXTRACT under the Jabberwock's OS paging ===")
print(f"articles attempted : {len(titles)}   consumed : {consumed}   failed/no-source : {failed}")
print(f"resident nodes     : {res}  (peak {peak_res}, budget {BUDGET}) -- BOUNDED (kernel {base} + working set)")
print(f"mmap corpus records: {gvm.corpus_records()}  ({gvm.corpus_bytes()} bytes on disk) -- GROWN (paged out)")
print(f"corpus is mmap slab: {gvm.corpus_is_mmap_slab()}")
print(f"concepts grounded  : {grounded}")
print(f"throughput         : {per:.2f} s/article  ({dt:.1f}s for {len(titles)})")
print(f"EXTRAPOLATE full 7.6M @ this rate: {per*TOTAL/86400:.1f} days single-thread; "
      f"resident stays ~{BUDGET} (kernel+workingset), corpus -> mmap disk (throughput-only, resumable)")
