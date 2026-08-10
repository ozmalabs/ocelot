"""preamble_audit — DOES THIS ENTRYPOINT PIN THE ENGINE IT MEASURES ON?

A mechanical, read-only AST reporter. It imports no engine, evaluates no
Term, and draws no seed. That independence is the point: it is the
SECOND of two checks on the same invariant, and **it must not be computed
by the machinery it checks** (`domains/engine_provenance.py`).

WHY TWO CHECKS, AND WHY THEY MUST BE DIFFERENT MECHANISMS
----------------------------------------------------------
`engine_provenance.assert_measuring_engine()` answers, at RUNTIME, inside
the measuring process:

    "is the engine resident in THIS process a build of THIS tree's Rust?"

It is the strongest possible form of the question, and it has exactly one
blind spot: **a process that never calls `engine_preamble()` never asks
it.** The known instance is on record — a rung's diagnostic IMPORTED
`engine_preamble` and never CALLED it, and silently loaded the canonical
engine through the `.pth`.

This module answers, STATICALLY, over source:

    "which entrypoints can reach the engine without pinning it first?"

A runtime check cannot see a process that never runs it. A static check
cannot see what a process actually loads. Neither subsumes the other, and
neither is derived from the other's inputs -- so a common-mode failure
has to defeat two unrelated mechanisms.

WHY AST, NEVER SUBSTRING
------------------------
This arc has now lost FOUR selectors to substring matching, the most
recent going red on a DOCSTRING. `grep engine_preamble` cannot tell an
import from a call from a comment from this very paragraph -- which
mentions `engine_preamble()` several times and must not match itself.
So: parse, resolve the BINDING, and look for an `ast.Call` node whose
callee resolves to the imported function. Aliases, module-qualified
calls, and rebindings all fall out of that for free; none of them needs
its own case.

    from domains.engine_provenance import engine_preamble as pin
    pin()                                    # <- CALLED  (alias)

    from domains import engine_provenance
    engine_provenance.engine_preamble()      # <- CALLED  (qualified)

    from domains.engine_provenance import engine_preamble
    # engine_preamble()                      # <- NOT called (comment)

THE THIRD CATEGORY THIS FOUND, WHICH I DID NOT GO LOOKING FOR
--------------------------------------------------------------
`sys.path.insert(0, <tree>/runners/dsl/python)` is the OLD convention
that §10 rule 6 called "safe" and that PROTOCOL §10.2 then measured as
actively harmful in a worktree: it pins a HEADLESS package (the `.py`
files are tracked, `_native.abi3.so` is gitignored) which SHADOWS the
`.pth` and dies with a misleading circular-import error. So a script
doing this is neither "pinned" nor "unpinned" -- it is pinned to a
package that may have no engine in it. It is reported as its own class,
`path_insert_only`, rather than folded into either verdict.

PROTOCOL: §10 rule 3 (any non-pytest entrypoint must call
`engine_preamble()` itself), §10 rule 6, §10.2, §12 (a selector that
matches by substring is not a selector).
"""
from __future__ import annotations

import ast
import os

#: The function every non-pytest entrypoint is required to call (§10 rule 3).
PREAMBLE_FUNC = "engine_preamble"

#: The module it lives in. Both the dotted and the bare form appear in the
#: tree because `scripts/` inserts the repo root on `sys.path`.
PREAMBLE_MODULES = ("domains.engine_provenance", "engine_provenance")

#: The engine package. A module importing this can reach the binary.
ENGINE_PKG = "substrate_rs"

#: The tail of the old §10-rule-6 convention path.
_OLD_CONVENTION = os.path.join("runners", "dsl", "python")


