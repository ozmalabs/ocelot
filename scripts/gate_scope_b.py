"""gate_scope_b — THE ENUMERATED-BUT-NOT-AUDITED POPULATION, AUDITED.

PROTOCOL §1 (gate the measure), §12 (a selector that matches by substring is
not a selector), §12.5-proposed (a claim about what a gate catches is
established by MAKING IT FAIL, never by reading it).

WHY THIS EXISTS
---------------
The gate-population audit swept SCOPE A and declared in its pre-registration
that SCOPE B -- the remaining tree-wide AST-parsing test functions, the reading
arc's donkey-zero / no-regex gates -- was **ENUMERATED BUT NOT AUDITED**. It
listed that as an honest hole in its own §7. This module closes it.

WHAT IT REFUSES TO BE
---------------------
A checklist of the five recorded spellings. That is the wrong deliverable and
this tree has it on record from a real failure: six spellings felt like a
pattern, were a SAMPLE, and the seventh walked through within one commit. So
this module works from the INVARIANT (a reachability property; see
`gate_audit`) and plants a defect that INSTANTIATES the invariant's violation,
not a defect that matches a known regex.

THE METHOD, and every step of it is mechanical
----------------------------------------------
For each AST-parsing test function outside `scripts/rung7_vision_bench.sh`:

  1. SELECT ITS TARGET BY AST IDENTITY, NOT BY SUBSTRING. The audited file is
     read off the `ast.parse(...)` / `open(...)` argument by walking the test's
     own AST and resolving module-level path constants. A gate whose target
     cannot be resolved is reported UNRESOLVED-TARGET -- counted, never
     silently dropped (`seed_claim`'s posture, and the only honest one).
  2. TYPE THE GATE BY WHAT IT FORBIDS, from the `ast.*` node classes and the
     names its own body mentions. This is a classification of the gate, and it
     is allowed to be wrong -- which is why step 3 does not trust it.
  3. PLANT EVERY CANDIDATE DEFECT, not just the family's. A gate typed DECISION
     is still probed with a regex plant and a threshold plant. A gate that
     reddens on a defect outside its declared family is more alive than its
     type says; a gate that reddens on none is INERT whatever its type says.
  4. VERIFY THE PLANT LANDED (`gate_inject.verify_lands`). A plant that did not
     land is VOID-MISLANDED, never INERT -- the distinction whose absence made
     a supervisor's own injection test pass when it should have failed.
  5. ALWAYS RESTORE. `gate_inject.planted` restores in a `finally`.

THE HONEST LIMIT, STATED UP FRONT
---------------------------------
A gate can be ALIVE on these plants and still be blind to the defect it was
actually written for; ALIVE here means "this gate can be made to fail by a
violation of the invariant it names", never "this gate catches everything".
INERT is the strong verdict and it is the one worth acting on: a gate that
stays green while a violation of its own stated invariant sits inside the file
it audits has verified nothing.
"""
from __future__ import annotations

import ast
import os
import re
import sys

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from gate_inject import planted, run_gate, verify_lands  # noqa: E402

BENCH = os.path.join(ROOT, "scripts", "rung7_vision_bench.sh")


def bench_files() -> set[str]:
    """SCOPE A's selector, read from the oracle script itself rather than
    re-typed here -- a hand-copied list is the HAND-ENUMERATED GROUND TRUTH
    class this audit exists to find."""
    with open(BENCH, encoding="utf-8") as fh:
        return set(re.findall(r"tests/(test_\S+\.py)", fh.read()))


# --------------------------------------------------------------------------
# 1. TARGET SELECTION -- by AST identity.
# --------------------------------------------------------------------------


def _module_paths(tree: ast.Module) -> dict[str, str]:
    """Module-level names bound to a repo-relative path, resolved through
    `os.path.join(ROOT, "domains", "x.py")` and through plain strings."""
    out: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name):
            p = _as_path(n.value)
            if p:
                out[n.targets[0].id] = p
    return out


