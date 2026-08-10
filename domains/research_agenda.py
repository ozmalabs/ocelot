"""research_agenda — SELF-IMPROVEMENT #5: THE RESEARCH-AGENDA DRIVER.

The four self-improvement faculties now exist, each held and tested:

  #1  domains/self_capability_collapse  — PERCEIVE a gap in ITSELF (a behavioral
      failure on a challenge battery mints a CapabilityGap, the collapse residual).
  #2  domains/self_verification         — VERIFY a claimed fill (a discriminative
      control + no-regression + grounding gate; accept iff it survives).
  #3  domains/gap_driven_acquisition    — FILL a KNOWLEDGE gap (a thin/ungrounded
      dimension): read -> extract -> teach -> re-decode (coverage rises).
  #4  domains/substrate_extension       — FILL a CAPABILITY gap: compose a multi-rule
      faculty from held primitives (verify-before-trust), else spec a PrimitiveRequest.

This module is the META-LOOP that CHAINS them into the self-improvement CYCLE the
agent runs on ITSELF:

    PERCEIVE  (#1: the challenge battery -> a queue of CapabilityGaps)
      -> PRIORITIZE  (order the queue by a residual salience, over graph state)
      -> for each gap, in salience order:
           ROUTE     (by the gap's KIND -> its filler; a GRAPH dispatch, not a branch)
           FILL      (call the held faculty the route selected: #3 or #4)
           VERIFY    (#2 gates the fill: accept the real, reject the fake)
           ACCEPT/REJECT + record  (a rejected fill leaves the gap OPEN, honestly)
      -> LOOP to the next
      -> STOP  (the queue drains / no gap is left perceivable — a clean resting point)

WHAT THIS DRIVER ADDS: NOTHING but the SEQUENCING. The perceiving is #1's collapse
residual; the filling is #3/#4; the verifying is #2's Rust verdict rule. The one
decision the driver makes per gap -- WHICH FILLER -- is a GRAPH DISPATCH
(seeds/research_agenda_dispatch.json: the `route_pick` Program over GapRouteCue
nodes, evaluated in Rust), the exact twin of ground_concern's `composer_pick`. The
host only MARSHALS: it reads the kind the held faculties' own signals imply, writes
it as the gap's `kind` attr (the same admissible boundary read #1's `observe_outcome`
makes), evaluates the route Program, and calls the filler the Program named. No
if/else over graph state decides the route; no new cognition lives here.

HONEST SCOPE (stated plainly). This drives the cycle over the gaps #1 can PERCEIVE
(behavioral battery failures) + any CapabilityGap another faculty mints, and fills
them via #3 (knowledge) / #4 (capability). It is NOT an open-ended researcher: it
does not invent challenges, form novel hypotheses beyond a gap's own observation, or
reach past what #3/#4 can fill. It closes the loop end-to-end on a small scale -- the
session's own meta-process, run autonomously by the agent on itself. A gap it cannot
fill (no source; a primitive-needing capability; a fill that fails verification) is
left OPEN and reported, never falsely closed.

DISCIPLINE. The route-by-kind is graph data. The driver calls held faculties and
reads their verdicts back mechanically. The PRIORITIZE salience is a held Rust Term
(the shortfall-residual shape from seeds/residual_salience.json), evaluated -- not a
Python scoring heuristic. The queue drain is admissible host I/O (a mechanical loop
that terminates when no perceived gap remains).
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from domains import gap_driven_acquisition as gda
from domains import reflective_faculty as rf
from domains import self_capability_collapse as scc
from domains import self_verification as sv
from domains import substrate_extension as se

# statuses a CapabilityGap carries as it moves through the cycle.
PERCEIVED = "perceived"     # in the queue, not yet processed
CLOSED = "closed"           # filled + verification accepted
OPEN = "open"               # processed but not filled/accepted (honest: left open)

KNOWLEDGE = "knowledge"
CAPABILITY = "capability"


# ---------------------------------------------------------------------------
# resolve — the same duck-typing the four faculties + the composer use.
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


def _gap_attrs(agent, gap) -> dict:
    sub = getattr(agent, "s", agent)
    return dict(gap) if isinstance(gap, dict) else dict(sub.node(gap)["attrs"])


def _set(agent, gap, key, value) -> None:
    if isinstance(gap, dict):
        gap[key] = value
        return
    sub = getattr(agent, "s", agent)
    try:
        sub.set_attr(gap, key, value)
    except Exception:
        pass


# ===========================================================================
# (a) PERCEIVE — #1's collapse residual mints the queue.
# ===========================================================================
def perceive(agent, battery: Optional[list] = None) -> list:
    """Run #1's self-capability collapse over the challenge battery; return the
    CapabilityGap node ids in the queue (status == perceived). A pure marshal of
    self_capability_collapse.perceive_capability_gaps + a read of the perceived
    gaps already on the graph (another faculty may have minted some). The gap
    DECISION is #1's collapse residual, not this function."""
    sub = getattr(agent, "s", agent)
    if battery is not None:
        scc.perceive_capability_gaps(agent, battery=battery)
    queue = []
    for n in sub.nodes("CapabilityGap"):
        if sub.node(n)["attrs"].get("status", PERCEIVED) == PERCEIVED:
            queue.append(n)
    return queue