class _Audit(ast.NodeVisitor):
    """Resolve BINDINGS, then look for a Call whose callee is one of them.

    Two binding sets are tracked, because `engine_preamble` can be reached
    two ways and both are legitimate:

      * ``func_names``   -- names bound DIRECTLY to the function
                            (``from ... import engine_preamble [as X]``)
      * ``module_names`` -- names bound to the MODULE
                            (``from domains import engine_provenance``,
                             ``import domains.engine_provenance as ep``)

    A call counts if its callee is a Name in ``func_names`` or an
    Attribute ``<m>.engine_preamble`` where ``<m>`` is in ``module_names``.
    """

    def __init__(self) -> None:
        self.func_names: set[str] = set()
        self.module_names: set[str] = set()
        self.imports_preamble = False
        self.calls_preamble = False
        self.imports_engine = False
        self.path_insert = False
        self.has_main_guard = False

    # -- imports ----------------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.name
            if name == ENGINE_PKG or name.startswith(ENGINE_PKG + "."):
                self.imports_engine = True
            if name in PREAMBLE_MODULES:
                # `import domains.engine_provenance` binds `domains`;
                # `... as ep` binds `ep`. Both reach the function.
                self.module_names.add(alias.asname or name.split(".")[0])
                self.imports_preamble = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        if mod == ENGINE_PKG or mod.startswith(ENGINE_PKG + "."):
            self.imports_engine = True
        if mod in PREAMBLE_MODULES:
            for alias in node.names:
                if alias.name == PREAMBLE_FUNC:
                    self.func_names.add(alias.asname or alias.name)
                    self.imports_preamble = True
        # `from domains import engine_provenance` -- the MODULE is bound.
        if mod in ("domains", "") or mod.endswith(".domains"):
            for alias in node.names:
                if alias.name == "engine_provenance":
                    self.module_names.add(alias.asname or alias.name)
                    self.imports_preamble = True
        self.generic_visit(node)

    # -- calls ------------------------------------------------------------
    def visit_Call(self, node: ast.Call) -> None:
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id in self.func_names:
            self.calls_preamble = True
        elif isinstance(fn, ast.Attribute) and fn.attr == PREAMBLE_FUNC:
            base = fn.value
            if isinstance(base, ast.Name) and base.id in self.module_names:
                self.calls_preamble = True
            elif isinstance(base, ast.Attribute) and base.attr == "engine_provenance":
                self.calls_preamble = True
        elif isinstance(fn, ast.Attribute) and fn.attr == "insert":
            base = fn.value
            if (isinstance(base, ast.Attribute) and base.attr == "path"
                    and isinstance(base.value, ast.Name) and base.value.id == "sys"):
                if _mentions_old_convention(node):
                    self.path_insert = True
        self.generic_visit(node)

    # -- entrypoint shape -------------------------------------------------
    def visit_If(self, node: ast.If) -> None:
        test = node.test
        if (isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and any(isinstance(c, ast.Constant) and c.value == "__main__"
                        for c in test.comparators)):
            self.has_main_guard = True
        self.generic_visit(node)


def _mentions_old_convention(call: ast.Call) -> bool:
    """Does this `sys.path.insert` target `runners/dsl/python`?

    Shape, not text: walk the argument expression for any string constant
    naming the convention's directory, in either separator form. A joined
    path (`os.path.join(ROOT, "runners", "dsl", "python")`) is caught by
    the component form.
    """
    parts: list[str] = []
    for sub in ast.walk(call):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            parts.append(sub.value)
    joined = "/".join(parts).replace("\\", "/")
    return "runners/dsl/python" in joined or _OLD_CONVENTION in joined


def audit_source(src: str, path: str = "<string>") -> dict:
    """Audit one module's SOURCE. Pure; no filesystem, no import."""
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return {"file": path, "parse_error": f"{type(exc).__name__}: {exc}",
                "imports_preamble": False, "calls_preamble": False,
                "imports_engine": False, "path_insert_only": False,
                "entrypoint": False, "verdicts": []}

    a = _Audit()
    a.visit(tree)

    verdicts: list[str] = []
    # (1) THE OBSERVED DEFECT, exactly: bound and never called.
    if a.imports_preamble and not a.calls_preamble:
        verdicts.append("imported_not_called")
    # (2) THE CLASS IT BELONGS TO: an entrypoint that can reach the engine
    #     and never pins it. Covers instances nobody has observed yet --
    #     a detector built only from (1) would cover only (1).
    if a.has_main_guard and a.imports_engine and not a.calls_preamble:
        verdicts.append("engine_without_preamble")

    return {
        "file": path,
        "parse_error": None,
        "imports_preamble": a.imports_preamble,
        "calls_preamble": a.calls_preamble,
        "imports_engine": a.imports_engine,
        "path_insert_only": a.path_insert and not a.calls_preamble,
        "entrypoint": a.has_main_guard,
        "verdicts": verdicts,
    }


def audit_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return audit_source(fh.read(), path)


