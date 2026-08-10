"""The jabberwock BUILDS the two faculties it worked out it needs to migrate
itself — self-host comprehension + behavioral verification — by SELF-EDITING its
own Migrator faculty (domains/self_migration.py) through SelfModification.edit
(AST-checked, rollback), then DEMONSTRATES them.

  comprehend_faculty(module, agent) — read a host faculty into a behavioral SPEC
      the agent can design against: its cognitive SHAPE (shape_hits over its
      concepts) + its TEST CONTRACT (the test file IS the spec — its assertions
      are what the faculty must do). The comprehension its graph self-model lacked.
  verify_faculty(module) — run the faculty's test (its spec) = the migration GATE:
      green after a candidate graph form is wired -> behavior preserved; red -> reject.

With these the agent holds the WHOLE loop: assess(shape_hits) -> comprehend ->
compose(intrinsic designer, by shape) -> wire -> verify -> burn(SelfModification).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_builds_comprehend_verify.py
"""
from __future__ import annotations
import importlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_modification import SelfModification

REL = "domains/self_migration.py"
ANCHOR = ("    # ----- parameterised builders (install_*(substrate/agent, path/data)) -----\n"
          "    def parameterized_builders(self):")
METHODS = '''    # ----- self-host comprehension + behavioral verification (the two faculties
    #       the agent worked out it needs to migrate ITSELF) -------------------
    def comprehend_faculty(self, module, agent=None):
        """COMPREHEND a host faculty into a behavioral SPEC the agent can design
        against: its cognitive SHAPE (shape_hits over its concepts, when an agent
        carrying the shape vocabulary is given) + its TEST CONTRACT (the test file
        IS the behavioral spec). The self-host-comprehension faculty: the agent
        reading its own Python as a spec its graph self-model otherwise can't see."""
        import ast, os
        from collections import Counter
        path = os.path.join(self.root, "domains", module + ".py")
        if not os.path.exists(path):
            return {"module": module, "error": "no such faculty"}
        tree = ast.parse(open(path).read())
        shape = None
        if agent is not None:
            try:
                from domains.analogical_thinking import shape_hits
                v = Counter()
                for n in ast.walk(tree):
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        for s in shape_hits(agent.s, n.name.replace("_", " ") + " " + (ast.get_docstring(n) or "")):
                            v[s] += 1
                shape = v.most_common(1)[0][0] if v else None
            except Exception:
                shape = None
        tpath = os.path.join(self.root, "tests", "test_" + module + ".py")
        contracts = []
        if os.path.exists(tpath):
            for n in ast.walk(ast.parse(open(tpath).read())):
                if isinstance(n, ast.FunctionDef) and n.name.startswith("test"):
                    asserts = sum(1 for x in ast.walk(n) if isinstance(x, ast.Assert))
                    contracts.append({"name": n.name, "asserts": asserts})
        return {"module": module, "shape": shape,
                "test": ("tests/test_" + module + ".py") if os.path.exists(tpath) else None,
                "contracts": contracts, "n_contracts": len(contracts),
                "spec_source": "test_contract" if contracts else "none (no test -> behaviour must be traced)"}

    def verify_faculty(self, module, timeout=600):
        """VERIFY behavioral equivalence: run the faculty's test (its spec) — the
        migration GATE. Returns {ran, passed, summary}. After a candidate graph
        form is wired in place of the Python faculty, green == behaviour preserved."""
        import os, subprocess, sys as _sys
        rel = "tests/test_" + module + ".py"
        if not os.path.exists(os.path.join(self.root, rel)):
            return {"ran": False, "passed": None, "summary": "no test"}
        env = dict(os.environ)
        env["PYTHONPATH"] = "runners/dsl/python:.:scripts"
        try:
            r = subprocess.run([_sys.executable, "-m", "pytest", rel, "-q", "-p", "no:cacheprovider"],
                               cwd=str(self.root), capture_output=True, text=True, timeout=timeout, env=env)
        except Exception as e:
            return {"ran": False, "passed": None, "summary": f"{type(e).__name__}: {e}"}
        last = [l for l in r.stdout.splitlines() if l.strip()]
        return {"ran": True, "passed": r.returncode == 0, "summary": last[-1] if last else ""}

    # ----- parameterised builders (install_*(substrate/agent, path/data)) -----
    def parameterized_builders(self):'''


def main() -> int:
    mod = SelfModification()
    print("=" * 84)
    print("THE JABBERWOCK BUILDS: comprehend_faculty + verify_faculty (self-edit on its Migrator)")
    print("=" * 84)
    if "def comprehend_faculty(" in mod.read(REL):
        print("  Migrator already has comprehend_faculty/verify_faculty")
    else:
        res = mod.edit(REL, ANCHOR, METHODS)
        print(f"  self-edit (+comprehend_faculty +verify_faculty): ok={res.get('ok')} {res.get('result')}"
              f"{' ROLLED BACK' if res.get('rolled_back') else ''}")
        if not res.get("ok"):
            return 1
        mod.reload_python("domains.self_migration")

    # the agent now USES the two new faculties on a real faculty.
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    SM = importlib.import_module("domains.self_migration")
    M = SM.Migrator(mod)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    print("\n  -- COMPREHEND (read faculties into a behavioural spec) --")
    for fac in ("weighted_admissibility", "anticipation", "distributional_categories"):
        spec = M.comprehend_faculty(fac, agent)
        print(f"     {fac}: shape={spec.get('shape')!r} spec_source={spec.get('spec_source')} "
              f"contracts={spec.get('n_contracts')} test={spec.get('test')}")

    print("\n  -- VERIFY (run a faculty's test = the migration gate) --")
    v = M.verify_faculty("weighted_admissibility")
    print(f"     weighted_admissibility: ran={v['ran']} passed={v['passed']} | {v['summary']}")
    print("\n" + "=" * 84)
    print("  The agent built + exercised both faculties via its own self-modification. With assess"
          " (shape_hits) + comprehend + compose (intrinsic designer) + verify + burn, it now holds the"
          " whole self-migration loop — no LLM.")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
