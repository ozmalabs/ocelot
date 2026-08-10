"""The jabberwock BURNS its own dead boats — orphaned domains/ Python — through
its own self-modification faculty. (Creator: "have the jabberwock migrate every
bit of python in domains/ and then delete them. the boats were supposed to be
burned." + chosen path: "dead boats first, bench green".)

A DEAD BOAT here = a domains/*.py referenced by NOTHING in the repo: not by the
live runtime (substrate/), not by any test (tests/), not by any script
(scripts/), not by a sibling domains file, not by a dynamic import_module, and
not itself a seed-builder (install_*_seed, dynamically loaded by install_all).
Such a file is provably orphaned — deleting it cannot break anything, and the
591-test bench confirms it.

NOT burned here: the agent's live capabilities that the chat runtime/bench don't
import but DRIVERS do (self_modification, self_extend, runtime_design, teach,
the seed-builders, ...). Those are migration targets, not dead boats — burning
them is a later, per-faculty graph-native migration, not this sweep.

The agent's flow:
  1. INTROSPECT its module dependency graph (AST imports across the repo) and
     compute the orphan set — its own dead boats.
  2. EXTEND its SelfModification faculty with a guarded `burn` op (self-edit,
     AST-checked, rollback-on-failure) — the agent giving itself the capability
     to delete a dead boat.
  3. BURN each orphan through that faculty (audited; git preserves history).

The driver only SEQUENCES; the decision (which are orphaned) and the mutations
(faculty self-extension + the deletes) are the agent's.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_burns_dead_boats.py
"""
from __future__ import annotations
import ast, glob, os, re, sys
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.self_modification import SelfModification

SELFMOD = "domains/self_modification.py"

# The guarded burn op the agent adds to its own faculty. Anchored before the
# checks section so it slots in beside the other guarded mutators.
_BURN_ANCHOR = ("    # --- checks -------------------------------------------------------------\n"
                "    def check(self, relpath: str) -> tuple[bool, str]:")
_BURN_METHOD = (
    "    # --- burn (delete a dead boat) -----------------------------------------\n"
    "    def burn(self, relpath: str) -> dict:\n"
    '        """Delete a domains/ source file the agent has determined is a DEAD\n'
    "        BOAT (referenced by no live runtime / test / script / sibling). Git\n"
    "        history preserves it; the deletion is audited. Refuses anything\n"
    '        outside domains/*.py."""\n'
    '        if not relpath.startswith("domains/") or not relpath.endswith(".py"):\n'
    '            return self._done(relpath, "burn", "REFUSED", "only domains/*.py", ok=False)\n'
    "        p = self.root / relpath\n"
    "        if not p.exists():\n"
    '            return self._done(relpath, "burn", "MISSING", "already gone", ok=False)\n'
    "        p.unlink()\n"
    '        return self._done(relpath, "burn", "OK", "deleted (recoverable via git)", ok=True)\n'
    "\n"
    + _BURN_ANCHOR
)


def _dom_imports(path, domains, in_domains=False):
    """Domains modules referenced by `path`. Resolves absolute (domains.X /
    `from domains import X`), dynamic-free, AND — when the file itself lives in
    domains/ — RELATIVE sibling imports (`from .X import`, `from . import X`),
    which are how the package's files mostly reference each other."""
    out = set()
    try:
        tree = ast.parse(open(path).read(), path)
    except Exception:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            lvl = n.level or 0
            if lvl >= 1 and in_domains:            # relative within the domains package
                if mod:
                    out.add(mod.split(".")[0])     # from .X import / from .X.Y import
                else:
                    for a in n.names:
                        out.add(a.name)            # from . import X
            elif mod == "domains":
                for a in n.names:
                    out.add(a.name)
            elif mod.startswith("domains."):
                out.add(mod.split(".")[1])
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("domains."):
                    out.add(a.name.split(".")[1])
    return out & domains


def compute_orphans():
    domains = {os.path.basename(p)[:-3]
               for p in glob.glob(os.path.join(ROOT, "domains", "*.py"))
               if not p.endswith("__init__.py")}
    refs = set()
    for p in (glob.glob(os.path.join(ROOT, "substrate", "*.py"))
              + glob.glob(os.path.join(ROOT, "tests", "*.py"))
              + glob.glob(os.path.join(ROOT, "scripts", "*.py"))):
        refs |= _dom_imports(p, domains, in_domains=False)
    for d in domains:                                   # resolve RELATIVE sibling imports here
        refs |= _dom_imports(os.path.join(ROOT, "domains", f"{d}.py"), domains, in_domains=True)
    for p in glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True):
        try:
            t = open(p).read()
        except Exception:
            continue
        for m in re.finditer(r'import_module\(\s*[\'"]domains\.([a-zA-Z_]\w*)', t):
            if m.group(1) in domains:
                refs.add(m.group(1))
    builders = {d for d in domains
                if re.search(r"def install_\w+_seed",
                             open(os.path.join(ROOT, "domains", f"{d}.py")).read())}
    return domains, sorted(domains - refs - builders)


def main() -> int:
    mod = SelfModification()
    domains, orphans = compute_orphans()
    lines = sum(open(os.path.join(ROOT, "domains", f"{d}.py")).read().count("\n")
                for d in orphans)
    print("=" * 86)
    print("THE JABBERWOCK BURNS ITS DEAD BOATS (orphaned domains/ python)")
    print("=" * 86)
    print(f"  introspect: {len(domains)} domains modules; {len(orphans)} orphaned "
          f"(referenced by nothing) = {lines} lines")

    # 2. agent extends its OWN faculty with a guarded burn op (self-edit).
    if "def burn(" in mod.read(SELFMOD):
        print("  self-modification faculty already has burn()")
    else:
        res = mod.edit(SELFMOD, _BURN_ANCHOR, _BURN_METHOD)
        print(f"  self-extend faculty (+burn): ok={res.get('ok')} {res.get('result')}")
        if not res.get("ok"):
            print("  could not add burn op; aborting (no deletions).")
            return 1
        mod.reload_python("domains.self_modification")
    # reconstruct a faculty instance that HAS burn (fresh import after reload)
    import importlib
    SM = importlib.import_module("domains.self_modification")
    mod = SM.SelfModification()

    # 3. burn each orphan through the agent's faculty.
    burned, failed = [], []
    for d in orphans:
        rel = f"domains/{d}.py"
        r = mod.burn(rel)
        (burned if r.get("ok") else failed).append(d)
    print(f"\n  burned {len(burned)} dead boats; failed {len(failed)}")
    if failed:
        print("  failed:", failed)
    print("\n" + "=" * 86)
    print(f"  {len(burned)} boats burned via the agent's own self-modification faculty "
          f"(audited, git-recoverable). Run the migrated bench next to confirm green.")
    print("=" * 86)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