# ===========================================================================
# KIND — a mechanical boundary read off the held faculties' own signals (the
# same admissible translation #1's observe_outcome makes). NOT the route: this
# only translates the gap into its kind TOKEN; the route (kind -> filler) is the
# graph Program below.
# ===========================================================================
def classify_kind(agent, gap) -> str:
    """Read the gap's KIND off held signals and write it as the gap's `kind` attr.

    KNOWLEDGE iff the gap names a knowledge DOMAIN (gap_driven_acquisition.
    gap_domain_of) AND that domain is a knowledge gap by the concept-graph
    coverage read (gap_driven_acquisition.is_knowledge_gap -- the learner's own
    signal, unchanged). Otherwise CAPABILITY (a behavioral faculty failure #4
    composes or specs). This is a boundary translation of held signals into a
    token, not a decision about what to DO -- the routing decision is the graph
    dispatch keyed on this token."""
    at = _gap_attrs(agent, gap)
    kind = at.get("kind")
    if kind in (KNOWLEDGE, CAPABILITY):
        return kind
    domain = gda.gap_domain_of(agent, at)
    is_knowledge = bool(domain) and gda.is_knowledge_gap(agent, domain)
    kind = KNOWLEDGE if is_knowledge else CAPABILITY
    _set(agent, gap, "kind", kind)
    return kind


# ===========================================================================
# (b) PRIORITIZE — order the queue by a residual salience, over graph state.
# The salience is the held shortfall-residual shape (seeds/residual_salience.
# json: max(0, target - measured)) evaluated in Rust -- not a Python heuristic.
# measured = how grounded the gap already is (a knowledge gap's coverage-best;
# a capability behavioral failure is maximally ungrounded -> measured 0).
# ===========================================================================
def _shortfall_salience(agent, measured: float) -> float:
    """max(0, 1 - measured), the residual-salience shortfall shape, evaluated by
    the Rust DSL (Max/Minus/Lit) -- the SAME residual the project wires salience
    to. Python builds the Term + dispatches ONE evaluate."""
    _sub, native, _ag = _resolve(agent)
    term = {"type": "Max", "items": [
        {"type": "Lit", "value": 0.0},
        {"type": "Minus", "a": {"type": "Lit", "value": 1.0},
         "b": {"type": "Var", "name": "measured"}},
    ]}
    try:
        return float(native.evaluate(term, {"measured": float(measured)}))
    except Exception:
        return max(0.0, 1.0 - float(measured))


