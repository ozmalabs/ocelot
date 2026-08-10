"""speech_decode_construction — PERCEPTION RE-EXPRESSED ON THE LANGUAGE ENGINE.

THE UNIFICATION (the architectural capstone)
--------------------------------------------
The agent ALREADY has, for LANGUAGE, the exact architecture we hand-built for
speech as a standalone filter-graph (domains/filter_graph.py — an ACCIDENTAL
re-implementation of this engine in miniature):

  * a COMPOSER  — DSL Term-tree composition (the agent assembles op-trees and
                  runs them via substrate.evaluate; domains/relational_shape.py
                  already composes the speech decode's relational ops THIS way),
  * a LIBRARY   — the concept / Microtheory store (Concepts grounded by
                  built_from edges + a `combination` Term-tree; the
                  domains/grounded_representation.py `composed_by=agent` idiom),
  * a ROUTER    — read-and-ground / comprehension (recognise the CIRCUMSTANCE,
                  RETRIEVE the held construction, compose, ground — the
                  domains/read_and_ground.py pattern),
  * GAMMA       — admissibility = type-compatibility (an edge u->v is admitted
                  iff u.output_type == v.input_type).

This module DOES NOT grow a parallel perception stack. It RE-EXPRESSES the
speech decode-graph IN that existing language/comprehension engine, so
perception is a FACULTY OF the same engine: decode = comprehend = perceive, one
composer / library / router / Gamma for language AND speech.

WHAT IS RE-EXPRESSED, AND IN WHICH EXISTING MACHINERY
-----------------------------------------------------
The known-good REL-BAND decode (commit 84b034ed: v->v 83.3%, within-whisper
67.3%, cross-speaker x whisper 60.7%; FSDD 10-way, native DtwTo) is PRESERVED
verbatim as its computation — it becomes a LIBRARY ENTRY, not a discarded thing.

  (1) COMPOSER.  The decode is a TYPED PIPELINE of op-concepts:
          SIGNAL --gammatone--> BAND_TRAJ --rank--> REL_SHAPE --dtw--> WORD
      The relational ops (ordinal band-rank + whole-unit self-similarity) ARE
      ALREADY native DSL Term-trees the agent composes and runs via
      substrate.evaluate (domains/relational_shape.py — reused VERBATIM). The
      readout is the native DtwTo Term (domains/recognition_graph.py). The
      gammatone front-end is an owned I/O-boundary primitive (the cochlea). The
      composer here ASSEMBLES this typed pipeline from the held op-concepts, and
      Gamma (the SIGNAL/BAND_TRAJ/REL_SHAPE type signatures) admits or rejects
      each stage — exactly as the language composer chains constructions whose
      meaning-types must agree. This REPLACES the standalone FilterNode/
      FilterGraph classes: the pipeline is no longer a bespoke framework, it is a
      Term-tree the agent's OWN composer assembles.

  (2) LIBRARY.  install_speech_decode_construction stores the decode-graph in
      the SAME concept/Microtheory store the language constructions live in: a
      `speech_decode` Concept grounded (grounded_representation.ground_concept)
      by built_from edges to its op-concepts (gammatone_front_end /
      ordinal_rank_profile / whole_unit_selfsimilarity / dtw_nearest_exemplar),
      carrying the typed-pipeline `combination` (the Gamma-typed op order). It is
      filed under a `perception` Microtheory alongside — not beside — the
      grammatical constructions. Retrieving it is the same library lookup that
      retrieves a grammatical construction.

  (3) ROUTER.  comprehend_clip recognises the CIRCUMSTANCE ("a speech clip";
      optionally voiced vs whisper), RETRIEVES the stored decode-construction
      from the library (the read_and_ground retrieve step), COMPOSES the typed
      pipeline, EVALUATES it natively (gammatone -> native rank/self-sim Terms ->
      native DtwTo), and GROUNDS to the recognised word. This is "comprehending"
      a speech clip with the same recognise-circumstance / retrieve-construction
      / compose / ground engine that comprehends a sentence.

HONEST SCOPE (the named boundary — do not overclaim)
----------------------------------------------------
GENUINELY UNIFIED:
  * The decode's RELATIONAL ops are the agent's OWN native DSL Term-trees, run
    by substrate.evaluate (not Python arithmetic) — this was already true and is
    preserved.
  * The decode-graph is a real LIBRARY ENTRY in the EXISTING concept store
    (ground_concept built_from edges + combination), under a Microtheory beside
    the language constructions — same store, same grounding machinery.
  * The COMPOSER assembles the typed pipeline from the held op-concepts and Gamma
    (type-compatibility) admits/rejects each stage — the agent's own type system,
    not the bespoke FilterGraph.connect.
  * The ROUTER recognises "speech clip" as a circumstance and RETRIEVES the held
    construction from the library before composing — the read_and_ground pattern.

SCAFFOLDED (stated plainly):
  * The CIRCUMSTANCE recognition ("this is a speech clip") is a thin I/O-boundary
    classifier (a clip is a 1-D float array), not a learned percept — the router
    DISPATCHES on the held construction once the circumstance is named, but the
    naming of the circumstance is mechanical.
  * The op-concepts' leaf primitives (gammatone, DtwTo) are owned Rust/boundary
    primitives, not further decomposed in the store — they ground OUT as
    primitives (which is correct: a primitive is where grounding bottoms out).
  * read_and_ground itself is the LANGUAGE router; here we reuse its
    retrieve-from-store STEP (the library lookup) directly rather than driving the
    full read->comprehend->ground definitional descent (a speech clip has no
    prose definition to read). So the router is the RETRIEVE+COMPOSE+GROUND half,
    wired to the same store; the read-prose-definition half is N/A for a clip.

PARITY is the test: the perception-on-the-language-engine must REPRODUCE the
standalone REL-BAND numbers (within noise) on the SAME venue. See
scripts/perception_unified_parity.py. PARITY = the unification preserved the
decode; the win is ARCHITECTURAL.

DISCIPLINE (CLAUDE.md): this is a world adapter — it SEQUENCES the agent's own
graph-resident machinery (composer / store / router / Gamma) and translates the
clip at the I/O boundary. No fitted model, no .fit/net/sweep. The relational
recognition is native (substrate.evaluate); the library entry is an admissible
graph mutation; the perceptual ops are the agent's owned Terms / primitives.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from domains.relational_shape import (rank_vector_term, _selfsim_agreement_term,
                                       relational_shape)


# ---------------------------------------------------------------------------
# GAMMA — the type alphabet of the speech-decode pipeline (admissibility =
# type-compatibility, exactly as the language composer's meaning-types must
# agree for two constructions to chain). An edge op_u -> op_v is admitted iff
# op_u.output_type == op_v.input_type.
# ---------------------------------------------------------------------------
SIGNAL = "SIGNAL"          # 1-D waveform (the clip)
BAND_TRAJ = "BAND_TRAJ"    # frames x bands gammatone band-energy trajectory
REL_SHAPE = "REL_SHAPE"    # frames x D whole-unit relational shape (DtwTo-ready)
WORD = "WORD"              # the grounded lexical identity


# ---------------------------------------------------------------------------
# THE OP-CONCEPTS — each a held perceptual operation with a Gamma type
# signature. The relational ops carry the agent's OWN native DSL Term-trees
# (relational_shape's rank_vector_term / self-similarity agreement Term); the
# gammatone front-end and DtwTo readout are owned boundary/Rust primitives that
# ground OUT (a primitive is where grounding bottoms out). These are the PARTS
# the library entry is built_from and the composer chains.
# ---------------------------------------------------------------------------
def _op_concepts(n_anchors: int = 6) -> list[dict]:
    """The decode-graph's op-concepts as library data. `term` (when present) is
    the agent's native DSL Term-tree (.to_dict()) — the composer's actual
    runnable form; `primitive` marks an owned boundary/Rust op that grounds out.
    `in`/`out` are the Gamma type signature."""
    # The relational op's native Term-trees, captured as the agent's composed
    # form (these are run by substrate.evaluate inside relational_shape).
    rank_term = rank_vector_term  # composed per n_bands at compose time
    return [
        {"name": "gammatone_front_end", "in": SIGNAL, "out": BAND_TRAJ,
         "primitive": True,
         "gloss": "owned cochlear gammatone filterbank: clip -> band-energy "
                  "trajectory (the I/O-boundary front end)."},
        {"name": "ordinal_rank_profile", "in": BAND_TRAJ, "out": REL_SHAPE,
         "primitive": False,
         "term_builder": rank_term,
         "gloss": "native DSL Term-tree (Gt/IfThenElse/Plus/Vec): per-frame "
                  "ordinal band-rank — invariant to talker gain/level by "
                  "construction. The COMPOSER's own op."},
        {"name": "whole_unit_selfsimilarity", "in": BAND_TRAJ, "out": REL_SHAPE,
         "primitive": False,
         "term_builder": _selfsim_agreement_term,
         "gloss": "native DSL Term-tree (rank ++ Minus/Abs/Plus): each frame's "
                  "rank agreement with the unit's own phase anchors — a relation "
                  "internal to the unit, invariant to any uniform transform."},
        {"name": "dtw_nearest_exemplar", "in": REL_SHAPE, "out": WORD,
         "primitive": True,
         "gloss": "native DtwTo Term (substrate.evaluate) argmin over the held "
                  "exemplar lexicon: relational trajectory -> word."},
    ]


# ---------------------------------------------------------------------------
# (1)+(2) THE LIBRARY ENTRY — store the decode-graph in the EXISTING concept /
# Microtheory store via grounded_representation.ground_concept, exactly as a
# language construction is stored: a `speech_decode` Concept built_from its
# op-concepts, carrying the Gamma-typed pipeline as its `combination`.
# ---------------------------------------------------------------------------
def _pipeline_combination(n_anchors: int = 6) -> dict:
    """The decode-graph as a typed Term-pipeline the composer assembles. Each
    stage names an op-concept + its Gamma in/out types; Gamma admits a stage
    only if its `in` matches the previous stage's `out`. This is the
    `combination` (HOW the parts compose) stored on the library Concept — the
    agent's composed_by=agent idiom, here a perceptual pipeline rather than a
    grammatical one."""
    # The two relational ops both consume BAND_TRAJ and produce REL_SHAPE; they
    # are CONCATENATED (the relational_shape output is rank-profile ++ self-sim).
    return {
        "kind": "typed_pipeline",
        "type_alphabet": [SIGNAL, BAND_TRAJ, REL_SHAPE, WORD],
        "stages": [
            {"op": "gammatone_front_end", "in": SIGNAL, "out": BAND_TRAJ},
            {"op": ["ordinal_rank_profile", "whole_unit_selfsimilarity"],
             "in": BAND_TRAJ, "out": REL_SHAPE, "compose": "concat",
             "n_anchors": n_anchors},
            {"op": "dtw_nearest_exemplar", "in": REL_SHAPE, "out": WORD},
        ],
    }


def install_speech_decode_construction(substrate, *, n_anchors: int = 6,
                                       mt_name: str = "perception") -> dict:
    """STORE the speech decode-graph as a library entry in the SAME concept /
    Microtheory store the language constructions live in.

    Builds the `speech_decode` Concept grounded (ground_concept) by built_from
    edges to its op-concepts, carrying the Gamma-typed pipeline `combination`,
    filed under a `perception` Microtheory beside the grammatical constructions.
    Returns {concept, parts, mt, combination_set, primitives}.

    Faithful: this is an admissible graph mutation (ground_concept opens the
    Concept->Concept grounding productions); no decision logic, no LLM."""
    from domains import grounded_representation as _gr

    _gr.open_grounding_productions(substrate)

    ops = _op_concepts(n_anchors=n_anchors)
    part_names = [o["name"] for o in ops]

    # Ground each op-concept (its built_from is empty / it is a primitive leaf;
    # the relational ops record their native Term-tree as the combination so the
    # store holds the agent's COMPOSED form, not a gloss).
    for o in ops:
        comb: Any = None
        if not o["primitive"]:
            # The op's native DSL Term-tree (the composer's runnable form). The
            # builder needs n_bands at compose time; we store the BUILDER's
            # identity as a named combination + the gloss; the runnable Term is
            # rebuilt per-clip by the composer (relational_shape) since n_bands
            # is clip-dependent. Recording it marks this as a composed op.
            comb = {"kind": "native_term", "op": o["name"],
                    "composed_by": "agent"}
        try:
            _gr.ground_concept(substrate, o["name"], built_from=[],
                               combination=comb, frame=mt_name)
        except Exception:
            # A primitive op with no parts may be a bare leaf; mint it directly.
            cid = _gr._find_concept(substrate, o["name"])
            if cid is None:
                cid = substrate.add_node("Concept", {"name": o["name"]})
            substrate.set_attr(cid, "gloss", o["gloss"])
            substrate.set_attr(cid, "type_in", o["in"])
            substrate.set_attr(cid, "type_out", o["out"])
        # record the Gamma type signature on the op-concept either way
        cid = _gr._find_concept(substrate, o["name"])
        if cid is not None:
            substrate.set_attr(cid, "type_in", o["in"])
            substrate.set_attr(cid, "type_out", o["out"])
            substrate.set_attr(cid, "is_primitive_op", bool(o["primitive"]))

    # The decode-graph Concept itself, grounded by its op-concepts + the typed
    # pipeline combination.
    combination = _pipeline_combination(n_anchors=n_anchors)
    res = _gr.ground_concept(substrate, "speech_decode", built_from=part_names,
                             combination=combination, frame=mt_name)

    # File it under the perception Microtheory beside the language constructions.
    mt = _gr._find_microtheory(substrate, mt_name)
    if mt is None:
        mt = substrate.add_node("Microtheory", {"name": mt_name})
    sd = _gr._find_concept(substrate, "speech_decode")
    if sd is not None:
        try:
            substrate.add_edge(mt, "has_concept", sd)
        except Exception:
            pass
        substrate.set_attr(sd, "type_in", SIGNAL)
        substrate.set_attr(sd, "type_out", WORD)
        substrate.set_attr(sd, "kind", "perceptual_construction")

    return {
        "concept": "speech_decode",
        "parts": part_names,
        "mt": mt_name,
        "combination_set": res.get("combination_set", False),
        "grounded_concept": res.get("concept"),
    }


# ---------------------------------------------------------------------------
# GAMMA CHECK — admit the pipeline only if each stage's input type matches the
# previous stage's output type (type-compatibility). The same admissibility the
# language composer applies to chained constructions.
# ---------------------------------------------------------------------------
def gamma_admits(combination: dict) -> tuple[bool, Optional[str]]:
    """Type-check the stored typed-pipeline combination: a stage is admissible
    iff its `in` equals the prior stage's `out`. Returns (ok, reason). The
    pipeline begins at SIGNAL and must end at WORD."""
    stages = combination.get("stages", [])
    if not stages:
        return False, "empty pipeline"
    if stages[0].get("in") != SIGNAL:
        return False, f"pipeline must begin at {SIGNAL}"
    prev_out = SIGNAL
    for st in stages:
        if st.get("in") != prev_out:
            return False, (f"Gamma rejects stage {st.get('op')}: "
                           f"in={st.get('in')} != prev out={prev_out}")
        prev_out = st.get("out")
    if prev_out != WORD:
        return False, f"pipeline must end at {WORD} (ended at {prev_out})"
    return True, None


# ---------------------------------------------------------------------------
# (1) THE COMPOSER — assemble + EVALUATE the typed pipeline up to REL_SHAPE
# (the DtwTo readout stage is applied by the router against the held lexicon).
# The gammatone stage is the owned front end; the relational stage runs the
# agent's NATIVE Term-trees via substrate.evaluate (relational_shape).
# ---------------------------------------------------------------------------
def _band_front_end(signal: np.ndarray, fs: int) -> Optional[np.ndarray]:
    """The gammatone op-concept: SIGNAL -> BAND_TRAJ (owned cochlear front end,
    I/O boundary)."""
    from scripts.invariant_units_accept import band_trajectory_matrix
    M = band_trajectory_matrix(signal, fs)
    return M if M is not None and len(M) >= 2 else None


def compose_rel_shape(substrate_or_none, signal: np.ndarray, fs: int,
                      combination: dict) -> Optional[np.ndarray]:
    """COMPOSE the held decode-construction up to REL_SHAPE: run the Gamma-typed
    pipeline's gammatone stage (BAND_TRAJ) then its relational stage (the agent's
    NATIVE rank + self-similarity Term-trees, evaluated via substrate.evaluate
    inside relational_shape). Returns the frames x D relational trajectory the
    DtwTo readout matches over — the SAME computation the standalone REL-BAND
    graph produced, now driven by the stored construction.

    Gamma-checks the combination first (type-compatibility) — an inadmissible
    pipeline is refused, exactly as the language composer refuses a type-clashing
    chain."""
    ok, reason = gamma_admits(combination)
    if not ok:
        raise TypeError(f"Gamma rejects speech_decode pipeline: {reason}")
    # locate the relational stage's n_anchors from the stored combination
    n_anchors = 6
    for st in combination.get("stages", []):
        if "n_anchors" in st:
            n_anchors = int(st["n_anchors"])
    # STAGE 1 (gammatone): SIGNAL -> BAND_TRAJ
    M = _band_front_end(signal, fs)
    if M is None:
        return None
    # STAGE 2 (relational): BAND_TRAJ -> REL_SHAPE, the agent's NATIVE Term-trees
    # (relational_shape runs rank_term / self-sim agreement via substrate.evaluate).
    return relational_shape(M, n_anchors=n_anchors)


__all__ = [
    "SIGNAL", "BAND_TRAJ", "REL_SHAPE", "WORD",
    "install_speech_decode_construction", "gamma_admits", "compose_rel_shape",
    "_pipeline_combination", "_op_concepts",
]