def audit_tree(roots: list[str], *, base: str | None = None) -> dict:
    """Audit every `.py` under `roots`. Returns files with a verdict, plus
    the parse-error count -- which is this module's OWN unknown-sink
    number, reported for the same reason `seed_audit` reports its own: a
    check that passes with unknown sinks has verified nothing.
    """
    findings: list[dict] = []
    parse_errors: list[str] = []
    path_insert_only: list[str] = []
    scanned = 0
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in {"__pycache__", ".git", "target"})
            for name in sorted(filenames):
                if not name.endswith(".py"):
                    continue
                full = os.path.join(dirpath, name)
                rec = audit_file(full)
                scanned += 1
                rel = os.path.relpath(full, base) if base else full
                rec["file"] = rel
                if rec["parse_error"]:
                    parse_errors.append(rel)
                    continue
                if rec["path_insert_only"]:
                    path_insert_only.append(rel)
                if rec["verdicts"]:
                    findings.append(rec)
    return {
        "scanned": scanned,
        "findings": findings,
        "parse_errors": parse_errors,
        "path_insert_only": sorted(path_insert_only),
        "imported_not_called": sorted(
            f["file"] for f in findings
            if "imported_not_called" in f["verdicts"]),
        "engine_without_preamble": sorted(
            f["file"] for f in findings
            if "engine_without_preamble" in f["verdicts"]),
    }


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ROOTS = ("scripts", "domains", "substrate", "tools")

#: Committed grandfather floor for the `imported_not_called` gate.
FLOOR_PATH = os.path.join(ROOT, "results", "preamble_audit_floor.json")


def audit_repo(root: str = ROOT, roots=DEFAULT_ROOTS) -> dict:
    return audit_tree([os.path.join(root, d) for d in roots], base=root)


def read_floor(path: str = FLOOR_PATH) -> set[str]:
    """Files known to violate §10 rule 3 at the moment the gate shipped.

    NOT an amnesty and NOT a fix — each entry is a live defect, recorded
    so that the gate binds NEW ones instead of being red on arrival (the
    always-red gate is the one agents route around, §10.1). Repairing them
    is the supervisor's to sequence: they are other rungs' files, and §11
    rule 4 says do not edit them.
    """
    import json
    if not os.path.isfile(path):
        return set()
    with open(path, "r", encoding="utf-8") as fh:
        return set(json.load(fh)["known_violations"])


def read_repaired(path: str = FLOOR_PATH) -> set[str]:
    """Files that WERE `imported_not_called` and have since been REPAIRED.

    THE FLOOR HAD TO BE ABLE TO REACH ZERO. As shipped, the audit's only
    real-tree non-vacuity check asserted that floor entries still
    reproduce as violations — so repairing every one of them would have
    turned the ALIVENESS control red, and the cheapest way back to green
    would have been to leave a defect unfixed. **An instrument whose
    proof-of-life depends on the tree still being broken is the same
    defect class it was built to catch.**

    So the seven are retained here as a permanent REAL-TREE REGRESSION
    CORPUS with the assertion INVERTED: each must now CALL the preamble.
    That is strictly stronger than the old check — it lands on the same
    real files, and it also fails if any of them regresses.
    """
    import json
    if not os.path.isfile(path):
        return set()
    with open(path, "r", encoding="utf-8") as fh:
        return set(json.load(fh).get("repaired", []))


def new_violations(root: str = ROOT, *, floor_path: str = FLOOR_PATH) -> list[str]:
    """THE GATE: `imported_not_called` files that are not on the floor."""
    rep = audit_repo(root)
    return sorted(set(rep["imported_not_called"]) - read_floor(floor_path))


def write_floor(path: str = FLOOR_PATH, root: str = ROOT) -> list[str]:
    import json
    rep = audit_repo(root)
    known = sorted(rep["imported_not_called"])
    # The repaired corpus is HISTORY, not a scan result — carry it forward,
    # or regenerating the floor would silently delete the audit's only
    # real-tree landing check.
    prior = sorted(read_repaired(path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({
            "_README": (
                "GRANDFATHER FLOOR for the §10 rule 3 preamble gate. Every "
                "file listed here BINDS `engine_preamble` and never CALLS it "
                "— each reports provenance via `provenance_line()` while "
                "pinning the engine with the OLD `sys.path.insert("
                "runners/dsl/python)` convention that §10.2 measured as "
                "actively broken in a worktree. THESE ARE LIVE DEFECTS, NOT "
                "EXEMPTIONS. They are listed only so the gate binds NEW "
                "violations rather than being red on arrival. Fixing them is "
                "one line each (`ep.engine_preamble()`), but they are other "
                "rungs' files (§11 rule 4) — the supervisor sequences it. "
                "NEVER add to this list to silence a failure."),
            "known_violations": known,
            "repaired": prior,
        }, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return known


def main(argv) -> int:
    import json
    import sys as _sys
    if "--write-floor" in argv:
        known = write_floor()
        print(f"floor: {len(known)} known violation(s).")
        return 0
    rep = audit_repo()
    if "--gate" in argv:
        new = new_violations()
        print(json.dumps({"new_violations": new}, indent=1))
        return 1 if new else 0
    json.dump(rep, _sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main(_sys.argv[1:]))