def salience(agent, gap) -> float:
    """The gap's residual salience: how far it is from grounded. A KNOWLEDGE gap's
    grounding is concept_graph's region-cosine (coverage best); a CAPABILITY gap is
    a behavioral failure the agent claimed competence for -- maximally ungrounded
    (measured 0). Written as the gap's `salience` attr. Reuses #3's coverage read
    and the held shortfall Term -- no bespoke scoring."""
    kind = classify_kind(agent, gap)
    if kind == KNOWLEDGE:
        domain = gda.gap_domain_of(agent, _gap_attrs(agent, gap))
        measured = gda.coverage(agent, domain)["best"] if domain else 0.0
    else:
        measured = 0.0
    s = _shortfall_salience(agent, measured)
    _set(agent, gap, "salience", s)
    return s


def prioritize(agent, gaps: list) -> list:
    """Order the queue thickest-residual-first (highest salience). Mechanical sort
    over the graph-read salience -- admissible host I/O over graph state."""
    scored = [(salience(agent, g), i, g) for i, g in enumerate(gaps)]
    # highest salience first; stable by discovery order on ties.
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [g for _s, _i, g in scored]


# ===========================================================================
# (c) ROUTE — the ONE decision, as a GRAPH DISPATCH (route_pick Program over
# GapRouteCue, evaluated in Rust). The twin of ground_concern's composer_pick.
# ===========================================================================
def _ensure_dispatch_seed(agent) -> None:
    """Idempotently load seeds/research_agenda_dispatch.json (the GapRouteCue
    nodes + the route_pick Program) onto the graph, guarded by a Seed node -- the
    SAME idempotency pattern substrate_extension._ensure_pipeline_vocab and
    reflective_faculty._ensure_seed_chain use. Loading vocabulary is admissible
    adapter work, not a decision."""
    from substrate.seed_loader import manifest_for
    sub, native, ag_node = _resolve(agent)
    have = {sub.node(n)["attrs"].get("id") for n in sub.nodes("Seed")}
    if "research_agenda_dispatch" in have:
        return
    native.load_seed_manifest(manifest_for("research_agenda_dispatch"), ag_node)
    sub.add_node("Seed", {"id": "research_agenda_dispatch", "version": "1.0.0"})


def route(agent, kind: str) -> Optional[str]:
    """Evaluate the seeded `route_pick` Program (research_agenda_dispatch) over the
    gap's kind, returning the filler name the matching GapRouteCue carries (or None
    when no GapRouteCue matches). The kind -> filler decision IS this Rust
    Program (Argmin-by-priority over GapRouteCues whose kind Eq the gap's kind),
    not a Python branch -- this function only loads the seed + reads the verdict."""
    sub, _native, _ag = _resolve(agent)
    _ensure_dispatch_seed(agent)
    prog = rf._load_program(sub, "route_pick")
    if prog is None:
        return None
    val = _resolve(agent)[1].evaluate(prog, {"kind": kind})
    return val if isinstance(val, str) and val else None


# ===========================================================================
# (d) FILL + VERIFY — marshal the held filler the route selected, then gate on #2.
# The FILLER REGISTRY is a name-keyed lookup (the twin of rf._COMPOSER_REGISTRY):
# the Program names the filler; this maps the name to the held faculty call.
# ===========================================================================
def _fill_acquisition(agent, gap, *, seeds_dir=None) -> dict:
    """KNOWLEDGE fill: run #3 (gap_driven_acquisition.acquire_for_gap) on the gap's
    domain (reading a fed source_text off the gap if present), then GATE it with #2
    -- a discriminative control that the region is now edge-bearing (coverage rose)
    where a fake 'claims-everything-covered' twin FAILS. Returns {outcome, accepted,
    verify, fill}.

    `seeds_dir` is where #3 persists the acquired microtheory (reboot-proof). It
    defaults to gap_driven_acquisition's real seeds/ dir (honest persistence); a
    caller (a test, a demo) passes an isolated dir to avoid perturbing the repo."""
    at = _gap_attrs(agent, gap)
    domain = gda.gap_domain_of(agent, at)
    before = gda.coverage(agent, domain) if domain else {"bag": 0}
    _kw = {"seeds_dir": seeds_dir} if seeds_dir is not None else {}
    fill = gda.acquire_for_gap(
        agent, domain,
        source_text=at.get("source_text"),
        source_title=at.get("source_title") or at.get("source"),
        **_kw,
    )
    verify = sv.verify_claim(agent, _acquisition_claim(agent, domain, before["bag"]))
    return {"outcome": "acquisition", "domain": domain,
            "accepted": bool(verify.get("accepted")), "verify": verify, "fill": fill}


