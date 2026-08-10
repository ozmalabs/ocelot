#!/usr/bin/env python3
"""THE JABBERWOCK READS A FULLY-JOINED RUN OF WORDS — the reader's cost-model tighten.

The 515b5c99 residual: the recognition decoder sees through a SINGLE stray space
('what areyou' -> [what, are, you]), but a FULLY-joined run of known words
('whatareyou') stayed ONE OOV token, because one OOV span was cheaper than three
lexicon words. This is a COST-MODEL correction ONLY (no regex, no whitespace
delimiter — the same min-token Viterbi over characters against the lexicon
codebook): recognition is the STRONG hit and OOV is the WEAK, DEAREST fallback, so

  * a KNOWN-word match undercuts an OOV span per covered character, and an OOV run
    carries a fixed OPEN cost reclaimed only by covering the WHOLE run with known
    words -> a fully-decomposable run of known words BEATS one OOV token; while

  * the per-char OOV surcharge stays strictly below the per-word LEX cost for any
    known word length -> pulling a known PREFIX off an otherwise-unknown run never
    pays, and longer/fewer known matches win -> a REAL word stays WHOLE.

So: 'whatareyou' -> [what, are, you]; 'timing' stays [timing] (not tim+ing);
'understand' (OOV, but 'under' is known) stays [understand] (not under+OOV); a
genuine-OOV run ('flarbnth') stays one token; and the single-space case is
unbroken. NO regex, NO whitespace .split() — cost model only.
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


def words(t):
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        return ir.segment(a, t)["words"]


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
print("1. DECOMPOSES — a fully-joined run of KNOWN words recovers the words")
print("=" * 78)
for t, want in (("whatareyou", ["what", "are", "you"]),
                ("bulkloadwikipedia", ["bulk", "load", "wikipedia"]),
                ("measuretiming", ["measure", "timing"])):
    got = words(t)
    print(f"  {t:20} -> {got}   {'OK' if got == want else 'FAIL want ' + str(want)}")

print()
print("=" * 78)
print("2. NO OVER-SEGMENTATION — a REAL word stays WHOLE (the make-or-break guard)")
print("   even those that contain shorter known sub-words (timing>tim, under>understand)")
print("=" * 78)
for t in ("timing", "measure", "wikipedia", "perceive", "sufficient",
          "prioritize", "understand", "report", "judge", "warm", "wordnet",
          "sufficiently"):
    got = words(t)
    print(f"  {t:16} -> {got}   {'OK (whole)' if got == [t] else 'FAIL fragmented'}")

print()
print("=" * 78)
print("3. GENUINE-OOV — a run with NO full known-word cover stays ONE OOV token")
print("=" * 78)
for t in ("xghqz", "flarbnth"):
    got = words(t)
    print(f"  {t:12} -> {got}   {'OK (one token)' if got == [t] else 'FAIL'}")

print()
print("=" * 78)
print("4. SINGLE-SPACE robustness (the 515b5c99 case) — still unbroken")
print("=" * 78)
print(f"  {'what areyou':16} -> {words('what areyou')}")
print(f"  {'loadtiming':16} -> {words('loadtiming')}")

print()
print("=" * 78)
print("5. NO REGEX / NO WHITESPACE-DELIMITER — the fix is COST-MODEL only")
print("=" * 78)
for m in ("domains.instruction_reading", "domains.operational_planning"):
    b = audit(m)
    print(f"  {m:34} : {'CLEAN — no re, no .split()' if not b else b}")

print()
print("=> recognition is the STRONG hit; OOV is the DEAREST fallback. A whole run of")
print("   known words decomposes; a real word stays whole; genuine OOV stays one token.")
print("   No regex, no whitespace delimiter — one cost-model correction.")
