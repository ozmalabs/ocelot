"""collapse_run — PROVE the collapse loop is now a domain-agnostic CORE.

Runs scripts/collapse_engine.evaluate() — the ONE core — across three maximally
different REAL domains (sentences / letters / llvm passes), swapping ONLY the
plug. Demonstrates "one loop, pluggable scaffolding": the same core code, byte
for byte, drives every domain.

Run:  python -m scripts.collapse_run
"""
from __future__ import annotations

import inspect
import time

from scripts import collapse_engine as core
from scripts.collapse_engine import evaluate, report
from scripts import collapse_domains as dom


def _self_proof():
    """Show the CORE functions that run every domain are literally identical (one
    source) — the proof that only the plug is swapped. We print the source hash of
    the loop + manifold so the report can assert byte-identity across domains."""
    import hashlib
    src = (inspect.getsource(core.run_collapse)
           + inspect.getsource(core.manifold)
           + inspect.getsource(core.evaluate))
    h = hashlib.sha256(src.encode()).hexdigest()[:16]
    print(f"CORE self-proof: run_collapse+manifold+evaluate source sha256[:16]="
          f"{h}")
    print(f"  the SAME three functions (above hash) execute for every domain "
          f"below — only the DomainPlug argument changes.")
    # also assert the core EXECUTABLE CODE names no domain. We check the runtime
    # symbol table + function bytecode names, NOT the docstrings (the docstrings
    # explain the design and legitimately discuss the domains). If the core's
    # CODE referenced a domain it would show up as a name/const in a code object.
    import types
    leaked = set()
    forbidden = ("word", "letter", "sentence", "librispeech", "llvm", "cochlea",
                 "phoneme", "speaker", "opt_level", "instcombine")
    for obj in vars(core).values():
        if isinstance(obj, types.FunctionType):
            co = obj.__code__
            names = " ".join(co.co_names + co.co_varnames
                             + tuple(str(c) for c in co.co_consts
                                     if isinstance(c, str)
                                     and c is not obj.__doc__)).lower()
            for term in forbidden:
                if term in names:
                    leaked.add(term)
    assert not leaked, f"core CODE leaked domain term(s): {sorted(leaked)}"
    print(f"  core executable code references ZERO domain terms "
          f"(word/letter/sentence/llvm/...): asserted (docstrings exempt).")


def main():
    t0 = time.time()
    print("=" * 72)
    print("COLLAPSE CORE — one loop, pluggable scaffolding")
    print("=" * 72)
    _self_proof()

    print("\nbuilding domain plugs (real data; counts only)...", flush=True)
    plugs = []
    s_plug, n_sents = dom.sentences_plug(n_pool=1200, n_targets=200)
    print(f"  [sentences] {n_sents} unique LibriSpeech sentences; "
          f"pool {len(s_plug.pool)} train {len(s_plug.train)} "
          f"targets {len(s_plug.targets)}", flush=True)
    plugs.append(s_plug)

    l_plug, n_words = dom.letters_plug(n_pool=1500, n_targets=200)
    print(f"  [letters]   {n_words} distinct words as letter-sequences; "
          f"pool {len(l_plug.pool)} train {len(l_plug.train)} "
          f"targets {len(l_plug.targets)}", flush=True)
    plugs.append(l_plug)

    v_plug, n_sched = dom.llvm_plug(n_targets=120)
    print(f"  [llvm]      {n_sched} real opt pass-schedules; "
          f"pool {len(v_plug.pool)} train {len(v_plug.train)} "
          f"targets {len(v_plug.targets)}", flush=True)
    plugs.append(v_plug)

    evals = []
    for plug in plugs:
        print(f"\n>>> running THE ONE CORE on plug '{plug.name}' ...", flush=True)
        tp = time.time()
        ev = evaluate(plug)            # <-- identical call, only `plug` differs
        print(f"    done ({time.time()-tp:.0f}s)", flush=True)
        report(ev)
        evals.append(ev)

    print("\n" + "=" * 72)
    print("CROSS-DOMAIN SUMMARY — same core, plug swapped")
    print("=" * 72)
    print(f"{'domain':>14} | {'H0.1->H0.9':>14} | {'ECE':>6} | "
          f"{'rec-frac':>8} | {'nw t1 real/shuf':>16} | {'gaps':>5} | {'gates'}")
    for ev in evals:
        r = ev.real
        ratio = ev.nw_t1_real / max(ev.nw_t1_shuf, 1e-9)
        gates = "".join("Y" if g else "." for g in
                        (ev.collapses, ev.honest, ev.cohort, ev.seq_driven))
        print(f"{ev.name:>14} | "
              f"{r.ent[0.1]:>5.2f}->{r.ent[0.9]:<6.2f} | {ev.ece:>6.3f} | "
              f"{core._mean(r.rec_points):>8.2f} | "
              f"{ev.nw_t1_real:.3f}/{ev.nw_t1_shuf:.3f}={ratio:>4.1f}x | "
              f"{len(r.gaps):>5} | {gates}")

    n_ok = sum(1 for ev in evals if ev.collapses and ev.cohort)
    n_seq = sum(1 for ev in evals if ev.seq_driven)
    print(f"\nDOMAINS that collapse+cohort through the ONE core: {n_ok}/{len(evals)}")
    print(f"DOMAINS driven by real sequential structure (shuffle control): "
          f"{n_seq}/{len(evals)}")
    print(f"DONKEY AUDIT (all domains counts-only graph-resident): "
          f"{'ALL PASS' if all(ev.donkey_ok for ev in evals) else 'FAIL'}")

    print(f"\n(elapsed {time.time()-t0:.0f}s)")
    print("COLLAPSE_RUN_COMPLETED")


if __name__ == "__main__":
    main()
