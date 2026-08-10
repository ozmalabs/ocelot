"""Make it so the JABBERWOCK can do the migration ITSELF.

The agent already owns SelfModification (edit/burn/check/rollback). This gives it
the full domains/ -> graph-native MIGRATION as its own faculty: the agent adds a
`migrate()` method to its SelfModification (via SELF-EDIT, AST-checked, rollback)
that delegates to the Migrator capability (domains/self_migration.py — discover
dead boats, prove builder graph-equivalence, capture-to-seed, burn). After this,
the agent runs the whole migration with `self_mod.migrate(apply=..., builders=...)`
— no external script, no LLM. The driver only installs + demonstrates; the
decision-free analysis is mechanical and the deletions are the agent's burn.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_gains_migration_faculty.py
"""
from __future__ import annotations
import importlib, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.self_modification import SelfModification

REL = "domains/self_modification.py"
ANCHOR = ("    # --- checks -------------------------------------------------------------\n"
          "    def check(self, relpath: str) -> tuple[bool, str]:")
METHOD = (
    "    # --- migration (the agent's own domains/ -> graph-native burn) ---------\n"
    "    def migrate(self, apply: bool = False, builders: bool = False) -> dict:\n"
    '        """Run the agent\'s OWN migration: discover dead-boat domains/*.py\n'
    "        (referenced by nothing) and, with apply, BURN them via self.burn; with\n"
    "        builders=True also capture+burn the seed-builders the seed boot\n"
    "        reproduces. Delegates to the Migrator capability. apply=False = dry\n"
    '        run. The agent can now migrate itself with no external script."""\n'
    "        from domains.self_migration import Migrator\n"
    "        return Migrator(self).run(apply=apply, builders=builders)\n"
    "\n"
    + ANCHOR
)


def main() -> int:
    mod = SelfModification()
    print("=" * 84)
    print("THE JABBERWOCK GAINS ITS OWN MIGRATION FACULTY")
    print("=" * 84)
    if "def migrate(" in mod.read(REL):
        print("  SelfModification already has migrate()")
    else:
        res = mod.edit(REL, ANCHOR, METHOD)
        print(f"  self-edit (+migrate): ok={res.get('ok')} {res.get('result')} "
              f"{'ROLLED BACK' if res.get('rolled_back') else ''}")
        if not res.get("ok"):
            print("  install failed; faculty untouched.")
            return 1
        mod.reload_python("domains.self_modification")

    # the agent now runs the migration ITSELF (dry run — discover only).
    SM = importlib.import_module("domains.self_modification")
    agent_mod = SM.SelfModification()
    print("\n  the agent runs migrate(apply=False, builders=True) via its OWN faculty:")
    report = agent_mod.migrate(apply=False, builders=True)
    print(f"     orphan dead boats found: {len(report.get('orphans', []))}")
    b = report.get("builders", {})
    print(f"     builders: equivalent={len(b.get('equivalent', []))} "
          f"gaps={len(b.get('gaps', []))} in_use={len(b.get('in_use', []))} "
          f"unverifiable={len(b.get('unverifiable', []))}")
    if report.get("orphans"):
        print(f"     (orphans it would burn: {report['orphans'][:8]}{'...' if len(report['orphans'])>8 else ''})")
    print("\n" + "=" * 84)
    print("  The jabberwock can now run the migration itself: self_mod.migrate(apply=True[, "
          "builders=True]) — discover + capture + burn, all via its own faculty, no LLM.")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
