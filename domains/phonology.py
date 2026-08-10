"""Phonology Microtheory — acoustic-process concepts as graph data.

The substrate already learns AcousticSigns from observation alone:
trajectory cluster → DTW match → vote. What's missing is the
UNDERSTANDING side — the agent has no graph-resident notion of
voicing, sibilance, sonority, manner of articulation. This module
installs the deep-research-grounded phonological vocabulary:

  Microtheory(phonology)
    contains → Concept(voicing)         — periodic glottal source
    contains → Concept(sibilant)        — high-freq fricative
    contains → Concept(sonorant)        — voiced + low-freq dominant
    contains → Concept(formant_present) — concentrated mid-band
    contains → Concept(noise_burst)     — unvoiced + transient

Each Concept holds a predicate Term-tree (stored on the Concept as
the `predicate_json` attr — JSON-serialised graph data the agent
can read via Attr(c, "predicate_json")). The predicate reads the
sign's summary attrs:

  f0_hz           — already EMA'd onto every sign (F0-voicebox work)
  low_band_mean   — mean trajectory energy in bands < 800 Hz
  mid_band_mean   — 800–2500 Hz
  high_band_mean  — > 3000 Hz

`compute_sign_band_stats` populates those summary attrs by walking
the lex's signs + the graph's (patch_name → centre_hz) mapping.
`classify_signs` evaluates each predicate against each sign and
writes an `exhibits` edge from sign → matching concept.

Once tagged, the agent's reasoning over its lexicon stops being
"which trajectory does this sound like" and becomes "what kind of
sound is this." Recognition can then weight evidence at the
concept level (a word taught as 'zero' should match sibilant
signs; a word taught as 'one' should match sonorant signs).
"""
from __future__ import annotations

from substrate_rs import (
    And, Attr, Gt, Lit, Lt, Lte, Or, Plus, Times, Var,
)
from . import belief_revision as _br


# Phonology's binding of the generic belief-revision machinery.
# All phonology-domain detection/investigation/analysis routes
# through these context settings. The local helpers below remain
# phonology-named for backwards compatibility with the cortex's
# reflex response functions.

def _phonology_position_classifier(substrate, sign):
    """Used by belief_revision in position-aware mode. Defined
    here to avoid an import cycle (this module also defines
    `_position_of_sign` which is the actual implementation)."""
    # Forward to _position_of_sign once it's defined.
    return _position_of_sign(substrate, sign)


_PHONOLOGY_BR_CTX = _br.BeliefRevisionContext(
    feature_concept_origin="phonology",
    variant_concept_origin="phonology_variant",
    denotes_edge="denotes",
    exhibits_edge="exhibits",
    marker_prefix="marker_prob_",
    divergence_kind="phonology_divergence",
    observation_type="AcousticSign",
    position_classifier=_phonology_position_classifier,
)


# Each concept has: (name, description, threshold_default, min_bound, max_bound, step).
# `threshold` is the SINGLE graph-resident knob the agent can tune:
# lower threshold = more permissive predicate (more signs match).
# Semantics differ per predicate kind but the direction is uniform:
#   voicing         — Hz lower bound on f0; lower = more permissive
#   sibilant        — slack multiplier on (low+mid); lower = more permissive
#   sonorant        — slack multiplier on high; lower = more permissive
#   formant_present — absolute threshold on mid_band_mean; lower = more permissive
#   noise_burst     — slack multiplier on low; lower = more permissive
_PHONOLOGY_CONCEPTS = [
    ("voicing",
     "periodic acoustic energy from glottal pulsing; F0 in human "
     "vocal range (50-400 Hz).",
     50.0, 20.0, 200.0, 5.0),
    ("sibilant",
     "voiceless fricative with high-frequency energy concentrated "
     "above 3 kHz; /s/, /ʃ/, /z/, /ʒ/.",
     1.0, 0.1, 2.0, 0.1),
    ("sonorant",
     "voiced sound with low-frequency energy dominant: vowels, "
     "nasals, liquids, glides. Sonority hierarchy peaks here.",
     1.0, 0.1, 2.0, 0.1),
    ("formant_present",
     "concentrated mid-band energy (800-2500 Hz); F1/F2 resonance "
     "characteristic of vowels and approximants.",
     0.010, 0.001, 0.050, 0.002),
    ("noise_burst",
     "unvoiced transient energy without sustained F0; stop "
     "releases, plosives, brief affricate components.",
     1.0, 0.1, 2.0, 0.1),
]


def _voicing_predicate(threshold: float = 50.0):
    """A sign is voiced when F0 falls in the human vocal range
    AND low-band energy is present.

    Autocorrelation-based f0 estimation finds spurious periodicity
    in /s/-like noise — the original `f0 in range` clause alone
    was too permissive. The added `low_band_mean > threshold/4000`
    clause requires actual harmonic/sonorant energy, which /s/
    lacks. Threshold scaling (÷4000) ties the low-band cutoff to
    the same knob the retuning loop already manages: a higher
    threshold means BOTH a higher f0 minimum AND a stricter
    low-band floor, which is the right direction for a
    less-lenient voicing detector."""
    return And(items=(
        Gt(Attr(Var("sign"), "f0_hz"), Lit(float(threshold))),
        Lt(Attr(Var("sign"), "f0_hz"), Lit(400.0)),
        Gt(Attr(Var("sign"), "low_band_mean"),
           Lit(float(threshold) / 4000.0)),
    ))


def _sibilant_predicate(threshold: float = 1.0):
    """High-band mean exceeds `threshold` * (low + mid). Threshold
    acts as a slack multiplier — lower = more permissive."""
    return Gt(
        Attr(Var("sign"), "high_band_mean"),
        Times(items=(
            Lit(float(threshold)),
            Plus(items=(
                Attr(Var("sign"), "low_band_mean"),
                Attr(Var("sign"), "mid_band_mean"),
            )),
        )),
    )


def _sonorant_predicate(threshold: float = 1.0):
    """Voiced AND low-band > threshold * high. Threshold = slack
    multiplier on high-band — lower = more permissive."""
    return And(items=(
        Gt(Attr(Var("sign"), "f0_hz"), Lit(50.0)),
        Gt(Attr(Var("sign"), "low_band_mean"),
           Times(items=(
               Lit(float(threshold)),
               Attr(Var("sign"), "high_band_mean"),
           ))),
    ))


def _formant_present_predicate(threshold: float = 0.010):
    """Mid-band energy above an absolute threshold — characteristic
    of vowels + glides. Threshold tuned against actual unit-
    normalised trajectory means (~0.005-0.025 range)."""
    return Gt(Attr(Var("sign"), "mid_band_mean"),
                Lit(float(threshold)))


def _noise_burst_predicate(threshold: float = 1.0):
    """High-band > threshold * low. Threshold = slack multiplier on
    low — lower = more permissive (more bursts fire)."""
    return Gt(
        Attr(Var("sign"), "high_band_mean"),
        Times(items=(
            Lit(float(threshold)),
            Attr(Var("sign"), "low_band_mean"),
        )),
    )


_PREDICATE_FACTORIES = {
    "voicing": _voicing_predicate,
    "sibilant": _sibilant_predicate,
    "sonorant": _sonorant_predicate,
    "formant_present": _formant_present_predicate,
    "noise_burst": _noise_burst_predicate,
}


_PHONOLOGY_PRODUCTIONS = [
    # Microtheory holds concepts.
    ("Microtheory", "contains", "Concept",
     "phonology:mt_contains_concept"),
    # A sign exhibits a phonological property — the classification
    # edge the predicate evaluator writes.
    ("AcousticSign", "exhibits", "Concept",
     "phonology:sign_exhibits_concept"),
    # A word concept has a phonological signature — Concept(word)
    # --has_phonological_marker[prob=p]→ Concept(property). p is the
    # empirical P(sign exhibits property | sign votes for word),
    # learned by `learn_word_signatures` or set by teaching.
    ("Concept", "has_phonological_marker", "Concept",
     "phonology:word_has_marker"),
]


def _ensure_concept(substrate, name, description):
    """Find Concept{name=name}, else mint."""
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == name:
            return c
    return substrate.add_node("Concept", {
        "name": name,
        "description": description,
        "origin": "phonology",
    })


def _has_edge(substrate, src, edge_type, tgt) -> bool:
    return tgt in substrate.neighbours(src, edge_type)


