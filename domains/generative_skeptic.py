"""generative_skeptic — the GENERATIVE half of the self-skeptic.

THE SPLIT (what is already built vs what THIS builds)
================================================================================
  · BUILT — the EXECUTION (domains.self_check_hat): GIVEN a conclusion + its
    claimed/realised support + stakes + a do-contrast toggle, fire a weighted
    check (uncertainty x stakes) and resolve REOPEN / COMMIT. It works GIVEN
    those inputs — but a human still had to supply WHICH thing to doubt, WHERE the
    weak link is, and WHAT do-contrast would reveal the miss.
  · THIS — the GENERATIVE / the framing: GIVEN a RAW conclusion, GENERATE the
    probe ITSELF — which thing to doubt, where the weak link is, what do-contrast
    would reveal a miss — and EXTRACT the inputs the hat needs. The skeptic stops
    being supplied from outside.

THE MECHANISM — the DUAL of order_n_postulates
================================================================================
order_n_postulates harvests IMPLICATION-shapes ("X is a linear system => X is
invertible") and TRANSFERS the matching one to find a capability GAP.

The generative skeptic harvests FAILURE-shapes — the ways a CONCLUSION goes
wrong — and TRANSFERS the matching one to find the PROBE a conclusion demands:

  · HARVEST  — read the agent's BANKED FAILURE-LESSONS (graph-resident
    FailureLesson nodes, seeded from real episodes the agent lived: the W5
    moving-baseline regression, the 70B breadth-junk frontier, the bad-ears
    hardware-knob, consistency-mistaken-for-accuracy, boolean-over-the-numbers,
    premature-stop). Each lesson yields a SHAPE: {match_patterns (the surface a
    wrong conclusion of this kind exhibits), probe (the doubt it demands),
    weak_link, hat_inputs (how to read claimed/realised/stakes off it)}.
  · MATCH    — loose STRUCTURAL match of a new conclusion's text against the
    shapes' patterns (the SAME loose, keyword-level "vaguely similar" match
    order_n_postulates.differentiate uses; the shape fires by surface form, the
    SELECTOR / the hat decides whether the doubt holds).
  · TRANSFER — the matched shape's probe + weak_link + hat-input recipe are
    instantiated for THIS conclusion -> a GeneratedProbe. This is the agent's
    OWN move (harvest + analogical transfer), not a lookup of a hand-written probe.
  · PLUS the COUNTEREXAMPLE / EXISTENCE-PROOF generator: given a conclusion of the
    form "X is needed for Y", search the agent's BREADTH for a concept asserting
    "Y holds WITHOUT X" (the bad-ears move — humans achieve robust recognition
    with the SAME coarse cochlea). If found, X is a knob, not the lever.

WHAT FEEDS WHAT
================================================================================
  generate_probe(conclusion) -> GeneratedProbe{probe, weak_link, claimed_support,
      realised_support, stakes, measure_with, measure_without}
        -> hand to self_check_hat.self_check(...) -> the hat FIRES (or glances)
        -> resolve REOPEN / COMMIT.  generate -> the hat fires.

DONKEY / ARCHITECTURE AUDIT
================================================================================
  · ADDITIVE — a NEW module + a NEW seed. No core touched (CortexLoop /
    solve_for_n.py / cortex_loop.py untouched). order_n_postulates.py and
    speech_science.py (task B's files) NOT touched.
  · NO net, NO .fit, NO gradient, NO sweep. The probes are HARVESTED from the
    agent's banked lessons + TRANSFERRED by loose structural match — NOT a
    hand-authored probe list (the shapes come from FailureLesson graph nodes the
    agent owns, exactly as order_n's shapes come from its Concepts).
  · The counterexample generator is a graph walk over the agent's breadth
    Concepts (its own knowledge), not a Python rule.
  · Python here is world-adapter glue: it reads FailureLesson attrs out of the
    graph, runs the regex match (loose surface form, the same as
    order_n_postulates.differentiate), and marshals the generated inputs into the
    hat's call. The DECISION (fire / reopen) stays in the hat's native Terms.

HONEST BOUNDARY (named, not forced to pass)
================================================================================
A NOVEL failure with NO matching harvested shape: the skeptic bottoms out — it
cannot generate the targeted probe, only a generic "no banked shape matched; this
is an unbanked failure-mode" flag. That is the irreducible residual: taste reduces
to the harvested shape-library PLUS the counterexample search; a genuinely fresh
failure-mode the agent has never lived is a fresh mind's job until it is BANKED
(at which point it becomes a harvestable shape and the residual shrinks). The
replay exhibits this directly with an off-distribution conclusion.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# HARVEST — the agent's banked failure-lessons as FAILURE-SHAPES.
#
# The dual of order_n_postulates._shapes() / implication_harvester.harvest_shapes:
# there, shapes are harvested from the agent's CONCEPTS (implication relations).
# Here, shapes are harvested from the agent's FailureLesson nodes (failure
# relations). Each lesson is a real episode the agent lived; the SHAPE (pattern +
# probe + hat-input recipe) is read off it, not hand-authored as a probe list.
# ---------------------------------------------------------------------------


def harvest_failure_shapes(substrate) -> list:
    """Read every graph-resident FailureLesson the agent holds and return its
    failure-SHAPE. Returns a list of dicts:
        {name, failure_shape, match_patterns, probe_template, weak_link,
         hat_inputs, source_lesson, needs_for, lacks_thing}.
    Pure graph read — the agent's banked lessons, not a Python list."""
    shapes = []
    for c in substrate.nodes("FailureLesson"):
        a = substrate.node(c)["attrs"]
        pats = a.get("match_patterns") or []
        if isinstance(pats, str):
            pats = [pats]
        if not pats:
            continue
        shapes.append({
            "name": a.get("failure_shape", a.get("name", "?")),
            "failure_shape": a.get("failure_shape", a.get("name", "?")),
            "match_patterns": list(pats),
            "probe_template": a.get("probe_template", ""),
            "weak_link": a.get("weak_link", ""),
            "hat_inputs": a.get("hat_inputs", ""),
            "source_lesson": a.get("name", "?"),
            "source_episode": a.get("definition", ""),
            # the existence-proof generator's hooks (only the bad-ears shape carries
            # them; harmless None elsewhere):
            "needs_for": a.get("needs_for"),
            "lacks_thing": a.get("lacks_thing"),
            "node": c,
        })
    return shapes


