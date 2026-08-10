"""Code-authoring cognitive content — Mt + Concepts + Reflexes.

This is the substrate-resident knowledge the `CodeWritingCortex` owns.
The cortex itself (in `code_writing_cortex.py`) is a thin world-adapter
that boots this content and dispatches the reflex loop; the REASONING
about *which* hot path to attack, *what* to ask the self-teacher,
*whether* a draft passes validation — that lives here, as graph data.

  * `code_authoring` Microtheory (genlMt: compiler_theory)
  * Concepts: `hot_path`, `replacement_target`, `code_draft`,
    `validation_result`, `code_installation`
  * Reflexes (one per pipeline phase):
      cw_identify_target   — scan op_stats, pick the slowest op
      cw_request_author    — invoke self_teacher with target spec
      cw_drain_teacher     — collect the authored draft when ready
      cw_validate          — compile + test the draft
      cw_install_if_better — swap in iff the draft is faster

Each reflex's stimulus is a Term-tree predicate over graph state on
the cortex node; the response is a Python step callable registered
on the Reflex graph node (matches the existing
`install_phonology_reflexes` shape).

The cortex IS the agent's intrinsic code-writing faculty. It doesn't
depend on what the code is FOR — pointed at the LLVM IR runner, the
phonology pipeline, a parser, the rule engine, anything. The
`replacement_target.path` attr is what makes it concrete per
invocation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_CW_PRODUCTIONS = [
    # Microtheory inheritance anchor (genlMt) — install_code_authoring_mt wires
    # this edge; declare it so it is admissible on a substrate without a blanket
    # Microtheory production (e.g. the seed-booted WorldAdapter). Additive.
    ("Microtheory", "genlMt", "Microtheory", "code_authoring:mt_genlMt"),
    # Cortex ownership.
    ("CodeWritingCortex", "owns_microtheory", "Microtheory",
     "code_authoring:owns_mt"),
    ("CodeWritingCortex", "owns_root", "CodeAuthoringRoot",
     "code_authoring:owns_root"),
    ("CodeWritingCortex", "has_reflex", "Reflex",
     "code_authoring:has_reflex"),

    # State edges — the cortex's working set.
    ("CodeAuthoringRoot", "current_target", "ReplacementTarget",
     "code_authoring:current_target"),
    ("ReplacementTarget", "has_draft", "CodeDraft",
     "code_authoring:has_draft"),
    ("ReplacementTarget", "authored_in", "ProgrammingLanguage",
     "code_authoring:authored_in"),
    ("ReplacementTarget", "uses_pattern", "DesignPattern",
     "code_authoring:uses_pattern"),
    ("CodeDraft", "validated_by", "ValidationResult",
     "code_authoring:validated_by"),
    ("CodeDraft", "installed_as", "CodeInstallation",
     "code_authoring:installed_as"),

    # Language knowledge.
    ("ProgrammingLanguage", "subClassOf", "ProgrammingLanguage",
     "code_authoring:lang_subclass"),

    # Mt → Concept ownership. The arch-cortex's orphaned_concept smell
    # flags Concept nodes without inbound has_concept; this production
    # makes the wiring grammatical.
    ("Microtheory", "has_concept", "Concept",
     "code_authoring:mt_has_concept"),
]


# ---------------------------------------------------------------------------
# Language knowledge — the agent's comparative model of languages.
#
# Each attr is the agent's calibration of that language's properties on a
# small set of dimensions that matter for picking a language for a specific
# rewrite task. The data is what makes "compare languages and choose" a
# graph query, not a hardcoded if-else. Future updates: the agent measures
# its own builds and revises these values from observation.
# ---------------------------------------------------------------------------

_LANG_SEED_PATH = (Path(__file__).resolve().parent.parent /
                   "seeds" / "programming_languages.json")


def _load_lang_seed() -> dict:
    with _LANG_SEED_PATH.open() as f:
        return json.load(f)


def install_language_concepts(substrate) -> dict[str, int]:
    """Install ProgrammingLanguage graph nodes + LanguageExclusion
    nodes + a ScoringConfig node carrying the weights — all read from
    `seeds/programming_languages.json`. No language data lives in
    Python. Idempotent.

    Returns name → NodeID map."""
    seed = _load_lang_seed()
    out: dict[str, int] = {}
    for nid in substrate.nodes("ProgrammingLanguage"):
        out[substrate.node(nid)["attrs"]["name"]] = nid
    for lang in seed.get("languages", []):
        name = lang["name"]
        if name in out:
            continue
        out[name] = substrate.add_node("ProgrammingLanguage", dict(lang))

    # Exclusion pairs as LanguageExclusion graph nodes.
    for ex in seed.get("exclusions", []):
        attr_eq, req_tag = ex
        existing = None
        for n in substrate.nodes("LanguageExclusion"):
            a = substrate.node(n)["attrs"]
            if (a.get("attr_eq") == attr_eq
                    and a.get("requirement_tag") == req_tag):
                existing = n
                break
        if existing is None:
            substrate.add_node("LanguageExclusion", {
                "attr_eq": attr_eq,
                "requirement_tag": req_tag,
                "origin": "programming_languages",
            })

    # Scoring config (weights) as a graph node so the selector reads
    # the weights from the graph, not from Python.
    found_cfg = False
    for n in substrate.nodes("LanguageScoringConfig"):
        found_cfg = True
        break
    if not found_cfg:
        sc = seed.get("scoring_components", {})
        substrate.add_node("LanguageScoringConfig", {
            "ozma_substrate_native_bonus":
                float(sc.get("ozma_substrate_native_bonus", 5)),
            "speed_weight":
                float(sc.get("speed_weight", -1.0)),
            "maturity_plus_ecosystem_weight":
                float(sc.get("maturity_plus_ecosystem_weight", 1.0)),
            "origin": "programming_languages",
        })

    return out


def _read_language_exclusions(substrate) -> list[tuple[str, str]]:
    out = []
    for n in substrate.nodes("LanguageExclusion"):
        a = substrate.node(n)["attrs"]
        out.append((a.get("attr_eq", ""), a.get("requirement_tag", "")))
    return out


def _read_language_scoring_config(substrate) -> dict:
    for n in substrate.nodes("LanguageScoringConfig"):
        return dict(substrate.node(n)["attrs"])
    return {"ozma_substrate_native_bonus": 5.0,
            "speed_weight": -1.0,
            "maturity_plus_ecosystem_weight": 1.0}


def pick_language_for_target(substrate, requirements: list[str]) -> str:
    """Rank ProgrammingLanguage graph nodes against `requirements`,
    consulting LanguageExclusion + LanguageScoringConfig graph nodes
    for the rules. Pure orchestration — no language data or weights in
    this function."""
    langs = []
    for nid in substrate.nodes("ProgrammingLanguage"):
        attrs = substrate.node(nid)["attrs"]
        langs.append((attrs["name"], attrs))
    if not langs:
        return "rust"
    req_set = set(requirements)
    exclusions = _read_language_exclusions(substrate)
    weights = _read_language_scoring_config(substrate)

    def score(attrs: dict) -> tuple:
        # Hard exclusions: each exclusion is `attr_eq:value` paired with
        # a requirement tag. If the language carries the matching attr
        # AND the target carries the requirement, exclude.
        for attr_eq, req_tag in exclusions:
            if ":" not in attr_eq or req_tag not in req_set:
                continue
            k, v = attr_eq.split(":", 1)
            v_bool = v.lower() == "true"
            if bool(attrs.get(k)) == v_bool:
                return (-1, 0.0, 0.0, 0.0)
        matches = len(req_set & set(attrs.get("best_for", [])))
        native_bonus = (float(weights["ozma_substrate_native_bonus"])
                        if attrs.get("ozma_substrate_native") else 0.0)
        speed_contrib = (float(weights["speed_weight"])
                         * float(attrs.get("typical_speed_vs_c", 1.0)))
        mat_contrib = (float(weights["maturity_plus_ecosystem_weight"])
                       * (int(attrs.get("maturity_score", 0))
                          + int(attrs.get("ecosystem_breadth", 0))))
        return (matches, native_bonus, speed_contrib, mat_contrib)

    langs.sort(key=lambda kv: score(kv[1]), reverse=True)
    return langs[0][0]


# ---------------------------------------------------------------------------
# Microtheory + Concepts (the agent's cognitive content)
# ---------------------------------------------------------------------------

def install_code_authoring_mt(substrate) -> int:
    """Install the `code_authoring` Microtheory and its core Concepts.
    Idempotent — re-running returns the existing Mt's NodeID.

    The Mt's genlMt-ancestry includes `compiler_theory` (installed by
    the prior session's compiler_theory_seed), so the agent's existing
    compiler-design knowledge is in scope when code-authoring reasoning
    fires."""
    # Find existing Mt.
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "code_authoring":
            return n

    mt = substrate.add_node("Microtheory", {
        "name": "code_authoring",
        "description": (
            "The agent's intrinsic faculty for authoring its own "
            "internal code: identifying hot paths, framing a "
            "replacement spec, consulting the self-teacher, validating "
            "the draft against the original, installing if better. "
            "Generic over *what* code is being authored — Rust runner, "
            "Python world-adapter, anything the agent can introspect "
            "and target."),
    })

    # Wire genlMt → compiler_theory (so concepts like cost_equivalence,
    # constant_folding, etc. are in scope when code-authoring reasoning
    # runs). The compiler_theory Mt was installed by compiler_theory_seed.
    for mt2 in substrate.nodes("Microtheory"):
        if substrate.node(mt2)["attrs"].get("name") == "compiler_theory":
            try:
                substrate.add_edge(mt, "genlMt", mt2, {})
            except Exception:
                pass
            break

    # Concepts the cortex's reflexes will reference. Each is a
    # graph-resident node WIRED to the code_authoring Mt via
    # `has_concept` so they're not orphans (the architecture cortex
    # caught this on a previous assessment — the install used to
    # mint Concept nodes without linking them to the Mt that owns
    # them, which made them dangling vocabulary the agent couldn't
    # find via Mt-scoped queries).
    _install_concept(substrate, mt, "hot_path",
        "An op whose mean cost or aggregate cost crosses an attention "
        "threshold — the cortex's intuition for what's worth rewriting.")
    _install_concept(substrate, mt, "replacement_target",
        "A specific code unit the cortex has selected for re-authoring. "
        "Carries the path (file or symbol), the existing source, the "
        "performance baseline, and an attention rationale.")
    _install_concept(substrate, mt, "code_draft",
        "An authored replacement returned by the self-teacher. Carries "
        "the source text and a back-reference to its target.")
    _install_concept(substrate, mt, "validation_result",
        "Outcome of compiling + testing a draft against the original: "
        "compile_ok, tests_pass, perf_improvement_factor.")
    _install_concept(substrate, mt, "code_installation",
        "A draft that was validated and installed — replaces the "
        "original in production. The cortex tracks installations as "
        "its own memory of successful self-improvement.")

    return mt


def _install_concept(substrate, owning_mt: int, name: str,
                     definition: str, term: dict | None = None) -> int:
    """Mint or find a Concept node and wire it to `owning_mt` via
    `has_concept`. The Mt edge is what keeps the concept from being
    flagged as orphaned by the architecture cortex's smell detector.

    If `term` is non-None, also register it as the concept's Term-tree
    via `define_concept(name, term)` so Holds-dispatch resolves at
    install time (without needing the runtime concept_grounding walker
    to re-promote it each session)."""
    existing = None
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == name:
            existing = c
            break
    if existing is None:
        existing = substrate.add_node("Concept", {
            "name": name,
            "definition": definition,
            "origin": "code_authoring",
        })
    try:
        substrate.add_edge(owning_mt, "has_concept", existing, {})
    except Exception:
        pass
    _register_concept_term(substrate, name, term)
    return existing


def _register_concept_term(substrate, name: str,
                           term: dict | None) -> bool:
    """Register a Term-tree as `name`'s definition via the substrate's
    `define_concept` PyO3 method. Accepts either the Python wrapper
    `substrate_rs.Substrate` (which expects a `Term` object) or the
    raw inner `_native.Substrate` (which accepts a JSON dict directly).
    Returns True on success, False on no-op or failure. Idempotent —
    later calls overwrite the prior Term-tree.

    The seed-resident path: each loader passes `term=c.get("term")` so
    the Term-tree is registered at install time. This makes seeds
    self-sufficient — Holds-dispatch resolves without first running
    `concept_grounding.install_concept_grounding`."""
    if term is None:
        return False
    # Always use the raw PyO3 method (accepts JSON dict). The Python
    # wrapper's `define_concept` wants a `Term` object — we go around
    # it via `_inner`.
    inner = getattr(substrate, "_inner", substrate)
    try:
        inner.define_concept(name, term)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Reflexes — the cortex's autonomous loop
# ---------------------------------------------------------------------------
#
# Reflex shape (matches the existing pattern: a Reflex graph node carries
# a `step` callable as an attr — the substrate dispatches it when the
# stimulus matches). For an MVP, stimuli are simple guards reading the
# cortex's working set. As the cortex matures, stimuli become Term-tree
# predicates that the substrate evaluates without a Python helper.


# Reflex step callables can't live as substrate attrs (Values must be
# JSON-serializable). Hold them in a module-level registry keyed by
# reflex name; the Reflex graph node stores the name, the registry
# resolves it at dispatch time. The cortex still sees first-class
# graph reflexes — this is just the world-adapter detail.
_STEP_REGISTRY: dict[str, callable] = {}


def get_step(name: str):
    return _STEP_REGISTRY.get(name)


def install_code_authoring_reflexes(substrate, cortex_nid: int) -> list[int]:
    """Install the five autonomous-loop reflexes on `cortex_nid`. Each
    reflex's step callable reads the cortex's working set, decides
    whether to act, and (if so) mutates state OR spawns work."""
    out: list[int] = []

    out.append(_install_reflex(substrate, cortex_nid,
        name="cw_identify_target",
        priority=7,
        stimulus_desc="no current target AND op_stats has at least one op",
        concerns=["op_stats", "current_target"],
        step=_step_identify_target))

    # Design step: pick an architectural pattern BEFORE asking for code.
    # This is the meta-programming move — between identify and author the
    # cortex consults its design-pattern library and picks one that fits
    # the target's tags. The chosen pattern's name + mechanism land in
    # the spec sent to the teacher.
    out.append(_install_reflex(substrate, cortex_nid,
        name="cw_select_design_pattern",
        priority=6,
        stimulus_desc="current target AND no chosen pattern yet",
        concerns=["current_target", "chosen_design_pattern"],
        step=_step_select_design_pattern))

    # The FAITHFUL drafting step. Fires BEFORE request_author: when the
    # target is an EMITTABLE primitive/Term-shaped op (a PrimitiveSpec the
    # agent already specified), the agent composes its OWN Rust via the
    # mechanical emitter — teacher-free, no LLM. Non-emittable (module-
    # scale) targets return False and fall through to the teacher step.
    out.append(_install_reflex(substrate, cortex_nid,
        name="cw_mechanical_draft",
        priority=5,
        stimulus_desc=("current target AND no draft AND target is an "
                       "emittable PrimitiveSpec"),
        concerns=["current_target", "current_draft", "primitive_spec"],
        step=_step_mechanical_draft))

    out.append(_install_reflex(substrate, cortex_nid,
        name="cw_request_author",
        priority=4,
        stimulus_desc="current target AND no draft AND no teacher in flight",
        concerns=["current_target", "teacher_thread"],
        step=_step_request_author))

    out.append(_install_reflex(substrate, cortex_nid,
        name="cw_drain_teacher",
        priority=3,
        stimulus_desc="teacher thread present AND completed",
        concerns=["teacher_thread", "current_draft"],
        step=_step_drain_teacher))

    out.append(_install_reflex(substrate, cortex_nid,
        name="cw_validate",
        priority=2,
        stimulus_desc="draft present AND no validation result yet",
        concerns=["current_draft", "validation_result"],
        step=_step_validate))

    out.append(_install_reflex(substrate, cortex_nid,
        name="cw_install_if_better",
        priority=1,
        stimulus_desc="validation present AND draft strictly better",
        concerns=["validation_result", "code_installation"],
        step=_step_install_if_better))

    return out


def _install_reflex(substrate, cortex_nid: int, *,
                    name: str, priority: int, stimulus_desc: str,
                    concerns: list[str] | None = None,
                    step) -> int:
    _STEP_REGISTRY[name] = step
    # Find or mint the Reflex.
    for r in substrate.nodes("Reflex"):
        if (substrate.node(r)["attrs"].get("name") == name
                and substrate.node(r)["attrs"].get("origin") == "code_authoring"):
            try:
                substrate.add_edge(cortex_nid, "has_reflex", r, {})
            except Exception:
                pass
            return r
    r = substrate.add_node("Reflex", {
        "name": name,
        "priority": int(priority),
        "stimulus_desc": stimulus_desc,
        "concerns": list(concerns) if concerns else [],
        "origin": "code_authoring",
        "refractory_ticks": 0,
    })
    try:
        substrate.add_edge(cortex_nid, "has_reflex", r, {})
    except Exception:
        pass
    return r


# ---------------------------------------------------------------------------
# Reflex step callables — the agent's reasoning, expressed as small
# graph mutations that read state and decide. Each step takes (ctx)
# where ctx is the cortex object; it returns True if the reflex fired
# (state changed), False otherwise.
# ---------------------------------------------------------------------------

def _step_identify_target(ctx) -> bool:
    """Pick the next thing to rewrite, preferring the agent's impl-substrate
    SELF-MODEL over the legacy wall-clock profiler.

    The categorically-correct 'slow that should be fast' signal in this
    architecture is not a hot-path timing — it is 'is this Python in the agent'.
    So FIRST consult the requires_replacement self-model (rust_rewrite_world):
    the graph-resident Rule has already flagged which Python units are
    agent-logic that the Rust runtime must own; pick the highest-priority one.
    Only when the surface has not been enumerated yet (no self-model present)
    fall back to the op_stats hot-path. The 'attempted' set prevents re-picking
    a unit whose previous draft was discarded (re-pick → re-author → re-discard)."""
    if ctx.current_target() is not None:
        return False
    attempted = ctx.attempted_op_names()
    # 1. SELF-MODEL: the next agent-logic Python unit flagged requires_replacement
    #    (the Rule's verdict). next_replacement_target also registers its
    #    CodeTarget so the authoring step can read the source. None until the
    #    surface is enumerated -> fall through to op_stats.
    try:
        from domains.rust_rewrite_world import next_replacement_target
        picked = next_replacement_target(ctx.s, attempted)
    except Exception:
        picked = None
    if picked is not None:
        name, baseline = picked
        ctx.set_target(name, baseline=baseline)
        return True
    # 2. FALLBACK: legacy op_stats hot-path (until the surface is enumerated).
    candidates = {k: v for k, v in ctx.op_stats_snapshot().items()
                  if k not in attempted}
    if not candidates:
        return False
    target_name, stats = max(
        candidates.items(),
        key=lambda kv: (kv[1].get("total_ms", 0.0), kv[0]),
    )
    if stats.get("total_ms", 0.0) <= 0:
        return False
    ctx.set_target(target_name, baseline=stats)
    return True


def _step_select_design_pattern(ctx) -> bool:
    """The meta-programming step. Before asking for code, pick the
    architectural pattern that fits this target. Reads the agent's
    DesignPattern library (graph data) and ranks by tag-match ×
    expected_speedup; attaches the winning pattern via a
    `uses_pattern` edge from the target.

    Returns True iff a pattern was selected (or no-match recorded)."""
    target = ctx.current_target()
    if target is None:
        return False
    if ctx.chosen_design_pattern() is not None:
        return False
    # If we already searched and found nothing, don't re-fire.
    target_attrs = ctx.s.node(target)["attrs"]
    if target_attrs.get("design_pattern_search") == "no_match":
        return False
    chosen = ctx.pick_pattern_for_current_target()
    if chosen is None:
        ctx.note_no_pattern_matched()
        return True
    ctx.attach_design_pattern(chosen)
    return True


def _step_mechanical_draft(ctx) -> bool:
    """The FAITHFUL, teacher-free drafting step — the agent composes its
    OWN implementation, NO LLM. Two teacher-free draft SOURCES, tried in
    order; both pre-empt the teacher (`_step_request_author`) whenever
    they apply:

      1. EMITTABLE PRIMITIVE — the target is a Term/primitive-shaped op
         the agent already specified as a PrimitiveSpec: it emits the
         four-home Rust fragments (runtime_design.emit_primitive_rust)
         and assembles them into a CodeDraft (origin='mechanical_emitter').

      2. READ-METHOD GAP — the target carries a `method_text` describing a
         capability the agent lacks: it READS the method, GROUNDS the
         binding, and SYNTHESISES a RewriteRule
         (read_method_draft.draft_from_reading), attaching a
         `read_method_rule` CodeDraft. This is the read→implement path
         plugged in as a draft source: the same downstream validate +
         install reflexes then verify-by-running and adopt it.

    Returns False (fall through to the teacher step) when there is no
    current target, a draft already exists, or the target is NEITHER an
    emittable primitive NOR a read-method gap (module-scale agent-logic
    — the open problem; no mechanical Python->Rust compiler, and we do
    not phone an LLM)."""
    target = ctx.current_target()
    if target is None:
        return False
    if ctx.current_draft() is not None:
        return False
    # source 1: emittable primitive spec -> mechanical Rust emitter.
    if ctx.emittable_spec_for_target(target) is not None:
        return ctx.mechanically_draft(target) is not None
    # source 2: a read-method gap -> read + ground + synthesise a rule.
    if ctx.has_read_method(target):
        return ctx.draft_read_method_rule(target) is not None
    return False


def _step_request_author(ctx) -> bool:
    """If a target is set and no draft exists yet, frame the request
    and spawn the self-teacher thread. Returns True iff a request was
    sent in this step."""
    target = ctx.current_target()
    if target is None:
        return False
    if ctx.current_draft() is not None:
        return False
    if ctx.teacher_in_flight():
        return False
    question = ctx.compose_authoring_question(target)
    if question is None:
        return False
    ctx.spawn_teacher(question)
    return True


def _step_drain_teacher(ctx) -> bool:
    """If a teacher thread is complete, absorb its response as the
    target's draft."""
    if not ctx.teacher_in_flight():
        return False
    payload = ctx.try_collect_teacher_payload()
    if payload is None:
        return False
    ctx.attach_draft(payload)
    return True