def install_phonology(substrate) -> dict:
    """Install productions + the phonology Microtheory + its concepts
    + each concept's predicate Term-tree (as a JSON attr). Idempotent.

    Returns name → NodeID for the Mt and every concept.
    """
    for src_t, et, tgt_t, prov in _PHONOLOGY_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass

    mt = None
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "phonology":
            mt = n
            break
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "phonology",
            "description": (
                "Acoustic-phonological concepts: voicing, sibilance, "
                "sonority, formants, manner-of-articulation. Predicate "
                "Term-trees read AcousticSign summary attrs (f0_hz, "
                "low/mid/high_band_mean) and tag signs via `exhibits` "
                "edges."
            ),
            "origin": "phonology",
        })

    out = {"_mt": mt}
    import json as _json
    for entry in _PHONOLOGY_CONCEPTS:
        name, desc, default, lo, hi, step = entry
        cid = _ensure_concept(substrate, name, desc)
        if not _has_edge(substrate, mt, "contains", cid):
            try:
                substrate.add_edge(mt, "contains", cid)
            except Exception:
                pass
        # Persist the threshold + its bounds on the concept itself.
        # The agent can read/write `threshold` at runtime via Attr/
        # set_attr (and the apply_top_hypotheses remedy does so).
        a = substrate.node(cid)["attrs"]
        if "threshold" not in a:
            substrate.set_attr(cid, "threshold", float(default))
        substrate.set_attr(cid, "threshold_min", float(lo))
        substrate.set_attr(cid, "threshold_max", float(hi))
        substrate.set_attr(cid, "threshold_step", float(step))
        if name in _PREDICATE_FACTORIES:
            t = _PREDICATE_FACTORIES[name](
                float(substrate.node(cid)["attrs"]["threshold"]))
            substrate.set_attr(cid, "predicate_json",
                                  _json.dumps(t._json))
        out[name] = cid
    return out


def _current_predicates(substrate) -> dict:
    """Build a fresh {name: Term-tree} dict for every phonology
    concept using its CURRENT graph-resident `threshold` attr.
    Called at the start of each classify_signs pass so any tuning
    that happened since the last run takes effect immediately.

    Two paths:
      1. Concepts with a registered _PREDICATE_FACTORIES factory
         (the 5 hand-coded ones). Threshold attr → Term-tree.
      2. Concepts with `derived_from: <parent_name>` attr (the
         predicate-invention path). The new concept's predicate
         is the PARENT's predicate at this concept's own
         threshold — a derived/specialised detector. Lets the
         agent's `feature_too_coarse` remedy mint
         `<feature>_strong` / `<feature>_weak` Concepts
         dynamically without registering new factories.
    """
    import json as _json
    out: dict = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") != "phonology":
            continue
        name = a.get("name")
        thr = float(a.get("threshold", 0.0))
        if name in _PREDICATE_FACTORIES:
            out[name] = _PREDICATE_FACTORIES[name](thr)
            continue
        parent = a.get("derived_from")
        if parent and parent in _PREDICATE_FACTORIES:
            out[name] = _PREDICATE_FACTORIES[parent](thr)
    return out


def classify_signs(substrate, lexicon_name: str = "stt") -> dict:
    """Walk every AcousticSign, evaluate each phonology predicate
    Term-tree against the current graph-resident thresholds, and
    update `exhibits` edges. Idempotent in BOTH directions: existing
    exhibits-to-phonology-concept edges are removed if the predicate
    no longer fires, so a tuning round (which lowers/raises
    thresholds) is reflected in the next classification pass.
    Returns {concept_name: count}."""
    concept_by_name = {}
    concept_ids: set = set()
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            concept_by_name[a.get("name")] = c
            concept_ids.add(c)
    lex = None
    for n in substrate.nodes("AcousticLexicon"):
        if substrate.node(n)["attrs"].get("name") == lexicon_name:
            lex = n
            break
    if lex is None or not concept_by_name:
        return {n: 0 for n in concept_by_name}
    counts = {n: 0 for n in concept_by_name}
    predicates = _current_predicates(substrate)
    name_by_cid = {cid: n for n, cid in concept_by_name.items()}
    for s in substrate.neighbours(lex, "has_entry"):
        # Snapshot current phonology exhibits so we can remove the
        # ones that no longer fire under the current thresholds.
        existing = {c for c in substrate.neighbours(s, "exhibits")
                       if c in concept_ids}
        should_exhibit: set = set()
        for name, t in predicates.items():
            try:
                result = substrate.evaluate(t, {"sign": s})
            except Exception:
                continue
            if result is True:
                should_exhibit.add(concept_by_name[name])
                counts[name] += 1
        # Add new exhibits.
        for cid in should_exhibit - existing:
            try:
                substrate.add_edge(s, "exhibits", cid)
            except Exception:
                pass
        # Remove stale exhibits (predicate flipped to False under
        # the new thresholds).
        for cid in existing - should_exhibit:
            try:
                substrate.remove_edge(s, "exhibits", cid)
            except Exception:
                pass
    return counts


def learn_word_signatures(substrate, vote_counts: dict,
                            lexicon_name: str = "stt",
                            min_exhibition_prob: float = 0.0) -> dict:
    """Walk the lexicon's voted signs + their phonology `exhibits`
    edges. For each (word, phonology_concept) pair, compute
      p = P(sign exhibits property | sign top-votes for word)
        = (# word-voted signs that exhibit) / (# word-voted signs)
    Write Concept(word) --has_phonological_marker[prob=p]→ Concept(property)
    edges into the graph. The agent's recognition layer reads these
    edges as the word's phonological signature.

    vote_counts is the {(sign_sort_key, word): count} dict the
    learner builds during training. We use it to discover which
    signs top-vote for each word, then count their exhibits-edges.

    Returns {word: {phonology_concept: prob}} for the report side.
    """
    # phonology concepts.
    pconcepts = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
    if not pconcepts:
        return {}
    # Build per-sign top word from vote_counts.
    per_sign: dict = {}
    for (sk, word), cnt in vote_counts.items():
        per_sign.setdefault(sk, {})[word] = (
            per_sign.setdefault(sk, {}).get(word, 0) + cnt
        )
    # Walk lexicon.
    lex = None
    for n in substrate.nodes("AcousticLexicon"):
        if substrate.node(n)["attrs"].get("name") == lexicon_name:
            lex = n
            break
    if lex is None:
        return {}
    # Build a fast (sort_key → sign NodeID) lookup once.
    from .stt_pipeline import _node_sort_key
    sign_by_sk = {_node_sort_key(s): s
                    for s in substrate.neighbours(lex, "has_entry")}

    # Aggregate counts.
    word_totals: dict = {}
    word_exhibits: dict = {}  # word → {p_concept_name: count}
    for sk, votes in per_sign.items():
        sign = sign_by_sk.get(sk)
        if sign is None or not votes:
            continue
        top_word = max(votes.items(), key=lambda kv: kv[1])[0]
        word_totals[top_word] = word_totals.get(top_word, 0) + 1
        exhibits = set(substrate.neighbours(sign, "exhibits"))
        for pname, pid in pconcepts.items():
            if pid in exhibits:
                d = word_exhibits.setdefault(top_word, {})
                d[pname] = d.get(pname, 0) + 1

    # Write each word's signature: edge sets up structure
    # (has_phonological_marker), per-marker probabilities live as
    # named attrs on the word concept (`marker_prob_<phonology>`).
    # Edge-attribute access isn't exposed in the Python API yet, so
    # we keep the probabilities on the word node where Attr() Terms
    # can read them.
    signatures: dict = {}
    for word, total in word_totals.items():
        if total == 0:
            continue
        word_cid = None
        for c in substrate.nodes("Concept"):
            if substrate.node(c)["attrs"].get("name") == word:
                word_cid = c
                break
        if word_cid is None:
            continue
        sig = {}
        for pname, pid in pconcepts.items():
            count = word_exhibits.get(word, {}).get(pname, 0)
            prob = count / total
            sig[pname] = prob
            substrate.set_attr(word_cid,
                                  f"marker_prob_{pname}",
                                  float(prob))
            if prob >= min_exhibition_prob:
                already = pid in list(substrate.neighbours(
                    word_cid, "has_phonological_marker"))
                if not already:
                    try:
                        substrate.add_edge(
                            word_cid, "has_phonological_marker", pid,
                        )
                    except Exception:
                        pass
        signatures[word] = sig
    return signatures