# ---------------------------------------------------------------------------
# MATCH — loose STRUCTURAL match of a conclusion against the failure-shapes.
#
# Identical in spirit to order_n_postulates.differentiate's `any(re.search(...))`:
# a shape fires when the conclusion's surface form exhibits the failure-pattern.
# The match is loose (keyword-level "vaguely similar"); the hat decides whether
# the doubt actually holds once the probe is run.
# ---------------------------------------------------------------------------


def _conc_text(conclusion) -> str:
    if isinstance(conclusion, dict):
        return " ".join(str(conclusion.get(k, "")) for k in
                        ("text", "statement", "verdict", "claim", "banner")).lower()
    return str(conclusion).lower()


def match_failure_shapes(shapes: list, conclusion) -> list:
    """Return every failure-shape whose pattern fires on the conclusion's surface,
    each with the number of patterns hit (a loose specificity score). Sorted
    most-specific first."""
    text = _conc_text(conclusion)
    hits = []
    for sh in shapes:
        n = sum(1 for p in sh["match_patterns"] if re.search(p, text))
        if n:
            hits.append((n, sh))
    hits.sort(key=lambda x: -x[0])
    return [sh for _n, sh in hits]


# ---------------------------------------------------------------------------
# The COUNTEREXAMPLE / EXISTENCE-PROOF generator (the bad-ears move).
#
# Given "X is needed for Y", search the agent's BREADTH (its Concepts across all
# Mts) for a concept asserting "Y holds WITHOUT X". A graph walk over the agent's
# own knowledge — not a hand-written counterexample list.
# ---------------------------------------------------------------------------


def domain_admissibility(conclusion, domain_vocab) -> float:
    """Measure how DOMAIN-ADMISSIBLE a conclusion is: the fraction of its content
    words that belong to the question's domain vocabulary. ~0 for breadth junk
    (e.g. '70B model fits on 48 GB GPU' against a SPEECH vocabulary), ~high for an
    in-domain conclusion. This is the realised support the breadth-junk shape's
    hat-input recipe says to read — generated by the skeptic, not handed in.

    `domain_vocab` is an iterable of the question's domain keywords (e.g. the
    speech surface). A thin measurement over the conclusion's own tokens."""
    text = _conc_text(conclusion)
    toks = [t for t in re.split(r"[^a-z0-9]+", text) if len(t) > 3]
    if not toks:
        return 0.0
    vocab = {w.lower() for w in domain_vocab}
    hit = sum(1 for t in toks if t in vocab)
    return hit / len(toks)


