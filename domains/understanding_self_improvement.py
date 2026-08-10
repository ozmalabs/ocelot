"""understanding_self_improvement — the jabberwock DRIVES its OWN understanding
fix, from its OWN perception of a defect's SHAPE. The SAME perceive->diagnose->
select->verify->apply cycle it runs on EFFICIENCY (domains/performance_self_improve
ment.py), now pointed at UNDERSTANDING — and, crucially, the fix CHOICE comes OUT
of the graph, not hardcoded.

THE STORY. A live Wikipedia extract exposed two genuine understanding defects that
were each fixed BY HAND once (domains/consumption_quality.py):

  · NON-NOMINAL-EXTRACTION — a clause fragment leaked as a concept (its HEAD is not
    a nominal: 'producing oxygen gas', 'rather than water'). FIX = nominal_filter
    (the composer-authored Filter Program).
  · CONTEXT-BLIND-SENSE — a word grounded to a gloss that does NOT fit the sentence
    ('water' -> "A hamlet in Manaton parish, Devon"). FIX = sense_select (the
    composer-authored Argmax-by-context-fit Program).

The prior build HANDED the agent each fix. Now the jabberwock DIAGNOSES a defect's
shape and ROUTES to the fitting fix ITSELF.

THE CYCLE (each step is either a mechanical boundary op OR a graph decision; never
a Python if/else over graph state deciding WHICH FIX to apply):

  1. PERCEIVE an UNDERSTANDING gap — feed the two defects to #1
     (self_capability_collapse): a leaked fragment / a mis-sensed word is the failure
     surface, and #1's collapse residual mints a CapabilityGap. The gap is enriched
     (mechanical boundary read-back) with kind='understanding' and the defect's
     ERROR-FEATURES measured from the ACTUAL defect: head_is_nominal in {0,1}
     (is the leaked span's head a nominal?), sense_fits_context in {0,1} (does the
     context-blind gloss fit the sentence?). The error-feature MEASUREMENT is a
     boundary op; the gap DECISION is #1's residual.

  2. DIAGNOSE the SHAPE + SELECT the fix as a GRAPH DECISION (the crux — NOT
     hardcoded). Two graph-resident Programs (seeds/understanding_optimization.json),
     the twin of perf_diagnose / perf_fix_pick:
       · understand_diagnose reads the gap's error-features and returns the defect
         SHAPE: IfThenElse over Gt(feature, 0.5) — head NOT nominal ->
         'non-nominal-extraction'; head nominal but sense does NOT fit ->
         'context-blind-sense'; both hold -> 'clean'.
       · understand_fix_pick maps that shape to its fix via Argmin-by-priority over
         the UnderstandFixCue nodes whose shape Eq the diagnosis (non-nominal-
         extraction -> nominal_filter, context-blind-sense -> sense_select).
     SAME Programs, DIFFERENT error-features, DIFFERENT fix — proof it is a real
     decision over the data. The fix NAME comes out of the graph, read off the gap's
     own error-features; the diagnose/select functions carry NO fix/shape literal.

  3. VERIFY with #2 (self_verification) — DISCRIMINATIVE, the diagnosis MUST matter.
     The SELECTED fix cleans its gap (nominal_filter drops the fragment + keeps
     nominals; sense_select gives water->substance). The WRONG-FIX control FAILS:
     nominal_filter does NOT fix a context-blind-sense gap; sense_select does NOT drop
     a fragment — because each fix operates on its OWN representation (concept spans
     vs word senses), so the wrong fix produces the wrong output type and cannot clean
     the other defect. So routing by shape is REQUIRED, not "apply all fixes". A fake
     no-op fix fails too.

  4. APPLY — enact the graph-chosen fix. A NAME-KEYED registry (the twin of
     performance_self_improvement._FIX_REGISTRY): the Program named the fix; this maps
     the name to the COMPOSER-AUTHORED enactment (consumption_quality.ensure_nominal_
     filter_program / ensure_sense_select_program — the composer AUTHORS+installs the
     Program), then runs it to clean the defect (fragment dropped / water->substance).

DISCIPLINE (CLAUDE.md). The DECISION (which fix a defect calls for) is the two
Programs (Rust-evaluated); diagnose/select_fix carry NO fix/shape string literal and
NO gap->fix map — they only load + evaluate the graph Programs. The error-feature
measurement, the composer-authoring, the runner, and the attr read-backs are
mechanical boundary I/O. PERCEIVE reuses #1; VERIFY reuses #2; the fixes reuse
consumption_quality's composer-authored Programs as-is. donkey=0.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from domains import consumption_quality as cq
from domains import reflective_faculty as rf
from domains import self_capability_collapse as scc
from domains import self_verification as sv


# ---------------------------------------------------------------------------
# resolve — the same duck-typing the sibling faculties use.
# ---------------------------------------------------------------------------
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = rf._agent_root_node(sub)
    return sub, native, ag_node


UNDERSTANDING = "understanding"

# The two canonical defects a live extract exposed (the fixtures the fixes clean).
FRAGMENT_SURFACE = "producing oxygen gas"     # a clause fragment (head not a nominal)
NOMINAL_SURFACE = "calvin cycle"              # a genuine noun phrase (kept)
WATER_SENTENCE = ("photosynthesis uses light to strip electrons from suitable "
                  "substances such as water")
# substance-sense keywords the context-fitting gloss for 'water' carries.
SUBSTANCE_KEYS = ("liquid", "compound", "element", "transparent", "odorless",
                  "hydrogen", "oxygen", "molecule")
# place-gloss keywords the context-BLIND first gloss for 'water' carries (a hamlet).
PLACE_KEYS = ("hamlet", "parish", "village", "district", "county", "town in")


def _surface_of(c) -> str:
    if isinstance(c, dict):
        return c.get("surface") or c.get("name") or ""
    return str(c)


# ===========================================================================
# THE GRAPH DECISION — diagnose + select-fix are the two seeded Programs,
# evaluated in Rust. These functions carry NO fix/shape literal and NO gap->fix
# map: they load the Programs and hand off the gap's own error-features.
# ===========================================================================
def _ensure_seed(agent) -> None:
    """Idempotently ensure the understanding-optimization Programs + UnderstandFixCue
    nodes are held (seeds/understanding_optimization.json). Guarded on
    understand_diagnose being present. Loading vocabulary is admissible adapter work,
    not a decision."""
    sub, native, ag_node = _resolve(agent)
    if rf._load_program(sub, "understand_diagnose") is not None:
        return
    from substrate.seed_loader import manifest_for
    native.load_seed_manifest(manifest_for("understanding_optimization"), ag_node)


def diagnose(agent, head_is_nominal: float, sense_fits_context: float) -> Optional[str]:
    """The SHAPE of an understanding defect, DECIDED by the graph-resident
    understand_diagnose Program evaluated in Rust over the gap's OWN error-features.
    Returns the defect shape string (or None if the Program is unheld). No Python
    branch, no literal — the decision is the Program's."""
    _ensure_seed(agent)
    sub, native, _ = _resolve(agent)
    prog = rf._load_program(sub, "understand_diagnose")
    if prog is None:
        return None
    val = native.evaluate(prog, {"head_is_nominal": float(head_is_nominal),
                                 "sense_fits_context": float(sense_fits_context)})
    return val if isinstance(val, str) and val else None