def score_signs_by_phonology(substrate, signs: list) -> dict:
    """Score every word concept against the AGGREGATE phonological
    exhibition pattern of the heard signs. For each phonology
    concept P, compute heard_freq(P) = (# heard signs exhibiting P)
    / (# heard signs). Compare to the word's signature with
    -KL-divergence on a Bernoulli, summed over concepts.

    Treating signs as independent log-Bernoulli observations
    over-counts: ~10 signs per utterance with strong correlation
    between them (one word's sounds) inflate the log-likelihood
    massively, drowning out the NB signal. The aggregate-frequency
    view treats the whole utterance as ONE observation of a
    distribution + measures distribution distance.

    Returns {word: log-score} where higher is better. Words without
    any markers are skipped.
    """
    import math
    pconcepts = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
    if not pconcepts or not signs:
        return {}
    # heard_freq per concept: fraction of heard signs that exhibit.
    n_signs = len(signs)
    heard_freq: dict = {}
    for pname, pid in pconcepts.items():
        exhibiting = 0
        for s in signs:
            if pid in substrate.neighbours(s, "exhibits"):
                exhibiting += 1
        heard_freq[pname] = exhibiting / n_signs

    # Collect each word's signature.
    word_signatures: dict = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            continue
        wname = a.get("name")
        if not wname:
            continue
        sig: dict = {}
        for pname in pconcepts:
            key = f"marker_prob_{pname}"
            if key in a:
                sig[pname] = float(a[key])
        if sig:
            word_signatures[wname] = sig

    # -KL(heard || word) per concept, summed: rewards word
    # distributions that closely match observed frequencies.
    eps = 0.05
    scores: dict = {}
    for word, sig in word_signatures.items():
        score = 0.0
        for pname, h in heard_freq.items():
            if pname not in sig:
                continue
            q = min(1.0 - eps, max(eps, sig[pname]))
            h_s = min(1.0 - eps, max(eps, h))
            # -KL(h || q) for a single Bernoulli concept
            score -= (h_s * math.log(h_s / q)
                       + (1.0 - h_s) * math.log((1.0 - h_s)
                                                  / (1.0 - q)))
        scores[word] = score
    return scores


def learn_sequence_signatures(substrate,
                                 lexicon_name: str = "stt") -> dict:
    """Sequence-level phonological signatures — extends bag-of-
    features with positional structure.

    For each word concept, walk every Utterance whose `heard_as`
    sign denotes that word. Within an Utterance's stream-chain
    (via `follows` edges), identify position:
      - first: no incoming `follows` edge from another Utterance
      - last:  no outgoing `follows` edge to another Utterance
      - mid:   everything else

    Aggregate phonology-exhibit observations per position:
      P_first(feature | word) = (# first-position signs of word
                                  exhibiting feature)
                                / (# first-position signs of word)
      P_last(feature | word)  = same, for last position

    Written as `first_marker_prob_<feature>` and
    `last_marker_prob_<feature>` attrs on each word Concept.

    Captures: zero starts /z/ (sibilant), six starts /s/
    (sibilant), but their middle/end profiles differ — temporal
    structure the bag-of-features signature couldn't represent.

    Returns {word: {position: {feature: prob}}} for reporting.
    """
    pconcepts: dict = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
    if not pconcepts:
        return {}
    lex = None
    for n in substrate.nodes("AcousticLexicon"):
        if substrate.node(n)["attrs"].get("name") == lexicon_name:
            lex = n
            break
    if lex is None:
        return {}
    # Walk Utterances. For each, classify position via follows.
    word_pos_counts: dict = {}   # word -> position -> total
    word_pos_exhibits: dict = {}  # word -> position -> {feat: count}
    for utt in substrate.nodes("Utterance"):
        signs = list(substrate.neighbours(utt, "heard_as"))
        if not signs:
            continue
        sign = signs[0]
        # Skip self-monitoring utterances — they don't bind to a
        # word concept and would corrupt the signature.
        if substrate.node(sign)["attrs"].get("from_self_motor",
                                                     False):
            continue
        denoted = list(substrate.neighbours(sign, "denotes"))
        if not denoted:
            continue
        word_concept = denoted[0]
        wname = substrate.node(word_concept)["attrs"].get("name")
        if not wname:
            continue
        has_prev = bool(list(
            substrate.neighbours(utt, "follows")))
        has_next = bool(list(
            substrate.in_neighbours(utt, "follows")))
        if not has_prev:
            position = "first"
        elif not has_next:
            position = "last"
        else:
            position = "mid"
        word_pos_counts.setdefault(wname, {}).setdefault(
            position, 0)
        word_pos_counts[wname][position] += 1
        exhibits = set(substrate.neighbours(sign, "exhibits"))
        for pname, pid in pconcepts.items():
            if pid in exhibits:
                d = word_pos_exhibits.setdefault(
                    wname, {}).setdefault(position, {})
                d[pname] = d.get(pname, 0) + 1
    # Compute probs + write attrs.
    out: dict = {}
    for wname, pos_counts in word_pos_counts.items():
        word_cid = None
        for c in substrate.nodes("Concept"):
            if substrate.node(c)["attrs"].get("name") == wname:
                word_cid = c
                break
        if word_cid is None:
            continue
        out[wname] = {}
        for position in ("first", "last"):
            total = pos_counts.get(position, 0)
            if total == 0:
                continue
            sig = {}
            for pname in pconcepts:
                count = (word_pos_exhibits.get(wname, {})
                            .get(position, {})
                            .get(pname, 0))
                prob = count / total
                sig[pname] = prob
                substrate.set_attr(word_cid,
                    f"{position}_marker_prob_{pname}",
                    float(prob))
            out[wname][position] = sig
    return out


def _reset_detect_gate(substrate) -> None:
    """Force the detect reflex's gate to re-open so newly-taught
    signatures get processed by the autopoietic loop. The detect
    layer is gated on `last_detect_tick == 0` to avoid re-running
    every tick; teaching events legitimately need a re-detect."""
    for n in substrate.nodes("PhonologyRoot"):
        substrate.set_attr(n, "last_detect_tick", 0)
        return


def teach_word_position_signature(substrate, word: str,
                                       position: str,
                                       signature: dict) -> int:
    """Top-down per-position signature teaching. Writes
    `<position>_marker_prob_<feature>` attrs onto the word
    concept. Used by the LLM/expert phonology teacher to inject
    curated signatures the agent then uses for recognition.

    position ∈ {"first", "mid", "last"}. signature is
    {feature_name: probability}."""
    if position not in ("first", "mid", "last"):
        return 0
    pconcepts = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
    word_cid = None
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == word:
            word_cid = c
            break
    if word_cid is None:
        return 0
    for fname, prob in signature.items():
        if fname not in pconcepts:
            continue
        substrate.set_attr(word_cid,
                              f"{position}_marker_prob_{fname}",
                              float(prob))
    substrate.set_attr(word_cid, "signature_origin", "taught")
    # Force the detect reflex to re-fire so the new taught
    # signature gets compared against observation.
    _reset_detect_gate(substrate)
    return 1


def teach_word_signature(substrate, word: str,
                            signature: dict[str, float]) -> int:
    """Top-down teaching path. The teacher provides a word's
    phonological signature directly:

        teach_word_signature(sub, "zero",
            {"sibilant": 0.9, "voicing": 0.7,
             "sonorant": 0.5, "noise_burst": 0.3})

    The agent grounds it as graph data: the word concept gains
    `marker_prob_<pname>` attrs and `has_phonological_marker` edges
    to the named phonology concepts. Subsequent recognition reads
    these the same way it reads learned signatures.

    Returns 1 if the word concept was found/touched, 0 otherwise.

    Difference from `learn_word_signatures`: that one COMPUTES the
    signature from observed votes; this one ACCEPTS a signature
    from outside. Both write the same graph structure, so they're
    interchangeable from the recognition layer's view — pure
    capability extension via the same data shape.
    """
    pconcepts = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
    word_cid = None
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == word:
            word_cid = c
            break
    if word_cid is None:
        return 0
    for pname, prob in signature.items():
        if pname not in pconcepts:
            continue
        pid = pconcepts[pname]
        substrate.set_attr(word_cid, f"marker_prob_{pname}",
                              float(prob))
        already = pid in list(substrate.neighbours(
            word_cid, "has_phonological_marker"))
        if not already:
            try:
                substrate.add_edge(
                    word_cid, "has_phonological_marker", pid,
                )
            except Exception:
                pass
    # Mark this word's signature origin so insight logic can
    # distinguish taught vs learned signatures later.
    substrate.set_attr(word_cid, "signature_origin", "taught")
    return 1


