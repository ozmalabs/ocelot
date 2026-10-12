"""Compare definition-genus readers on the exact genus benchmark (tranche 18).

  A0 t17       the tranche-17 head reader, loaded verbatim from commit f7c016b1
  A  t18       domains/lexical_qualia.definition_genus (tranche-18 head reader)
  B  agent     the agent's own reader: reading_collapse.read_clause_order_n on
               "<word> is <first definition sentence>" -> its is_a genus
  C  agent+t18 B, falling back to A when B names no genus with a noun sense

Writes evaluation/results/genus_reader_compare.json (buckets per reader) and
prints the FREE-TEXT dev/test rows. Usage:
  OZMA_SEED_PERSIST_DISABLED=1 python evaluation/genus_reader_compare.py [readers...]
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from evaluation import genus_reader_benchmark as bench  # noqa: E402

OUT = ROOT / "evaluation" / "results" / "genus_reader_compare.json"


def main(names):
    from domains import lexical_qualia as lq
    held = bench.held_words_cached()
    readers = {"t17": _t17_reader(), "t18": lq.definition_genus}
    if any(n not in readers for n in names):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
        readers["agent"] = lambda w, d: lq.definition_genus_by_reading(a, w, d)
        readers["agent+t18"] = lambda w, d: (lq.definition_genus_by_reading(a, w, d)
                                             or lq.definition_genus(w, d))
    report = json.loads(OUT.read_text()) if OUT.exists() else {}
    for n in names:
        t = time.time()
        r = bench.score(readers[n], held)
        # buckets only: the per-word rows are reproducible from the fixture
        report[n] = {"buckets": r["buckets"], "elapsed_s": round(time.time() - t, 1)}
        b = r["buckets"]
        print("%-10s free:dev %s | free:test %s | gloss:test %s" % (
            n, _fmt(b["free:dev"]), _fmt(b["free:test"]), _fmt(b["gloss:test"])), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")


def _t17_reader():
    """definition_genus exactly as committed in tranche 17 (git show)."""
    import subprocess
    import types
    src = subprocess.run(["git", "show", "f7c016b1:domains/lexical_qualia.py"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    mod = types.ModuleType("lexical_qualia_t17")
    mod.__file__ = str(ROOT / "domains" / "lexical_qualia.py")
    exec(compile(src, "lexical_qualia@f7c016b1", "exec"), mod.__dict__)
    return mod.definition_genus


def _fmt(b):
    return "P=%.3f Ps=%.3f cov=%.3f (n=%d)" % (b["precision"] or 0, b["specific_precision"] or 0,
                                              b["coverage"] or 0, b["n"])


if __name__ == "__main__":
    main(sys.argv[1:] or ["t17", "t18", "agent", "agent+t18"])
