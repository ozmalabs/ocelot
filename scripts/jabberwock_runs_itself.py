#!/usr/bin/env python3
"""THE PAYOFF: feed the WHOLE assess-and-improve cycle as ONE operational instruction
and have the jabberwock PLAN it and RUN it ITSELF — no human sequencing. Everything the
session built (load, timing, sufficiency, perceive, prioritize, fix/diagnose/verify, stop,
report) driven by the meta-layer (parse_instruction -> run_plan) from a single instruction."""
import sys, os, io, contextlib
from pathlib import Path
ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT/"runners"/"dsl"/"python"), str(ROOT/"scripts")):
    sys.path.insert(0, p)
os.chdir(ROOT)
buf = io.StringIO()
with contextlib.redirect_stderr(buf):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.operational_planning as op

def quiet(fn, *a, **k):
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        return fn(*a, **k)

# THE WHOLE assess-and-improve cycle, as one arbitrary-length, multi-layer instruction:
INSTRUCTION = (
    "Bulk load Wikipedia. "
    "Measure the load timing and judge whether it is sufficiently fast; "
    "if it is not fast enough, warm up wordnet. "
    "Then perceive the other gaps and prioritize them; "
    "for each gap you find, if it is worth fixing, fix it. "
    "Stop when the rest is sufficient. "
    "Finally report what was loaded and which gaps were fixed."
)

with contextlib.redirect_stderr(buf):
    a = WorldAdapter(seeds=()); load_all_seeds(a)

print("THE JABBERWOCK RUNS ITSELF — one instruction, planned + orchestrated by the agent\n")
print("INSTRUCTION (the whole assess-and-improve cycle):")
print(f'  "{INSTRUCTION}"\n')

# 1. PLAN — the jabberwock parses the whole cycle into a plan tree (no human sequencing)
parsed = quiet(op.parse_instruction, a, INSTRUCTION)

def show(step, depth=1):
    ind = "  " * depth
    at = a.s.node(step)["attrs"]
    kind = at.get("kind"); clause = (at.get("clause") or "")[:48]
    cap = at.get("capability")
    extra = f" -> {cap}" if cap else (" [no-match]" if kind == "act" else "")
    print(f"{ind}{kind:8} '{clause}'{extra}")
    for sub in a.inner.neighbours(step, "substep"):
        show(sub, depth + 1)

print("1. PLAN (parse_instruction — the agent decomposed the instruction into a tree):")
print(f"   n top-level steps = {len(parsed.get('steps', []))}")
for s in parsed.get("steps", []):
    show(s)

# 2. RUN — the orchestrator fires the whole plan; the agent does the work
print("\n2. RUN (run_plan — the jabberwock executes its own plan end-to-end):")
res = quiet(op.run_plan, a, parsed, max_load=8)
for t in res.get("trace", []):
    if isinstance(t, str):
        print(f"   {t}"); continue
    kind = t.get("kind", ""); clause = (t.get("clause") or "")[:40]; cap = t.get("capability") or ""
    if t.get("executed"):
        print(f"   [RAN] {cap:16} ({clause})")
        out = t.get("output")
        if out is not None:
            print(f"         -> {str(out)[:150]}")
    elif t.get("note"):
        print(f"   [--]  {kind:8} ({clause}) : {t.get('note')}")
    else:
        print(f"   [ctl] {kind:8} ({clause})")

print("\n=> the WHOLE assess-and-improve cycle was PLANNED and RUN by the jabberwock")
print("   from a single instruction. The human wrote the sentence; the agent did the rest.")