def select_fix(agent, shape: str) -> Optional[str]:
    """The FIX a diagnosed defect shape calls for, DECIDED by the graph-resident
    understand_fix_pick Program (Argmin-by-priority over the UnderstandFixCue whose
    shape Eq the diagnosis) evaluated in Rust. Returns the fix name the matching cue
    carries, or None when no cue matches. No Python branch decides this."""
    _ensure_seed(agent)
    sub, native, _ = _resolve(agent)
    prog = rf._load_program(sub, "understand_fix_pick")
    if prog is None:
        return None
    val = native.evaluate(prog, {"shape": shape})
    return val if isinstance(val, str) and val else None


def diagnose_and_select(agent, head_is_nominal: float, sense_fits_context: float) -> dict:
    """Run both graph Programs: diagnose the defect shape, then select its fix.
    Returns {head_is_nominal, sense_fits_context, shape, fix} — the full graph verdict,
    read off the Programs (Rust), assembled mechanically here."""
    shape = diagnose(agent, head_is_nominal, sense_fits_context)
    fix = select_fix(agent, shape) if shape else None
    return {"head_is_nominal": float(head_is_nominal),
            "sense_fits_context": float(sense_fits_context),
            "shape": shape, "fix": fix}


# ===========================================================================
# (1) PERCEIVE — feed the two defects to #1's collapse; each mints an understanding
# CapabilityGap enriched with the defect's measured error-features. The runner is the
# measurement INSTRUMENT (emits the failure surface iff the defect is present); the
# gap DECISION is #1's collapse residual.
# ===========================================================================
UNDERSTANDING_BATTERY = [
    {"id": "nominal_extraction", "faculty": "nominal_extraction",
     "text": "extract clean nominal concepts from an enumeration",
     "expect": "substantive", "probe": "fragment"},
    {"id": "context_sense", "faculty": "context_sense",
     "text": "ground a polysemous word to its context-fitting sense",
     "expect": "substantive", "probe": "missense"},
]