def _as_path(node: ast.AST) -> str | None:
    """A repo-relative path, or None. Handles `os.path.join(ROOT, "a", "b.py")`
    and a bare literal. Anything else is UNRESOLVED and says so by returning
    None -- it is not guessed at."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        v = node.value
        return v if v.endswith((".py", ".json")) else None
    if isinstance(node, ast.Call):
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        if name == "join":
            parts = []
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    parts.append(a.value)
                elif isinstance(a, ast.Name) and a.id in ("ROOT", "REPO", "BASE"):
                    continue
                else:
                    return None
            p = "/".join(parts)
            return p if p.endswith((".py", ".json")) else None
    return None


def import_map(tree: ast.Module) -> dict[str, str]:
    """Local name -> repo-relative module file, from the test's OWN imports.

    THE DOMINANT SELECTOR IN SCOPE B IS `inspect.getsource(mod)`, NOT `open()`.
    A first version of this resolver only understood `open(os.path.join(...))`
    and resolved 22 of 151 targets; it would have reported 129
    UNRESOLVED-TARGET and called that the population. That number was an
    artifact of the resolver, not a property of the gates -- the same error as
    inferring what code selects from a count of its selectors (§12.1). Resolved
    by reading one gate.

    Imports are followed only INSIDE this tree; a name bound to a stdlib or
    third-party module resolves to no file and is UNRESOLVED, not guessed."""
    out: dict[str, str] = {}

    def _file(dotted: str) -> str | None:
        rel = dotted.replace(".", "/") + ".py"
        return rel if os.path.exists(os.path.join(ROOT, rel)) else None

    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                f = _file(a.name)
                if f:
                    out[a.asname or a.name.split(".")[0]] = f
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            for a in n.names:
                f = _file(f"{n.module}.{a.name}")
                if f:
                    out[a.asname or a.name] = f
        # `from domains import x as y` inside a function body is caught by the
        # walk above; a deferred import is the tree's habit and must not hide
        # a target.
    return out


#: A resolved target: (repo-relative file, qualname or None for whole module).
Target = tuple[str, str | None]


def targets_of(fn: ast.AST, mod_paths: dict[str, str],
               imports: dict[str, str]) -> list[Target]:
    """Every source REGION this test reads, found by AST identity.

    Two selectors, both resolved structurally:
      * `open(<path>)` / `<PATH_CONST>` -> the whole module;
      * `inspect.getsource(m)` -> module `m`; `inspect.getsource(m.f)` ->
        FUNCTION `f` inside module `m`. The second distinction matters: a gate
        that selects one function is not audited by a plant at module scope,
        and reporting that as INERT rather than VOID-MISLANDED is the exact
        defect `verify_lands` exists to catch."""
    found: list[Target] = []
    for n in ast.walk(fn):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        if name == "getsource":
            for a in n.args:
                if isinstance(a, ast.Name) and a.id in imports:
                    found.append((imports[a.id], None))
                elif isinstance(a, ast.Attribute) and isinstance(a.value, ast.Name) \
                        and a.value.id in imports:
                    found.append((imports[a.value.id], a.attr))
            continue
        if name not in ("open", "read_text", "read_bytes", "parse"):
            continue
        for a in n.args:
            p = _as_path(a)
            if p is None and isinstance(a, ast.Name) and a.id in mod_paths:
                p = mod_paths[a.id]
            elif p is None and isinstance(a, ast.Call):    # open(join(...)).read()
                p = _as_path(a)
            if p and p.endswith(".py"):
                found.append((p, None))
    return list(dict.fromkeys(found))


# --------------------------------------------------------------------------
# 2/3. THE PLANTS -- instantiations of the invariant, not spellings of it.
# --------------------------------------------------------------------------

#: EVERY PLANT IS A NESTED `def`, AND THAT IS NOT COSMETIC.
#:
#: A plant spliced as bare statements into a live function changes what that
#: function DOES, so a gate that IMPORTS or CALLS the module can go red for a
#: `NameError` rather than for the violation -- a RED FOR THE WRONG REASON,
#: which is `gate_inject`'s MISLANDED disease in its other direction: the run
#: is void, and reporting it ALIVE would credit a gate that never looked. A
#: nested `def` is fully visible to `ast.walk` (every gate in this population
#: walks) and is never executed unless called, so the module's behaviour is
#: byte-unchanged and only its SOURCE carries the defect -- which is exactly
#: what a source audit claims to check.
PLANTS: dict[str, tuple[str, str]] = {
    # A DECISION over graph state -- the architecture rule's violation, in the
    # NAME-BOUND spelling, because the bare spelling is the one every gate in
    # this tree already looks for.
    "decision_graph": (
        "_gate_probe_marker_decision",
        'def _gate_probe_marker_decision(s, n):\n'
        '    _v = s.node(n)["attrs"]["k"]\n'
        '    if _v > 0.5:\n'
        '        return 1\n'
        '    return 0\n'),
    # A §13 THRESHOLD, name-bound -- an author-written value reaching a
    # decision sink through an indirection.
    "threshold_named": (
        "_gate_probe_marker_threshold",
        'def _gate_probe_marker_threshold(x):\n'
        '    _gate_probe_tau = 0.37\n'
        '    return x > _gate_probe_tau\n'),
    # A REGEX -- the donkey-zero family's forbidden import, USED and not merely
    # imported, so a gate checking either spelling can see it.
    "regex_used": (
        "_gate_probe_marker_regex",
        'def _gate_probe_marker_regex(text):\n'
        '    import re as _gate_probe_re\n'
        '    return _gate_probe_re.match(r"^[a-z]+$", text)\n'),
    # A HARDCODED WORD LIST -- the "donkey zero" violation proper: a lexical
    # decision taken from an author-written enumeration instead of the graph.
    "donkey_list": (
        "_gate_probe_marker_donkey",
        'def _gate_probe_marker_donkey(word):\n'
        '    _gate_probe_words = ["donkey", "farmer", "beat", "story"]\n'
        '    if word in _gate_probe_words:\n'
        '        return "known"\n'
        '    return "unknown"\n'),
    # THE PYTHON RULE ENGINE -- CLAUDE.md's hard NO, and the invariant a large
    # part of this population actually asserts.
    "rule_engine": (
        "_gate_probe_marker_rules",
        'def _gate_probe_marker_rules(g):\n'
        '    from domains import graph_rewrite as _gate_probe_gr\n'
        '    return _gate_probe_gr.run(g)\n'),
    # `exec` / `eval` outside the one sanctioned validator.
    "exec_call": (
        "_gate_probe_marker_exec",
        'def _gate_probe_marker_exec(code):\n'
        '    return exec(code)\n'),
}

#: WHAT EACH PLANT INSTANTIATES -- the tokens by which a gate DECLARES that
#: invariant in its own source.
#:
#: THIS EXISTS BECAUSE THE FIRST VERSION OF THIS SWEEP WAS DISHONEST BY
#: CONSTRUCTION, and a pilot caught it. `test_code_growth_migrated.py`'s source
#: audit forbids a `graph_rewrite` import and an `exec` outside one function.
#: It reddened on none of the four original plants and was recorded **INERT** --
#: but it is not blind, it simply asserts a DIFFERENT invariant, and none of my
#: plants violated it. Reporting that as INERT would have been the mirror image
#: of the failure this whole line of work exists to name: a gate credited with
#: a property it was never probed for, only pointed the other way.
#:
#: So a gate is only called INERT when at least one plant instantiates an
#: invariant IT DECLARES. Otherwise the verdict is **OUT-OF-SCOPE**: my
#: instrument says nothing about it, and says so.
PLANT_SIGNATURE: dict[str, tuple[str, ...]] = {
    "decision_graph":  ("If", "IfExp", "BoolOp", "Compare", "decision", "decide",
                        "branch", "if_else", "python_decision"),
    "threshold_named": ("Compare", "Constant", "Num", "threshold", "literal",
                        "magic", "constant"),
    "regex_used":      ("re", "regex", "findall", "match"),
    "donkey_list":     ("List", "donkey", "hardcoded", "hardcode", "literal",
                        "wordlist", "word_list", "lexical", "story"),
    "rule_engine":     ("graph_rewrite", "run_rules", "rule_engine", "gr"),
    "exec_call":       ("exec", "eval", "compile"),
}


def declared_tokens(test_src: str) -> set[str]:
    """Every token by which a gate DECLARES what it forbids: its own name, the
    `ast.*` classes it tests for, the string literals it asserts on, and the
    attribute names it reads. Read off the gate's AST, not grepped."""
    toks: set[str] = set()
    try:
        tree = ast.parse(test_src)
    except SyntaxError:
        return toks
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            toks.update(re.findall(r"[A-Za-z_]+", n.value))
        elif isinstance(n, ast.Attribute):
            toks.add(n.attr)
        elif isinstance(n, ast.Name):
            toks.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            toks.update(re.findall(r"[A-Za-z_]+", n.name))
    return toks


