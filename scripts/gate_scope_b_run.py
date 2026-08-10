"""Drive the SCOPE B sweep. One JSON row per gate, written incrementally so a
truncated run is a PARTIAL RESULT rather than nothing.

ON RESTORATION, AND A DEFECT MEASURED IN `gate_inject` ITSELF
------------------------------------------------------------
`gate_inject.planted` restores in a `finally`, and its docstring claims that
"a gate that raises, a pytest that segfaults or a KeyboardInterrupt cannot
leave a defect in the tree". **That claim is false for a SIGNAL.** This sweep
was stopped with `pkill` mid-plant and left

    domains/comprehend_text.py  +8   (a planted hardcoded word list)

in the working tree -- a defect in a landed adapter, indistinguishable from a
real one to anything that read the file next. `finally` does not run on
SIGTERM/SIGKILL. Measured, not reasoned about: `git status` showed the file
modified after the kill.

Two repairs, both here rather than in `gate_inject` (§11 rule 4 -- that file
belongs to the rung that wrote it, and the FINDING is reported instead):
  * SIGTERM/SIGINT/SIGHUP are trapped and re-raised as `KeyboardInterrupt`,
    which `finally` DOES run for;
  * the sweep refuses to start against a dirty audited tree and re-checks
    when it finishes, so a leaked plant is LOUD instead of silently becoming
    the next reader's baseline.
"""
import json, os, signal, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_scope_b import ROOT, scope_b, probe_gate
import ast as _ast


def _gate_source(testfile: str, name: str) -> str:
    """The gate's OWN source, by AST identity. Passed to `probe_gate` so an
    INERT verdict can be distinguished from an OUT-OF-SCOPE one -- the pilot
    conflated them and would have accused a narrow-but-working gate."""
    with open(os.path.join(ROOT, "tests", testfile), encoding="utf-8") as fh:
        src = fh.read()
    for n in _ast.walk(_ast.parse(src)):
        if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef)) and n.name == name:
            return _ast.get_source_segment(src, n) or ""
    return ""
from gate_inject import run_gate


def _dirty() -> list[str]:
    """Audited-tree files with uncommitted changes. `domains/` and `seeds/` are
    where plants land; a dirty one at start or end is a leak."""
    out = subprocess.run(["git", "status", "--porcelain", "domains", "seeds"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [ln for ln in out.splitlines() if ln.strip()]


def _die(signum, _frame):
    raise KeyboardInterrupt(f"signal {signum}")


for _sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(_sig, _die)

out_path = sys.argv[1]
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9

pre = _dirty()
if pre:
    sys.exit("REFUSING TO START -- audited tree is dirty:\n" + "\n".join(pre))

pop = [(f, n, t) for f, n, t in scope_b() if t][lo:hi]
done = set()
if os.path.exists(out_path):
    for line in open(out_path):
        done.add(json.loads(line)["node"])

try:
    with open(out_path, "a") as fh:
        for i, (f, n, targets) in enumerate(pop):
            node = f"tests/{f}::{n}"
            if node in done:
                continue
            t0 = time.time()
            base_ok, base_out = run_gate(node)
            rows = []
            for tgt, qual in targets:
                r = probe_gate(node, tgt, qual, base_ok=base_ok,
                               base_out=base_out, test_src=_gate_source(f, n))
                r["qualname"] = qual
                rows.append(r)
            verdicts = [r["verdict"] for r in rows]
            # ALIVE dominates: a gate proven able to fail on ANY of its targets
            # is alive. INERT is only claimed when a plant LANDED and nothing
            # reddened -- never when every plant missed.
            overall = ("BASELINE-RED" if "BASELINE-RED" in verdicts else
                       "ALIVE" if "ALIVE" in verdicts else
                       "INERT" if "INERT" in verdicts else
                       "OUT-OF-SCOPE" if "OUT-OF-SCOPE" in verdicts else verdicts[0])
            rec = {"node": node, "verdict": overall, "rows": rows,
                   "secs": round(time.time() - t0, 1)}
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            print(f"[{lo+i+1}/{lo+len(pop)}] {overall:16s} {node} ({rec['secs']}s)",
                  flush=True)
finally:
    post = _dirty()
    if post:
        print("LEAKED PLANT -- audited tree dirty on exit:\n" + "\n".join(post),
              file=sys.stderr, flush=True)