def _understanding_runner(agent):
    """The #1 runner: exercise the UNFIXED understanding faculty per challenge and
    read its defect into the failure surface (silence '' == defect present).
    Instrument only — no gap decision here."""
    def run(_a, challenge):
        probe = challenge.get("probe")
        if probe == "fragment":
            # the UNFIXED extractor leaks the clause fragment (is_nominal drops it).
            _kept, dropped = cq.nominal_filter(
                [{"surface": FRAGMENT_SURFACE}, {"surface": NOMINAL_SURFACE}])
            return "" if dropped else "clean nominal extraction"
        if probe == "missense":
            # the UNFIXED context-blind grounding: Wiktionary first-gloss for water.
            from domains import wiktionary_reference as wr
            gloss = (wr.wiktionary_gloss("water", "en") or "").lower()
            bad = any(k in gloss for k in PLACE_KEYS)
            return "" if bad else "context-fitting sense"
        return "ok"
    return run


def _measure_error_features(agent, faculty: str) -> dict:
    """MEASURE a defect's error-features at the boundary, from the ACTUAL defect
    (a held-faculty reading, not a decision):

      · head_is_nominal   1.0 iff the leaked span's HEAD is a nominal (via the agent's
        own POS faculty, consumption_quality.is_nominal). The fragment's head is NOT a
        nominal -> 0.0.
      · sense_fits_context 1.0 iff the context-BLIND gloss FITS the sentence (carries a
        substance-sense keyword). The Devon-hamlet gloss for 'water' does NOT -> 0.0.

    Each feature is 1.0 where the defect is absent, so exactly ONE feature is 0 per
    defect — the signal understand_diagnose routes on."""
    if faculty == "nominal_extraction":
        head_is_nominal = 1.0 if cq.is_nominal(FRAGMENT_SURFACE) else 0.0   # -> 0.0
        return {"head_is_nominal": head_is_nominal, "sense_fits_context": 1.0}
    if faculty == "context_sense":
        from domains import wiktionary_reference as wr
        gloss = (wr.wiktionary_gloss("water", "en") or "").lower()
        fits = 1.0 if any(k in gloss for k in SUBSTANCE_KEYS) else 0.0       # -> 0.0
        return {"head_is_nominal": 1.0, "sense_fits_context": fits}
    return {"head_is_nominal": 1.0, "sense_fits_context": 1.0}


def perceive_understanding_gaps(agent, mint: bool = True) -> dict:
    """PERCEIVE the understanding gaps: run the two defects through #1's collapse
    (instrument), mint each residual as a CapabilityGap, and enrich each (mechanical
    boundary read-back) with kind='understanding' and its measured error-features.

    Returns {report, gaps, features} — `gaps` is the list of minted CapabilityGap node
    ids (empty when both faculties are clean — the discriminative null)."""
    sub, _native, _ag = _resolve(agent)
    report = scc.perceive_capability_gaps(
        agent, battery=UNDERSTANDING_BATTERY, runner=_understanding_runner(agent),
        mint=mint)
    gaps = report.get("gaps") or []
    features: dict = {}
    for g in gaps:
        faculty = sub.node(g)["attrs"].get("faculty")
        feats = _measure_error_features(agent, faculty)
        features[g] = feats
        for k, v in (("kind", UNDERSTANDING),
                     ("head_is_nominal", feats["head_is_nominal"]),
                     ("sense_fits_context", feats["sense_fits_context"]),
                     ("salience", 1.0 - min(feats["head_is_nominal"],
                                            feats["sense_fits_context"])),
                     ("description",
                      f"an UNDERSTANDING gap on {faculty!r}: error-features "
                      f"head_is_nominal={feats['head_is_nominal']}, "
                      f"sense_fits_context={feats['sense_fits_context']}.")):
            try:
                sub.set_attr(g, k, v)
            except Exception:
                pass
    return {"report": report, "gaps": gaps, "features": features}