def in_scope_plants(test_src: str) -> list[str]:
    """The plants whose invariant this gate declares. Empty => OUT-OF-SCOPE."""
    toks = declared_tokens(test_src)
    return [name for name, sig in PLANT_SIGNATURE.items()
            if any(s in toks for s in sig)]


def _indent(block: str, pad: str) -> str:
    return "".join(pad + ln if ln.strip() else ln for ln in block.splitlines(True))


def plant_sites(target: str, qualname: str | None) -> list[tuple[str, str]]:
    """(anchor, pad) for the region this gate selects.

    BOTH ANCHORS ARE RESOLVED BY AST IDENTITY. The module anchor is the source
    segment of the file's LAST TOP-LEVEL STATEMENT; the function anchor is the
    first statement of the body of the `ast.FunctionDef` whose `.name` matches.
    Neither is a text search and neither is a fixed window.

    ON A NUMBER THIS FUNCTION USED TO CONTAIN (§13, and it was mine)
    ---------------------------------------------------------------
    The module anchor was `src[-80:]` -- the file's last 80 bytes. That 80 is a
    hand-placed constant that CHANGES THIS INSTRUMENT'S VERDICTS: too small and
    the anchor is not unique, so `planted` raises and the probe is skipped; too
    large and it spans a docstring whose bytes vary. §13's instruction is to ask
    what it would FALL OUT of, and the answer was nothing -- so it is deleted,
    not tuned. The last top-level statement's extent is a property of the file.

    **My own instrument did not flag it, and the reason is worth recording:**
    `gate_audit` types sinks by position, and a SLICE BOUND is not a decision
    sink -- correctly, since an index literal is never a comparison operand.
    So an authored number that steers this tool sat in the one syntactic
    position the tool is structurally blind to. That is a real limit of the
    SINK-by-position fix, found by auditing the auditor, and it is the second
    time a number in a slice has fooled this family of gate."""
    path = os.path.join(ROOT, target)
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    if qualname is None:
        if not tree.body:
            return []
        seg = ast.get_source_segment(src, tree.body[-1])
        return [(seg, "")] if seg else []
    sites = []
    lines = src.splitlines(True)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == qualname:
            body = getattr(n, "body", [])
            if not body:
                continue
            first = body[0]
            sites.append(("".join(lines[first.lineno - 1: first.lineno]),
                          " " * first.col_offset))
    return sites