def _detect_phonology_impasses_impl(substrate,
                                  lexicon_name: str = "stt",
                                  divergence_threshold: float = 0.4
                                  ) -> list:
    """Compare each word's LEARNED signature to each of its
    individual voted signs' phonology exhibits. If a sign is
    labeled as word W but its exhibits-set diverges significantly
    from W's signature, raise an Impasse — a graph-resident
    contradiction node that the agent's reflex layer can later
    investigate.

    Divergence = Σ_p |exhibits(p) - sig(p)| (Bernoulli L1).

    The Impasse carries:
      `kind: phonology_divergence`
      `about_word: <word>`        — edge or attr
      `about_sign: <sign nid>`    — edge to the surprising sign
      `divergence: <value>`       — how bad the mismatch is

    Returns the list of newly-minted Impasse NodeIDs.

    Why this matters: an Impasse is the substrate's "I don't know
    what to do here" marker. The reflex layer can pattern-match
    on it and trigger investigation — recompute the sign's band
    means, ask for more examples, or revise the predicate.
    """
    pconcepts = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
    # Word concepts with signatures.
    word_sigs: dict = {}
    word_cids: dict = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            continue
        wname = a.get("name")
        if not wname:
            continue
        sig: dict = {}
        for pname in pconcepts:
            key = f"marker_prob_{pname}"
            if key in a:
                sig[pname] = float(a[key])
        if sig:
            word_sigs[wname] = sig
            word_cids[wname] = c
    # Productions for the Impasse vocabulary (idempotent).
    for src, et, tgt, prov in [
        ("Impasse", "about_word", "Concept",
         "phonology:impasse_about_word"),
        ("Impasse", "about_sign", "AcousticSign",
         "phonology:impasse_about_sign"),
    ]:
        try:
            substrate.add_production({
                "src": {"type": src, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass

    # Lexicon walk.
    lex = None
    for n in substrate.nodes("AcousticLexicon"):
        if substrate.node(n)["attrs"].get("name") == lexicon_name:
            lex = n
            break
    if lex is None:
        return []
    new_impasses: list = []
    for sign in substrate.neighbours(lex, "has_entry"):
        # What word does this sign denote? (One Concept edge.)
        denoted = list(substrate.neighbours(sign, "denotes"))
        if not denoted:
            continue
        word_concept = denoted[0]
        wname = substrate.node(word_concept)["attrs"].get("name")
        if not wname or wname not in word_sigs:
            continue
        # Sign's exhibit vector.
        exhibits = set(substrate.neighbours(sign, "exhibits"))
        sig = word_sigs[wname]
        divergence = 0.0
        for pname, prob in sig.items():
            pid = pconcepts[pname]
            obs = 1.0 if pid in exhibits else 0.0
            divergence += abs(obs - prob)
        if divergence < divergence_threshold:
            continue
        # Mint an Impasse (idempotent — skip if one already points
        # at this sign).
        existing = False
        for ip in substrate.nodes("Impasse"):
            if (ip in substrate.nodes("Impasse")
                    and sign in substrate.neighbours(ip,
                                                       "about_sign")):
                existing = True
                break
        if existing:
            continue
        imp = substrate.add_node("Impasse", {
            "kind": "phonology_divergence",
            "divergence": float(divergence),
            "origin": "phonology",
        })
        try:
            substrate.add_edge(imp, "about_word", word_concept)
            substrate.add_edge(imp, "about_sign", sign)
        except Exception:
            pass
        new_impasses.append(imp)
    return new_impasses


def detect_phonology_impasses(substrate,
                                  lexicon_name: str = "stt",
                                  divergence_threshold: float = 0.4
                                  ) -> list:
    """Detect divergence between signs' phonology exhibits and
    their word's signature. Now delegates to the generic belief-
    revision machinery using the phonology context binding."""
    return _br.detect_impasses(
        substrate, _PHONOLOGY_BR_CTX,
        divergence_threshold=divergence_threshold,
    )


def investigate_phonology_impasses(
        substrate,
        learning_rate: float = 0.2,
        respect_taught: bool = True,
) -> dict:
    """Close the autopoietic loop: walk every unresolved
    phonology_divergence Impasse and use its observation to update
    the belief that produced it.

    For each open Impasse pointing at (word W, sign S):

      * If W's signature_origin is "taught" (`teach_word_signature`
        wrote it) AND respect_taught is True, DON'T overwrite —
        instead mark the impasse `persistent_taught_mismatch: true`.
        The agent records that a teaching disagrees with its
        observations and surfaces it for later resolution.

      * Otherwise, for every phonology concept P that W has a
        marker_prob_P for, Bayesian-style nudge toward the observed:
            new = current * (1 - α) + observed * α
        where observed ∈ {0, 1} and α = learning_rate.

      * Mark the Impasse `investigated: true` (refractory) and
        record what was changed.

    This is the substrate's "let me reconcile observation with my
    current belief by adjusting the belief." Mechanical formula
    application — the architecturally pure form would be 5
    graph_rewrite Rules (one per phonology concept) sharing the
    Impasse match pattern. Same effect; this function is the
    fast-path while the rule-engine port is in flight.

    Returns {investigated, nudged, persistent, changed_words}.
    Delegates to belief_revision.investigate_impasses with the
    phonology context binding.
    """
    out = _br.investigate_impasses(
        substrate, _PHONOLOGY_BR_CTX,
        learning_rate=learning_rate,
        respect_taught=respect_taught,
    )
    return {
        "investigated": out["investigated"],
        "nudged": out["nudged"],
        "persistent": out["persistent"],
        "changed_words": out["changed_holders"],
    }


def analyse_persistent_mismatches(
        substrate,
        min_impasses_per_pair: int = 3,
) -> list:
    """Delegates to belief_revision.analyse_persistent_mismatches
    with the phonology context binding. Phonology-domain
    MismatchHypothesis nodes are returned with kind names like
    `predicate_too_strict`, `teaching_too_strong`, etc."""
    return _br.analyse_persistent_mismatches(
        substrate, _PHONOLOGY_BR_CTX,
        min_impasses_per_pair=min_impasses_per_pair,
    )


def _analyse_persistent_mismatches_old(
        substrate,
        min_impasses_per_pair: int = 3,
) -> list:
    """OLD impl kept as reference; new code uses
    `analyse_persistent_mismatches` above which delegates to
    belief_revision. Will be removed in a follow-up cleanup.

    The agent's autopoietic loop (`investigate_phonology_impasses`)
    preserves taught signatures but surfaces the disagreement as
    persistent impasses. This function takes the next step: it
    *reasons about the source of the belief*. For each cluster of
    persistent impasses on the same (word, phonology_concept)
    pair, the agent mints candidate `MismatchHypothesis` nodes —
    each a graph-resident proposal for WHY the teaching disagrees
    with observation:

      "predicate_too_strict"  — the detector misses the property
                                 in real audio (most signs
                                 systematically under-exhibit).
      "teaching_too_strong"   — same evidence; the textbook
                                 estimate of P is higher than
                                 reality for this speaker set.
      "signs_misclassified"   — a small set of outlier signs
                                 dominates the divergence; their
                                 word label may be wrong.
      "sub_class_within_word" — bimodal distribution; the word
                                 has variant pronunciations.

    Each MismatchHypothesis carries:
      kind:          the hypothesis name (above)
      score:         normalised support [0..1]
      about_word:    edge → Concept(word)
      about_concept: edge → Concept(phonology_property)
      summary:       short human-readable evidence summary

    This is the agent reasoning about its OWN beliefs' provenance.
    A downstream Reflex (the next layer) would pattern-match on
    the highest-scoring hypothesis and act — retune the predicate
    threshold, weaken the teaching, or re-classify the outlier
    signs.

    Returns the list of newly-minted MismatchHypothesis NodeIDs.
    """
    # Productions (idempotent).
    for src, et, tgt, prov in [
        ("MismatchHypothesis", "about_word", "Concept",
         "phonology:hypothesis_about_word"),
        ("MismatchHypothesis", "about_concept", "Concept",
         "phonology:hypothesis_about_concept"),
        ("MismatchHypothesis", "evidence_from", "Impasse",
         "phonology:hypothesis_evidence_from"),
    ]:
        try:
            substrate.add_production({
                "src": {"type": src, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass

    pconcepts: dict = {}
    pconcept_by_id: dict = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
            pconcept_by_id[c] = a.get("name")
    if not pconcepts:
        return []

    # Walk persistent impasses + bucket by (word, concept).
    # For each impasse: read the sign's exhibits set, the word's
    # marker_prob_<P> for each concept; record per-concept gap.
    clusters: dict = {}  # (word_cid, p_cid) -> list of (impasse_id, observed_int, taught, sign_id)
    for imp in substrate.nodes("Impasse"):
        a = substrate.node(imp)["attrs"]
        if a.get("kind") != "phonology_divergence":
            continue
        if not a.get("persistent_taught_mismatch", False):
            continue
        words = list(substrate.neighbours(imp, "about_word"))
        signs = list(substrate.neighbours(imp, "about_sign"))
        if not words or not signs:
            continue
        word_cid = words[0]
        sign = signs[0]
        wa = substrate.node(word_cid)["attrs"]
        exhibits = set(substrate.neighbours(sign, "exhibits"))
        for pname, pid in pconcepts.items():
            key = f"marker_prob_{pname}"
            if key not in wa:
                continue
            taught = float(wa[key])
            obs = 1.0 if pid in exhibits else 0.0
            # Only collect per-concept disagreements where this
            # concept contributed meaningfully to the divergence.
            if abs(obs - taught) < 0.3:
                continue
            clusters.setdefault((word_cid, pid), []).append(
                (imp, obs, taught, sign))

    # Snapshot which (word, concept) pairs already have a hypothesis.
    # The analyse Reflex re-fires until quiescent; without this
    # dedup it would mint duplicates forever.
    existing_hyp_pairs: set = set()
    for h in substrate.nodes("MismatchHypothesis"):
        if substrate.node(h)["attrs"].get("origin") != "phonology":
            continue
        ws = list(substrate.neighbours(h, "about_word"))
        cs = list(substrate.neighbours(h, "about_concept"))
        if ws and cs:
            existing_hyp_pairs.add((ws[0], cs[0]))

    # For each cluster, score candidate hypotheses.
    new_hyps: list = []
    for (word_cid, p_cid), entries in clusters.items():
        if len(entries) < min_impasses_per_pair:
            continue
        if (word_cid, p_cid) in existing_hyp_pairs:
            # Already analysed in a previous pass — mark the
            # constituent impasses analysed and move on so the
            # Reflex stimulus drops to 0.
            for imp_id, _, _, _ in entries:
                substrate.set_attr(imp_id, "analysed", True)
            continue
        wname = substrate.node(word_cid)["attrs"].get("name", "?")
        pname = pconcept_by_id[p_cid]
        n = len(entries)
        observations = [obs for _, obs, _, _ in entries]
        taught = entries[0][2]
        mean_obs = sum(observations) / n
        n_under = sum(1 for o in observations if o < taught)
        n_over = sum(1 for o in observations if o > taught)
        direction = "under" if n_under > n_over else "over"
        # Uniform under/over-exhibition score: fraction of signs
        # agreeing on the direction.
        uniformity = max(n_under, n_over) / n
        # Sub-class score: how close to half-split (bimodal).
        if observations.count(0.0) and observations.count(1.0):
            ones = observations.count(1.0)
            zeros = observations.count(0.0)
            balance = min(ones, zeros) / max(ones, zeros) \
                          if max(ones, zeros) > 0 else 0
        else:
            balance = 0.0
        # Outlier score: fraction of signs contributing >1 stdev
        # vs the rest. With binary {0,1} observations this is
        # simpler: outlier-ness = how concentrated the divergence
        # is on a small subset.
        gap = abs(mean_obs - taught)
        outlier_score = max(0.0, 1.0 - n / 20.0) * gap

        hypotheses: list = []
        # predicate_too_strict / teaching_too_strong: same evidence,
        # different proposed remedy. Mint both — the next layer
        # picks one to act on.
        if uniformity >= 0.7 and direction == "under":
            hypotheses.append(("predicate_too_strict",
                                  uniformity,
                                  f"{n} signs under-exhibit "
                                  f"{pname} (obs={mean_obs:.2f} "
                                  f"vs taught={taught:.2f}); "
                                  f"detector may miss real audio"))
            hypotheses.append(("teaching_too_strong",
                                  uniformity,
                                  f"{n} signs under-exhibit "
                                  f"{pname} (obs={mean_obs:.2f} "
                                  f"vs taught={taught:.2f}); "
                                  f"textbook P may be too high"))
        elif uniformity >= 0.7 and direction == "over":
            hypotheses.append(("teaching_too_weak",
                                  uniformity,
                                  f"{n} signs over-exhibit "
                                  f"{pname} (obs={mean_obs:.2f} "
                                  f"vs taught={taught:.2f})"))
        if balance >= 0.4:
            hypotheses.append(("sub_class_within_word",
                                  balance,
                                  f"{pname} bimodal across signs "
                                  f"of {wname}: variant prons?"))
        if outlier_score >= 0.4 and n <= 8:
            hypotheses.append(("signs_misclassified",
                                  outlier_score,
                                  f"only {n} outlier signs cause "
                                  f"the {pname} divergence on "
                                  f"{wname}"))

        # Mint MismatchHypothesis nodes + mark every impasse in the
        # cluster as `analysed: True`. The `evidence_from` edges
        # still capture a sample trail (top-5) for graph
        # introspection; the analysed flag is what the Reflex
        # stimulus reads, ensuring the loop converges.
        for kind, score, summary in hypotheses:
            hyp = substrate.add_node("MismatchHypothesis", {
                "kind": kind,
                "score": float(score),
                "summary": summary,
                "n_evidence": int(n),
                "mean_observed": float(mean_obs),
                "taught": float(taught),
                "origin": "phonology",
            })
            try:
                substrate.add_edge(hyp, "about_word", word_cid)
                substrate.add_edge(hyp, "about_concept", p_cid)
                for imp_id, _, _, _ in entries[:5]:
                    substrate.add_edge(hyp, "evidence_from", imp_id)
            except Exception:
                pass
            new_hyps.append(hyp)
        for imp_id, _, _, _ in entries:
            substrate.set_attr(imp_id, "analysed", True)
    return new_hyps


def apply_top_hypotheses(
        substrate,
        min_score: float = 0.8,
        teaching_nudge_rate: float = 0.4,
        lexicon_name: str = "stt",
) -> dict:
    """The outermost loop: act on high-confidence MismatchHypotheses.

    The agent now has hypotheses about its own beliefs' mismatch
    with observation; each carries a `score` reflecting how
    cleanly the disagreement pattern fits that hypothesis kind.
    This walks them and APPLIES the remedy implied by each kind:

      "teaching_too_weak"   → nudge marker_prob_<P> on Concept(W)
                              UPWARD toward observed mean.
      "teaching_too_strong" → nudge DOWNWARD toward observed mean.
                              In both cases, the agent is
                              REVISING the textbook based on
                              accumulated evidence.
      "sub_class_within_word"
                            → mint Concept(W_variant) with the
                              MINORITY observation pattern; tag
                              the matching signs as denoting the
                              variant instead of W. The agent
                              splits a word into pronunciation
                              variants.
      "signs_misclassified" → write a `label_uncertain: True`
                              attr on each outlier sign (the
                              agent flags the relabeling for
                              later resolution).
      "predicate_too_strict"→ NOT auto-applied. The predicate
                              Term-trees are stored as JSON but
                              evaluated from Python factories;
                              graph-tuning predicates requires
                              promoting their Lit thresholds to
                              TunableParameter nodes (next layer).
                              The agent records `action_taken =
                              "deferred_external"` and continues.

    Idempotent: hypotheses with `acted: True` are skipped.

    Returns {action_taken: count} tally plus a list of changed
    word concepts.
    """
    pconcepts: dict = {}
    pconcept_by_id: dict = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
            pconcept_by_id[c] = a.get("name")

    # Productions for the variant-split + uncertain-label paths.
    for src, et, tgt, prov in [
        ("Concept", "is_variant_of", "Concept",
         "phonology:variant_of"),
    ]:
        try:
            substrate.add_production({
                "src": {"type": src, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass

    tally: dict = {}
    changed_words: set = set()
    minted_variants: list = []

    # Sort hypotheses by score descending so highest-confidence
    # remedies apply first. This matters for cases where two
    # hypotheses on the same (word, concept) could fight (e.g.
    # teaching_too_strong AND predicate_too_strict on the same
    # cluster — both are candidates; we trust the higher score).
    hyps = sorted(
        substrate.nodes("MismatchHypothesis"),
        key=lambda h: -float(
            substrate.node(h)["attrs"].get("score", 0.0)),
    )

    # Track which (word, concept) pairs we've already acted on,
    # so the lower-scoring sibling doesn't duplicate work.
    acted_pairs: set = set()

    for h in hyps:
        ha = substrate.node(h)["attrs"]
        if ha.get("acted", False):
            continue
        score = float(ha.get("score", 0.0))
        if score < min_score:
            continue
        kind = ha.get("kind", "?")
        ws = list(substrate.neighbours(h, "about_word"))
        cs = list(substrate.neighbours(h, "about_concept"))
        if not ws or not cs:
            continue
        word_cid = ws[0]
        p_cid = cs[0]
        wname = substrate.node(word_cid)["attrs"].get("name", "?")
        pname = pconcept_by_id.get(p_cid, "?")
        # Include position in the dedup pair so per-position
        # hypotheses on the same (word, feature) don't shadow
        # each other.
        position_attr = ha.get("position")
        pair = (wname, pname, position_attr)
        mean_obs = float(ha.get("mean_observed", 0.0))
        taught = float(ha.get("taught", 0.0))

        action = None
        if kind in ("teaching_too_weak", "teaching_too_strong"):
            if pair in acted_pairs:
                # A higher-scoring sibling already handled this
                # pair; skip the duplicate.
                substrate.set_attr(h, "acted", True)
                substrate.set_attr(h, "action_taken", "skipped_duplicate")
                continue
            current = float(substrate.node(word_cid)["attrs"]
                              .get(f"marker_prob_{pname}", taught))
            new_val = current * (1.0 - teaching_nudge_rate) \
                          + mean_obs * teaching_nudge_rate
            substrate.set_attr(word_cid,
                                  f"marker_prob_{pname}",
                                  float(new_val))
            # Mark signature as observation-revised so subsequent
            # investigate passes treat it like a learned signature.
            substrate.set_attr(word_cid, "signature_origin",
                                  "taught_revised")
            action = f"nudged_{kind}_{taught:.2f}_to_{new_val:.2f}"
            changed_words.add(wname)
            acted_pairs.add(pair)
        elif kind == "sub_class_within_word":
            # Mint Concept(word_variant_<pname>) and reassign the
            # signs whose exhibits pattern on `pname` doesn't match
            # the parent's marker_prob_pname majority. Sub-classing
            # by which side of the bimodal distribution they sit on.
            variant_name = f"{wname}_var_{pname}"
            variant_cid = None
            for c in substrate.nodes("Concept"):
                if substrate.node(c)["attrs"].get("name") == variant_name:
                    variant_cid = c
                    break
            if variant_cid is None:
                variant_cid = substrate.add_node("Concept", {
                    "name": variant_name,
                    "description": (f"Pronunciation variant of "
                                       f"{wname}: signs that "
                                       f"differ on {pname}"),
                    "origin": "phonology_variant",
                })
                try:
                    substrate.add_edge(variant_cid, "is_variant_of",
                                          word_cid)
                except Exception:
                    pass
            # Reassign: find signs denoting `wname` whose exhibits
            # on pname is the MINORITY side and point them at the
            # variant. Minority = the side closer to mean_obs vs
            # taught: if mean_obs > 0.5 then majority exhibits.
            majority_exhibits = (mean_obs >= 0.5)
            lex = None
            for n in substrate.nodes("AcousticLexicon"):
                if substrate.node(n)["attrs"].get("name") == lexicon_name:
                    lex = n
                    break
            if lex is None:
                # Can't reassign without a lexicon; still mint variant
                action = (f"minted_variant_{variant_name}"
                            f"_lexicon_missing")
            else:
                reassigned = 0
                for sign in substrate.neighbours(lex, "has_entry"):
                    if word_cid not in list(
                            substrate.neighbours(sign, "denotes")):
                        continue
                    exhibits = set(substrate.neighbours(
                        sign, "exhibits"))
                    sign_exhibits_p = p_cid in exhibits
                    if sign_exhibits_p == majority_exhibits:
                        continue
                    # Minority sign — relabel toward variant. We
                    # ADD a denotes edge to variant; we DON'T
                    # remove the existing one (the variant is_a
                    # variant_of the parent, so both labels are
                    # consistent).
                    if variant_cid not in list(
                            substrate.neighbours(sign, "denotes")):
                        try:
                            substrate.add_edge(sign, "denotes",
                                                  variant_cid)
                            reassigned += 1
                        except Exception:
                            pass
                action = f"minted_{variant_name}_reassigned_{reassigned}"
                minted_variants.append(variant_name)
                changed_words.add(wname)
        elif kind == "signs_misclassified":
            # Flag each impasse's about_sign as `label_uncertain`.
            # The next layer (recognition reweighting, e.g.) can
            # downweight these signs' votes.
            evidence_impasses = list(substrate.neighbours(
                h, "evidence_from"))
            flagged = 0
            for imp_id in evidence_impasses:
                signs = list(substrate.neighbours(
                    imp_id, "about_sign"))
                for s in signs:
                    substrate.set_attr(s, "label_uncertain", True)
                    flagged += 1
            action = f"flagged_{flagged}_signs_uncertain"
        elif kind == "predicate_too_strict":
            # Lower the phonology Concept's `threshold` attr by one
            # step (bounded by `threshold_min`). Lower threshold =
            # more permissive predicate = more signs satisfy it.
            pa = substrate.node(p_cid)["attrs"]
            current = float(pa.get("threshold", 0.0))
            step = float(pa.get("threshold_step", 0.0))
            lo = float(pa.get("threshold_min", current))
            new_thr = max(lo, current - step)
            if abs(new_thr - current) < 1e-12:
                action = (f"predicate_threshold_at_min_"
                            f"{current:.4f}")
            else:
                substrate.set_attr(p_cid, "threshold",
                                      float(new_thr))
                action = (f"predicate_threshold_{pname}_"
                            f"{current:.4f}_to_{new_thr:.4f}")
        elif kind == "feature_too_coarse":
            # PREDICATE INVENTION. Mint a new phonology Concept
            # `<feature>_strong` with a stricter (×1.5) threshold,
            # derived_from the parent feature. classify_signs's
            # _current_predicates picks it up via the derived_from
            # fallback and applies it on the next pass. The
            # signature layer can then learn how the new
            # sub-feature distributes across words.
            new_name = f"{pname}_strong"
            existing_new = None
            for c in substrate.nodes("Concept"):
                ca = substrate.node(c)["attrs"]
                if (ca.get("name") == new_name
                        and ca.get("origin") == "phonology"):
                    existing_new = c
                    break
            if existing_new is not None:
                action = (f"feature_split_already_minted_"
                            f"{new_name}")
            else:
                pa = substrate.node(p_cid)["attrs"]
                parent_thr = float(pa.get("threshold", 1.0))
                # Stricter threshold for the strong variant.
                strong_thr = parent_thr * 1.5
                new_cid = substrate.add_node("Concept", {
                    "name": new_name,
                    "description": (
                        f"Stronger variant of {pname} — "
                        f"predicate fires only with stricter "
                        f"thresholds. Derived by the agent's "
                        f"feature-invention remedy when the "
                        f"parent feature exhibited bimodal "
                        f"patterns across word observations."),
                    "origin": "phonology",
                    "threshold": float(strong_thr),
                    "threshold_min": float(
                        pa.get("threshold_min", 0.5)),
                    "threshold_max": float(
                        pa.get("threshold_max", 5.0)),
                    "threshold_step": float(
                        pa.get("threshold_step", 0.1)),
                    "derived_from": pname,
                })
                # Mt containment.
                for mt in substrate.nodes("Microtheory"):
                    if (substrate.node(mt)["attrs"].get("name")
                            == "phonology"):
                        try:
                            substrate.add_edge(mt, "contains",
                                                  new_cid)
                        except Exception:
                            pass
                        break
                # Parent → child via has_variant edge (production
                # registered lazily to allow concept-on-concept
                # links).
                try:
                    substrate.add_production({
                        "src": {"type": "Concept",
                                  "var": "src"},
                        "edge_type": "has_variant",
                        "tgt": {"type": "Concept",
                                  "var": "tgt"},
                        "provenance": (
                            "phonology:concept_has_variant"),
                    })
                except Exception:
                    pass
                try:
                    substrate.add_edge(p_cid, "has_variant",
                                          new_cid)
                except Exception:
                    pass
                action = (f"invented_feature_{new_name}_thr_"
                            f"{strong_thr:.3f}")
        elif kind == "predicate_too_lenient":
            # Mirror of predicate_too_strict — RAISE the threshold
            # to make the predicate more selective. Triggered by
            # over-exhibition: the detector fires on inputs the
            # taught signature says shouldn't exhibit. The agent
            # tightens its own perceptual machinery autonomously.
            pa = substrate.node(p_cid)["attrs"]
            current = float(pa.get("threshold", 0.0))
            step = float(pa.get("threshold_step", 0.0))
            hi = float(pa.get("threshold_max", current))
            new_thr = min(hi, current + step)
            if abs(new_thr - current) < 1e-12:
                action = (f"predicate_threshold_at_max_"
                            f"{current:.4f}")
            else:
                substrate.set_attr(p_cid, "threshold",
                                      float(new_thr))
                action = (f"predicate_lenient_{pname}_"
                            f"{current:.4f}_to_{new_thr:.4f}")
        else:
            action = f"unknown_kind_{kind}"

        substrate.set_attr(h, "acted", True)
        substrate.set_attr(h, "action_taken", str(action))
        tally[kind] = tally.get(kind, 0) + 1

    return {
        "applied": tally,
        "changed_words": changed_words,
        "minted_variants": minted_variants,
    }


# ============================================================
# Autonomous Reflex loop — D layer
# ============================================================
# Seven graph-resident Reflex nodes, each with a stimulus Term-tree
# that fires when the corresponding work is pending. `fire_phonology_
# reflexes` walks them in priority order and loops until quiescent.
#
# State lives on a single `phonology_root` node as count attrs the
# Term-tree stimuli read via Attr(Var("root"), "n_<thing>").
# `surface_phonology_state` recomputes the counts after each Reflex
# fires. The cycle is a fixpoint over those counts.


_REFLEX_SPECS = [
    # (name, stimulus_count_attr, response_key, priority)
    # priority orders firing within a tick; lower fires first.
    ("phonology_perceive",   "n_signs_unclassified",      "perceive",   10),
    ("phonology_abstract",   "n_signatures_pending",      "abstract",   20),
    ("phonology_detect",     "n_impasses_to_raise",       "detect",     30),
    ("phonology_investigate", "n_impasses_unresolved",     "investigate", 40),
    ("phonology_analyse",    "n_persistent_unanalysed",   "analyse",    50),
    ("phonology_act",        "n_hypotheses_unacted",      "act",        60),
    ("phonology_verify",     "n_thresholds_dirty",        "verify",     70),
    # propagate_groundings — watches for Concepts with fresh
    # denotes-edges from AcousticSigns (compared to a per-Concept
    # last_propagated_n_denotes counter) and sets pending_intent
    # so IntentCortex's stimulus picks up. Replaces the
    # world-adapter shim that previously wrote pending_intent
    # directly; the signal is now cortex-driven.
    ("phonology_propagate",  "n_fresh_groundings",        "propagate",  80),
]


def _phonology_root(substrate):
    """Find or mint the phonology_root state node — home for the
    count attrs the Reflex stimuli read."""
    for n in substrate.nodes("PhonologyRoot"):
        return n
    return substrate.add_node("PhonologyRoot", {
        "origin": "phonology",
        "last_fire_tick": 0,
    })


def install_phonology_reflexes(substrate) -> dict:
    """Install seven graph-resident Reflex nodes. Each Reflex's
    `stimulus_kind` + `count_attr` says WHEN it fires; its
    `response_key` says WHAT to call. Idempotent — re-installs
    update existing Reflexes in place.

    The Reflexes' stimulus Term-trees read counts off
    `phonology_root` (`PhonologyRoot{}` node). The dispatcher
    `fire_phonology_reflexes` walks them, evaluates each stimulus,
    and runs the matching response function.

    Returns {name: NodeID} for the installed Reflexes + root.
    """
    # Production for PhonologyRoot.
    try:
        substrate.add_production({
            "src": {"type": "PhonologyRoot", "var": "src"},
            "edge_type": "has_reflex",
            "tgt": {"type": "Reflex", "var": "tgt"},
            "provenance": "phonology:root_has_reflex",
        })
    except Exception:
        pass

    root = _phonology_root(substrate)
    out: dict = {"_root": root}
    import json as _json
    for name, count_attr, response_key, priority in _REFLEX_SPECS:
        # Stimulus: `Gt(Attr(Var("root"), count_attr), Lit(0))`.
        # The evaluator gets root in env, so a single count > 0
        # fires the Reflex.
        stimulus = Gt(Attr(Var("root"), count_attr), Lit(0))
        # Find existing reflex by name.
        existing = None
        for r in substrate.nodes("Reflex"):
            ra = substrate.node(r)["attrs"]
            if (ra.get("name") == name
                    and ra.get("origin") == "phonology"):
                existing = r
                break
        attrs = {
            "name": name,
            "origin": "phonology",
            "count_attr": count_attr,
            "response": response_key,
            "priority": int(priority),
            "stimulus_json": _json.dumps(stimulus._json),
            "fire_count": 0,
            "last_fired_tick": -1,
        }
        if existing is None:
            rid = substrate.add_node("Reflex", attrs)
            try:
                substrate.add_edge(root, "has_reflex", rid)
            except Exception:
                pass
        else:
            rid = existing
            for k, v in attrs.items():
                substrate.set_attr(rid, k, v)
        out[name] = rid
    return out


def surface_phonology_state(substrate, root=None,
                                lexicon_name: str = "stt",
                                vote_counts: dict | None = None) -> dict:
    """Recompute the count attrs on phonology_root that the Reflex
    stimuli read. Called before each Reflex evaluation pass so the
    stimuli see the current world state. Returns the count dict."""
    if root is None:
        root = _phonology_root(substrate)
    # Phonology concepts.
    pconcept_ids: set = set()
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("origin") == "phonology":
            pconcept_ids.add(c)
    # Lexicon.
    lex = None
    for n in substrate.nodes("AcousticLexicon"):
        if substrate.node(n)["attrs"].get("name") == lexicon_name:
            lex = n
            break
    signs = (list(substrate.neighbours(lex, "has_entry"))
                if lex is not None else [])
    # n_signs_unclassified: signs with band-means but no phonology
    # exhibit edge. Empty exhibits on a sign that has band-means
    # means classify hasn't run on it yet.
    n_unclassified = 0
    for s in signs:
        a = substrate.node(s)["attrs"]
        if "low_band_mean" not in a:
            continue
        existing = set(substrate.neighbours(s, "exhibits"))
        if not (existing & pconcept_ids):
            n_unclassified += 1
    # n_signatures_pending: vote_counts has entries but at least one
    # voted-for word lacks marker_prob_voicing.
    n_sig_pending = 0
    if vote_counts:
        voted_words: set = set()
        for (_sk, w), _ in vote_counts.items():
            voted_words.add(w)
        for c in substrate.nodes("Concept"):
            a = substrate.node(c)["attrs"]
            if a.get("name") in voted_words \
                    and "marker_prob_voicing" not in a:
                n_sig_pending += 1
    # n_impasses_to_raise: rough heuristic — non-zero only on first
    # pass. Detect always re-runs but only mints impasses for fresh
    # divergences (kept distinct from existing via the existing
    # check inside detect_phonology_impasses).
    n_to_raise = 1 if signs else 0
    # Once we've raised at least one impasse this cycle, this should
    # drop. We track last_detect_tick on the root.
    if substrate.node(root)["attrs"].get("last_detect_tick", 0) > 0:
        n_to_raise = 0
    # n_impasses_unresolved: phonology_divergence impasses without
    # investigated=True.
    n_unresolved = 0
    n_persistent_unanalysed = 0
    for imp in substrate.nodes("Impasse"):
        ia = substrate.node(imp)["attrs"]
        if ia.get("kind") != "phonology_divergence":
            continue
        if not ia.get("investigated", False):
            n_unresolved += 1
        if (ia.get("persistent_taught_mismatch", False)
                and not ia.get("analysed", False)):
            n_persistent_unanalysed += 1
    # n_hypotheses_unacted: MismatchHypothesis with acted!=True
    # AND score >= 0.8. Accept both legacy (`origin=phonology`)
    # and belief_revision-minted (`domain=phonology_divergence`)
    # hypothesis nodes.
    n_unacted = 0
    for h in substrate.nodes("MismatchHypothesis"):
        a = substrate.node(h)["attrs"]
        is_phon = (a.get("origin") == "phonology"
                       or a.get("domain") == "phonology_divergence")
        if not is_phon:
            continue
        if a.get("acted", False):
            continue
        if float(a.get("score", 0.0)) >= 0.8:
            n_unacted += 1
    # n_thresholds_dirty: phonology concept whose `threshold` differs
    # from `last_threshold_applied`. Set after a successful classify.
    n_dirty = 0
    for c in pconcept_ids:
        a = substrate.node(c)["attrs"]
        cur = a.get("threshold")
        last = a.get("last_threshold_classified")
        if cur is None:
            continue
        if last is None or abs(float(cur) - float(last)) > 1e-9:
            n_dirty += 1

    # n_fresh_groundings: word concepts (non-phonology) whose
    # incoming `denotes` edges from AcousticSigns exceed their
    # last_propagated_n_denotes attr. The propagate reflex bumps
    # the counter when it sets pending_intent.
    n_fresh = 0
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            continue
        if a.get("origin") == "phonology_variant":
            continue
        current = 0
        for sign in substrate.in_neighbours(c, "denotes"):
            # Only count edges from AcousticSign nodes (other types
            # may use denotes for unrelated reasons).
            if substrate.node(sign)["type"] == "AcousticSign":
                current += 1
        last = int(a.get("last_propagated_n_denotes", 0))
        if current > last:
            n_fresh += 1

    counts = {
        "n_signs_unclassified": int(n_unclassified),
        "n_signatures_pending": int(n_sig_pending),
        "n_impasses_to_raise": int(n_to_raise),
        "n_impasses_unresolved": int(n_unresolved),
        "n_persistent_unanalysed": int(n_persistent_unanalysed),
        "n_hypotheses_unacted": int(n_unacted),
        "n_thresholds_dirty": int(n_dirty),
        "n_fresh_groundings": int(n_fresh),
    }
    for k, v in counts.items():
        substrate.set_attr(root, k, int(v))
    return counts


def fire_phonology_reflexes(
        substrate,
        vote_counts: dict | None = None,
        lexicon_name: str = "stt",
        max_iterations: int = 25,
) -> list:
    """The autonomous loop. Walk every installed phonology Reflex,
    evaluate its graph-resident stimulus Term-tree, and run its
    response when the stimulus is truthy. Loop until quiescent
    (no Reflex fires in a full pass) or `max_iterations` reached.

    Returns the ordered list of (iteration, reflex_name, count)
    tuples — the agent's audit trail of which layer fired when.
    The stimuli are graph-resident; only the response dispatch
    sits in Python (one step shy of fully-graph-resident, which
    would route via the Rust runtime's dispatcher).
    """
    root = _phonology_root(substrate)
    # Build the Reflex list once + sort by priority.
    refs = []
    for r in substrate.nodes("Reflex"):
        ra = substrate.node(r)["attrs"]
        if ra.get("origin") != "phonology":
            continue
        refs.append((int(ra.get("priority", 0)), r, ra))
    refs.sort()

    responses = {
        "perceive": lambda: classify_signs(substrate,
                                                lexicon_name=lexicon_name),
        "abstract": lambda: (
            learn_word_signatures(substrate, vote_counts or {})
            if vote_counts else {}),
        "detect": lambda: (
            detect_phonology_impasses(substrate,
                                          divergence_threshold=1.0),
            substrate.set_attr(root, "last_detect_tick", 1),
        ),
        "investigate": lambda: investigate_phonology_impasses(
            substrate, learning_rate=0.3),
        "analyse": lambda: analyse_persistent_mismatches(
            substrate, min_impasses_per_pair=3),
        "act": lambda: apply_top_hypotheses(substrate,
                                                  min_score=0.8),
        "verify": lambda: (
            classify_signs(substrate, lexicon_name=lexicon_name),
            _record_thresholds_applied(substrate),
        ),
        "propagate": lambda: _propagate_groundings(substrate),
    }

    audit: list = []
    for it in range(1, max_iterations + 1):
        surface_phonology_state(substrate, root, lexicon_name,
                                    vote_counts)
        fired_any = False
        for _, rid, ra in refs:
            # The stimulus Term-tree is graph-resident (stored as
            # JSON on the Reflex node + introspectable by any
            # observer). For dispatching we use the shortcut: every
            # phonology stimulus has the shape
            # `Gt(Attr(Var("root"), count_attr), Lit(0))`, so we
            # read the count attr off root directly. Equivalent to
            # evaluating the Term, far faster, same semantics.
            key = ra.get("count_attr")
            count = int(substrate.node(root)["attrs"].get(key, 0))
            ok = count > 0
            if not ok:
                continue
            # Fire.
            try:
                responses[ra["response"]]()
                substrate.set_attr(rid, "fire_count",
                                      int(ra.get("fire_count", 0)) + 1)
                substrate.set_attr(rid, "last_fired_tick", it)
                audit.append((it, ra.get("name"),
                                int(substrate.node(root)["attrs"]
                                      .get(ra.get("count_attr"), 0))))
                fired_any = True
            except Exception as ex:
                audit.append((it, ra.get("name") or "?",
                                f"error: {ex}"))
        if not fired_any:
            break
    return audit


def _propagate_groundings(substrate) -> int:
    """For each non-phonology Concept whose incoming denotes-edges
    from AcousticSigns exceed `last_propagated_n_denotes`, set
    `pending_intent: True` and bump the counter. The intent layer
    (IntentCortex) reads pending_intent and mints Intent nodes.

    This replaces the world-adapter shim where `teach_one` set
    pending_intent directly. Now the signal is cortex-driven:
    SpeechCortex observes that signs have grounded to a concept
    and propagates the perception event to downstream cortices
    via shared graph state.
    """
    n = 0
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            continue
        if a.get("origin") == "phonology_variant":
            continue
        current = 0
        for sign in substrate.in_neighbours(c, "denotes"):
            if substrate.node(sign)["type"] == "AcousticSign":
                current += 1
        last = int(a.get("last_propagated_n_denotes", 0))
        if current > last:
            substrate.set_attr(c, "pending_intent", True)
            substrate.set_attr(c, "last_propagated_n_denotes",
                                  int(current))
            n += 1
    return n


def _record_thresholds_applied(substrate) -> None:
    """After classify_signs runs, snapshot each phonology concept's
    current `threshold` as `last_threshold_classified` so the
    `phonology_verify` Reflex's dirty count drops to 0."""
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology" and "threshold" in a:
            substrate.set_attr(c, "last_threshold_classified",
                                  float(a["threshold"]))


def _position_of_sign(substrate, sign) -> str | None:
    """Classify a sign's position in its Utterance follows-chain:
    'first' (no incoming follows), 'last' (no outgoing follows),
    or 'mid'. None if the sign has no Utterance pointing at it."""
    # Find the Utterance via heard_as in-edge.
    utt = None
    for u in substrate.in_neighbours(sign, "heard_as"):
        utt = u
        break
    if utt is None:
        return None
    has_prev = bool(list(substrate.neighbours(utt, "follows")))
    has_next = bool(list(substrate.in_neighbours(utt, "follows")))
    if not has_prev:
        return "first"
    if not has_next:
        return "last"
    return "mid"


def score_signs_by_position_phonology(substrate,
                                            signs: list) -> dict:
    """Position-aware Bernoulli scoring against per-word
    first/last marker_prob signatures (Q's extension of H).

    For each test sign:
      1. Classify position (first / mid / last)
      2. For each candidate word W, compute log-likelihood of the
         sign's exhibits under W's position signature
         (`<position>_marker_prob_<feature>` attrs)
      3. Sum across signs to get total word score

    Returns {word: log-likelihood}. Words without per-position
    signatures are skipped. Designed to be blended with NB
    log-scores via the existing phonology_weight knob.

    The agent's recognition layer now distinguishes onset
    phonology from coda phonology — e.g. seven's first=unvoiced
    vs zero's first=voiced becomes a discriminative signal."""
    import math

    pconcepts: dict = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            pconcepts[a.get("name")] = c
    if not pconcepts or not signs:
        return {}

    # Pre-compute per-sign (position, exhibits set).
    sign_data: list = []
    for s in signs:
        pos = _position_of_sign(substrate, s)
        if pos is None:
            continue
        exhibits = set(substrate.neighbours(s, "exhibits"))
        sign_data.append((pos, exhibits))

    # Collect each word's per-position signatures.
    word_position_sigs: dict = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == "phonology":
            continue
        wname = a.get("name")
        if not wname:
            continue
        per_pos: dict = {}
        for pos in ("first", "last", "mid"):
            sig: dict = {}
            for pname in pconcepts:
                key = f"{pos}_marker_prob_{pname}"
                if key in a:
                    sig[pname] = float(a[key])
            if sig:
                per_pos[pos] = sig
        if per_pos:
            word_position_sigs[wname] = per_pos

    eps = 0.05
    scores: dict = {}
    for word, per_pos in word_position_sigs.items():
        score = 0.0
        for pos, exhibits in sign_data:
            # Fall back to first/last if mid-signature absent
            # (which is normal — most digits are short enough
            # that "first" and "last" cover everything).
            sig = per_pos.get(pos)
            if sig is None and pos == "mid":
                sig = (per_pos.get("first")
                          or per_pos.get("last"))
            if sig is None:
                continue
            for pname, prob in sig.items():
                pid = pconcepts[pname]
                p = min(1.0 - eps, max(eps, prob))
                if pid in exhibits:
                    score += math.log(p)
                else:
                    score += math.log(1.0 - p)
        scores[word] = score
    return scores


def signs_by_concept(substrate, concept_name: str,
                       lexicon_name: str = "stt") -> list:
    """All AcousticSigns tagged with the named phonology concept.
    Trivial graph walk — useful for the agent's introspection
    queries ('which signs are sibilant?')."""
    target = None
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if (a.get("origin") == "phonology"
                and a.get("name") == concept_name):
            target = c
            break
    if target is None:
        return []
    return list(substrate.in_neighbours(target, "exhibits"))


__all__ = [
    "install_phonology",
    "classify_signs",
    "signs_by_concept",
    "learn_word_signatures",
    "learn_sequence_signatures",
    "teach_word_signature",
    "teach_word_position_signature",
    "score_signs_by_phonology",
    "score_signs_by_position_phonology",
    "detect_phonology_impasses",
    "investigate_phonology_impasses",
    "analyse_persistent_mismatches",
    "apply_top_hypotheses",
    "install_phonology_reflexes",
    "surface_phonology_state",
    "fire_phonology_reflexes",
    "_PHONOLOGY_CONCEPTS",
    "_PREDICATE_FACTORIES",
]