def _acquisition_claim(agent, domain: str, before_bag: int) -> sv.Claim:
    """The discriminative control for a knowledge acquisition: the acquired DOMAIN
    must now be EDGE-BEARING (its concept-graph bag rose above the pre-acquisition
    baseline) AND an untaught nonsense domain must NOT be (it stays empty). A fake
    twin that claims EVERY domain is covered passes the positive case but FAILS the
    orphan -- so the control has teeth. Grounding: the taught microtheory was read
    from an EXTERNAL source (a fed reference / the wiki slab), so the claim's support
    reaches a SensorAnchor (a reading is an external perception), the same mechanical
    anchor mapping ensure_grounding_edges makes for a perceives-neighbour."""
    _sub, native, _ag = _resolve(agent)

    def _edge_bearing(d: str) -> bool:
        try:
            return gda.coverage(agent, d)["bag"] > before_bag
        except Exception:
            return False

    def mechanism(case) -> bool:
        d, expect_covered = case
        return _edge_bearing(d) == expect_covered

    def fake_twin(case) -> bool:
        # claims EVERY domain covered -> passes the positive, fails the orphan.
        _d, expect_covered = case
        return True == expect_covered

    orphan = "zzq_untaught_orphan_domain_qzz"
    control_cases = [(domain, True), (orphan, False)]
    prior_cases = [(domain, True)]              # no-regression: the domain stays edge-bearing

    def ground_support(s):
        ag = rf._agent_root_node(s) or s.add_node("Agent", {})
        # a READ of an external reference is an external perception -> SensorAnchor
        # (ensure_grounding_edges grounds any Agent -perceives-> node to SensorAnchor).
        ref = s.add_node("Reference", {"read": domain, "of": "acquired_source"})
        native.add_edge_unchecked(ag, "perceives", ref)
        node = s.add_node("Collapse", {"label": f"acquired_{domain}"})
        native.add_edge_unchecked(node, "grounded_in", ref)
        return node

    return sv.Claim(
        text=f"gap-driven acquisition made {domain!r} edge-bearing (coverage rose)",
        mechanism=mechanism,
        control_cases=control_cases,
        fake_twin=fake_twin,
        prior_cases=prior_cases,
        ground_support=ground_support,
    )


def _fill_extension(agent, gap) -> dict:
    """CAPABILITY fill: run #4 (substrate_extension.extend_for_gap) on the gap. #4
    already runs #2 (verify-before-trust) INTERNALLY for a composed faculty -- its
    returned `accepted` IS the #2 verdict. A primitive-request outcome is a specified
    boundary (not filled/accepted -> the gap stays open, honestly). Returns {outcome,
    accepted, verify, fill}."""
    fill = se.extend_for_gap(agent, gap, verify=True)
    outcome = fill.get("outcome")
    accepted = bool(fill.get("accepted")) if fill.get("accepted") is not None else False
    verify = fill.get("verified")
    return {"outcome": outcome, "accepted": accepted, "verify": verify, "fill": fill}


_FILLER_REGISTRY: dict[str, Callable[[Any, Any], dict]] = {
    # name-keyed marshaling -- the twin of rf._COMPOSER_REGISTRY. The route_pick
    # Program names the filler; this maps the name to the held faculty call. A
    # mechanical lookup, not a decision.
    "acquisition": _fill_acquisition,
    "substrate_extension": _fill_extension,
}


