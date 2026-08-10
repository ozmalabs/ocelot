"""self_extend_rust — RUNG-4, HARDENED: the agent proposes a change to its OWN
native runtime, entirely in a SANDBOX, and NEVER installs.

Why this module exists next to the older `domains/self_extend.py`: that module
is real and has landed real primitives (ArgMax, DtwTo, Whiten, WithinScatter,
BetweenScatter, WhitenMany, ...) across several historic commits — rung-4
WORKS. But it operates directly on the LIVE crate source
(`runners/dsl/src/*.rs`) and, when `build=True` (its default call site in
`reflective_faculty.self_extend_ladder`), runs `maturin develop --release` and
HOT-SWAPS the installed `_native*.so` other processes have already imported.
That is the right shape for a single agent with nobody else depending on the
binary. It is the WRONG shape while two concurrent agents depend on the
installed extension staying stable — a rung-4 attempt that fails mid-flight,
or one whose `build=False` early-return leaves the live tree patched (`extend`
only restores on FAILURE; a `cargo check`-only call that succeeds returns
without reverting), can leave `runners/dsl/src/*.rs` silently modified under
other agents' feet.

This module is the hardened replacement for VALIDATION (not installation):

    RustExtensionSpec (graph node, agent-authored)
        -> render (mechanical, template-based; composition of EXISTING Rust
           primitives where possible, new codegen only where composition
           cannot express the semantics — documented per-spec)
        -> sandbox copy of the crate (var/self_extend_sandbox/dsl_crate/,
           fully disjoint from runners/dsl/)
        -> apply the rendered fragments INTO THE SANDBOX COPY ONLY
        -> `cargo check` with CARGO_TARGET_DIR pointed at scratch (never the
           live target/, never touches the installed .so)
        -> diagnostics captured back onto the spec node (compiled: true/false
           + errors) so the agent can see WHY a proposal failed
        -> mint ExtensionProposal{status: validated|failed, requires_restart:
           True} and STOP.

Installation (the actual maturin rebuild + .so hot-swap) is a SEPARATE,
human-approved step this module never takes: see
`scripts/jabberwock_extends_runtime.py`'s runbook. A validated proposal is a
green light for a HUMAN to apply the same patch to the live tree and run the
existing (real, working) `domains/self_extend.py:PrimitiveExtension.extend`.
No code path in this module writes to `runners/dsl/src`, calls `maturin`, or
touches `_native*.so` / `_native.abi3.so`. Mechanical host I/O only — no
agent decisions here (CLAUDE.md); the DECISION (what primitive, what
semantics) is the agent's, expressed as a RustExtensionSpec graph node.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LIVE_DSL = ROOT / "runners" / "dsl"
LIVE_SRC = LIVE_DSL / "src"
INSTALLED_SO_CANDIDATES = [
    LIVE_DSL / "python" / "substrate_rs" / "_native.abi3.so",
]

SANDBOX_ROOT = ROOT / "var" / "self_extend_sandbox"
SANDBOX_CRATE = SANDBOX_ROOT / "dsl_crate"

# The forbidden operations, named so a reviewer (or a future edit) can grep
# for what this module PROMISES never to do. Nothing below calls these.
FORBIDDEN = ("maturin", "pip install", "_native.abi3.so write", "runners/dsl/src write")


# ---------------------------------------------------------------------------
# integrity: prove the live tree + installed extension were never touched
# ---------------------------------------------------------------------------

def _installed_so_paths() -> list[Path]:
    paths = [p for p in INSTALLED_SO_CANDIDATES if p.exists()]
    try:
        import substrate_rs
        import glob
        pkgdir = Path(substrate_rs.__file__).parent
        for f in glob.glob(str(pkgdir / "_native*.so")):
            fp = Path(f)
            if fp not in paths:
                paths.append(fp)
    except Exception:
        pass
    return paths


def fingerprint_live_tree() -> dict[str, str]:
    """md5 of every file under runners/dsl/src, plus every installed .so.
    Used by the gate test to PROVE a sandboxed run touched nothing live."""
    out = {}
    for p in sorted(LIVE_SRC.rglob("*.rs")):
        out[str(p.relative_to(ROOT))] = hashlib.md5(p.read_bytes()).hexdigest()
    for p in _installed_so_paths():
        out[str(p)] = hashlib.md5(p.read_bytes()).hexdigest()
    return out


def assert_live_tree_untouched(before: dict[str, str]) -> list[str]:
    """Returns a list of mismatches (empty = clean). Does not raise -- callers
    (tests) decide how to fail."""
    after = fingerprint_live_tree()
    problems = []
    for k, v in before.items():
        if after.get(k) != v:
            problems.append(f"CHANGED: {k}")
    for k in after:
        if k not in before:
            problems.append(f"NEW FILE: {k}")
    return problems


# ---------------------------------------------------------------------------
# sandbox lifecycle
# ---------------------------------------------------------------------------

def prepare_sandbox(*, force: bool = True) -> Path:
    """Fresh copy of the LIVE crate (source only, no target/, no .git) into
    the sandbox dir. READ-ONLY against runners/dsl -- shutil.copytree never
    writes to its source. force=True (default) always re-copies from live so
    every validation run starts byte-identical to the current live tree (no
    drift between sandbox runs)."""
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    gi = SANDBOX_ROOT / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n")
    if SANDBOX_CRATE.exists():
        if not force:
            return SANDBOX_CRATE
        shutil.rmtree(SANDBOX_CRATE)
    shutil.copytree(LIVE_DSL, SANDBOX_CRATE,
                     ignore=shutil.ignore_patterns("target", ".git", "__pycache__"))
    return SANDBOX_CRATE


def default_scratch_target(scratch_dir: str | Path) -> Path:
    d = Path(scratch_dir) / "self_extend_target"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# templates: spec -> Rust fragments (mechanical, deterministic, NO LLM)
# ---------------------------------------------------------------------------
# Composition-first: for semantic kinds the existing generator already knows
# (domains/runtime_design.emit_primitive_rust — ArgMax/DtwTo/Whiten/... and
# domains/struct_recursion_template — the AntiUnify family), render_spec
# reuses THOSE templates unmodified. This module adds exactly ONE new kind,
# "graph_reachability", because none of the ~9 existing kinds express an
# unbounded-depth graph walk. Composition was tried and genuinely fails for
# that shape: the DSL's only graph-neighbour primitive (`Neighbours`) is a
# SINGLE hop, and every composition surface (a Term-tree, or rung-3's
# dynamic-compose) is a FIXED, finite structure -- it cannot loop to a
# data-dependent fixpoint. Even so, the new arm does not invent a new way to
# touch the graph: its inner loop calls the SAME `ctx.graph.neighbours(...)`
# Neighbours already calls -- composition of the EXISTING graph primitive,
# with only the fixpoint loop as genuinely new code.

def agent_specify_reachable_from_primitive(substrate=None) -> dict:
    """The agent SPECIFIES `ReachableFrom` -- the same authoring move as every
    other rung-4 primitive in domains/runtime_design.py (agent_specify_*):
    inspect what it already has grounded, name the residual its language
    cannot express, specify the primitive. Records nothing itself (the caller,
    `self_extend_rust.validate_spec`, mints the graph-resident
    RustExtensionSpec + ExtensionProposal after the sandbox proves it
    compiles) -- this function ONLY returns the spec dict, mirroring
    runtime_design.agent_specify_primitive's contract exactly.

    The residual: worlds/browser.py's session/DOM adapter has to flatten an
    arbitrary-depth `contains` element tree in PYTHON (a `session -has_
    affordance-> affordance` mirror, commented in-file as "a graph rule
    choosing 'which affordance' would otherwise need an unbounded-depth
    `contains` traversal the DSL has no transitive-closure Term for") because
    every DSL Term is a FINITE tree evaluated once -- `Neighbours` gives one
    hop; nothing composes an unbounded, data-dependent number of hops into a
    Term-tree (rung-3's dynamic-compose is finite-arity too, so it was tried
    in reasoning and set aside, not silently skipped). The agent already has
    graph-reachability GROUNDED via the compiler_theory seed (dead-block /
    unreachable-code elimination is exactly this shape: "no instruction in
    any REACHABLE block branches to this block" -- reachability from an
    entry node via a fixed edge relation)."""
    grounded = False
    if substrate is not None:
        sub = getattr(substrate, "s", substrate)
        try:
            # compiler_theory's `load_seed_manifest` lands Concept nodes flat
            # (no Microtheory wrapper for this seed) -- scan both shapes so
            # the check is honest about whatever the loader actually did,
            # not a hardcoded assumption about seed-internal structure.
            candidates = list(sub.nodes("Concept"))
            for mt in sub.nodes("Microtheory"):
                candidates.extend(sub.neighbours(mt, "has_concept"))
            for c in candidates:
                attrs = sub.node(c)["attrs"]
                if attrs.get("name") in ("eliminate_unreachable_bb", "dead_block_elimination") \
                        and "reachable" in str(attrs.get("definition", "")).lower():
                    grounded = True
                    break
        except Exception:
            pass
    spec = {
        "name": "ReachableFrom",
        "signature": {"node": "Node", "edge_type": "Sym", "returns": "Set[Node]"},
        "semantics": {
            "kind": "graph_reachability",
            "composition_attempt": (
                "rung-3 (dynamic-compose, held Terms) and a plain Term-tree both "
                "produce a FIXED, finite structure; graph reachability needs a "
                "loop whose length depends on the live graph's shape -- no finite "
                "composition of Neighbours-hops bounds it, so composition was "
                "tried in reasoning and correctly abandoned, not skipped"),
            "reduces_to": (
                "BFS to fixpoint over the EXISTING ctx.graph.neighbours(node, "
                "edge_type) call Neighbours already uses -- the new code is only "
                "the visited-set loop, not a new way to touch the graph"),
        },
        "purpose": ("a native Term for the transitive closure of one edge type -- "
                    "'every node reachable from X via zero-or-more edge_type hops' "
                    "-- so a graph RULE can express unbounded-depth structure (a "
                    "DOM tree, a call graph, a containment hierarchy) without a "
                    "host adapter mechanically flattening it in Python first"),
        "why_new": ("the DSL's only graph-neighbour primitive, Neighbours, is ONE "
                    "hop; no Term expresses an unbounded, data-dependent walk -- "
                    "worlds/browser.py names this exact gap ('the DSL has no "
                    "transitive-closure Term') and works around it with a "
                    "mechanical one-hop mirror instead of a real closure"),
        "motivating_residual": "worlds/browser.py:514-522 (BrowserWorld.observe, "
                                "the has_affordance mirror comment)",
        "grounded_in_science": grounded,
        "is_agent_design": True,
    }
    return spec


def _emit_graph_reachability(spec: dict) -> dict:
    name = spec["name"]
    return {
        "term.rs (enum variant)":
            f"    {name} {{ node: TermIdx, edge_type: Sym, any_type: bool }},",
        "term.rs (copy_subtree arm)":
            f"        TermNode::{name} {{ node, edge_type, any_type }} =>\n"
            f"            TermNode::{name} {{ node: copy_subtree(src, dst, node), edge_type, any_type }},",
        "term.rs (evaluator arm)":
            f"        TermNode::{name} {{ node, edge_type, any_type }} => {{\n"
            f"            let v = evaluate(arena, *node, env, ctx);\n"
            f"            let Value::Node(start) = v else {{\n"
            f"                return Value::make_frozenset(vec![]);\n"
            f"            }};\n"
            f"            let et = if *any_type {{ None }} else {{ Some(*edge_type) }};\n"
            f"            // Transitive closure: BFS to fixpoint over the SAME\n"
            f"            // ctx.graph.neighbours() Neighbours calls for one hop --\n"
            f"            // composition of the existing graph primitive; only the\n"
            f"            // loop (data-dependent depth) is genuinely new, since no\n"
            f"            // finite Term-tree can express an unbounded walk.\n"
            f"            let mut visited: rustc_hash::FxHashSet<NodeID> = rustc_hash::FxHashSet::default();\n"
            f"            let mut frontier: Vec<NodeID> = vec![start];\n"
            f"            visited.insert(start);\n"
            f"            while let Some(cur) = frontier.pop() {{\n"
            f"                for nb in ctx.graph.neighbours(cur, et) {{\n"
            f"                    if visited.insert(nb) {{\n"
            f"                        frontier.push(nb);\n"
            f"                    }}\n"
            f"                }}\n"
            f"            }}\n"
            f"            visited.remove(&start);\n"
            f"            Value::make_frozenset(visited.into_iter().map(Value::Node).collect::<Vec<_>>())\n"
            f"        }}",
        "term.rs (children arm)":
            f"        TermNode::{name} {{ node, .. }} => out.push(*node),",
        "jsonio.rs (name arm)":
            f'        TermNode::{name} {{ .. }} => "{name}",',
        "jsonio.rs (serialize arm)":
            f"        TermNode::{name} {{ node, edge_type, any_type }} => {{\n"
            f'            m.insert("node".into(), child(*node, arena, interner));\n'
            f'            m.insert("edge_type".into(), sym_or_null(*edge_type, *any_type, interner));\n'
            f"        }}",
        "jsonio.rs (parse arm)":
            f'        "{name}" => {{\n'
            f'            let edge_type = get_optional_sym("edge_type", interner);\n'
            f'            let any_type = !matches!(obj.get("edge_type"), Some(J::String(_)));\n'
            f"            TermNode::{name} {{\n"
            f'                node: child_of("node", obj, arena, interner, variant)?,\n'
            f"                edge_type,\n"
            f"                any_type,\n"
            f"            }}\n"
            f"        }}",
        "reflect.rs (describe arm)":
            f'        TermNode::{name} {{ node, edge_type, any_type }} => ("{name}", vec![\n'
            f'            Child {{ name: "node", child: *node }},\n'
            f'            ScalarSym {{ name: "edge_type", value: if *any_type '
            f"{{ Sym::default() }} else {{ *edge_type }} }},\n"
            f"        ]),",
        "reflect.rs (parse arm)":
            f'        "{name}" => {{\n'
            f'            let edge_type = get_sym("edge_type")?;\n'
            f"            TermNode::{name} {{\n"
            f'                node: take_child!("node"),\n'
            f"                edge_type,\n"
            f"                any_type: edge_type == Sym::default(),\n"
            f"            }}\n"
            f"        }}",
    }


_TEMPLATES = {
    "graph_reachability": _emit_graph_reachability,
}


def render_spec(spec: dict) -> dict:
    """spec -> {home_key: rust_fragment}. Composition-first: try the EXISTING
    generators (runtime_design.emit_primitive_rust covers ArgMax/DtwTo/Whiten/
    WithinScatter/BetweenScatter/WhitenMany/XCorrPeak-shaped/structural-
    recursion kinds; struct_recursion_template covers the AntiUnify family).
    Only a semantic_kind absent from BOTH falls to this module's own new
    codegen template. Raises ValueError if nothing can render it (the spec
    names a semantics.kind this module does not yet know how to transcribe --
    a genuine gap, not silently ignored)."""
    kind = spec["semantics"]["kind"]
    try:
        from domains.runtime_design import emit_primitive_rust
        return emit_primitive_rust({**spec, "semantic_kind": kind})
    except ValueError:
        pass
    except ImportError:
        pass
    try:
        from domains.struct_recursion_template import emit_structural_recursion
        if kind == "structural_recursion":
            return emit_structural_recursion(spec["name"], spec["recur_kind"])
    except (ImportError, ValueError):
        pass
    if kind in _TEMPLATES:
        return _TEMPLATES[kind](spec)
    raise ValueError(
        f"render_spec: no composition template and no codegen template for "
        f"semantics.kind={kind!r} (have codegen kinds: {sorted(_TEMPLATES)})")


# ---------------------------------------------------------------------------
# anchors: exact, single-purpose insertion points derived from the SANDBOX
# copy's OWN text (never hand-transcribed line numbers -- if the live source
# reformats, the anchor lookup fails LOUDLY at preflight, it never silently
# inserts in the wrong place).
# ---------------------------------------------------------------------------
# Each entry: (home_key_prefix, file, anchor_line, before_or_after). The
# anchor_line (+ trailing "\n", to rule out a shorter arm being a PREFIX of a
# longer one -- e.g. the copy_subtree arm's "...=>" is a literal prefix of
# the evaluator arm's "...=> {") must appear EXACTLY ONCE in `file` (checked
# at apply time); the rendered fragment for `home_key` is spliced immediately
# before/after it.
_ANCHOR_PLAN = [
    ("term.rs (enum variant)", "src/term.rs",
     "    Neighbours { node: TermIdx, edge_type: Sym, any_type: bool },\n", "before"),
    ("term.rs (copy_subtree arm)", "src/term.rs",
     "        TermNode::Neighbours { node, edge_type, any_type } =>\n", "before"),
    ("term.rs (evaluator arm)", "src/term.rs",
     "        TermNode::Neighbours { node, edge_type, any_type } => {\n", "before"),
    ("term.rs (children arm)", "src/term.rs",
     "        TermNode::Neighbours { node, .. } | TermNode::InNeighbours { node, .. } => out.push(*node),\n",
     "after"),
    ("jsonio.rs (name arm)", "src/jsonio.rs",
     '        TermNode::Neighbours { .. } => "Neighbours",\n', "after"),
    ("jsonio.rs (serialize arm)", "src/jsonio.rs",
     "        TermNode::Neighbours { node, edge_type, any_type }\n", "before"),
    ("jsonio.rs (parse arm)", "src/jsonio.rs",
     '        "Neighbours" => {\n', "before"),
    ("reflect.rs (describe arm)", "src/reflect.rs",
     '        TermNode::Neighbours { node, edge_type, any_type } => ("Neighbours", vec![\n', "before"),
    ("reflect.rs (parse arm)", "src/reflect.rs",
     '        "Neighbours" => {\n', "before"),
]


def plan_inserts(frags: dict[str, str]) -> tuple[list[dict], list[str]]:
    """Build the insertion plan for a graph_reachability-shaped frags dict
    (the 9 homes above). Returns (inserts, errors) -- errors means a home key
    the plan doesn't know how to place (a template drifted from the anchor
    plan) -- NOT applied blind. For semantic kinds rendered by the EXISTING
    runtime_design templates (composition-first path), the CALLER should use
    those templates' own `domains/self_extend.PrimitiveExtension.plan` anchor
    machinery instead (unchanged, still live-source-only -- this sandbox
    module only re-derives anchors for the ONE kind it newly owns)."""
    inserts = []
    errors = []
    known = {k: (f, a, pos) for k, f, a, pos in _ANCHOR_PLAN}
    for key, frag in frags.items():
        if key not in known:
            errors.append(f"no anchor plan for home {key!r}")
            continue
        f, anchor, pos = known[key]
        inserts.append({"home": key, "file": f, "anchor": anchor, "insert": frag, "position": pos})
    return inserts, errors


def apply_to_sandbox(sandbox_crate: Path, inserts: list[dict]) -> dict:
    """Splice every insert into the SANDBOX copy. All-or-nothing PREFLIGHT:
    every anchor must appear EXACTLY ONCE in its (sandbox) file before ANY
    write happens. Never touches LIVE_SRC -- `sandbox_crate` is always a path
    under SANDBOX_ROOT, asserted below."""
    assert str(sandbox_crate).startswith(str(SANDBOX_ROOT)), \
        "apply_to_sandbox refuses a path outside the sandbox root"
    files_touched = sorted({i["file"] for i in inserts})
    texts = {f: (sandbox_crate / f).read_text() for f in files_touched}
    errors = []
    for ins in inserts:
        text = texts[ins["file"]]
        cnt = text.count(ins["anchor"])
        if cnt != 1:
            errors.append(f"{ins['file']}: anchor for {ins['home']!r} appears {cnt}x "
                           f"(need exactly 1): {ins['anchor'][:70]!r}")
    if errors:
        return {"ok": False, "stage": "preflight", "errors": errors}
    for ins in inserts:
        text = texts[ins["file"]]
        anchor = ins["anchor"]
        if ins["position"] == "before":
            replacement = ins["insert"] + "\n\n" + anchor
        else:
            replacement = anchor + ins["insert"] + "\n\n"
        texts[ins["file"]] = text.replace(anchor, replacement, 1)
    for f, text in texts.items():
        (sandbox_crate / f).write_text(text)
    return {"ok": True, "stage": "applied", "files": files_touched}


# ---------------------------------------------------------------------------
# cargo check (sandbox only, scratch target dir only, NEVER maturin)
# ---------------------------------------------------------------------------

def _extract_errors(stderr: str) -> str:
    """rustc interleaves errors with dozens of pre-existing dead-code/style
    WARNINGS (this crate has many); a plain tail() can bury the actual
    `error[...]` block under trailing warnings, which is exactly the
    diagnostic the agent needs to see. Pull out every `error` block (from an
    `error[...]:`/`error:` line to the next blank line) plus the final
    summary line, so the agent reads WHY, not a warning wall. Falls back to
    the raw tail if no `error` line is present (e.g. a timeout message)."""
    lines = stderr.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("error"):
            block = [lines[i]]
            i += 1
            while i < len(lines) and lines[i].strip() != "":
                block.append(lines[i])
                i += 1
            blocks.append("\n".join(block))
        else:
            i += 1
    if not blocks:
        return stderr[-2000:]
    tail_summary = next((ln for ln in reversed(lines) if "could not compile" in ln), "")
    out = "\n\n".join(blocks[:8])
    if tail_summary and tail_summary not in out:
        out += "\n\n" + tail_summary
    return out[-6000:]


def cargo_check(sandbox_crate: Path, target_dir: Path, *, timeout: int = 1500) -> dict:
    assert str(sandbox_crate).startswith(str(SANDBOX_ROOT)), \
        "cargo_check refuses a crate path outside the sandbox root"
    assert str(target_dir) != str(LIVE_DSL / "target"), \
        "cargo_check refuses the LIVE target dir -- pass a scratch dir"
    env = {**os.environ, "CARGO_TARGET_DIR": str(target_dir)}
    env.setdefault("CARGO_BUILD_JOBS", str(min(8, os.cpu_count() or 4)))
    t0 = time.time()
    try:
        r = subprocess.run(["cargo", "check", "--quiet", "--message-format=human"],
                            cwd=sandbox_crate, capture_output=True, text=True,
                            timeout=timeout, env=env)
        # keep the FULL stderr here (errors sort EARLY, ahead of dozens of
        # pre-existing warnings on this crate) -- truncation happens later,
        # in _extract_errors, AFTER pulling out the actual error block, not
        # before.
        return {"ok": r.returncode == 0, "returncode": r.returncode,
                "stdout": r.stdout[-2000:], "stderr": r.stderr,
                "seconds": round(time.time() - t0, 1)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": None,
                "stdout": "", "stderr": f"cargo check TIMED OUT after {timeout}s",
                "seconds": round(time.time() - t0, 1)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "returncode": None, "stdout": "",
                "stderr": f"cargo check failed to run: {e}",
                "seconds": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------
# the orchestrator: RustExtensionSpec node -> ExtensionProposal node
# ---------------------------------------------------------------------------

def _find_spec_node(substrate, name: str):
    sub = getattr(substrate, "s", substrate)
    for n in sub.nodes("RustExtensionSpec"):
        nid = n if isinstance(n, int) else getattr(n, "id", n)
        if not sub.has_node(nid):
            continue
        attrs = sub.node(nid)["attrs"] if hasattr(sub.node(nid), "__getitem__") else sub.node(nid).attrs
        if attrs.get("name") == name:
            return nid
    return None


def validate_spec(substrate, spec: dict, *, scratch_dir: str | Path,
                   timeout: int = 1500) -> dict:
    """The full sandboxed rung-4 pipeline for ONE RustExtensionSpec. Mechanical
    host I/O only: render -> sandbox copy -> apply -> cargo check -> record
    diagnostics on the spec node -> mint ExtensionProposal. Never installs.

    `substrate` may be a Python Substrate/WorldAdapter (must expose add_node /
    has_node / node / nodes) or None (dry run, no graph nodes minted -- used
    by the CLI driver for a plain compile probe)."""
    name = spec["name"]
    before = fingerprint_live_tree()
    result: dict[str, Any] = {"name": name, "ok": False, "stage": "start"}

    # A proposal whose primitive ALREADY EXISTS in the live runtime (the
    # creator approved + installed it) must not re-apply -- the fragments
    # would define the variant twice. Detect via the TermNode variant
    # declaration in the live term.rs and report honestly.
    live_term_rs = LIVE_SRC / "term.rs"
    if live_term_rs.exists() and f"{name} {{" in live_term_rs.read_text():
        result.update(stage="already_present", ok=True, already_installed=True,
                      diagnostics=f"TermNode::{name} already exists in the live "
                                  "runtime -- nothing to validate; no sandbox run")
        result["live_tree_untouched"] = True
        _record(substrate, spec, result)
        return result

    try:
        frags = render_spec(spec)
    except Exception as e:  # noqa: BLE001
        result.update(stage="render", ok=False, error=str(e))
        _record(substrate, spec, result)
        return result

    sandbox_crate = prepare_sandbox(force=True)
    inserts, plan_errors = plan_inserts(frags) if spec["semantics"]["kind"] in _TEMPLATES \
        else (_composition_inserts(frags), [])
    if plan_errors:
        result.update(stage="plan", ok=False, errors=plan_errors)
        _record(substrate, spec, result)
        return result

    applied = apply_to_sandbox(sandbox_crate, inserts)
    if not applied["ok"]:
        result.update(stage="preflight", ok=False, errors=applied["errors"])
        _record(substrate, spec, result)
        return result

    target_dir = default_scratch_target(scratch_dir)
    check = cargo_check(sandbox_crate, target_dir, timeout=timeout)
    diag = _extract_errors(check["stderr"]) if not check["ok"] else "cargo check ok"
    result.update(stage="cargo_check", ok=check["ok"], returncode=check["returncode"],
                   seconds=check["seconds"], diagnostics=diag,
                   files_touched=applied["files"], sandbox=str(sandbox_crate))

    problems = assert_live_tree_untouched(before)
    result["live_tree_untouched"] = not problems
    if problems:
        result["INTEGRITY_VIOLATION"] = problems

    _record(substrate, spec, result)
    return result


def _composition_inserts(frags: dict) -> list[dict]:
    """For specs rendered by an EXISTING (composition-first) semantic_kind
    (runtime_design.emit_primitive_rust / struct_recursion_template), reuse
    THAT module's own anchor derivation against the LIVE tree (read-only) so
    the fragments still land at the right spot, but apply them via THIS
    module's sandbox-only apply_to_sandbox -- never domains/self_extend's
    live-source path. Falls back to the ArgMax/AntiUnify anchors those
    modules already ship for bootstrap (same-shape sibling already in the
    tree)."""
    from domains.self_extend import ARGMAX_ANCHOR
    from domains.runtime_design import emit_primitive_rust
    anchor_frags = emit_primitive_rust(ARGMAX_ANCHOR)
    inserts = []
    for key, frag in frags.items():
        file = key.split(" ", 1)[0]
        if "helper" in key:
            inserts.append({"home": key, "file": file, "anchor": None,
                             "insert": frag, "position": "append"})
            continue
        anchor = anchor_frags.get(key)
        if anchor is None:
            continue
        pos = "group" if "group" in key else "before_arm"
        inserts.append({"home": key, "file": file, "anchor": anchor,
                         "insert": frag, "position": "arm_after" if pos != "group" else "group"})
    return inserts


def _record(substrate, spec: dict, result: dict) -> None:
    """Mint/refresh the RustExtensionSpec + ExtensionProposal graph nodes.
    Mechanical (no decisions): the RESULT (compiled true/false, diagnostics)
    is what cargo said; this just writes it onto the graph so the agent can
    read WHY. has_node-guarded (node ids recycle)."""
    if substrate is None:
        return
    sub = getattr(substrate, "s", substrate)
    name = spec["name"]
    existing = _find_spec_node(sub, name)
    canonical_spec = json.dumps(
        spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    spec_attrs = {"name": name, "semantics_kind": spec["semantics"]["kind"],
                  "purpose": spec.get("purpose", ""), "why_new": spec.get("why_new", ""),
                  "motivating_residual": spec.get("motivating_residual", ""),
                  # The graph record is the durable system of record used after
                  # restart.  A summary is not enough for templates whose
                  # semantics include reduce_op/band/recur_kind/etc.
                  "spec_json": canonical_spec,
                  "spec_sha256": hashlib.sha256(canonical_spec.encode("utf-8")).hexdigest(),
                  "compiled": bool(result.get("ok")), "stage": result.get("stage"),
                  "errors": str(result.get("errors") or result.get("diagnostics") or "")[:1500],
                  "origin": "agent_runtime_design"}
    if existing is not None and sub.has_node(existing):
        for k, v in spec_attrs.items():
            sub.set_attr(existing, k, v)
        spec_id = existing
    else:
        spec_id = sub.add_node("RustExtensionSpec", spec_attrs)

    if result.get("already_installed"):
        # The primitive is in the live runtime (creator-approved install);
        # the pipeline still installed nothing itself this run.
        status = "already_present"
    else:
        status = "validated" if result.get("ok") else "failed"
    prop_attrs = {"of": name, "status": status, "requires_restart": True,
                  "installed": False, "seconds": result.get("seconds"),
                  "live_tree_untouched": result.get("live_tree_untouched", True),
                  "sandbox": result.get("sandbox", ""), "ts": time.time()}
    prop_id = sub.add_node("ExtensionProposal", prop_attrs)
    try:
        inner = getattr(substrate, "inner", sub)
        inner.add_edge_unchecked(prop_id, "validates", spec_id)
    except Exception:
        pass
