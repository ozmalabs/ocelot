#!/usr/bin/env python3
"""Driver: the code-authoring loop DRAFTS teacher-free for primitive-shaped
targets — the agent composes its OWN Rust mechanically.

Today the rewrite loop reaches "awaiting_teacher": for any target it asks an
LLM self-teacher to author the replacement. Offline that teacher is absent;
and per the project ethos the agent must compose its OWN code, not phone an
LLM ("the donkey"). This driver shows the FAITHFUL path now closed for the
PRIMITIVE/Term-shaped class:

  1. The agent SPECIFIES a primitive it lacks (runtime_design.agent_specify_*)
     -> a PrimitiveSpec graph node, reasoned from its own science.
  2. A ReplacementTarget is minted for it (op_name = the spec's name) as the
     cortex's current_target.
  3. cortex.tick() fires the NEW `cw_mechanical_draft` reflex BEFORE
     request_author: it recognises the target as emittable, calls the
     mechanical emitter (emit_primitive_rust), and assembles the four-home
     Rust fragments into a CodeDraft (origin='mechanical_emitter'). The loop
     reaches "drafted" with NO teacher.

Then the CONTRAST: a module-scale requires_replacement target from the
self-model (rust_rewrite_world) is NOT emittable -> cw_mechanical_draft
returns False -> the loop stays awaiting_teacher. We print this honestly:
the mechanical emitter closes the primitive-shaped class; module-scale
agent-logic has no mechanical Python->Rust compiler (the open problem), and
we do NOT phone an LLM for it.

Run:  ulimit -v 6291456; timeout 300 python3 scripts/mechanical_draft.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from substrate_rs import _native

from domains import runtime_design
from domains import rust_rewrite_world as rrw
from domains.code_writing_cortex import CodeWritingCortex


# Node/edge types the cortex install + this driver touch. The strict
# `_native.Substrate` requires a Production for every (src, edge, tgt) it
# will see; we open them permissively (world-adapter boot I/O — no
# decisions), exactly as the cortex's own test harness does.
_NODE_TYPES = (
    "RustRewriteRoot", "PythonUnit", "PrimitiveSpec", "OperationSpec",
    "CodeWritingCortex", "CodeAuthoringRoot", "ReplacementTarget",
    "CodeDraft", "ValidationResult", "CodeInstallation",
    "Microtheory", "Concept", "Reflex", "ProgrammingLanguage",
    "DesignPattern", "CodeTarget", "DesignExclusion",
    "LanguageExclusion", "LanguageScoringConfig", "NetworkAssemblage",
    "AssemblageStep", "WeightTensor",
)
_EDGE_TYPES = (
    "has_unit", "rewrites_to",
    "owns_microtheory", "owns_root", "has_reflex", "current_target",
    "has_draft", "validated_by", "installed_as", "genlMt",
    "authored_in", "uses_pattern", "subClassOf", "has_concept",
    "decomposes", "in_category", "has_rule", "exclusion", "has_assemblage",
    "has_step", "has_weight", "watches", "controls",
)


def _open_substrate() -> "_native.Substrate":
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                try:
                    s.add_production({
                        "src": {"type": src_t, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tgt_t, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "mechanical_draft:open",
                    })
                except Exception:
                    pass
    return s


def _hr(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> int:
    s = _open_substrate()
    cortex = CodeWritingCortex(s).install()  # agent=None -> NO self-teacher
    has_teacher = (cortex.agent is not None
                   and getattr(cortex.agent, "_self_teacher", None) is not None)

    _hr("0. SETUP — CodeWritingCortex, no agent, no LLM self-teacher")
    print(f"self-teacher (LLM) online: {has_teacher}  (drafting must be "
          f"teacher-free)")
    reflexes = sorted(
        (s.node(r)["attrs"].get("priority", 0),
         s.node(r)["attrs"].get("name"))
        for r in s.neighbours(cortex.cortex_nid, "has_reflex"))
    print("reflex cascade (priority desc):")
    for pr, nm in sorted(reflexes, reverse=True):
        mark = "  <- mechanical drafter (NEW, pre-empts teacher)" \
            if nm == "cw_mechanical_draft" else ""
        print(f"    [{pr}] {nm}{mark}")

    # ---- 1. The agent SPECIFIES a primitive it lacks --------------------
    _hr("1. AGENT SPECIFIES A PRIMITIVE (reasoned from its own science)")
    spec = runtime_design.agent_specify_primitive(s)
    print(f"PrimitiveSpec minted: name={spec['name']!r}  "
          f"semantic_kind={spec['semantic_kind']!r}")
    print(f"  purpose : {spec['purpose']}")
    print(f"  why_new : {spec['why_new']}")

    # ---- 2. Mint a ReplacementTarget for it as current_target -----------
    _hr("2. TARGET — mint a ReplacementTarget (op_name = the spec's name)")
    tgt = cortex.set_target(spec["name"],
                            baseline={"total_ms": 0.0, "count": 0})
    print(f"current_target: ReplacementTarget(op_name={spec['name']!r}) "
          f"node {tgt}")
    print(f"emittable?     : "
          f"{cortex.emittable_spec_for_target(tgt) is not None}  "
          f"(a PrimitiveSpec the emitter has a template for)")

    # ---- 3. tick() -> the mechanical drafter fires, teacher-free --------
    _hr("3. cortex.tick() — the agent DRAFTS its own Rust mechanically")
    trail = cortex.tick()
    print(f"reflex audit trail: {trail}")
    drafted = "cw_mechanical_draft" in trail
    asked_teacher = "cw_request_author" in trail
    print(f"  cw_mechanical_draft fired : {drafted}")
    print(f"  cw_request_author fired   : {asked_teacher}  "
          f"(False == teacher pre-empted)")

    # The mechanically-emitted CodeDraft persists as a graph node even
    # after the downstream validate/install_if_better reflexes detach the
    # current_target edge (install stays GATED — see framing below). Find
    # it by origin so the drafted artifact is shown regardless of what the
    # rest of the cascade did to the target edge.
    draft = None
    for n in s.nodes("CodeDraft"):
        if s.node(n)["attrs"].get("origin") == "mechanical_emitter":
            draft = n
            break
    if draft is None:
        print("NO DRAFT — unexpected; aborting.")
        return 1
    da = s.node(draft)["attrs"]
    print(f"\nCodeDraft node {draft}:")
    print(f"  origin        : {da.get('origin')}")
    print(f"  primitive     : {da.get('primitive_name')}")
    print(f"  semantic_kind : {da.get('semantic_kind')}")
    # Report what the downstream validate step did with the multi-home
    # bundle (honest: it is not a single buildable lib.rs, so install is
    # gated — the drafting closed, the install did not).
    vnbrs = s.neighbours(draft, "validated_by")
    if vnbrs:
        v = s.node(vnbrs[0])["attrs"]
        print(f"  validation    : compile_ok={v.get('compile_ok')} "
              f"-> install gated (four-home fragments are not one "
              f"buildable lib.rs)")

    _hr("4. THE ACTUAL EMITTED RUST (the agent's mechanically-composed draft)")
    print(da.get("source", ""))

    # ---- 5. CONTRAST: a module-scale target is NOT emittable ------------
    _hr("5. CONTRAST — a module-scale agent-logic target (the open problem)")
    # Build the self-model so we have a real requires_replacement unit.
    rrw.enumerate_python_surface(s, roots=("domains",))
    info = rrw.install_requires_replacement_rule(s)
    rrw.classify_surface(s, info["rule_index"])
    picked = rrw.next_replacement_target(s, attempted={spec["name"]})
    if picked is None:
        print("(no requires_replacement unit found — skipping contrast)")
    else:
        mod_name, baseline = picked
        # Clear the primitive target so the module target becomes current.
        cortex.discard_target_and_draft(reason="demo_switch")
        mod_tgt = cortex.set_target(mod_name, baseline=baseline)
        print(f"current_target: ReplacementTarget(op_name={mod_name!r})")
        emittable = cortex.emittable_spec_for_target(mod_tgt) is not None
        print(f"emittable?     : {emittable}  (no PrimitiveSpec -> "
              f"mechanical emitter cannot draft it)")
        mod_trail = cortex.tick()
        # Dedup for readability: with no teacher online, request_author
        # re-fires each fixed-point round (spawn no-ops, no draft ever
        # appears) — show the distinct steps, note the repeat.
        seen, distinct = set(), []
        for nm in mod_trail:
            if nm not in seen:
                seen.add(nm)
                distinct.append(nm)
        n_author = mod_trail.count("cw_request_author")
        print(f"reflex audit trail (distinct): {distinct}")
        print(f"  (cw_request_author re-fired {n_author}x to fixed point — "
              f"no teacher online, so it never resolves to a draft)")
        print(f"  cw_mechanical_draft fired : "
              f"{'cw_mechanical_draft' in mod_trail}  (returns False — not "
              f"emittable)")
        print(f"  cw_request_author fired   : "
              f"{'cw_request_author' in mod_trail}  (reached the teacher "
              f"step)")
        mod_draft = cortex.current_draft()
        print(f"  draft produced            : {mod_draft is not None}  "
              f"(False: no LLM teacher online -> stays awaiting_teacher)")

    # ---- 6. HONEST FRAMING ----------------------------------------------
    _hr("6. HONEST FRAMING — which class closes teacher-free, which does not")
    print(
        "CLOSES teacher-free: the PRIMITIVE / Term-shaped class. The agent\n"
        "specifies a PrimitiveSpec from its own science; the mechanical\n"
        "emitter (runtime_design.emit_primitive_rust) composes the agent's\n"
        "OWN Rust across the four TermNode homes into a CodeDraft. No teacher,\n"
        "no LLM. The drafting step of the loop is now donkey-free for this\n"
        "class — the milestone: agent-composed Rust.\n\n"
        "STAYS OPEN: module-scale agent-logic (e.g. curious_agent, ~15k\n"
        "lines). There is no general Python->Rust compiler for it, so the\n"
        "mechanical drafter correctly returns False and the loop stays\n"
        "awaiting a REAL compiler rather than fabricating one via an LLM.\n"
        "That is the open problem, named honestly.\n\n"
        "INSTALL still gated (honest): the emitted fragments span FOUR homes\n"
        "(term.rs enum/eval/helper, jsonio.rs name/parse) — not a single\n"
        "buildable lib.rs. The cortex's compile_and_test expects a buildable\n"
        "surface, so validate/install of a multi-home primitive remains the\n"
        "next edge. The DRAFTING closes teacher-free; full validate/install\n"
        "of a multi-home primitive does not. No .rs is overwritten here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