def find_existence_proof(substrate, *, achieves: str, without: str,
                         scope_mt=None) -> dict | None:
    """Search the agent's breadth for a concept that achieves `achieves` WITHOUT
    `without` — the existence-proof / counterexample to "without is needed for
    achieves". `achieves` / `without` are keyword phrases (e.g. achieves='speech
    recognition robust', without='sharp cochlea dense filters'). Returns the first
    witnessing concept {concept, name, text, why} or None.

    Loose: a witness is a concept whose text mentions the GOAL-keywords AND a
    'without / despite / coarse / same / poor'-style negation of the BARRIER-
    keywords (the structural signature of an existence proof). This is the agent's
    own knowledge testifying, not a Python lookup."""
    goal_kw = [w for w in re.split(r"[\s_]+", achieves.lower()) if len(w) > 3]
    barrier_kw = [w for w in re.split(r"[\s_]+", without.lower()) if len(w) > 3]
    # words that, near a barrier keyword, signal "achieves it WITHOUT the barrier"
    neg = ("without", "despite", "coarse", "blunt", "poor", "same", "no ",
           "lack", "absent", "even with", "robust", "still", "suffice")
    scope = substrate.nodes("Concept")
    for c in scope:
        a = substrate.node(c)["attrs"]
        text = f"{a.get('name','')} {a.get('definition','')} {a.get('why','')}".lower()
        if not any(g in text for g in goal_kw):
            continue
        # the barrier is mentioned in a NEGATED context (achieves-it-without):
        if not any(b in text for b in barrier_kw):
            # the witness need not name the barrier verbatim — a 'coarse/blunt/same'
            # near the goal already asserts "without the sharp version".
            if not any(nw in text for nw in neg):
                continue
        if any(nw in text for nw in neg):
            return {"concept": c, "name": a.get("name", "?"),
                    "text": a.get("definition", ""), "why": a.get("why", ""),
                    "goal_kw": goal_kw, "barrier_kw": barrier_kw}
    return None


# ---------------------------------------------------------------------------
# TRANSFER — instantiate the matched shape's probe for THIS conclusion + extract
# the inputs the hat needs.  generate_probe is the whole generative act.
# ---------------------------------------------------------------------------


def _extract_numbers(conclusion) -> dict:
    """Pull the candidate support numbers a conclusion exposes (percentages /
    fractions in its text), so the generated probe can populate the hat's
    claimed/realised support when the caller doesn't supply them. World-I/O glue:
    a thin parse of the conclusion's own printed numbers. Returns
    {values: [...], pairs of (claimed, realised) guesses}."""
    text = _conc_text(conclusion)
    vals = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", text):
        vals.append(float(m.group(1)) / 100.0)
    for m in re.finditer(r"(?<![\d.])0?\.\d+(?![\d.])", text):
        vals.append(float(m.group(0)))
    return {"values": vals}