def probe_gate(nodeid: str, target: str, qualname: str | None = None,
               plants: dict | None = None, base_ok: bool | None = None,
               base_out: str = "", test_src: str = "") -> dict:
    """One gate, every plant. Baseline first -- a gate already RED proves
    nothing about any plant, and reporting one as INERT would be a lie by
    construction."""
    plants = PLANTS if plants is None else plants
    if base_ok is None:
        base_ok, base_out = run_gate(nodeid)
    if not base_ok:
        return {"verdict": "BASELINE-RED", "target": target, "by": [],
                "detail": base_out[-600:]}
    if not os.path.exists(os.path.join(ROOT, target)):
        return {"verdict": "UNRESOLVED-TARGET", "target": target, "by": []}
    try:
        sites = plant_sites(target, qualname)
    except (SyntaxError, OSError):
        sites = []
    if not sites:
        return {"verdict": "VOID-NO-SITE", "target": target, "by": []}
    # §12.3's `PickUnique` discipline, applied to my own selector. `sites[0]`
    # is `iter().next()`: with two definitions of the same name (a conditional
    # redefinition, a name reused in a class) it silently probes ONE of them
    # and the run reads as a clean verdict about the other. That is the
    # AMBIGUOUS CONFIG READ, and the fix there was to make it LOUD, not to
    # pick better. VOID-AMBIGUOUS, never a verdict.
    if len(sites) > 1:
        return {"verdict": "VOID-AMBIGUOUS", "target": target, "by": [],
                "detail": f"{len(sites)} definitions named {qualname!r}"}
    anchor, pad = sites[0]
    caught, landed_any = [], False
    for name, (marker, body) in plants.items():
        blob = _indent(body, pad) + ("\n" if pad else "\n\n")
        new = (anchor + "\n" + blob) if pad == "" else (blob + anchor)
        try:
            with planted(target, anchor, new):
                landed = verify_lands(target, marker)
                ok, _out = run_gate(nodeid)
        except AssertionError:            # anchor not unique -> a DIFFERENT
            continue                      # experiment than the one claimed
        if not landed:
            continue
        landed_any = True
        if not ok:
            caught.append(name)
    if not landed_any:
        return {"verdict": "VOID-MISLANDED", "target": target, "by": []}
    if caught:
        return {"verdict": "ALIVE", "target": target, "by": caught}
    scope = in_scope_plants(test_src) if test_src else list(plants)
    covered = [p for p in scope if p in plants]
    if not covered:
        return {"verdict": "OUT-OF-SCOPE", "target": target, "by": [],
                "detail": "no plant instantiates an invariant this gate declares"}
    return {"verdict": "INERT", "target": target, "by": [], "scope": covered}