def _step_validate(ctx) -> bool:
    """Compile + test the draft against the original. Records a
    ValidationResult on the draft."""
    draft = ctx.current_draft()
    if draft is None:
        return False
    if ctx.draft_validation(draft) is not None:
        return False
    result = ctx.compile_and_test(draft)
    ctx.attach_validation(draft, result)
    return True


def _step_install_if_better(ctx) -> bool:
    """If the draft validated and is faster than the baseline, install
    it. The criterion (perf_improvement_factor > 1) is the agent's
    own definition of 'better' — recorded in the validation node."""
    draft = ctx.current_draft()
    if draft is None:
        return False
    val = ctx.draft_validation(draft)
    if val is None:
        return False
    if not val.get("compile_ok") or not val.get("tests_pass"):
        ctx.discard_target_and_draft(reason="validation_failed")
        return True
    # A multi-home PRIMITIVE or a READ-METHOD RULE is a correctness addition
    # (a new Term / a new rule), not a perf rewrite — there is no faster/slower
    # bench to clear. Gate it on compile_ok + tests_pass only (for a rule-draft,
    # tests_pass == the described effect ran under the trigger). The perf>1.0
    # gate still governs the rewrite path (drafts without these kinds).
    draft_attrs = ctx.s.node(draft)["attrs"]
    if draft_attrs.get("kind") in ("multi_home_primitive", "read_method_rule"):
        ctx.install_draft(draft)
        return True
    factor = val.get("perf_improvement_factor", 1.0)
    if factor <= 1.0:
        ctx.discard_target_and_draft(reason="no_speedup")
        return True
    ctx.install_draft(draft)
    return True


__all__ = [
    "install_code_authoring_mt",
    "install_code_authoring_reflexes",
    "_CW_PRODUCTIONS",
]