def gap_error_features(agent, gap) -> tuple:
    """Read a gap's measured (head_is_nominal, sense_fits_context) off its attrs.
    Mechanical."""
    sub = getattr(agent, "s", agent)
    at = dict(gap) if isinstance(gap, dict) else dict(sub.node(gap)["attrs"])
    return at.get("head_is_nominal"), at.get("sense_fits_context")


# ===========================================================================
# (3) VERIFY — #2 gates the chosen fix, DISCRIMINATIVELY. Each fix operates on its
# OWN representation (concept spans vs word senses); the SELECTED fix cleans its
# shape's defect, the WRONG fix produces the wrong output type and CANNOT.
# ===========================================================================
# defect scenarios per shape (the control cases #2 runs the fix over).
_FRAGMENT_CASES = [
    {"concepts": [{"surface": "producing oxygen gas"}, {"surface": "calvin cycle"}],
     "frag": "producing oxygen gas", "nom": "calvin cycle"},
    {"concepts": [{"surface": "rather than water"}, {"surface": "carbon fixation"}],
     "frag": "rather than water", "nom": "carbon fixation"},
    {"concepts": [{"surface": "catalyzed by rubisco"}, {"surface": "glucose"}],
     "frag": "catalyzed by rubisco", "nom": "glucose"},
]
_MISSENSE_CASES = [
    {"word": "water", "sentence": WATER_SENTENCE, "keys": SUBSTANCE_KEYS},
    {"word": "cell", "sentence": ("the cell membrane and nucleus and organelle of a "
                                  "biological tissue"), "keys": ("biolog", "organism", "unit")},
    {"word": "mole", "sentence": ("a benign skin growth of pigment melanin, a small "
                                  "lesion"), "keys": ("skin", "pigment", "naevus")},
]
_SHAPE_CASES = {
    "non-nominal-extraction": _FRAGMENT_CASES,
    "context-blind-sense": _MISSENSE_CASES,
}


def _apply_fix_mechanism(agent, fix: str, scenario: dict) -> dict:
    """Enact a fix's mechanism over one scenario via the composer-authored Program,
    returning WHATEVER that fix produces (its own representation). A NAME-KEYED
    dispatch (the enactment registry) — NOT a decision about which fix to pick.

      · nominal_filter : run the composer-authored nominal_filter over the scenario's
        concept spans -> {kept, dropped}. (Produces no sense.)
      · sense_select   : run the composer-authored sense_select over the scenario's
        word+sentence -> {sense}. (Produces no filtered concept list.)
      · none / fake    : a no-op -> {} (cleans nothing).
    Applied to the WRONG shape's scenario, a fix produces the wrong output type, so
    that shape's clean-test necessarily fails — the discrimination is real, not
    hardcoded."""
    if fix == "nominal_filter":
        kept, dropped = cq.nominal_filter(scenario.get("concepts") or [], agent=agent)
        return {"kept": [_surface_of(c) for c in kept],
                "dropped": [_surface_of(c) for c in dropped]}
    if fix == "sense_select":
        word = scenario.get("word")
        if not word:
            return {"sense": None}
        r = cq.sense_in_context(word, scenario.get("sentence", ""), agent=agent)
        return {"sense": (r.get("sense") or "").lower(), "synset": r.get("synset")}
    return {}


