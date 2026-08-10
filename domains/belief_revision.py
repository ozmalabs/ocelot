"""Belief revision — domain-agnostic observation/expectation reconciliation.

The phonology Mt built a six-layer machinery for reconciling
observation with expectation:

    1. Classify observations against feature predicates
    2. Build per-labeled-thing signatures (marker_prob_<feature>)
    3. Detect divergence as Impasse nodes
    4. Investigate — Bayesian-nudge learned signatures, preserve
       taught signatures, surface taught/observed conflicts
    5. Reason about belief provenance — mint MismatchHypothesis
       nodes when teaching disagrees with observation
    6. Act on high-confidence hypotheses (nudge taught signature,
       split into variants, flag outliers, retune predicate
       thresholds)

That whole stack generalises beyond phonology. Any cortex that
holds (signature_holder, observations, feature_concepts) with an
exhibits-relation gets the same machinery for free. Examples:
- vision: (Concept(object), Image, geometric_feature_concepts)
- motor:  (Concept(action), MotorPattern, primitive_concepts)
- speech: (Concept(word), AcousticSign, phonology_concepts) — the
          original case, now a thin wrapper over this module.

The `BeliefRevisionContext` carries the per-domain bindings:
- which concepts are feature concepts (the predicates)
- which concepts are signature holders (the labels)
- which edge type observations use to denote signature holders
- which edge type observations use to exhibit features
- attr name prefix for per-feature signature probabilities
- string used for the Impasse `kind` attr

Functions take the context as their first arg. The phonology
module supplies a context constant and wraps these in domain
names. Same external behaviour; reusable internal machinery.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BeliefRevisionContext:
    """Per-domain bindings for the belief-revision machinery."""

    feature_concept_origin: str
    """Concept.origin attr value that marks a feature predicate
    (e.g. "phonology"). Concepts with this origin define what
    observations can exhibit."""

    variant_concept_origin: str = ""
    """Concept.origin for variants (sub_class_within_word
    remedy). Excluded from signature-holder scans."""

    denotes_edge: str = "denotes"
    """Edge type observation→signature_holder."""

    exhibits_edge: str = "exhibits"
    """Edge type observation→feature_concept."""

    marker_prefix: str = "marker_prob_"
    """Attr name prefix on signature_holder Concept nodes."""

    divergence_kind: str = "phonology_divergence"
    """Value of Impasse.kind for this domain."""

    holder_filter: callable = None
    """Optional: predicate (substrate, node) → bool that further
    restricts what counts as a signature_holder. If None, any
    Concept whose origin != feature_concept_origin and !=
    variant_concept_origin is eligible."""

    observation_type: str = "Concept"
    """Node type of observations (e.g. "AcousticSign" for the
    phonology context). Used to register the Impasse →
    about_observation production with the correct target type
    so edges actually insert."""

    position_classifier: callable = None
    """Optional: (substrate, observation_node) → str | None. When
    set, enables POSITION-AWARE detection. Returns a position
    label ("first", "last", "mid", etc.) for each observation;
    belief_revision then reads
    `<position>_marker_prob_<feature>` attrs from the holder
    INSTEAD of (or in addition to) the bag-of-features
    `marker_prob_<feature>` attrs. Different positions get their
    own impasses, hypotheses, and remedies — the autopoietic
    loop can detect that 'first-position voicing disagrees but
    last-position voicing agrees' and act on the specific
    mismatch."""


def _feature_concepts(substrate, ctx):
    """Return {name: NodeID} for every feature concept in this
    domain."""
    out = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == ctx.feature_concept_origin:
            out[a.get("name")] = c
    return out


def _signature_holders(substrate, ctx):
    """Iter over (concept_nid, name) tuples for every concept that
    can hold a signature in this domain."""
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        if a.get("origin") == ctx.feature_concept_origin:
            continue
        if (ctx.variant_concept_origin
                and a.get("origin") == ctx.variant_concept_origin):
            continue
        if ctx.holder_filter is not None:
            if not ctx.holder_filter(substrate, c):
                continue
        wname = a.get("name")
        if not wname:
            continue
        yield c, wname


def teach_signature(substrate, ctx, holder_name: str,
                       signature: dict) -> int:
    """Install or overwrite a signature_holder's marker
    probabilities from outside. Edges to feature concepts added if
    missing. Marks signature_origin='taught'."""
    feats = _feature_concepts(substrate, ctx)
    cid = None
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == holder_name:
            cid = c
            break
    if cid is None:
        return 0
    for fname, prob in signature.items():
        if fname not in feats:
            continue
        substrate.set_attr(cid, f"{ctx.marker_prefix}{fname}",
                              float(prob))
        # Add structural edge if missing — same convention as
        # phonology's has_phonological_marker.
        edge_type = "has_marker"
        if not _has_edge(substrate, cid, edge_type, feats[fname]):
            try:
                substrate.add_edge(cid, edge_type, feats[fname])
            except Exception:
                pass
    substrate.set_attr(cid, "signature_origin", "taught")
    return 1


def learn_signatures(substrate, ctx, observation_labels: dict
                        ) -> dict:
    """Learn signatures from observation→label associations.
    `observation_labels` is a {(observation_sort_key, label_name):
    count} dict (the caller's choice of sort key; the values are
    used to weight the maximum-likelihood signature). Returns
    {label_name: {feature_name: prob}}."""
    feats = _feature_concepts(substrate, ctx)
    if not feats:
        return {}
    # observation_sk → top label
    per_obs: dict = {}
    for (sk, label), cnt in observation_labels.items():
        per_obs.setdefault(sk, {})[label] = (
            per_obs.setdefault(sk, {}).get(label, 0) + cnt
        )
    # Need a way to find observations by sort key. Caller's
    # responsibility — accept a lookup dict instead.
    raise NotImplementedError(
        "learn_signatures has a callee-resolved lookup quirk; "
        "phonology.learn_word_signatures uses its own walk.")


def _has_edge(substrate, src, edge_type, tgt) -> bool:
    return tgt in substrate.neighbours(src, edge_type)


def detect_impasses(substrate, ctx,
                       divergence_threshold: float = 1.0) -> list:
    """For each observation that carries both:
      - a `denotes_edge` to a signature_holder, AND
      - some `exhibits_edge`s to feature concepts
    compute the L1 divergence between the holder's signature and
    the observation's exhibits-set. If divergence ≥ threshold,
    mint an Impasse{kind: ctx.divergence_kind} pointing at both.
    """
    feats = _feature_concepts(substrate, ctx)
    # Productions (idempotent).
    for src, et, tgt, prov in [
        ("Impasse", "about_holder", "Concept",
         f"belief_revision:about_holder:{ctx.divergence_kind}"),
        ("Impasse", "about_observation", ctx.observation_type,
         f"belief_revision:about_observation:"
         f"{ctx.divergence_kind}"),
        # Back-compat with phonology's legacy edge names.
        ("Impasse", "about_word", "Concept",
         f"belief_revision:about_word:{ctx.divergence_kind}"),
        ("Impasse", "about_sign", ctx.observation_type,
         f"belief_revision:about_sign:{ctx.divergence_kind}"),
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

    # Snapshot existing impasses to avoid re-minting on the same
    # (holder, observation) pair.
    existing_pairs: set = set()
    for imp in substrate.nodes("Impasse"):
        a = substrate.node(imp)["attrs"]
        if a.get("kind") != ctx.divergence_kind:
            continue
        hs = list(substrate.neighbours(imp, "about_holder"))
        os_ = list(substrate.neighbours(imp, "about_observation"))
        if hs and os_:
            existing_pairs.add((hs[0], os_[0]))

    new_imps: list = []
    position_aware = ctx.position_classifier is not None

    for holder, hname in _signature_holders(substrate, ctx):
        ha = substrate.node(holder)["attrs"]

        # Bag-of-features signature (always read; positions can
        # supplement but don't replace).
        bag_sig: dict = {}
        for fname in feats:
            key = f"{ctx.marker_prefix}{fname}"
            if key in ha:
                bag_sig[fname] = float(ha[key])

        # Per-position signatures (when context supports them).
        position_sigs: dict = {}
        if position_aware:
            for pos_name in ("first", "mid", "last"):
                p_sig: dict = {}
                for fname in feats:
                    key = f"{pos_name}_{ctx.marker_prefix}{fname}"
                    if key in ha:
                        p_sig[fname] = float(ha[key])
                if p_sig:
                    position_sigs[pos_name] = p_sig

        if not bag_sig and not position_sigs:
            continue

        for obs in substrate.in_neighbours(holder, ctx.denotes_edge):
            if (holder, obs) in existing_pairs:
                continue
            exhibits = set(substrate.neighbours(
                obs, ctx.exhibits_edge))

            # Choose signature: per-position if available + obs
            # has a classifiable position; else fall back to bag.
            chosen_sig = bag_sig
            obs_position = None
            if position_aware:
                obs_position = ctx.position_classifier(
                    substrate, obs)
                if obs_position and obs_position in position_sigs:
                    chosen_sig = position_sigs[obs_position]
            if not chosen_sig:
                continue

            divergence = 0.0
            for fname, prob in chosen_sig.items():
                pid = feats[fname]
                obs_val = 1.0 if pid in exhibits else 0.0
                divergence += abs(obs_val - prob)
            if divergence < divergence_threshold:
                continue
            imp_attrs = {
                "kind": ctx.divergence_kind,
                "divergence": float(divergence),
                "origin": "belief_revision",
            }
            if obs_position is not None:
                imp_attrs["position"] = obs_position
            imp = substrate.add_node("Impasse", imp_attrs)
            try:
                substrate.add_edge(imp, "about_holder", holder)
                substrate.add_edge(imp, "about_observation", obs)
                substrate.add_edge(imp, "about_word", holder)
                substrate.add_edge(imp, "about_sign", obs)
            except Exception:
                pass
            new_imps.append(imp)
    return new_imps


def investigate_impasses(substrate, ctx,
                              learning_rate: float = 0.3,
                              respect_taught: bool = True) -> dict:
    """For each unresolved Impasse of this domain kind:
      - If signature_origin == "taught" AND respect_taught, mark
        persistent_taught_mismatch + leave the signature.
      - Else Bayesian-nudge each marker_prob_<feature> toward the
        observed value at learning_rate.
      - Mark investigated=True regardless.
    """
    feats = _feature_concepts(substrate, ctx)
    if not feats:
        return {"investigated": 0, "nudged": 0,
                  "persistent": 0, "changed_holders": set()}
    inv = nud = per = 0
    changed: set = set()
    for imp in list(substrate.nodes("Impasse")):
        a = substrate.node(imp)["attrs"]
        if a.get("kind") != ctx.divergence_kind:
            continue
        if a.get("investigated", False):
            continue
        holders = list(substrate.neighbours(imp, "about_holder"))
        if not holders:
            # Fall back to legacy about_word for phonology.
            holders = list(substrate.neighbours(imp, "about_word"))
        obs_ = list(substrate.neighbours(imp, "about_observation"))
        if not obs_:
            obs_ = list(substrate.neighbours(imp, "about_sign"))
        if not holders or not obs_:
            continue
        holder, obs = holders[0], obs_[0]
        ha = substrate.node(holder)["attrs"]
        hname = ha.get("name", "?")
        origin = ha.get("signature_origin", "learned")
        if respect_taught and origin == "taught":
            substrate.set_attr(imp, "investigated", True)
            substrate.set_attr(imp, "persistent_taught_mismatch",
                                  True)
            per += 1
            continue
        exhibits = set(substrate.neighbours(obs,
                                                  ctx.exhibits_edge))
        any_change = False
        for fname, pid in feats.items():
            key = f"{ctx.marker_prefix}{fname}"
            if key not in ha:
                continue
            obs_val = 1.0 if pid in exhibits else 0.0
            current = float(ha[key])
            new_val = (current * (1.0 - learning_rate)
                          + obs_val * learning_rate)
            if abs(new_val - current) > 1e-9:
                substrate.set_attr(holder, key, float(new_val))
                any_change = True
        substrate.set_attr(imp, "investigated", True)
        inv += 1
        if any_change:
            nud += 1
            changed.add(hname)
    return {"investigated": inv, "nudged": nud,
              "persistent": per, "changed_holders": changed}


def _invention_balance_threshold(substrate) -> float:
    """Read the feature-invention balance threshold from the
    DevelopmentRoot node, if present. This is the wire that lets
    the agent's meta-cognitive layer (DevelopmentCortex) control
    how readily it invents new features: when it diagnoses
    over-convergence, it lowers this value, which makes the
    `feature_too_coarse` hypothesis fire on less-extreme bimodal
    distributions. Defaults to 0.7 (the original hardcoded value)
    when no DevelopmentRoot exists."""
    for n in substrate.nodes("DevelopmentRoot"):
        v = substrate.node(n)["attrs"].get(
            "invention_balance_threshold")
        if v is not None:
            return float(v)
    return 0.7


def analyse_persistent_mismatches(substrate, ctx,
                                       min_impasses_per_pair: int = 3
                                       ) -> list:
    """Cluster persistent_taught_mismatch impasses by (holder,
    feature) and mint MismatchHypothesis nodes describing
    candidate explanations. Idempotent — already-analysed pairs
    are marked + skipped on subsequent passes.

    The `feature_too_coarse` hypothesis (which triggers feature
    invention) fires when a feature's bimodal `balance` exceeds
    the invention threshold read from DevelopmentRoot — so the
    agent's own meta-cognitive diagnosis of stagnation lowers the
    bar for inventing new features."""
    feats = _feature_concepts(substrate, ctx)
    feat_by_id = {v: k for k, v in feats.items()}
    invention_threshold = _invention_balance_threshold(substrate)

    for src, et, tgt, prov in [
        ("MismatchHypothesis", "about_holder", "Concept",
         "belief_revision:hypothesis_about_holder"),
        ("MismatchHypothesis", "about_feature", "Concept",
         "belief_revision:hypothesis_about_feature"),
        ("MismatchHypothesis", "evidence_from", "Impasse",
         "belief_revision:hypothesis_evidence_from"),
        # Back-compat with phonology's legacy edge names.
        ("MismatchHypothesis", "about_word", "Concept",
         "belief_revision:hypothesis_about_word"),
        ("MismatchHypothesis", "about_concept", "Concept",
         "belief_revision:hypothesis_about_concept"),
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

    # Dedup is per-KIND: each (holder, feature, position, kind)
    # is independently mintable. This matters for feature
    # invention — when the agent later lowers the invention
    # threshold, the `feature_too_coarse` kind can be minted on a
    # cluster that already has other hypothesis kinds, because the
    # (holder, feature, position, 'feature_too_coarse') key isn't
    # in the set yet.
    existing_hyp_keys: set = set()
    for h in substrate.nodes("MismatchHypothesis"):
        ha2 = substrate.node(h)["attrs"]
        if ha2.get("origin") != "belief_revision":
            continue
        hs = list(substrate.neighbours(h, "about_holder"))
        fs = list(substrate.neighbours(h, "about_feature"))
        if hs and fs:
            existing_hyp_keys.add(
                (hs[0], fs[0], ha2.get("position"),
                   ha2.get("kind")))

    # Bucket persistent impasses by (holder, feature, position).
    # Position is None for bag-of-features impasses (back-compat
    # path); otherwise pulled from the impasse's `position` attr.
    clusters: dict = {}
    for imp in substrate.nodes("Impasse"):
        ia = substrate.node(imp)["attrs"]
        if ia.get("kind") != ctx.divergence_kind:
            continue
        if not ia.get("persistent_taught_mismatch", False):
            continue
        holders = list(substrate.neighbours(imp, "about_holder")) \
                      or list(substrate.neighbours(imp,
                                                        "about_word"))
        obs_ = list(substrate.neighbours(imp, "about_observation")) \
                  or list(substrate.neighbours(imp, "about_sign"))
        if not holders or not obs_:
            continue
        holder, obs = holders[0], obs_[0]
        ha = substrate.node(holder)["attrs"]
        exhibits = set(substrate.neighbours(obs,
                                                  ctx.exhibits_edge))
        position = ia.get("position")
        for fname, fid in feats.items():
            # Choose the signature attr based on position: per-
            # position when known, bag-of-features otherwise.
            if position:
                key = f"{position}_{ctx.marker_prefix}{fname}"
            else:
                key = f"{ctx.marker_prefix}{fname}"
            if key not in ha:
                continue
            taught = float(ha[key])
            obs_v = 1.0 if fid in exhibits else 0.0
            if abs(obs_v - taught) < 0.3:
                continue
            clusters.setdefault((holder, fid, position), []).append(
                (imp, obs_v, taught, obs))

    new_hyps: list = []
    for (holder, fid, position), entries in clusters.items():
        if len(entries) < min_impasses_per_pair:
            continue
        hname = substrate.node(holder)["attrs"].get("name", "?")
        fname = feat_by_id[fid]
        n = len(entries)
        observations = [o for _, o, _, _ in entries]
        taught = entries[0][2]
        mean_obs = sum(observations) / n
        n_under = sum(1 for o in observations if o < taught)
        n_over = sum(1 for o in observations if o > taught)
        direction = "under" if n_under > n_over else "over"
        uniformity = max(n_under, n_over) / n
        if (observations.count(0.0)
                and observations.count(1.0)):
            ones = observations.count(1.0)
            zeros = observations.count(0.0)
            balance = (min(ones, zeros) / max(ones, zeros)
                          if max(ones, zeros) > 0 else 0)
        else:
            balance = 0.0
        gap = abs(mean_obs - taught)
        outlier_score = max(0.0, 1.0 - n / 20.0) * gap

        hypotheses: list = []
        if uniformity >= 0.7 and direction == "under":
            hypotheses.append((
                "predicate_too_strict", uniformity,
                f"{n} obs under-exhibit {fname} "
                f"(obs={mean_obs:.2f} vs taught={taught:.2f}); "
                f"detector may miss real cases"))
            hypotheses.append((
                "teaching_too_strong", uniformity,
                f"{n} obs under-exhibit {fname} "
                f"(obs={mean_obs:.2f} vs taught={taught:.2f}); "
                f"textbook P may be too high"))
        elif uniformity >= 0.7 and direction == "over":
            hypotheses.append((
                "teaching_too_weak", uniformity,
                f"{n} obs over-exhibit {fname} "
                f"(obs={mean_obs:.2f} vs taught={taught:.2f})"))
            # Symmetric to predicate_too_strict on under-
            # exhibition: when observation OVER-fires relative to
            # a taught signature, the detector might be TOO
            # LENIENT — firing on inputs that shouldn't trigger
            # it. Acting on this raises the predicate's
            # threshold, making it more selective. This is the
            # autopoietic close-on-predicate path: the agent
            # discovers its own perceptual machinery is firing
            # spuriously and tightens it.
            hypotheses.append((
                "predicate_too_lenient", uniformity,
                f"{n} obs over-exhibit {fname} "
                f"(obs={mean_obs:.2f} vs taught={taught:.2f}); "
                f"detector may be firing on inputs that don't "
                f"truly exhibit it"))
        if balance >= 0.4:
            hypotheses.append((
                "sub_class_within_holder", balance,
                f"{fname} bimodal across obs of {hname}: "
                f"variants?"))
        # Predicate-invention signal: when a feature's exhibition
        # is BIMODAL across observations of the same labeled
        # thing, the feature itself may be too coarse — it can't
        # distinguish a present-strong case from a present-weak
        # case. The agent's invention remedy can split the
        # feature into <name>_strong / <name>_weak.
        if balance >= invention_threshold:
            hypotheses.append((
                "feature_too_coarse", balance,
                f"{fname} fires too coarsely on {hname} "
                f"(balance={balance:.2f} >= "
                f"invent_thr={invention_threshold:.2f}): "
                f"could split into stronger/weaker variants"))
        if outlier_score >= 0.4 and n <= 8:
            hypotheses.append((
                "obs_misclassified", outlier_score,
                f"only {n} outlier obs cause the {fname} "
                f"divergence on {hname}"))

        minted_any = False
        for kind, score, summary in hypotheses:
            # Per-kind dedup: skip if this exact
            # (holder, feature, position, kind) already exists.
            if (holder, fid, position, kind) in existing_hyp_keys:
                continue
            existing_hyp_keys.add((holder, fid, position, kind))
            hyp_attrs = {
                "kind": kind,
                "score": float(score),
                "summary": summary,
                "n_evidence": int(n),
                "mean_observed": float(mean_obs),
                "taught": float(taught),
                "origin": "belief_revision",
                "domain": ctx.divergence_kind,
            }
            if position is not None:
                hyp_attrs["position"] = position
            hyp = substrate.add_node("MismatchHypothesis",
                                          hyp_attrs)
            try:
                substrate.add_edge(hyp, "about_holder", holder)
                substrate.add_edge(hyp, "about_feature", fid)
                # Phonology back-compat.
                substrate.add_edge(hyp, "about_word", holder)
                substrate.add_edge(hyp, "about_concept", fid)
                for imp, _, _, _ in entries[:5]:
                    substrate.add_edge(hyp, "evidence_from", imp)
            except Exception:
                pass
            new_hyps.append(hyp)
            minted_any = True
        # Only mark impasses analysed once SOMETHING was minted for
        # them — otherwise a future cycle with a lower invention
        # threshold can still pick them up.
        if minted_any:
            for imp, _, _, _ in entries:
                substrate.set_attr(imp, "analysed", True)
    return new_hyps


__all__ = [
    "BeliefRevisionContext",
    "teach_signature",
    "detect_impasses",
    "investigate_impasses",
    "analyse_persistent_mismatches",
]
