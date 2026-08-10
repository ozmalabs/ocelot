"""Teach discover_orphans to recognise ALLOWED PYTHON (CLAUDE.md).

discover_orphans flagged relation_ingest / shape_generation_programs as dead boats
because they're wired via graph data / dynamic routes, not Python imports. But per
CLAUDE.md those are ALLOWED Python — a Term/graph-data BUILDER and an ingest
ADAPTER — and the right response to such an unreferenced module is to RE-WIRE it,
never to auto-burn it. The detector already excluded install_*_seed builders; this
teaches it the rest of the allowed-Python shapes, so its burnable list contains
ONLY genuinely-inert Python and the allowed-but-unwired modules surface separately.

The agent self-edits its own Migrator (SelfModification):
  _is_allowed_python(module) — True if the module emits graph data ({"type":..}
      Term dicts, install_*_seed/*_program/build_*/make_* builders) or is a world
      ADAPTER (mechanical substrate I/O: .nodes(/.node(/.add_node(/.add_edge(, or
      ingest_*/emit_* functions).
  discover_orphans(include_allowed=False) — now returns only TRUE dead boats
      (inert + unreferenced); allowed-Python is excluded.
  discover_unwired() — the unreferenced allowed-Python (RE-WIRE candidates).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_teaches_orphan_detector.py
"""
from __future__ import annotations
import importlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_modification import SelfModification

REL = "domains/self_migration.py"

OLD = '''    def discover_orphans(self):
        domains, refs = self._referenced(roots_only=False)
        builders = set(self._builders())
        return sorted(domains - refs - builders)'''

NEW = '''    def discover_orphans(self, include_allowed=False):
        """domains/*.py referenced by NOTHING. By default returns only TRUE dead
        boats — inert Python that is NEITHER a seed-builder NOR allowed-Python.
        Allowed-Python (a Term/graph-data builder or a world adapter) is a RE-WIRE
        candidate, not a burn (see discover_unwired); the import graph can't see
        graph-data/dynamic wiring, so such a module must never be auto-burned.
        include_allowed=True returns every unreferenced module (the raw set)."""
        domains, refs = self._referenced(roots_only=False)
        builders = set(self._builders())
        unref = domains - refs - builders
        if include_allowed:
            return sorted(unref)
        return sorted(m for m in unref if not self._is_allowed_python(m))

    def discover_unwired(self):
        """Unreferenced ALLOWED-Python (Term/graph-data builders, world adapters) —
        capable code that is merely import-unwired. RE-WIRE candidates (restore
        access + a guarding test), NOT dead boats. A capability is only 'orphaned'
        w.r.t. the IMPORT graph; graph-wired/dynamically-routed code needs a test to
        pin it (as relation_ingest / shape_generation_programs were re-wired)."""
        domains, refs = self._referenced(roots_only=False)
        builders = set(self._builders())
        unref = domains - refs - builders
        return sorted(m for m in unref if self._is_allowed_python(m))

    def _is_allowed_python(self, module, src=None):
        """Recognise ALLOWED Python (CLAUDE.md) that must NOT be treated as a dead
        boat even when import-unreferenced: a Term/graph-data BUILDER (emits
        {"type": "..."} Term dicts, or install_*_seed / *_program / build_* / make_*
        graph-data builders) or an ingest/emit world ADAPTER (mechanical substrate
        I/O: .nodes( / .node( / .add_node( / .add_edge(, or ingest_* / emit_*
        functions). Such a module is a RE-WIRE candidate, never an auto-burn."""
        import ast as _ast, os as _os, re as _re
        if src is None:
            p = _os.path.join(self.root, "domains", module + ".py")
            if not _os.path.exists(p):
                return False
            src = open(p).read()
        if ('"type":' in src) or ("'type':" in src):           # emits Term dicts
            return True
        if any(t in src for t in (".add_node(", ".add_edge(", ".nodes(", ".node(")):
            return True                                          # mechanical substrate I/O (adapter)
        try:
            tree = _ast.parse(src)
        except Exception:
            return False
        for n in _ast.walk(tree):
            if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                nm = n.name
                if (_re.match(r"install_\\w+_seed$", nm) or nm.endswith("_program")
                        or nm.startswith(("build_", "make_", "ingest_", "emit_"))):
                    return True
        return False'''


def main() -> int:
    mod = SelfModification()
    print("=" * 90)
    print("TEACH discover_orphans TO RECOGNISE ALLOWED-PYTHON (self-edit on the Migrator)")
    print("=" * 90)
    if "_is_allowed_python" in mod.read(REL):
        print("  [skip] already taught")
    else:
        r = mod.edit(REL, OLD, NEW)
        print(f"  [edit] +_is_allowed_python +discover_unwired, discover_orphans excludes allowed: "
              f"ok={r.get('ok')}{' ROLLED BACK' if r.get('rolled_back') else ''}")
        if not r.get("ok"):
            print(f"         {r.get('result')}")
            return 1
        mod.reload_python("domains.self_migration")

    SM = importlib.import_module("domains.self_migration")
    M = SM.Migrator(mod)

    print("\n  classifier on the 2 re-wired keystones (allowed-Python -> True):")
    for m in ("relation_ingest", "shape_generation_programs"):
        print(f"     _is_allowed_python({m!r}) = {M._is_allowed_python(m)}")

    print("\n  discriminates: a genuinely-INERT module is NOT allowed-Python -> False:")
    inert = "def f(a, b):\n    return a * b + 1\n\nVALUE = 42\n"
    print(f"     _is_allowed_python('<inert pure-arithmetic>') = {M._is_allowed_python('x', src=inert)}")

    print("\n  detector state now:")
    print(f"     discover_orphans()            = {M.discover_orphans()}   (TRUE dead boats: safe to burn)")
    print(f"     discover_orphans(include_allowed=True) = {M.discover_orphans(include_allowed=True)}   (raw unreferenced)")
    print(f"     discover_unwired()            = {M.discover_unwired()}   (allowed-Python, re-wire candidates)")

    ok = (M._is_allowed_python("relation_ingest") and M._is_allowed_python("shape_generation_programs")
          and not M._is_allowed_python("x", src=inert))
    print("\n" + "=" * 90)
    print(f"  {'PASS' if ok else 'FAIL'} — discover_orphans now recognises allowed-Python: a Term/graph-data "
          f"builder or world adapter is a RE-WIRE candidate (discover_unwired), never a dead boat. The burnable "
          f"list is conservative+trustworthy; allowed-but-unwired code surfaces separately. No LLM.")
    print("=" * 90)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