# ===========================================================================
# THE CYCLE — perceive -> prioritize -> (route -> fill -> verify -> accept/open)
# per gap -> loop -> clean stop when the queue drains.
# ===========================================================================
def process_gap(agent, gap, *, seeds_dir=None) -> dict:
    """One gap through route -> fill -> verify -> accept/open. The route is the
    graph dispatch; the fill is the held faculty it named; the accept is #2's
    verdict; the status write-back is mechanical."""
    kind = classify_kind(agent, gap)
    filler_name = route(agent, kind)
    at = _gap_attrs(agent, gap)
    record = {"gap": gap if not isinstance(gap, dict) else at.get("faculty", "<dict>"),
              "faculty": at.get("faculty"), "domain": gda.gap_domain_of(agent, at),
              "kind": kind, "filler": filler_name,
              "salience": at.get("salience")}
    filler = _FILLER_REGISTRY.get(filler_name) if filler_name else None
    if filler is None:
        _set(agent, gap, "status", OPEN)
        record.update({"accepted": False, "verdict": "unroutable",
                       "status": OPEN, "note": f"no filler for kind {kind!r}"})
        return record
    _kw = {"seeds_dir": seeds_dir} if (seeds_dir is not None and filler is _fill_acquisition) else {}
    result = filler(agent, gap, **_kw)
    accepted = bool(result.get("accepted"))
    status = CLOSED if accepted else OPEN
    _set(agent, gap, "status", status)
    verify = result.get("verify") or {}
    record.update({
        "accepted": accepted,
        "status": status,
        "outcome": result.get("outcome"),
        "verdict": (verify.get("reason") if isinstance(verify, dict) else None),
        "fill_reason": (result.get("fill") or {}).get("reason")
                        if isinstance(result.get("fill"), dict) else None,
    })
    return record


def run_cycle(agent, battery: Optional[list] = None, *, max_iters: int = 64,
              seeds_dir=None) -> dict:
    """The whole self-improvement CYCLE, end to end:

      PERCEIVE  the gap queue (#1) ->
      loop:  PRIORITIZE the still-perceived gaps by salience; take the top;
             ROUTE it (graph dispatch) -> FILL (held #3/#4) -> VERIFY (#2) ->
             mark CLOSED (accepted) or OPEN (rejected/unfillable) ->
      STOP  when no perceived gap remains (drained) or max_iters (a safety bound).

    Each iteration marks its gap non-perceived, so the queue strictly shrinks --
    the loop terminates at a clean resting point. Returns {perceived, processed,
    closed, open, drained, iterations}. A rejected fill leaves its gap OPEN
    (honest) -- it is removed from the active queue but recorded as unresolved."""
    sub = getattr(agent, "s", agent)
    perceived = perceive(agent, battery)
    processed: list = []
    iterations = 0
    while iterations < max_iters:
        # re-read the still-perceived queue (a fill may have minted new gaps).
        queue = [n for n in sub.nodes("CapabilityGap")
                 if sub.node(n)["attrs"].get("status", PERCEIVED) == PERCEIVED]
        if not queue:
            break                               # DRAINED -> clean stop
        ordered = prioritize(agent, queue)
        gap = ordered[0]
        rec = process_gap(agent, gap, seeds_dir=seeds_dir)
        processed.append(rec)
        iterations += 1
        # safety: if the gap somehow stayed perceived, force it open so the queue
        # cannot loop forever (a clean-stop guarantee, never a silent close).
        if sub.node(gap)["attrs"].get("status", PERCEIVED) == PERCEIVED:
            _set(agent, gap, "status", OPEN)
            rec["status"] = OPEN
    drained = not [n for n in sub.nodes("CapabilityGap")
                   if sub.node(n)["attrs"].get("status", PERCEIVED) == PERCEIVED]
    closed = [r for r in processed if r.get("status") == CLOSED]
    open_ = [r for r in processed if r.get("status") == OPEN]
    return {"perceived": len(perceived), "processed": processed,
            "closed": closed, "open": open_,
            "drained": drained, "iterations": iterations}


__all__ = [
    "perceive", "classify_kind", "salience", "prioritize",
    "route", "process_gap", "run_cycle",
    "KNOWLEDGE", "CAPABILITY", "PERCEIVED", "CLOSED", "OPEN",
    "_FILLER_REGISTRY",
]
