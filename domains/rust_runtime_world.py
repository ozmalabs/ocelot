"""Rust-runtime world — the agent's world for designing its own runtime.

The agent has long designed its own runner. This is the WORLD it
operates in to do so. Two affordances:

  · INPUT  — text arrives in the world as a WorldInput graph node.
             The agent senses it via its existing graph machinery.

  · BUTTON — checkpoint_and_restart(). Mechanically: save the graph,
             then SANDBOX-VALIDATE the agent's DesignedFile /
             DesignedPatch nodes (see SAFETY POSTURE below) and
             return status. Nothing is written to the live workspace
             and nothing is installed by this world.

That's the entire world adapter. Mechanical I/O, no decisions about
content. The agent's PluggableArchitectureDesign is graph data the
agent composes; the button validates it in a disposable sandbox.

WHAT THE AGENT SENDS — the design

The agent's design lives as DesignedFile / DesignedPatch graph
nodes. DesignedFile has:

  · path:    relative path under the workspace root
             (e.g. 'src/my_plugin.rs')
  · content: the full file contents as a string

DesignedPatch has `target_path` / `anchor` / `position` (before /
after / replace) / `content` — anchor-based surgery on an existing
file. Either may instead carry an `ast_root` / `content_ast_root`
edge to a RustSource AST graph, rendered mechanically by
`render_ast_to_source`.

NO RENDERING DECISIONS IN PYTHON. The world adapter does not author
Rust. It writes whatever the agent's graph nodes say to write — into
a throwaway sandbox copy of the crate, never the live tree. If the
agent's content is empty or invalid, `cargo check` fails; the
failure is reported back as graph data the agent can sense.

------------------------------------------------------------------
SAFETY POSTURE (HOST/SAFETY — read before changing this file)
------------------------------------------------------------------
This world used to write DesignedFile/DesignedPatch content STRAIGHT
into the live `workspace_root`, run `cargo build`, and — by default
(`do_install=True`) — run `maturin develop --release`, hot-swapping
the installed `_native*.so`. No sandbox, no approval gate. That was
flagged as a third unguarded self-modification surface in commit
54bbecf4's runbook (rung-4's `domains/self_extend_rust.py` +
`domains/proposal_install.py` already got the sandbox-first +
human-approval treatment; this world did not).

This module now reuses that SAME sandbox machinery
(`domains/self_extend_rust.py`: `cargo_check`, `fingerprint_live_tree`,
`assert_live_tree_untouched`, `default_scratch_target`, `LIVE_DSL`)
via `validate_designs_in_sandbox()`:

  1. copy the live crate into a disposable sandbox
     (`var/self_extend_sandbox/rust_runtime_world_dsl_crate` — a
     SIBLING directory to self_extend_rust's own
     `var/self_extend_sandbox/dsl_crate`, nested under the same
     `SANDBOX_ROOT` so `ser.cargo_check`'s own safety assertion can be
     reused as-is, but a DISTINCT crate copy + a distinct
     CARGO_TARGET_DIR, so a concurrent rung-4 validation run and a
     rust_runtime_world validation run never race on the same file);
  2. apply every DesignedFile / DesignedPatch into THAT COPY ONLY;
  3. `cargo check` with CARGO_TARGET_DIR pointed at a scratch dir
     (never the live target/, never touches the installed .so);
  4. mint a `DesignedRuntimeProposal` node — status
     `validated` | `failed`, `installed: false`,
     `requires_restart: true`, `live_tree_untouched` proven via
     `assert_live_tree_untouched` — and STOP.

`checkpoint_and_restart` now ROUTES THROUGH THIS PATH BY DEFAULT
(`route_to_sandbox=True`). The old direct-to-workspace write +
`cargo build` + `maturin develop` path has been REMOVED — there is
no flag on this world that reaches `runners/dsl/src` or calls
`maturin`. Passing `do_install=True` is an explicit REFUSAL
(`status: "install_refused"`), not a silent no-op and not a crash:
the message points at the one sanctioned installer.

HONEST RESIDUAL: unlike rung-4's `RustExtensionSpec` (a small,
composition-first, template-rendered shape — `render_spec` only
knows a handful of `semantics.kind`s), a `DesignedFile`/
`DesignedPatch` is FREE-FORM: arbitrary path, arbitrary content, no
template. That freedom is exactly what makes it useful for the
agent's own AST-composition experiments, and exactly why it cannot
be losslessly unified into the `RustExtensionSpec` shape
`domains.proposal_install.install_proposal` knows how to install.
So `validate_designs_in_sandbox()` mints a DIFFERENT node type,
`DesignedRuntimeProposal` (not `ExtensionProposal`), and this module
provides NO installer for it at all — the only route from a
validated `DesignedRuntimeProposal` to the live tree is a HUMAN
reading the sandbox diff/diagnostics and hand-applying the same
patch via the real, sanctioned installer
(`domains.self_extend.PrimitiveExtension.extend`), exactly as
`scripts/jabberwock_extends_runtime.py`'s runbook already documents
for rung-4. Belt-and-suspenders: even in a hypothetical future where
a `DesignedRuntimeProposal` is coerced into the `ExtensionProposal`
shape and handed to `install_proposal`, that function's own
guardrail 4 (fresh `render_spec` re-validation) refuses it outright
— there is no `semantics.kind` template for free-form patches — and
guardrail 5 (the `ALLOWED_INSTALL_FILES` denylist) refuses anything
touching a file outside `term.rs` / `jsonio.rs` / `reflect.rs` /
`py.rs` / `shape.rs` even if guardrail 4 were somehow bypassed.

THE LLM-TEACHER HATCH (`invoke_teacher`): a DISTINCT, BIGGER trust
surface than the agent authoring its own spec — an LLM, not the
agent, decides what Rust to propose, with no template and no
composition-first constraint. It is gated behind an explicit
`enable_network=False`-by-default flag, independent of `dry_run`
(see that method's docstring). Its output still only ever reaches
`DesignedPatch` graph nodes — sandbox-validated the same way, never
installed by this module.

WHAT THE WORLD DOES NOT DO

  · Compose the design.
  · Pick file paths.
  · Author Rust source.
  · Decide architecture.
  · Diagnose build errors beyond capturing stderr verbatim.
  · Write to the live workspace or call maturin (see SAFETY POSTURE).

The world is a world. The agent is the agent. The boundary is a
disposable sandbox copy of the crate + the cargo CLI.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from domains import self_extend_rust as ser

# This world's OWN sandbox CRATE COPY — a distinct directory from
# self_extend_rust.SANDBOX_CRATE ("dsl_crate"), so the two validation paths
# never race on the same copy when a concurrent agent is driving rung-4 at
# the same time. Deliberately NESTED under self_extend_rust.SANDBOX_ROOT
# (not a wholly separate root): ser.cargo_check's own safety assertion only
# requires `str(sandbox_crate).startswith(str(ser.SANDBOX_ROOT))` — reusing
# that function (rather than re-implementing the cargo invocation) means
# living under the same parent, in our OWN sibling subdirectory. The
# CARGO_TARGET_DIR (RRW_SCRATCH_DEFAULT) is a separate scratch dir too, so
# there is no shared mutable state at all between the two pipelines, just a
# shared parent directory.
RRW_SANDBOX_ROOT = ser.SANDBOX_ROOT
RRW_SANDBOX_CRATE = ser.SANDBOX_ROOT / "rust_runtime_world_dsl_crate"
RRW_SCRATCH_DEFAULT = ser.SANDBOX_ROOT / "rust_runtime_world_scratch"
# Default graph-checkpoint location -- under var/, never inside the live
# `workspace_root` (self.root). A checkpoint dump is data, not code, but
# "defaults touch nothing live" means the live workspace directory itself,
# not merely "nothing that affects compilation".
RRW_CHECKPOINT_DEFAULT = ser.ROOT / "var" / "rust_runtime_world_checkpoints" / "world_checkpoint.json"


class RustRuntimeWorld:
    """The substrate's Rust workspace exposed as a world. Input + button."""

    def __init__(self, substrate, workspace_root: str | Path):
        self.s = substrate
        self.root = Path(workspace_root)
        if not self.root.exists():
            raise FileNotFoundError(f"workspace root does not exist: {self.root}")
        if not (self.root / "Cargo.toml").exists():
            raise FileNotFoundError(
                f"workspace root has no Cargo.toml: {self.root}")
        self._ensure_productions()

    def _ensure_productions(self) -> None:
        """Open productions for the world's own node types. Idempotent."""
        world_types = (
            "WorldInput", "DesignedFile", "DesignedPatch",
            "CheckpointResult", "BuildError",
            # The sandbox-validation result for a free-form DesignedFile /
            # DesignedPatch batch. Deliberately NOT "ExtensionProposal" —
            # see the SAFETY POSTURE docstring: this shape has no
            # `render_spec` template, so it is never installable via
            # domains.proposal_install.install_proposal.
            "DesignedRuntimeProposal",
            # Rust AST node types — the agent composes these; the world
            # renders them to source via render_ast_to_source().
            "RustSource", "RustEnumVariant", "RustMatchArm",
            "RustFn", "RustStmt", "RustLine", "RustRaw",
        )
        for t in world_types:
            for u in world_types:
                for et in ("sense", "sends", "results_in", "carries",
                            "ast_root", "content_ast_root", "summarizes",
                            "has_item", "has_arm", "has_field",
                            "has_param", "has_stmt"):
                    try:
                        self.s.add_production({
                            "src": {"type": t, "var": "a"},
                            "edge_type": et,
                            "tgt": {"type": u, "var": "b"},
                            "where": None,
                            "weight": {"type": "Lit", "value": 1.0},
                            "provenance": "rust_runtime_world",
                        })
                    except Exception:
                        pass

    # -------------------- SENSE: read what's already in the world --------

    def read_file(self, relpath: str | Path) -> str:
        """Sense: read a file under the workspace. The agent observes its
        own runtime source code through this."""
        return (self.root / relpath).read_text()

    def list_files(self, glob_pattern: str = "**/*.rs") -> list[str]:
        """Sense: enumerate files matching a glob under the workspace."""
        return [str(p.relative_to(self.root))
                for p in self.root.glob(glob_pattern)]

    # -------------------- RENDER: AST graph → Rust source --------------

    def render_ast_to_source(self, root_nid) -> str:
        """Walk the AST rooted at `root_nid` and emit Rust source.

        Mechanical translation per node type:

          RustSource     — items rendered in order, joined by newlines
          RustRaw        — emit attrs['text'] verbatim (escape hatch)
          RustLine       — emit attrs['text'] + '\\n'
          RustEnumVariant — emit `    {name} {{ {fields} }},\\n`
                            (fields built from has_field children:
                             RustRaw with text='name: Type')
          RustMatchArm   — emit `    {pattern} => {body},\\n`
                            (pattern from attrs; body is rendered via
                             has_stmt children joined into a block)
          RustFn         — emit `fn {name}({params}) {return_type} {{\\n
                            {body}\\n}}` (body from has_stmt children)
          RustStmt       — emit attrs['text'] + ';\\n' (or just text if
                            ends with semicolon)

        Unknown node types render as `// unknown: {type}\\n`. The world
        does not invent translations; it walks what the agent built.

        Agent doesn't have to learn the rules; if it wants a fragment
        the renderer doesn't handle, it composes a RustRaw with literal
        text. The render is just structured concatenation."""
        return self._render(root_nid)

    def _render(self, nid) -> str:
        node = self.s.node(nid)
        ntype = node.get("type", "")
        a = node.get("attrs", {})
        if ntype == "RustSource":
            items = self.s.neighbours(nid, "has_item")
            return "".join(self._render(i) for i in items)
        if ntype == "RustRaw":
            return str(a.get("text", ""))
        if ntype == "RustLine":
            return str(a.get("text", "")) + "\n"
        if ntype == "RustEnumVariant":
            fields = self.s.neighbours(nid, "has_field")
            fields_src = ", ".join(self._render(f).strip() for f in fields)
            return f"    {a.get('name','?')} {{ {fields_src} }},\n"
        if ntype == "RustMatchArm":
            pattern = str(a.get("pattern", ""))
            stmts = self.s.neighbours(nid, "has_stmt")
            body_src = "".join(self._render(st) for st in stmts).rstrip()
            if not body_src:
                body_src = str(a.get("body", ""))
            return f"        {pattern} => {body_src},\n"
        if ntype == "RustFn":
            params = self.s.neighbours(nid, "has_param")
            params_src = ", ".join(self._render(p).strip() for p in params)
            ret = str(a.get("return_type", ""))
            ret_src = f" -> {ret}" if ret else ""
            stmts = self.s.neighbours(nid, "has_stmt")
            body_src = "".join("    " + self._render(st)
                                  for st in stmts)
            return (f"fn {a.get('name','?')}({params_src}){ret_src} {{\n"
                    f"{body_src}}}\n")
        if ntype == "RustStmt":
            t = str(a.get("text", ""))
            if not t.endswith(";"):
                t += ";"
            return t + "\n"
        # Unknown node — surface verbatim so the agent can sense the gap.
        return f"// unknown AST node type: {ntype}\n"

    # -------------------- AFFORDANCE 1: INPUT ----------------------------

    def input(self, text: str) -> "object":
        """Affordance 1: a WorldInput arrives. The agent senses it as a
        graph node; subsequent ticks let the agent reason about it."""
        nid = self.s.add_node("WorldInput", {
            "text": text,
            "received_at": time.time(),
            "origin": "rust_runtime_world",
        })
        return nid

    # -------------------- SANDBOX VALIDATION (the real button target) ----

    def _prepare_rrw_sandbox(self) -> Path:
        """Fresh sandbox copy of the LIVE crate, for this world's free-form
        DesignedFile/DesignedPatch validation. Refuses (raises) unless this
        world's `workspace_root` IS the live `runners/dsl` crate
        self_extend_rust knows how to fingerprint — a different
        workspace_root has no known live-tree baseline to prove untouched,
        so validation honestly declines rather than silently sandboxing (or
        worse, silently trusting) the wrong tree. Read-only against the live
        tree: shutil.copytree never writes to its source."""
        if self.root.resolve() != ser.LIVE_DSL.resolve():
            raise ValueError(
                "sandbox validation only supports workspace_root == "
                f"{ser.LIVE_DSL} (the live runners/dsl crate self_extend_rust "
                f"fingerprints); got {self.root}. Refusing rather than "
                "guessing at a live-tree baseline.")
        RRW_SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
        gi = RRW_SANDBOX_ROOT / ".gitignore"
        if not gi.exists():
            gi.write_text("*\n")
        if RRW_SANDBOX_CRATE.exists():
            shutil.rmtree(RRW_SANDBOX_CRATE)
        shutil.copytree(ser.LIVE_DSL, RRW_SANDBOX_CRATE,
                         ignore=shutil.ignore_patterns("target", ".git", "__pycache__"))
        return RRW_SANDBOX_CRATE

    def _apply_designs_to(self, target_root: Path) -> dict:
        """Write every DesignedFile / DesignedPatch node's content into
        `target_root` — a SANDBOX copy, never `self.root`. Same mechanical
        translation the old live-write path used (render/read/splice), just
        re-rooted, and asserted to stay inside the sandbox. Records
        BuildError graph nodes for render/write/patch failures exactly as
        before (the agent senses failures the same way it always did)."""
        assert str(target_root).startswith(str(RRW_SANDBOX_ROOT)), \
            "_apply_designs_to refuses to write outside the rust_runtime_world sandbox"

        applied_files: list[str] = []
        applied_patches: list[str] = []
        errors: list[str] = []

        for nid in self.s.nodes("DesignedFile"):
            attrs = self.s.node(nid)["attrs"]
            relpath = str(attrs.get("path", "")).strip()
            if not relpath:
                continue
            content = ""
            ast_roots = self.s.neighbours(nid, "ast_root")
            if ast_roots:
                try:
                    content = self.render_ast_to_source(ast_roots[0])
                except Exception as e:
                    self.s.add_node("BuildError", {
                        "kind":   "render_failed",
                        "path":   relpath,
                        "error":  f"{type(e).__name__}: {e}",
                        "origin": "rust_runtime_world_sandbox",
                    })
                    errors.append(f"{relpath}: render_failed: {e}")
                    continue
            else:
                content = str(attrs.get("content", ""))
            target = target_root / relpath
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
                applied_files.append(relpath)
            except Exception as e:
                self.s.add_node("BuildError", {
                    "kind":   "write_failed",
                    "path":   relpath,
                    "error":  f"{type(e).__name__}: {e}",
                    "origin": "rust_runtime_world_sandbox",
                })
                errors.append(f"{relpath}: write_failed: {e}")

        for nid in self.s.nodes("DesignedPatch"):
            attrs = self.s.node(nid)["attrs"]
            relpath = str(attrs.get("target_path", "")).strip()
            anchor = str(attrs.get("anchor", ""))
            position = str(attrs.get("position", "after")).strip().lower()
            if not relpath or not anchor:
                continue

            content = str(attrs.get("content", ""))
            content_ast = self.s.neighbours(nid, "content_ast_root")
            if content_ast:
                try:
                    content = self.render_ast_to_source(content_ast[0])
                except Exception as e:
                    self.s.add_node("BuildError", {
                        "kind":   "patch_render_failed",
                        "target": relpath,
                        "error":  f"{type(e).__name__}: {e}",
                        "origin": "rust_runtime_world_sandbox",
                    })
                    errors.append(f"{relpath}: patch_render_failed: {e}")
                    continue

            target = target_root / relpath
            if not target.exists():
                self.s.add_node("BuildError", {
                    "kind":   "patch_target_missing",
                    "target": relpath,
                    "anchor": anchor[:200],
                    "origin": "rust_runtime_world_sandbox",
                })
                errors.append(f"{relpath}: patch_target_missing")
                continue

            try:
                src = target.read_text()
            except Exception as e:
                self.s.add_node("BuildError", {
                    "kind":   "patch_read_failed",
                    "target": relpath,
                    "error":  f"{type(e).__name__}: {e}",
                    "origin": "rust_runtime_world_sandbox",
                })
                errors.append(f"{relpath}: patch_read_failed: {e}")
                continue

            idx = src.find(anchor)
            if idx < 0:
                self.s.add_node("BuildError", {
                    "kind":     "patch_anchor_not_found",
                    "target":   relpath,
                    "anchor":   anchor[:200],
                    "origin":   "rust_runtime_world_sandbox",
                })
                errors.append(f"{relpath}: patch_anchor_not_found")
                continue

            if position == "before":
                new_src = src[:idx] + content + src[idx:]
            elif position == "replace":
                new_src = src[:idx] + content + src[idx + len(anchor):]
            else:  # 'after' (default)
                end = idx + len(anchor)
                new_src = src[:end] + content + src[end:]

            try:
                target.write_text(new_src)
                applied_patches.append(relpath)
            except Exception as e:
                self.s.add_node("BuildError", {
                    "kind":   "patch_write_failed",
                    "target": relpath,
                    "error":  f"{type(e).__name__}: {e}",
                    "origin": "rust_runtime_world_sandbox",
                })
                errors.append(f"{relpath}: patch_write_failed: {e}")

        return {"applied_files": applied_files,
                "applied_patches": applied_patches,
                "errors": errors}

    def validate_designs_in_sandbox(self, *,
                                       scratch_dir: str | Path | None = None,
                                       run_cargo_check: bool = True,
                                       timeout: int = 1500) -> dict:
        """THE SAFE PATH: sandbox-validate every DesignedFile / DesignedPatch
        node currently in the agent's graph. Never touches the live tree,
        never installs. See the module SAFETY POSTURE docstring for the
        full design.

        Returns a dict with keys:
          · status:              'no_design' | 'validated' | 'failed' |
                                  'applied_no_check' (run_cargo_check=False)
          · applied_files:       DesignedFile paths written into the sandbox
          · applied_patches:     DesignedPatch target paths spliced in the
                                  sandbox
          · errors:              list of str, one per DesignedFile/Patch
                                  application failure (BuildError nodes are
                                  also minted, same as before)
          · diagnostics:         cargo check output (errors extracted) or
                                  'cargo check ok'
          · sandbox:              path to the disposable sandbox crate
          · live_tree_untouched: bool, proven via fingerprint diff
          · proposal_node:       the minted DesignedRuntimeProposal node id
        """
        design_nodes = list(self.s.nodes("DesignedFile"))
        patch_nodes = list(self.s.nodes("DesignedPatch"))
        if not design_nodes and not patch_nodes:
            return {"status": "no_design",
                    "applied_files": [], "applied_patches": []}

        before = ser.fingerprint_live_tree()
        sandbox_crate = self._prepare_rrw_sandbox()
        applied = self._apply_designs_to(sandbox_crate)

        result: dict = {
            "applied_files":   applied["applied_files"],
            "applied_patches": applied["applied_patches"],
            "errors":          applied["errors"],
            "sandbox":         str(sandbox_crate),
        }

        if not run_cargo_check:
            problems = ser.assert_live_tree_untouched(before)
            result["status"] = "applied_no_check"
            result["diagnostics"] = "cargo check skipped (run_cargo_check=False)"
            result["live_tree_untouched"] = not problems
        else:
            target_dir = ser.default_scratch_target(scratch_dir or str(RRW_SCRATCH_DEFAULT))
            check = ser.cargo_check(sandbox_crate, target_dir, timeout=timeout)
            diag = ser._extract_errors(check["stderr"]) if not check["ok"] else "cargo check ok"
            problems = ser.assert_live_tree_untouched(before)
            result["cargo_ok"] = check["ok"]
            result["cargo_seconds"] = check.get("seconds")
            result["diagnostics"] = diag
            result["live_tree_untouched"] = not problems
            ok = check["ok"] and not applied["errors"]
            result["status"] = "validated" if ok else "failed"

        if problems:
            result["INTEGRITY_VIOLATION"] = problems

        prop_attrs = {
            "kind":                "designed_runtime_patch",
            "status":              result["status"],
            "installed":           False,
            "requires_restart":    True,
            "live_tree_untouched": result["live_tree_untouched"],
            "sandbox":             result["sandbox"],
            "diagnostics":         str(result.get("diagnostics", ""))[:4000],
            "applied_files":       result["applied_files"],
            "applied_patches":     result["applied_patches"],
            "errors":              result["errors"],
            "ts":                  time.time(),
            "origin":              "rust_runtime_world",
        }
        prop_id = self.s.add_node("DesignedRuntimeProposal", prop_attrs)
        for nid in design_nodes + patch_nodes:
            try:
                self.s.add_edge(prop_id, "summarizes", nid)
            except Exception:
                pass
        result["proposal_node"] = prop_id.value if hasattr(prop_id, "value") else prop_id
        return result

    # -------------------- AFFORDANCE 2: THE BUTTON -----------------------

    def checkpoint_and_restart(self,
                                  save_graph_to: str | Path | None = None,
                                  do_build: bool = True,
                                  do_install: bool = False,
                                  route_to_sandbox: bool = True,
                                  scratch_dir: str | Path | None = None) -> dict:
        """Affordance 2: THE BUTTON — HOST/SAFETY hardened.

        Mechanically, by default (`route_to_sandbox=True`, the only
        supported mode):
          1. Save the substrate's graph to a checkpoint file (harmless: a
             JSON dump, not code — never compiled, never executed).
          2. Sandbox-validate every DesignedFile / DesignedPatch node via
             `validate_designs_in_sandbox()` — copy the live crate into a
             disposable sandbox, apply the design THERE, `cargo check`
             THERE. The live tree is never written to.
          3. Return a status dict. Nothing is installed; nothing requires
             (or gets) a process restart from THIS method.

        `do_install=True` is a REFUSAL, not an install: this method no
        longer runs `maturin develop` under any argument combination — that
        surface was flagged unguarded in commit 54bbecf4's runbook and has
        been removed. The one sanctioned path from a validated design to
        the live runtime is a human (or policy) reading the sandbox
        diagnostics and hand-applying the patch via
        `domains.self_extend.PrimitiveExtension.extend`, exactly as
        `scripts/jabberwock_extends_runtime.py`'s runbook documents for
        rung-4 — see the module docstring's HONEST RESIDUAL section for why
        a free-form DesignedFile/DesignedPatch cannot go through
        `domains.proposal_install.install_proposal` directly.

        `do_build=False` skips the `cargo check` step (fast path: apply the
        design into the sandbox and stop there, still never touching the
        live tree) — status becomes `'applied_no_check'` rather than
        `'validated'`, since without a compile check nothing was actually
        proven.

        `route_to_sandbox=False` is refused outright (not silently aliased
        to the sandbox path): the direct-to-workspace write this argument
        used to select no longer exists in this module at all.
        """
        # ----- 1. checkpoint the graph (harmless: JSON, not code) -----
        # Default location is under var/, NOT self.root -- "defaults touch
        # nothing live" means the live workspace directory itself, not just
        # runners/dsl/src. A checkpoint dump is not code and is never
        # compiled, but there is no reason for it to land inside the cargo
        # workspace by default either.
        cp_path = Path(save_graph_to) if save_graph_to else \
            RRW_CHECKPOINT_DEFAULT
        try:
            cp_path.parent.mkdir(parents=True, exist_ok=True)
            graph_data = self.s.graph_to_dict()
            cp_path.write_text(json.dumps(graph_data))
        except Exception as e:
            return {"status": "checkpoint_failed",
                    "error": f"{type(e).__name__}: {e}",
                    "applied_files": []}

        if not route_to_sandbox:
            return {"status": "live_write_removed",
                    "reason": (
                        "the direct-to-workspace DesignedFile/DesignedPatch "
                        "write + cargo build/maturin path has been removed "
                        "(HOST/SAFETY, commit 54bbecf4's runbook). Use "
                        "route_to_sandbox=True (the default) or call "
                        "validate_designs_in_sandbox() directly."),
                    "checkpoint_path": str(cp_path)}

        if do_install:
            return {"status": "install_refused",
                    "reason": (
                        "checkpoint_and_restart no longer writes to the live "
                        "workspace or calls maturin directly. Live install "
                        "now requires a human/policy-approved installer "
                        "(domains.proposal_install.install_proposal) over a "
                        "structured RustExtensionSpec/ExtensionProposal — a "
                        "free-form DesignedFile/DesignedPatch is not that "
                        "shape (see module docstring, HONEST RESIDUAL). Call "
                        "validate_designs_in_sandbox() to get a sandbox-"
                        "checked DesignedRuntimeProposal; installing it is a "
                        "human hand-applying the same patch via "
                        "domains.self_extend.PrimitiveExtension.extend, "
                        "never this method."),
                    "checkpoint_path": str(cp_path)}

        result = self.validate_designs_in_sandbox(
            scratch_dir=scratch_dir, run_cargo_check=do_build)
        result["checkpoint_path"] = str(cp_path)
        return result

    # -------------------- TEACHER: babble across boundary ---------------

    def invoke_teacher(self, intent: str, *,
                         context_paths: list[str] | None = None,
                         model: str = "claude-sonnet-4-6",
                         max_tokens: int = 4096,
                         dry_run: bool = False,
                         enable_network: bool = False) -> dict:
        """Babble across boundary: send the agent's design intent to an
        LLM teacher; teacher grounds it as DesignedPatch nodes.

        HOST/SAFETY — a DISTINCT, BIGGER trust surface than the agent
        authoring its own RustExtensionSpec (rung-4): here an LLM, not the
        agent, decides what Rust to propose, with no template, no
        composition-first constraint, and no bound on what code appears.
        `enable_network` therefore defaults to False and gates the ACTUAL
        API call INDEPENDENTLY of `dry_run` — even a caller that explicitly
        passes `dry_run=False` gets no network call unless
        `enable_network=True` is ALSO passed explicitly. The resulting
        DesignedPatch nodes (on the rare call where the network path does
        run) are still only ever sandbox-validated by
        `validate_designs_in_sandbox()` — they reach `runners/dsl/src` only
        via the same human-hand-applies-the-diff path as every other
        free-form design (see module SAFETY POSTURE); this method never
        installs anything itself.

        Per memory note [[ozma_babble_grounding]]: babble = form + test
        across a boundary. Here the agent forms an intent (graph data);
        the teacher (LLM) translates it into patches (graph data);
        the world tests via cargo-in-a-sandbox; feedback comes back as
        BuildError / DesignedRuntimeProposal nodes the agent senses.

        Args:
          intent:         text describing what to build
          context_paths:  files to include in the prompt as context.
                           Defaults to the substrate's TermNode + jsonio
                           + reflect + Python __init__.
          model:          Anthropic model ID
          dry_run:        if True, returns the prompt without calling the
                           API. Forced True whenever enable_network=False.
          enable_network: OFF BY DEFAULT. Must be explicitly True for this
                           method to ever attempt a real network call.
          max_tokens:     upper bound on response length

        Returns a dict:
          · prompt:          the prompt sent (or would have been sent)
          · response_text:   raw LLM response (empty if dry_run / no key)
          · patches_created: list of DesignedPatch node IDs added
          · dry_run:         True if no API call was made
          · enable_network:  the resolved flag value, for the caller to see
          · note:            optional explanation when dry_run=True
        """
        if not enable_network:
            dry_run = True
        if enable_network and not dry_run:
            # OZMA_NO_LLM hard switch: a live hosted call was explicitly
            # requested — refuse LOUDLY rather than silently degrade, so a
            # regression is detectable. (dry_run prompts remain fine.)
            from domains.no_llm import assert_llm_allowed
            assert_llm_allowed(
                "RustRuntimeWorld.invoke_teacher (hosted anthropic call)")
        # Build context from existing source — show the LLM what the
        # substrate's runtime currently looks like at the patch sites.
        # Limited to chunks around likely anchors so the prompt is
        # token-budget-aware.
        if context_paths is None:
            context_paths = [
                "src/term.rs", "src/jsonio.rs", "src/reflect.rs",
                "python/substrate_rs/__init__.py",
            ]
        context_parts: list[str] = []
        for p in context_paths:
            try:
                content = self.read_file(p)
                context_parts.append(
                    f"\n--- FILE: {p} ({len(content)} chars total) ---\n"
                    + content[:6000]
                )
            except Exception:
                context_parts.append(f"\n--- FILE: {p} (read failed) ---\n")

        prompt = (
            "You are a code-translation teacher for the substrate's Rust runtime.\n"
            "\n"
            "The agent has a conceptual intent for a new primitive. Your job: "
            "produce a JSON LIST of patches that splice the new code into "
            "existing files.\n"
            "\n"
            "Each patch object has EXACTLY these fields:\n"
            "  target_path: file path relative to workspace root\n"
            "  anchor:      a UNIQUE verbatim string already in that file\n"
            "  position:    'after' | 'before' | 'replace'\n"
            "  content:     the text to insert / replace\n"
            "\n"
            "RULES:\n"
            "  · Anchors must be VERBATIM strings in the file (no edits).\n"
            "  · Anchors must be unique within their target_path.\n"
            "  · Compose anchors that mirror existing variant patterns\n"
            "    (e.g. add after Pick if Pick is the closest neighbour).\n"
            "  · For a new TermNode variant, you need patches across\n"
            "    src/term.rs (enum + copy_subtree + evaluator + children),\n"
            "    src/jsonio.rs (name + parse + serialize),\n"
            "    src/reflect.rs (child list + parse),\n"
            "    python/substrate_rs/__init__.py (constructor).\n"
            "\n"
            "AGENT INTENT:\n"
            f"{intent}\n"
            "\n"
            "EXISTING SOURCE (relevant excerpts):\n"
            f"{''.join(context_parts)}\n"
            "\n"
            "OUTPUT: a single JSON code block containing the patches list. "
            "No prose outside the JSON block."
        )

        if dry_run:
            note = ("dry_run=True; no API call made" if enable_network else
                     "enable_network=False (default): the LLM-teacher network "
                     "call is off by default -- an LLM authoring the agent's "
                     "Rust is a DISTINCT, BIGGER trust surface than the agent "
                     "authoring its own RustExtensionSpec (no template, no "
                     "composition-first constraint). Pass enable_network=True "
                     "explicitly to invoke the real teacher; even then, any "
                     "resulting DesignedPatch only ever reaches "
                     "runners/dsl/src via a human hand-applying a "
                     "sandbox-validated diff, never automatically.")
            return {"dry_run": True, "enable_network": enable_network,
                     "prompt": prompt, "response_text": "",
                     "patches_created": [], "note": note}

        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"dry_run": True, "enable_network": enable_network,
                     "prompt": prompt,
                     "response_text": "", "patches_created": [],
                     "note": "no ANTHROPIC_API_KEY in env; returning "
                              "prompt only. Set the key + retry to actually "
                              "invoke the teacher."}

        try:
            import anthropic
        except ImportError:
            return {"dry_run": True, "enable_network": enable_network,
                     "prompt": prompt,
                     "response_text": "", "patches_created": [],
                     "note": "anthropic SDK not installed"}

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        # response.content is a list of content blocks; join text blocks.
        response_text = "".join(
            getattr(b, "text", "") for b in response.content
        )

        # Parse JSON from response.
        import json as _json
        import re as _re
        patches_created: list = []
        match = _re.search(r"```(?:json)?\s*(\[.*?\])\s*```",
                            response_text, _re.DOTALL)
        if match:
            json_text = match.group(1)
        else:
            # Fall back to whole response if no fence.
            json_text = response_text.strip()
        try:
            patches = _json.loads(json_text)
            if not isinstance(patches, list):
                raise ValueError("expected JSON list")
        except Exception as e:
            return {"dry_run": False, "enable_network": enable_network,
                     "prompt": prompt,
                     "response_text": response_text,
                     "patches_created": [],
                     "note": f"couldn't parse JSON from response: "
                              f"{type(e).__name__}: {e}"}

        # Materialize as DesignedPatch nodes. Data only -- these still only
        # ever reach the sandbox via validate_designs_in_sandbox(); nothing
        # here writes to the live tree.
        for p in patches:
            if not isinstance(p, dict):
                continue
            nid = self.s.add_node("DesignedPatch", {
                "target_path": str(p.get("target_path", "")),
                "anchor":      str(p.get("anchor", "")),
                "position":    str(p.get("position", "after")),
                "content":     str(p.get("content", "")),
                "origin":      "invoke_teacher",
            })
            patches_created.append(nid)

        return {"dry_run": False, "enable_network": enable_network,
                 "prompt": prompt,
                 "response_text": response_text,
                 "patches_created": patches_created}

    # -------------------- BABBLE LOOP: form + test across boundary -------

    def babble_loop(self, *,
                      max_iters: int = 6,
                      tick_steps: int = 100_000,
                      do_install: bool = False,
                      save_path: str | Path | None = None) -> dict:
        """The babble loop. Press the button, tick the agent, repeat.

        Per the project's babble = grounding pattern (memory note
        [[ozma_babble_grounding]]): form + test run across a boundary
        is how a system learns. Here the agent forms an AST design;
        cargo-in-a-sandbox tests it; errors surface as BuildError graph
        data; the agent senses + refines; press again.

        Each iteration:
          1. checkpoint_and_restart(do_build=True) — sandbox-validate
             (never a live write, never a build/install).
          2. If status == 'validated', return success.
          3. self.s.tick(tick_steps) — the agent reasons about the
             new BuildError node if any rules fire on it.
          4. Detect deadlock — if no DesignedFile / ast graph changed
             since last iteration, the agent's reasoning has no
             refinement for this error, exit.

        `do_install` is accepted for backward compatibility but ALWAYS
        ignored (forced False): `checkpoint_and_restart` refuses
        `do_install=True` outright (HOST/SAFETY — see its docstring), so
        honouring a True value here would just spin the loop to
        `max_iters` on repeated refusals instead of validating anything.
        Installing a validated design is a separate, human/policy-approved
        step this loop never takes.

        Returns:
          · status:      'converged' | 'deadlock' | 'max_iters'
          · iters:       number of iterations run
          · final_state: last iteration's status dict
          · history:     list of (iter, status, n_files, n_errors)
                          for inspection
        """
        history = []
        prev_design_sig = None
        for i in range(max_iters):
            result = self.checkpoint_and_restart(
                save_graph_to=save_path,
                do_build=True, do_install=False,
            )
            n_files = len(result.get("applied_files", []))
            n_errors = len(self.s.nodes("BuildError"))
            history.append((i, result["status"], n_files, n_errors))

            if result["status"] == "validated":
                return {"status":      "converged",
                        "iters":       i + 1,
                        "final_state": result,
                        "history":     history}

            # Let the agent reason about the failure.
            self.s.tick(tick_steps)

            # Deadlock detection: if the DesignedFile + AST graph
            # hasn't changed since last iteration, no refinement is
            # happening. Exit honestly rather than spinning.
            sig = self._design_signature()
            if sig == prev_design_sig:
                return {"status":      "deadlock",
                        "iters":       i + 1,
                        "final_state": result,
                        "history":     history,
                        "note":        "no design change between iterations; "
                                       "agent has no refinement rules for "
                                       "the surfaced errors"}
            prev_design_sig = sig

        return {"status":      "max_iters",
                "iters":       max_iters,
                "final_state": result,
                "history":     history}

    def _design_signature(self) -> tuple:
        """A cheap signature of the current design graph. Used by the
        babble loop for deadlock detection — if it doesn't change
        between iterations, the agent isn't refining."""
        out = []
        for nid in self.s.nodes("DesignedFile"):
            a = self.s.node(nid)["attrs"]
            out.append((str(a.get("path", "")),
                         str(a.get("content", "")),
                         len(self.s.neighbours(nid, "ast_root"))))
        # Also sample the AST graph size
        ast_count = sum(len(self.s.nodes(t)) for t in
                          ("RustSource","RustEnumVariant","RustMatchArm",
                            "RustFn","RustStmt","RustLine","RustRaw"))
        out.append(("__ast_count__", ast_count, 0))
        return tuple(sorted(out))
