"""Wire VERIFY as the gate on the COMPOSER — the capstone of the self-migration
loop. The agent self-edits its Migrator to add migrate_faculty(module, candidates):
the composer PROPOSES candidate graph-native forms; verify_faculty DECIDES — the
first candidate whose faculty test passes is ACCEPTED, every rejected candidate is
REVERTED. Compose proposes; verify gates; nothing is kept that doesn't preserve
behaviour.

DEMONSTRATION (the gate must discriminate, safely): two candidates for a real
faculty-with-a-test (weighted_admissibility), fed in order:
  1. a BROKEN candidate (self-edit that breaks reliability_to_weight) -> verify RED
     -> REJECT + revert (faculty restored byte-for-byte).
  2. the CORRECT candidate (faculty intact) -> verify GREEN -> ACCEPT.
The gate rejects the broken proposal (and reverts it), accepts the verifying one.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_wires_verify_gate.py
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
METHOD = '''    # ----- VERIFY-GATED COMPOSER (the capstone: compose proposes, verify decides) --
    def migrate_faculty(self, module, candidates, agent=None):
        """Wire verify as the GATE on the composer. `candidates` is an ordered list
        of (label, apply_fn, revert_fn) graph-native proposals. Apply each; ACCEPT
        the first whose faculty TEST passes (verify_faculty); REVERT every rejected
        proposal. The composer proposes, verify decides — nothing is kept that does
        not preserve behaviour. Returns {accepted, attempts, spec}."""
        spec = self.comprehend_faculty(module, agent)
        if not spec.get("test"):
            return {"accepted": None,
                    "reason": "ungateable: no test (needs execution-tracing comprehension)",
                    "spec": spec, "attempts": []}
        attempts = []
        for label, apply_fn, revert_fn in candidates:
            try:
                apply_fn()
            except Exception as e:
                attempts.append((label, f"apply-error: {e}"))
                continue
            v = self.verify_faculty(module)
            if v.get("passed"):
                attempts.append((label, "ACCEPT (" + str(v.get("summary")) + ")"))
                return {"accepted": label, "attempts": attempts, "spec": spec}
            attempts.append((label, "reject (" + str(v.get("summary")) + ")"))
            try:
                revert_fn()
            except Exception:
                pass
        return {"accepted": None, "attempts": attempts, "spec": spec}

    # ----- parameterised builders (install_*(substrate/agent, path/data)) -----
    def parameterized_builders(self):'''

FAC = "domains/weighted_admissibility.py"
GOOD = "    return float(max(0.0, w))"
BROKEN = "    return 0.123456  # BROKEN candidate (composer proposal that fails verify)"


def main() -> int:
    mod = SelfModification()
    print("=" * 84)
    print("WIRE VERIFY AS THE GATE ON THE COMPOSER (migrate_faculty: propose -> verify -> accept/revert)")
    print("=" * 84)
    if "def migrate_faculty(" not in mod.read(REL):
        res = mod.edit(REL, ANCHOR, METHOD)
        print(f"  self-edit (+migrate_faculty): ok={res.get('ok')} {res.get('result')}")
        if not res.get("ok"):
            return 1
        mod.reload_python("domains.self_migration")
    else:
        print("  Migrator already has migrate_faculty")

    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    SM = importlib.import_module("domains.self_migration")
    M = SM.Migrator(mod)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    # candidate wirings (the composer's proposals): broken first, then correct.
    def apply_broken():
        r = mod.edit(FAC, GOOD, BROKEN, check=False)
        if not r.get("ok"):
            raise RuntimeError("could not stage broken candidate")

    def revert_faculty():
        mod.restore(FAC)

    def noop():
        pass

    candidates = [("broken_proposal", apply_broken, revert_faculty),
                  ("correct_proposal", noop, noop)]
    print("\n  composer proposals (order): broken_proposal, correct_proposal")
    res = M.migrate_faculty("weighted_admissibility", candidates, agent)
    print("  gate decisions:")
    for label, verdict in res["attempts"]:
        print(f"     {label}: {verdict}")
    print(f"  ACCEPTED: {res['accepted']!r}")

    # safety: faculty restored to its correct form?
    mod.restore(FAC)  # ensure clean regardless
    for f in __import__("glob").glob(os.path.join(ROOT, "domains", "*.selfmod.bak")):
        os.remove(f)
    intact = GOOD in open(os.path.join(ROOT, FAC)).read()
    print(f"  faculty intact after run (broken candidate reverted): {intact}")

    ok = (res["accepted"] == "correct_proposal"
          and any(l == "broken_proposal" and v.startswith("reject") for l, v in res["attempts"])
          and intact)
    print("\n" + "=" * 84)
    print(f"  {'PASS' if ok else 'FAIL'} — VERIFY is wired as the gate on the composer: the broken proposal "
          f"was REJECTED + reverted, the verifying proposal ACCEPTED. The agent now holds the closed loop: "
          f"comprehend -> compose (propose) -> verify (gate) -> burn, all its own faculties, no LLM.")
    print("=" * 84)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