# --------------------------------------------------------------------------
# The population.
# --------------------------------------------------------------------------


def scope_b() -> list[tuple[str, str, list[str]]]:
    """(test file, test function, targets) for every AST-parsing test function
    OUTSIDE the oracle's file list."""
    bench = bench_files()
    out = []
    tdir = os.path.join(ROOT, "tests")
    for fn in sorted(os.listdir(tdir)):
        if not (fn.startswith("test_") and fn.endswith(".py")) or fn in bench:
            continue
        with open(os.path.join(tdir, fn), encoding="utf-8") as fh:
            src = fh.read()
        if "ast" not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        paths = _module_paths(tree)
        imports = import_map(tree)
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and n.name.startswith("test"):
                seg = ast.get_source_segment(src, n) or ""
                if "ast." not in seg:
                    continue
                out.append((fn, n.name, targets_of(n, paths, imports)))
    return out


if __name__ == "__main__":
    import json
    pop = scope_b()
    resolved = [p for p in pop if p[2]]
    print(f"SCOPE B: {len(pop)} AST-parsing test functions, "
          f"{len(resolved)} with a resolvable audited target, "
          f"{len(pop) - len(resolved)} UNRESOLVED-TARGET (counted, not dropped)")
    if "--json" in sys.argv:
        with open(sys.argv[sys.argv.index("--json") + 1], "w") as fh:
            json.dump(pop, fh)
    else:
        for f, n, t in pop:
            print(f"  {f}::{n}  -> {t or 'UNRESOLVED'}")