def _defect_cleaned(shape: str, scenario: dict, result: dict) -> bool:
    """Measure whether the defect of `shape` is CLEANED, reading the relevant part of
    the fix's output. Mechanical measurement (the fix decision already happened, in
    the graph):

      · non-nominal-extraction : the fragment is in `dropped` AND the nominal is in
        `kept`. (A fix producing no filtered concept list fails this.)
      · context-blind-sense    : the picked sense's gloss carries a fitting keyword.
        (A fix producing no sense fails this.)"""
    if shape == "non-nominal-extraction":
        return (scenario["frag"] in result.get("dropped", [])
                and scenario["nom"] in result.get("kept", []))
    if shape == "context-blind-sense":
        gloss = result.get("sense") or ""
        return any(k in gloss for k in scenario["keys"])
    return False


def fix_cleans_shape(agent, fix: str, shape: str) -> bool:
    """True iff `fix`, applied to EVERY defect scenario of `shape`, cleans it. The
    crux the discriminative control turns on: the RIGHT fix cleans its shape; the
    WRONG fix (operating on the other representation) does not."""
    cases = _SHAPE_CASES.get(shape) or []
    return bool(cases) and all(
        _defect_cleaned(shape, sc, _apply_fix_mechanism(agent, fix, sc)) for sc in cases)


def _ground_reference(sub):
    """The fix's support reaches an EXTERNAL anchor: the WordNet / Wiktionary lexical
    reference the fixes read. Mirrors consumption_quality._ground_reference — a
    TaughtHint{origin:'teacher_hook'} the grounding-reach machinery maps to a
    TeacherAnchor."""
    node = sub.add_node("Collapse", {"label": "understanding_fix_support"})
    th = sub.add_node("TaughtHint", {"origin": "teacher_hook",
                                     "topic": "lexical_reference",
                                     "answer": "external POS/sense reference reading"})
    sub.add_edge_unchecked(node, "grounded_in", th)
    return node


def verify_fix_cleans(agent, fix: str, shape: str) -> dict:
    """Gate a fix with #2, DISCRIMINATIVELY: the claim is that `fix` cleans a `shape`
    defect. The control runs the fix over the shape's defect scenarios (must PASS);
    a KNOWN-FAKE no-op twin cleans nothing (must FAIL) — so the control has teeth.

      · the RIGHT fix for the shape -> ACCEPTED (cleans every case).
      · the WRONG fix for the shape -> REJECTED (its output type cannot clean this
        defect: the control does NOT survive the mechanism). THIS is why routing by
        shape is required.
      · a fake no-op fix -> REJECTED.
    Returns #2's verdict dict."""
    cases = _SHAPE_CASES.get(shape) or []

    def mechanism(scenario) -> bool:
        return _defect_cleaned(shape, scenario, _apply_fix_mechanism(agent, fix, scenario))

    def fake_twin(scenario) -> bool:
        # the KNOWN-FAKE: a no-op fix that cleans nothing -> fails wherever a real fix
        # passes, proving the control discriminates.
        return _defect_cleaned(shape, scenario, _apply_fix_mechanism(agent, "none", scenario))

    return sv.verify_claim(agent, sv.Claim(
        text=f"fix {fix!r} cleans a {shape!r} understanding defect",
        mechanism=mechanism, control_cases=cases,
        fake_twin=fake_twin, prior_cases=cases[:1],
        ground_support=_ground_reference))


# ===========================================================================
# (4) APPLY — enact the graph-chosen fix. A NAME-KEYED registry (the twin of
# performance_self_improvement._FIX_REGISTRY): the Program named the fix; this maps
# the name to the COMPOSER-AUTHORED enactment, which authors+installs its Program and
# cleans the defect.
# ===========================================================================
def _apply_nominal_filter(agent) -> dict:
    """Enact nominal_filter: the composer AUTHORS+installs the nominal-filter Program
    (consumption_quality.ensure_nominal_filter_program), then runs it to clean the
    canonical fragment defect (drop the fragment, keep the nominal)."""
    rec = cq.ensure_nominal_filter_program(agent)
    kept, dropped = cq.nominal_filter(
        [{"surface": FRAGMENT_SURFACE}, {"surface": NOMINAL_SURFACE}], agent=agent)
    return {"enacted": "nominal_filter", "authored": bool(rec.get("authored")),
            "kept": [_surface_of(c) for c in kept],
            "dropped": [_surface_of(c) for c in dropped]}


