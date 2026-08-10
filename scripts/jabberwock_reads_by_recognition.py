#!/usr/bin/env python3
"""THE JABBERWOCK READS ITS OWN INSTRUCTION BY RECOGNITION — cognition all the way
down to the WORD. The ONLY I/O is raw text -> a CHARACTER stream in the graph; the
WORDS EMERGE by recognition (lexicon decode + forward_segmentation TP-troughs over
the Char stream, whitespace a WEAK cue); the clause/control structure is graph
connective In-Terms + the graph VERB-HEAD Term. NO regex. NO whitespace delimiter.

It shows: (1) the zero-regex/zero-whitespace source audit; (2) missing-whitespace
robustness (recognition right, whitespace .split() wrong); (3) segmentation-by-
recognition (Char stream -> lexicon matches + TP-troughs); (4) the verb-head 'and'
discrimination; (5) the capstone whole-cycle instruction planned correctly.
"""
import sys, os, io, ast, inspect, contextlib
from pathlib import Path
ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    sys.path.insert(0, p)
os.chdir(ROOT)
buf = io.StringIO()
with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.operational_planning as op
    from domains import instruction_reading as ir
    a = WorldAdapter(seeds=()); load_all_seeds(a); op._ensure_seed(a)


def quiet(fn, *A, **K):
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        return fn(*A, **K)


def audit(modname):
    import importlib
    src = inspect.getsource(importlib.import_module(modname))
    bad = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import) and any(x.name.split(".")[0] == "re" for x in n.names):
            bad.append("import re")
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "re":
            bad.append("from re")
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "re":
            bad.append(f"re.{n.attr}")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in ("split", "rsplit", "splitlines"):
            bad.append(f".{n.func.attr}()")
    return bad


print("=" * 78)
print("1. ZERO-REGEX + ZERO-WHITESPACE-DELIMITER SOURCE AUDIT")
print("=" * 78)
for m in ("domains.operational_planning", "domains.instruction_reading"):
    b = audit(m)
    print(f"  {m:34} : {'CLEAN — no re, no .split()' if not b else b}")

print()
print("=" * 78)
print("2. MISSING-WHITESPACE ROBUSTNESS (recognition right; whitespace .split() wrong)")
print("=" * 78)
mis = "bulkload wikipedia. measuretiming and judge whether it is fast"
print(f"  instruction         : {mis!r}")
print(f"  RECOGNITION (right) : {quiet(ir.segment, a, mis)['words']}")
print(f"  .split()    (WRONG) : {mis.split()}")

print()
print("=" * 78)
print("3. SEGMENTATION-BY-RECOGNITION (Char stream -> lexicon matches + TP-troughs)")
print("=" * 78)
seg = quiet(ir.segment, a, "Measure the load timing.")
print(f"  raw text -> {len(seg['char_nodes'])} Char nodes (THE ONLY I/O)")
print(f"  lexicon codebook    : {seg['lexicon_size']} known words (LexEntry + operational + closed-class)")
print(f"  lexicon matches     : {seg['lexicon_matches']}")
print(f"  words (emerged)     : {seg['words']}")
print(f"  joined 'loadtiming' recovered by recognition -> {quiet(ir.segment, a, 'loadtiming')['words']}")

print()
print("=" * 78)
print("4. VERB-HEAD 'and' DISCRIMINATION (same 'and', different split — graph Term)")
print("=" * 78)
for t in ("Warm up wordnet and measure the timing.",
          "Report what was loaded and which gaps were fixed."):
    p = quiet(op.parse_instruction, a, t)
    binds = [a.s.node(s)["attrs"].get("binding_key") for s in p["steps"]]
    print(f"  {t!r}\n     -> {p['n_steps']} step(s): {binds}")
print(f"  verb_headed('warm up wordnet')       = {ir.is_verb_headed('warm up wordnet')}")
print(f"  verb_headed('measure the timing')    = {ir.is_verb_headed('measure the timing')}")
print(f"  verb_headed('which gaps were fixed') = {ir.is_verb_headed('which gaps were fixed')}")

print()
print("=" * 78)
print("5. THE CAPSTONE — the whole assess-and-improve cycle, read by recognition")
print("=" * 78)
CAP = ("Bulk load Wikipedia. Measure the load timing and judge whether it is "
       "sufficiently fast; if it is not fast enough, warm up wordnet. Then perceive "
       "the other gaps and prioritize them; for each gap you find, if it is worth "
       "fixing, fix it. Stop when the rest is sufficient. Finally report what was "
       "loaded and which gaps were fixed.")
parsed = quiet(op.parse_instruction, a, CAP)


def show(step, d=1):
    at = a.s.node(step)["attrs"]; k = at.get("kind"); cl = (at.get("clause") or "")[:44]
    cap = at.get("capability")
    tag = f" -> {cap}" if cap else (f" cond={at.get('cond_phrase')!r}"
                                    if k in ("ifthen", "stop") else "")
    print("   " + "  " * d + f"{k:8} {cl!r}{tag}")
    for s in a.inner.neighbours(step, "substep"):
        show(s, d + 1)


print(f"  n top-level steps = {parsed['n_steps']}  (measure+judge SEPARATE; ifthen->warm "
      "SEPARATE; foreach{{ifthen->fix}}; stop; report LAST)")
for s in parsed["steps"]:
    show(s)
print("\n=> the instruction became a plan WITHOUT one regex or one whitespace split —")
print("   raw chars in, words recognised, clauses decided by graph Terms.")