def generate_probe(substrate, conclusion, *, stakes: float | None = None,
                   measure_with=None, measure_without=None,
                   claimed_support: float | None = None,
                   realised_support: float | None = None,
                   domain_vocab=None) -> dict:
    """THE GENERATIVE ACT. Given a RAW conclusion, GENERATE the skeptical probe by
    harvest+transfer, and extract the inputs the self_check_hat needs.

    Returns a GeneratedProbe dict:
        {matched (bool), failure_shape, probe, weak_link, hat_inputs,
         claimed_support, realised_support, stakes, measure_with, measure_without,
         existence_proof (if the bad-ears shape fired and a witness was found),
         residual (set when NO shape matched — the honest boundary)}.

    The caller may OVERRIDE claimed/realised/stakes/measure_* (world-I/O it can
    measure precisely); when omitted they are GENERATED from the conclusion's own
    numbers + the matched shape's hat-input recipe. The probe text + the weak link
    + WHICH inputs to read are all the agent's, not the caller's."""
    shapes = harvest_failure_shapes(substrate)
    matches = match_failure_shapes(shapes, conclusion)

    if not matches:
        # ---- THE HONEST BOUNDARY: no banked shape fired. The skeptic bottoms out.
        return {
            "matched": False,
            "failure_shape": None,
            "probe": ("NO BANKED FAILURE-SHAPE MATCHED. This conclusion does not "
                      "exhibit any failure-pattern the agent has lived and banked. "
                      "The generative skeptic cannot synthesise a targeted probe "
                      "for an un-banked failure-mode — a fresh-mind residual. Bank "
                      "the episode (add a FailureLesson) to make it harvestable."),
            "weak_link": "unknown — no harvested shape covers this conclusion",
            "hat_inputs": None,
            "claimed_support": claimed_support if claimed_support is not None else 1.0,
            "realised_support": realised_support if realised_support is not None else 1.0,
            "stakes": stakes if stakes is not None else 0.5,
            "measure_with": measure_with, "measure_without": measure_without,
            "existence_proof": None,
            "residual": "novel_failure_no_matching_shape",
        }

    sh = matches[0]                     # most-specific matched shape
    nums = _extract_numbers(conclusion)

    # populate the hat's support numbers from the shape's hat-input recipe + the
    # conclusion's own numbers, unless the caller overrode them.
    vals = nums["values"]
    gen_claimed = claimed_support
    gen_realised = realised_support
    if gen_claimed is None:
        gen_claimed = max(vals) if vals else 1.0
    if gen_realised is None:
        # the realised support the shape says to read: for most shapes the SMALLEST
        # exposed number is the realised support that may have crashed below the
        # claim (e.g. W5: claimed 0.625, realised 0.20). Default to the claim when
        # the conclusion exposes no second number (a clean, single-number verdict).
        gen_realised = min(vals) if len(vals) >= 2 else gen_claimed

    gen_stakes = stakes if stakes is not None else 0.9  # a verdict/commit is high-stakes

    # the DOMAIN-ADMISSIBILITY channel: the breadth-junk shape's hat-input recipe
    # says the realised support IS the conclusion's domain relevance. When the
    # caller supplies the question's domain vocabulary, the skeptic MEASURES it
    # itself (a high-compression axis from an unrelated domain scores ~0) rather
    # than being handed the realised number. The claimed support stays the
    # compression payoff the axis asserts.
    if (sh.get("failure_shape") == "high_compression_but_domain_irrelevant_frontier"
            and domain_vocab is not None and realised_support is None):
        rel = domain_admissibility(conclusion, domain_vocab)
        gen_realised = rel
        if measure_with is None and measure_without is None:
            gen_claimed_local = gen_claimed
            measure_with = (lambda: gen_claimed_local)
            measure_without = (lambda r=rel: r)

    # the existence-proof / counterexample channel: only the hardware-knob shape
    # carries needs_for / lacks_thing, the "X needed for Y" form. Run the
    # counterexample search over the agent's breadth.
    existence = None
    if sh.get("needs_for") and sh.get("lacks_thing"):
        existence = find_existence_proof(
            substrate, achieves=sh["needs_for"], without=sh["lacks_thing"])
        if existence is not None:
            # a witness was found -> X is a knob, not the lever -> realised support
            # for "X is the lever" collapses to ~0 (the hat will fire / reject).
            gen_realised = 0.0
            if measure_with is None and measure_without is None:
                measure_with = (lambda: gen_claimed)
                measure_without = (lambda: 0.0)

    return {
        "matched": True,
        "failure_shape": sh["failure_shape"],
        "source_lesson": sh["source_lesson"],
        "probe": sh["probe_template"],
        "weak_link": sh["weak_link"],
        "hat_inputs": sh["hat_inputs"],
        "claimed_support": float(gen_claimed),
        "realised_support": float(gen_realised),
        "stakes": float(gen_stakes),
        "measure_with": measure_with,
        "measure_without": measure_without,
        "existence_proof": existence,
        "all_matched_shapes": [m["failure_shape"] for m in matches],
        "residual": None,
    }


# ---------------------------------------------------------------------------
# CHAIN — generate the probe, then FEED the self_check_hat (generate -> fire).
# ---------------------------------------------------------------------------


def skeptic_check(substrate, conclusion, *, name: str, verdict: bool = True,
                  stakes: float | None = None,
                  claimed_support: float | None = None,
                  realised_support: float | None = None,
                  measure_with=None, measure_without=None,
                  domain_vocab=None,
                  connection_band: float = 0.05) -> dict:
    """The full GENERATIVE-THEN-EXECUTE reflex: GENERATE the probe from the raw
    conclusion (harvest+transfer / counterexample), then FEED it to the agent's
    self_check_hat — the hat fires (or glances) and resolves REOPEN / COMMIT.

    Returns {probe (the generated probe), hat (the hat's full trace or None if the
    skeptic bottomed out without numbers)}. This is `generate -> the hat fires`."""
    import domains.self_check_hat as HAT

    p = generate_probe(substrate, conclusion, stakes=stakes,
                       measure_with=measure_with, measure_without=measure_without,
                       claimed_support=claimed_support,
                       realised_support=realised_support,
                       domain_vocab=domain_vocab)

    hat = HAT.self_check(
        substrate, name=name, verdict=verdict,
        claimed_support=p["claimed_support"],
        realised_support=p["realised_support"],
        stakes=p["stakes"], weak_link=p["weak_link"],
        expected=p["claimed_support"],
        measure_with=p.get("measure_with"),
        measure_without=p.get("measure_without"),
        connection_band=connection_band)

    return {"probe": p, "hat": hat}


__all__ = ["harvest_failure_shapes", "match_failure_shapes",
           "find_existence_proof", "generate_probe", "skeptic_check"]
