#!/usr/bin/env python3
"""Re-run the extract with the COMPOSER-AUTHORED fixes and compare to fixes-off (the old
behaviour), on the SAME articles: fragment-count, concepts, throughput. Under OS paging.
Honest: fixes ON exercises the composer-authored Programs (nominal-filter / sense-select /
cache-serve), installed via consumption_quality.ensure_*; OFF = quality=False (pre-fix)."""
import sys, os, time, io, contextlib
from pathlib import Path
ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT/"runners"/"dsl"/"python"), str(ROOT/"scripts")):
    sys.path.insert(0, p)
os.chdir(ROOT)
buf = io.StringIO()
with contextlib.redirect_stderr(buf):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.wikipedia_consumption as wc
    import domains.consumption_quality as cq
    import domains.graph_virtual_memory as gvmmod

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
TITLES = ["Photosynthesis","Cryptography","Volcano","Glacier","Antibiotic","Mitochondrion",
 "Evolution","Enzyme","Ecosystem","Vaccine","Neuron","Bacteria","Virus","Earthquake",
 "Blockchain","Compiler","Democracy","Guitar","Metabolism","Telescope"][:N]

def is_fragment(name):   # a grounded concept whose head is NOT a nominal = a clause fragment
    try:
        return not cq.is_nominal(name.replace("_"," "))
    except Exception:
        return False

def run(agent, quality, cache):
    t0 = time.time(); concepts = 0; frags = 0; consumed = 0
    for title in TITLES:
        with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
            r = wc.consume_article(agent, title, quality=quality, cache=cache)
        adm = (r.get("admitted") if isinstance(r, dict) else None) or []
        if adm:
            consumed += 1
            for lex in adm:
                concepts += 1
                if is_fragment(lex.get("name","")): frags += 1
    return dict(t=time.time()-t0, concepts=concepts, frags=frags, consumed=consumed)

# OFF: fixes off (the old behaviour) — fresh agent
with contextlib.redirect_stderr(buf):
    a0 = WorldAdapter(seeds=()); load_all_seeds(a0)
off = run(a0, quality=False, cache=None)

# ON: composer-authored fixes, under OS paging — fresh agent
with contextlib.redirect_stderr(buf):
    a1 = WorldAdapter(seeds=()); load_all_seeds(a1)
    base = a1.inner.node_count()
    gvm = gvmmod.GraphVirtualMemory(a1.inner, corpus="rerun", budget_nodes=base+500)
    # install the composer-authored Programs; consume_article threads `agent` so the
    # authored SENSE program runs (nominal runs its byte-identical adapter leaf).
    cq.ensure_nominal_filter_program(a1); cq.ensure_sense_select_program(a1); cq.ensure_cache_serve_program(a1)
    cache = cq.GroundingCache()   # sense-cache interface (get_sense/put_sense); gives the speedup
on = run(a1, quality=True, cache=cache)

print(f"RE-RUN over {len(TITLES)} real articles — OFF (pre-fix) vs ON (composer-authored fixes, under paging)")
print(f"{'':16}{'concepts':>10}{'fragments':>11}{'frag-%':>9}{'s/article':>11}")
for lbl, d in [("OFF (old)", off), ("ON (authored)", on)]:
    fp = 100*d['frags']/max(1,d['concepts'])
    print(f"{lbl:16}{d['concepts']:>10}{d['frags']:>11}{fp:>8.1f}%{d['t']/len(TITLES):>11.3f}")
print(f"\nUNDERSTANDING: fragments {off['frags']} -> {on['frags']}  "
      f"({100*off['frags']/max(1,off['concepts']):.1f}% -> {100*on['frags']/max(1,on['concepts']):.1f}%)")
print(f"EFFICIENCY   : {off['t']/len(TITLES):.3f} -> {on['t']/len(TITLES):.3f} s/article "
      f"({off['t']/max(1e-9,on['t']):.2f}x)")
st = getattr(cache, "stats", lambda: {})() if callable(getattr(cache, "stats", None)) else getattr(cache, "_stats", {})
hits = getattr(cache, "hits", st.get("hits", "?")); misses = getattr(cache, "misses", st.get("misses", "?"))
print(f"CACHE        : hits={hits} misses={misses} (repetition across articles is what the cache monetizes)")
print(f"OS PAGING    : resident {a1.inner.node_count()} (budget {base+500}, bounded) | "
      f"corpus {gvm.corpus_records()} mmap records ({gvm.corpus_bytes()} bytes)")
print("Fixes ON exercise the composer-authored Programs (nominal_filter / sense_select / cache_serve).")