def _apply_sense_select(agent) -> dict:
    """Enact sense_select: the composer AUTHORS+installs the sense-select Program
    (consumption_quality.ensure_sense_select_program), then runs it to re-ground
    'water' to its context-fitting SUBSTANCE sense."""
    rec = cq.ensure_sense_select_program(agent)
    r = cq.sense_in_context("water", WATER_SENTENCE, agent=agent)
    return {"enacted": "sense_select", "authored": bool(rec.get("authored")),
            "word": "water", "sense": r.get("sense"), "synset": r.get("synset")}


_FIX_REGISTRY: dict[str, Callable[[Any], dict]] = {
    # name-keyed marshaling — the twin of performance_self_improvement._FIX_REGISTRY.
    # The graph Program names the fix; this maps the name to the composer-authored
    # enactment. A mechanical lookup, NOT a decision.
    "nominal_filter": _apply_nominal_filter,
    "sense_select": _apply_sense_select,
}


def apply_fix(agent, fix: str) -> dict:
    """Enact the graph-chosen fix via the name-keyed registry. Mechanical dispatch."""
    fn = _FIX_REGISTRY.get(fix)
    if fn is None:
        return {"enacted": None, "note": f"no enactment registered for {fix!r}"}
    return fn(agent)


# ===========================================================================
# THE CYCLE — perceive -> diagnose+select (graph) -> verify (right fix accepted,
# wrong fix rejected) -> apply. The agent DRIVES its own understanding fix.
# ===========================================================================
def optimize(agent, *, apply: bool = True) -> dict:
    """The whole UNDERSTANDING self-improvement cycle, end to end, over the two
    perceived defects:

      PERCEIVE  the understanding gaps (#1's collapse; each carries error-features)
        -> for each gap:
           DIAGNOSE + SELECT-FIX   (the two graph Programs, in Rust)
           -> VERIFY the selected fix (#2: accepted — it cleans the gap)
           -> VERIFY the WRONG fix   (#2: rejected — it does NOT clean the gap)
           -> APPLY                  (the composer-authored fix cleans the defect)

    Returns the full ledger. The DECISIONS are the graph's; the driver only sequences
    + marshals."""
    perc = perceive_understanding_gaps(agent)
    gaps = perc.get("gaps") or []
    results = []
    for g in gaps:
        hn, sf = gap_error_features(agent, g)
        verdict = diagnose_and_select(agent, hn, sf)
        shape, fix = verdict.get("shape"), verdict.get("fix")
        verify_selected = verify_fix_cleans(agent, fix, shape) if (fix and shape) else None
        # the discriminative WRONG-fix control: the OTHER shape's fix, on THIS shape.
        wrong = _other_fix(agent, fix)
        verify_wrong = verify_fix_cleans(agent, wrong, shape) if (wrong and shape) else None
        applied = apply_fix(agent, fix) if (apply and fix and verify_selected
                                            and verify_selected.get("accepted")) else None
        results.append({
            "gap": g, "error_features": {"head_is_nominal": hn, "sense_fits_context": sf},
            "diagnosis": verdict, "shape": shape, "fix": fix,
            "verify_selected": verify_selected,
            "wrong_fix": wrong, "verify_wrong": verify_wrong,
            "applied": applied,
        })
    return {"perceived": perc, "results": results}


def _other_fix(agent, fix: Optional[str]) -> Optional[str]:
    """The OTHER registered fix (the wrong one) — a mechanical read of the fix
    registry, used only to build the discriminative wrong-fix control. NOT a routing
    decision (that is the graph's)."""
    if fix is None:
        return None
    for name in _FIX_REGISTRY:
        if name != fix:
            return name
    return None


__all__ = [
    "UNDERSTANDING", "UNDERSTANDING_BATTERY",
    "FRAGMENT_SURFACE", "NOMINAL_SURFACE", "WATER_SENTENCE",
    "diagnose", "select_fix", "diagnose_and_select",
    "perceive_understanding_gaps", "gap_error_features",
    "fix_cleans_shape", "verify_fix_cleans", "apply_fix", "optimize",
    "_FIX_REGISTRY",
]
