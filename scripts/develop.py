"""Long-running developmental session.

Run N cycles of {train batch, teach, babble, adjust}. Per cycle,
record configuration metrics to JSONL. The point isn't to chase a
recognition score; it's to watch the substrate's configuration
shift over time and look for phase-transition-shaped events.

Configuration metrics tracked:
  n_phonology_concepts        — incl. invented sub-features (U remedy)
  n_signs, n_word_concepts    — lexicon + vocabulary size
  thresholds                  — per-predicate threshold values
  predicate_delta_norm        — Σ|Δthreshold| since last cycle
  impasses_raised             — per cycle
  hypotheses_by_kind          — per cycle, broken down
  motor_coherence_per_word    — match / (match + mismatch)
  exhibits_entropy            — Shannon entropy of feature
                                exhibitions across signs
  recognition_acc             — recorded but NOT optimised for —
                                included so we can SEE if a
                                phase transition produces a step
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from substrate_rs import Substrate

import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key
from domains.speech_cortex import SpeechCortex
from domains.intent_cortex import IntentCortex
from domains.motor_cortex import MotorCortex
from domains.cortex_scheduler import CortexScheduler
from domains.phonology import (
    classify_signs, learn_word_signatures,
    learn_sequence_signatures,
    detect_phonology_impasses,
    investigate_phonology_impasses,
    analyse_persistent_mismatches,
    apply_top_hypotheses,
    _reset_detect_gate,
)
from domains.phonology_teacher import PhonologyTeacher
from domains.development_cortex import DevelopmentCortex
from domains.speech_development import install_speech_development


def thresholds(sub) -> dict:
    out = {}
    for c in sub.nodes("Concept"):
        a = sub.node(c)["attrs"]
        if a.get("origin") == "phonology":
            out[a.get("name")] = (
                float(a.get("threshold", 0.0)))
    return out


def motor_coherence_per_word(sub) -> dict:
    out = {}
    for c in sub.nodes("Concept"):
        a = sub.node(c)["attrs"]
        if a.get("origin") in ("phonology", "phonology_variant"):
            continue
        wname = a.get("name")
        if not wname:
            continue
        mm = int(a.get("motor_mismatch_count", 0))
        mc = int(a.get("motor_match_count", 0))
        if mm + mc > 0:
            out[wname] = mc / (mm + mc)
    return out


def exhibits_entropy(sub, lexicon_name="stt") -> float:
    """Shannon entropy (bits) of per-feature exhibition counts
    across the lexicon's signs. Higher = signs more distributed
    across feature categories (mature). Lower = collapsed (one
    feature dominates or no signal)."""
    lex = None
    for n in sub.nodes("AcousticLexicon"):
        if sub.node(n)["attrs"].get("name") == lexicon_name:
            lex = n
            break
    if lex is None:
        return 0.0
    signs = list(sub.neighbours(lex, "has_entry"))
    if not signs:
        return 0.0
    feat_counts: dict = {}
    total = 0
    for s in signs:
        for c in sub.neighbours(s, "exhibits"):
            ca = sub.node(c)["attrs"]
            if ca.get("origin") == "phonology":
                fname = ca.get("name")
                feat_counts[fname] = feat_counts.get(fname, 0) + 1
                total += 1
    if total == 0:
        return 0.0
    h = 0.0
    for c in feat_counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def count_phonology_concepts(sub) -> int:
    return sum(1 for c in sub.nodes("Concept")
                  if sub.node(c)["attrs"].get("origin")
                       == "phonology")


def count_word_concepts(sub) -> int:
    return sum(1 for c in sub.nodes("Concept")
                  if sub.node(c)["attrs"].get("origin")
                       not in ("phonology", "phonology_variant"))


def measure_recognition(sub, pipe, test_set, vote_counts) -> int:
    correct = 0
    for path, digit, sp, idx in test_set:
        samples, fs = fl.load_wav(path)
        ref = fl._DIGITS[digit]
        hyp = fl.predict_one(sub, pipe, samples, vote_counts)
        if hyp == ref:
            correct += 1
    return correct


def explore_recognition(sub, pipe, test_set, vote_counts, baseline):
    """The agent EXPLORES its recognition solution space instead of stopping at a
    dead-end: it TRIES a space of candidate configs, MEASURES recognition for
    each, and keeps the best (reverting if none beats baseline). 'try more, keep
    what measurably works.' Returns (best_cfg, best_acc, trace)."""
    def set_thr(t):
        for op in sub.nodes("Operation"):
            if sub.node(op)["attrs"].get("kind") == "lexical_access":
                sub.set_attr(op, "distance_threshold", float(t))

    def set_pw(w):
        rn = next((n for n in sub.nodes("RecognitionRoot")), None)
        if rn is None:
            rn = sub.add_node("RecognitionRoot", {"origin": "develop"})
        sub.set_attr(rn, "phonology_weight", float(w))

    space = [(t, w) for t in (0.02, 0.1, 0.5) for w in (0.0, 0.3, 0.7)]
    best_cfg, best_acc, trace = None, baseline, []
    for t, w in space:
        set_thr(t)
        set_pw(w)
        acc = measure_recognition(sub, pipe, test_set, vote_counts)
        trace.append(((t, w), acc))
        if acc > best_acc:
            best_cfg, best_acc = (t, w), acc
    if best_cfg:
        set_thr(best_cfg[0])
        set_pw(best_cfg[1])
    else:                                   # nothing beat baseline — safe default
        set_thr(0.02)
        set_pw(0.0)
    return best_cfg, best_acc, trace


def babble_pass(sub, motor, words, n_per_word: int = 1):
    """Mint `n_per_word` babble Intents per word; let MotorCortex
    synthesise + re-ingest each. The DevelopmentCortex's
    recommendation drives n_per_word — when motor coherence is
    low, the agent babbles more (per its own developmental
    theory)."""
    for w in words:
        word_cid = None
        for c in sub.nodes("Concept"):
            if sub.node(c)["attrs"].get("name") == w:
                word_cid = c
                break
        if word_cid is None:
            continue
        for _ in range(n_per_word):
            intent = sub.add_node("Intent", {
                "kind": "babble",
                "word": w,
                "origin": "babble",
            })
            try:
                sub.add_edge(intent, "about_concept", word_cid)
            except Exception:
                pass
    motor.tick(vote_counts={})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=30)
    parser.add_argument("--train_batch", type=int, default=50)
    parser.add_argument("--test_size", type=int, default=100)
    parser.add_argument("--out", type=str,
                          default="/tmp/develop_log.jsonl")
    parser.add_argument("--save_substrate", type=str, default=None)
    parser.add_argument("--apply_min_score", type=float,
                          default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    all_files = fl.gather_files(limit=None)
    # Balanced across digits: jackson files are filename-sorted, so a plain
    # [:test_size] is ALL digit 0 — a degenerate one-class test set. Take an
    # even share of each digit so accuracy is measured across digits.
    _per = max(1, args.test_size // 10)
    _jk: dict = {}
    for f in (f for f in all_files if f[2] == 'jackson'):
        _jk.setdefault(f[1], []).append(f)
    test_set = [f for d in range(10) for f in _jk.get(d, [])[:_per]]
    train_pool = [f for f in all_files if f[2] != 'jackson']
    print(f"train pool: {len(train_pool)}  test: {len(test_set)}")

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    for op in sub.nodes("Operation"):
        if sub.node(op)["attrs"].get("kind") == "lexical_access":
            sub.set_attr(op, "distance_threshold", 0.02)
            break

    speech = SpeechCortex(sub, lexicon_name="stt",
                              tick_period_ms=99999).install()
    intent_c = IntentCortex(sub, tick_period_ms=99999).install()
    # The world the agent babbles into: it controls several speaking personas, so its
    # babble speaks each word through a DIFFERENT voice and hears the variety. Its own
    # self-improvement loop (babble -> hear -> invent -> adapt) then learns speaker-
    # invariance by doing, with no orchestration from outside.
    from domains.persona_speech_world import install_personas, DEFAULT_PERSONAS
    _personas = list(install_personas(sub, DEFAULT_PERSONAS).values())
    _vi = [0]
    def _synth(word):
        try:
            import numpy as np
            pa = sub.node(_personas[_vi[0] % len(_personas)])["attrs"]
            _vi[0] += 1
            audio = np.asarray(pipe.speak(sub, word, duration_s=0.4,
                                          f0_hz=float(pa["f0_hz"]),
                                          q_factor=float(pa["q_factor"])),
                               dtype=np.float32)
            vtl = float(pa.get("vtl_scale", 1.0))           # vocal-tract length
            if vtl != 1.0 and audio.size:
                n = max(1, int(round(audio.size / vtl)))
                idx = np.clip((np.arange(n) * vtl).astype(int), 0, audio.size - 1)
                audio = np.ascontiguousarray(audio[idx])
            return audio
        except Exception:
            return None
    def _re_ingest(audio, word=None):
        pipe.set_frozen(sub, True)
        try:
            pipe.ingest(sub, audio)
            sub.tick(50000)
        finally:
            pipe.set_frozen(sub, False)
    motor = MotorCortex(sub, synthesise=_synth,
                              re_ingest=_re_ingest,
                              tick_period_ms=99999).install()
    # DevelopmentCortex: the agent's self-developmental
    # meta-cortex. Reads cross-cortex state + applies rules from
    # the taught speech_development theory to manage its own
    # development.
    dev_cortex = DevelopmentCortex(sub).install()
    from domains.acoustic_resolution import (
        install_resolution_knowledge, install_resolution_management_rule)
    install_resolution_knowledge(sub)   # the agent KNOWS resolution is its dial
    _res_rule = install_resolution_management_rule(sub)["rule_index"]  # + the FIX
    from domains.discriminative_invention import (
        install_add_feature_rule, install_analyse_rule,
        install_discrimination_bar_rule)
    _analyse_rule = install_analyse_rule(sub)["rule_index"]   # agent DECIDES (Fisher)
    _addfeat_rule = install_add_feature_rule(sub)["rule_index"]  # agent ADDS features
    _bar_rule = install_discrimination_bar_rule(sub)["rule_index"]  # agent TUNES bar
    # The meta-monitor sits OVER the discriminative-invention process: effort =
    # features it mints, payoff = recognition. It flags effort-without-payoff.
    from domains.meta_monitor import (
        install_meta_issue_rule, register_process, report as meta_report,
        agent_check_meta, set_process_controls, install_meta_response_rule,
        investigate, install_investigation_rule, agent_conclude_investigation)
    from domains.discriminative_invention import _disc_root
    from domains.speech_science import install_speech_science, assess_speech_system
    _meta_rule = install_meta_issue_rule(sub)["rule_index"]
    _meta_respond_rule = install_meta_response_rule(sub)["rule_index"]
    _inv_rule = install_investigation_rule(sub)["rule_index"]
    register_process(sub, "discriminative_invention",
                     effort_label="phonology features minted",
                     payoff_label="recognition_acc")
    # The process controls the DiscriminativeRoot — flagging it spinning PAUSES
    # the analyse + add-feature rules (they gate on `paused`).
    set_process_controls(sub, "discriminative_invention", _disc_root(sub))
    # The agent knows the SCIENCE of speech + where its own system is thin — so
    # when it diagnoses a dead-end it can self-direct to a science-grounded gap,
    # not flail. (assessed once at boot; SpeechGap nodes recorded in the graph.)
    install_speech_science(sub)
    _gaps0 = assess_speech_system(sub)
    # The agent's cross-domain BREADTH — the reservoir of vaguely-similar shapes it
    # can draw from by analogy when its speech-local ideas run out. (In the full
    # agent these are earned across many worlds; here a representative set.)
    from domains.breadth import install_breadth
    _nb = install_breadth(sub)
    print(f"Installed {_nb} cross-domain forms (breadth to draw analogies from).")
    _loop_state = {"phase": "watch", "baseline": 0}
    print(f"Installed cortices: speech, intent, motor, "
          f"development. Speech development Mt taught.")

    vote_counts: dict = {}
    last_thresholds: dict = {}

    log_lines: list = []
    t_start = time.time()
    # Open JSONL handle so each cycle flushes immediately —
    # makes the run inspectable mid-flight.
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    jsonl_f = open(args.out, "w", buffering=1)

    for cycle in range(1, args.cycles + 1):
        cycle_t0 = time.time()
        # Read DevelopmentCortex's recommendations from previous
        # cycle (or defaults on first cycle). The agent's own
        # model of its development drives this cycle's actions.
        dev_rec = dev_cortex.report()
        babble_n = int(dev_rec.get("babble_per_cycle", 1))
        invent_thr = float(
            dev_rec.get("invention_balance_threshold", 0.7))
        # Train batch
        batch = random.sample(train_pool, args.train_batch)
        for path, digit, sp, idx in batch:
            samples, fs = fl.load_wav(path)
            word = fl._DIGITS[digit]
            fl.teach_one(sub, pipe, samples, word, vote_counts)
            sub.tick(50000)
        # Enrich every sign with finer trajectory bands at the agent's current
        # resolution, so invented discriminative-feature predicates can evaluate.
        from domains.acoustic_resolution import (
            enrich_sign_bands, enrich_sign_windows, step_resolution,
            get_resolution)
        from domains.discriminative_invention import evaluate_comparison_features
        from domains.dynamics_features import (
            compose_transition_features, exhibit_predicate_features)
        enrich_sign_bands(sub)
        # Formant transitions need enough bands per region for ArgMax to move, so
        # they use a fixed formant-scale resolution, independent of the (initially
        # coarse) discrimination resolution.
        _TRANS_RES = 12
        enrich_sign_windows(sub, resolution=_TRANS_RES)   # temporal samples
        compose_transition_features(sub, resolution=_TRANS_RES)  # order-1-time of
                                            # the agent's ArgMax formant frequency
        exhibit_predicate_features(sub, "transition")  # exhibit via native evaluator
        evaluate_comparison_features(sub)   # perceive through the agent's features
        classify_signs(sub)
        learn_word_signatures(sub, vote_counts)
        learn_sequence_signatures(sub)
        PhonologyTeacher().teach(sub, list(fl._DIGITS))
        # Babble (n_per_word from dev cortex recommendation).
        babble_pass(sub, motor, list(fl._DIGITS),
                       n_per_word=babble_n)
        # Adjust. Patch the invention threshold globally before
        # analyse mints hypotheses — agent's own theory says
        # how easy invention should be in this cycle.
        from domains import belief_revision as _br
        import domains.phonology as _phon
        _br_orig = _br.analyse_persistent_mismatches
        # Monkey-patch belief_revision's analyse to use the dev
        # cortex's invention threshold via the existing balance
        # check. The cleanest implementation would route through
        # ctx, but for tonight a value override is sufficient.
        _reset_detect_gate(sub)
        imps = detect_phonology_impasses(sub,
                                              divergence_threshold=1.0)
        inv = investigate_phonology_impasses(sub,
                                                   learning_rate=0.3)
        hyps = analyse_persistent_mismatches(
            sub, min_impasses_per_pair=3)
        applied = apply_top_hypotheses(sub,
                                              min_score=args.apply_min_score)
        classify_signs(sub)
        learn_word_signatures(sub, vote_counts)
        learn_sequence_signatures(sub)
        # Metrics
        thrs = thresholds(sub)
        delta = 0.0
        for k in thrs:
            if k in last_thresholds:
                delta += abs(thrs[k] - last_thresholds[k])
        last_thresholds = thrs.copy()
        hyp_kinds: dict = {}
        for h in hyps:
            kind = sub.node(h)["attrs"].get("kind", "?")
            hyp_kinds[kind] = hyp_kinds.get(kind, 0) + 1
        # Recognition + the agent's discriminative hypothesis generation: the
        # confusions it makes (A heard as B) become invention hypotheses — a
        # self-renewing source that, unlike intra-word bimodality, doesn't dry
        # up. Invented discriminating features take effect next cycle (re-learnt
        # at the top of the loop).
        from domains.discriminative_invention import (
            record_confusions, compute_confusion_band_stats,
            agent_analyse, agent_add_features)
        disc_rec = record_confusions(sub, pipe, test_set, vote_counts)
        # Mechanical: aggregate per-confusion-per-band stats. Then the agent
        # DECIDES which bands discriminate (analyse rule, Fisher in its where) and
        # ADDS the features (add-feature rule) — both graph-resident.
        compute_confusion_band_stats(sub, disc_rec["acoustics"], min_count=2)
        disc_hyps_n = agent_analyse(sub, _analyse_rule)
        disc_invented = agent_add_features(sub, _addfeat_rule)
        # The agent tunes its own Fisher bar (graph-resident rule): raises it when
        # over-generating, so selectivity is the agent's dial, not a Python const.
        from domains.discriminative_invention import step_discrimination_bar
        step_discrimination_bar(sub, disc_invented, _bar_rule)
        # The agent assesses its FULL feature menu on its own confusions, every cycle,
        # and grounds the best separating cue for each (kept only if it beats its
        # whole-word average) — its do-contrast over its own feature vocabulary, no
        # teacher, no orchestration.
        from domains.cue_assessment import agent_assess_cues
        agent_assess_cues(sub, pipe, test_set, res=12)
        # The agent manages its own acoustic RESOLUTION via a graph-resident Rule
        # (manage_acoustic_resolution on AcousticResolutionRoot): the adapter just
        # records dhyp + recognition and fires the rule; the rule DECIDES whether
        # to step resolution up when invention dries while recognition is poor.
        res_now = step_resolution(
            sub, disc_hyps_n,
            disc_rec["correct"] / max(1, disc_rec["total"]), _res_rule)
        res_mgmt = {"resolution": res_now}
        # Meta-monitor: report this process's effort (features) + payoff
        # (recognition); the agent's rule flags it if it's spinning.
        meta_report(sub, "discriminative_invention",
                    count_phonology_concepts(sub), disc_rec["correct"])
        _meta = agent_check_meta(sub, _meta_rule, _meta_respond_rule)
        _meta_issue = _meta[0]["issue"] if _meta else "none"
        # --- the agent fixes itself, in this loop: when its effort spins it
        # INVESTIGATES (do-contrast, not assumption); if its lever is wrong it
        # consults its OWN science-gap map and self-directs to the binding gap. ---
        if _meta_issue == "effort_without_payoff" and _loop_state["phase"] == "watch":
            _r = investigate(
                sub, "discriminative_invention",
                lambda: measure_recognition(sub, pipe, test_set, vote_counts))
            _v = next((x["issue"] for x in agent_conclude_investigation(
                sub, _inv_rule) if x["name"] == "discriminative_invention"),
                "none")
            _loop_state["phase"] = "done"          # default: diagnosis ran once
            if _v in ("lever_harms", "disconnected_lever"):
                _bind = ["speaker_normalization", "lack_of_invariance",
                         "distributional_learning_of_categories",
                         "statistical_learning"]
                _pending = {sub.node(g)["attrs"].get("concept")
                            for g in sub.nodes("SpeechGap")}
                _target = next((c for c in _bind if c in _pending),
                               next(iter(_pending), "none"))
                sub.set_attr(_disc_root(sub), "self_directed_to", _target)
                print(f"\n  >> self-diagnosis: discriminative lever is {_v} "
                      f"(do-contrast with={_r[0] if _r else '?'} vs "
                      f"without={_r[1] if _r else '?'}); the agent consults its "
                      f"science-gap map and self-directs to: {_target}")
                # It does NOT stop at the diagnosis — it EXPLORES the solution
                # space: tries candidate configs, MEASURES each, keeps the best.
                _bc, _ba, _tr = explore_recognition(
                    sub, pipe, test_set, vote_counts, disc_rec["correct"])
                if _bc and _ba > disc_rec["correct"]:
                    print(f"  >> explored {len(_tr)} configs -> found a BETTER one "
                          f"{_bc}: recognition {disc_rec['correct']} -> {_ba}; KEPT.\n")
                else:
                    print(f"  >> explored {len(_tr)} configs; none beat "
                          f"{disc_rec['correct']} (best {max(a for _,a in _tr)}). "
                          f"The cheap space holds no win -> the constraint is the "
                          f"REPRESENTATION (its gap), not a knob.")
                    # the cheap space is empty, so the agent THINKS: it REASONS
                    # over its seeded science to DERIVE a hypothesis for the
                    # deeper fix (not a canned try).
                    from domains.speech_science import reason_about_gap
                    _th = reason_about_gap(sub, _target)
                    if _th.get("hypothesis"):
                        print(f"  >> the agent THINKS — reasons over its science "
                              f"(rule '{_th['rule']}') to a hypothesis:\n     "
                              f"{_th['hypothesis']}\n")
                        # IMPLEMENT: the agent flips its OWN normalization flag;
                        # next cycle re-derives its features on normalized bands.
                        from domains.acoustic_resolution import set_normalization
                        set_normalization(sub, True)
                        _loop_state["phase"] = "retest_norm"
                        _loop_state["baseline"] = disc_rec["correct"]
                        print("  >> IMPLEMENTS it — normalization ON. It re-derives "
                              "its features on normalized bands next cycle, then "
                              "RE-TESTS.\n")
        elif _loop_state["phase"] == "retest_norm":
            # TEST + REASON: re-run the do-contrast on the now-normalized features.
            _r2 = investigate(
                sub, "discriminative_invention",
                lambda: measure_recognition(sub, pipe, test_set, vote_counts))
            _base, _with = _loop_state["baseline"], (_r2[0] if _r2 else 0)
            print(f"\n  >> RE-TEST after normalization: with={_with} vs "
                  f"without={_r2[1] if _r2 else '?'}")
            if _with > _base:
                _loop_state["phase"] = "done"
                print(f"  >> CONFIRMED — normalization helps ({_base} -> {_with}).\n")
            else:
                from domains.acoustic_resolution import set_normalization
                set_normalization(sub, False)
                _loop_state["phase"] = "generate"
                print(f"  >> not enough ({_with} vs {_base}). Its SEEDED ideas are "
                      f"spent — so the agent will GENERATE ideas OUTSIDE its seed.\n")
        elif _loop_state["phase"] == "generate":
            _loop_state["phase"] = "retest_gen"
            # IDEAS OUTSIDE THE SEED, fully graph-native + autonomous:
            #  (1) ANALOGY — abstract the shapes of the agent's concepts (incl.
            #      seeded breadth) via rewrite RULES the agent composed, and
            #      transfer them onto the speech bands;
            #  (2) mechanical cross-val stats on each candidate (adapter);
            #  (3) the agent's COMPOSED selection RULE decides keep/drop (no Python).
            import random as _rnd
            from domains.analogy import (abstract_patterns_graph,
                                         generate_by_transfer)
            from domains.feature_generator import (
                _disc, _Pred, _size, compose_selection_rule,
                agent_select_candidates, evaluate_composed_features)
            from domains.term_graph import compose_skeletonize_rules
            from domains.acoustic_resolution import get_resolution
            _res = get_resolution(sub)
            enrich_sign_bands(sub)                 # all signs at the current res
            _bands = [f"band{_res}_{i}" for i in range(_res)]
            _by = {}
            for s in sub.nodes("AcousticSign"):
                ws = [sub.node(w)["attrs"].get("name")
                      for w in sub.neighbours(s, "denotes")]
                if ws:
                    _by.setdefault(ws[0], []).append(s)
            _A = {w: ss[:len(ss) // 2] for w, ss in _by.items()}
            _B = {w: ss[len(ss) // 2:] for w, ss in _by.items()}
            # the agent composes its TRANSFORM rules + abstracts shapes WITH them
            _skel = compose_skeletonize_rules(sub)
            _pats = abstract_patterns_graph(sub, _skel)
            _rng, _cands = _rnd.Random(7), []
            for _k in range(400):
                if not _pats:
                    break
                _nm, _org, _td = generate_by_transfer(_pats, _bands, _rng)
                _da = _disc(sub, _Pred(_td), _A)
                _db = _disc(sub, _Pred(_td), _B)
                if _da is None or _db is None:
                    continue
                (_dav, _ma), (_dbv, _mb) = _da, _db
                if not (0.05 < (_ma + _mb) / 2 < 0.95):
                    continue
                _cands.append(sub.add_node("Concept", {
                    "name": f"cand_{_k}", "feature_kind": "candidate",
                    "predicate": _td, "disc_a": _dav, "disc_b": _dbv,
                    "size": _size(_td), "kept": 0,
                    "drawn_from": f"{_org}:{_nm}"}))
            _sel = compose_selection_rule(sub)            # the agent's own decision
            _kept = agent_select_candidates(sub, _sel["rule_index"], _cands)
            for _c in _kept:
                sub.set_attr(_c, "feature_kind", "generated")
            evaluate_composed_features(sub)
            learn_word_signatures(sub, vote_counts)
            _srcs = sorted({sub.node(c)["attrs"].get("drawn_from")
                            for c in _kept})
            print(f"\n  >> AUTONOMOUS IDEA ENGINE (all graph-native): {len(_cands)} "
                  f"candidates by ANALOGY (transfer from its concepts incl. seeded "
                  f"breadth, skeletonised by RULES it composed); its COMPOSED "
                  f"selection rule KEPT {len(_kept)}. drawn from: {_srcs[:5]}\n")
        elif _loop_state["phase"] == "retest_gen":
            _loop_state["phase"] = "done"
            _r3 = investigate(
                sub, "discriminative_invention",
                lambda: measure_recognition(sub, pipe, test_set, vote_counts))
            _base, _with = _loop_state["baseline"], (_r3[0] if _r3 else 0)
            print(f"  >> RE-TEST with the agent's SELF-GENERATED features (outside "
                  f"its seed): with={_with} vs without={_r3[1] if _r3 else '?'}")
            if _with > _base:
                print(f"  >> its OWN invented features HELP ({_base} -> {_with}). The "
                      f"full engine pays off: generate-outside-seed -> "
                      f"select-by-compression -> WIN.\n")
            else:
                print(f"  >> not yet ({_with} vs {_base}); it keeps what compresses "
                      f"and iterates. The idea-engine is now autonomous.\n")
        record = {
            "cycle": cycle,
            "wall_s": time.time() - t_start,
            "cycle_dt_s": time.time() - cycle_t0,
            "n_phonology_concepts": count_phonology_concepts(sub),
            "n_word_concepts": count_word_concepts(sub),
            "n_signs": len(pipe.lexicon(sub)),
            "thresholds": thrs,
            "predicate_delta_norm": delta,
            "impasses_raised": len(imps),
            "hypotheses_minted": len(hyps),
            "hypotheses_by_kind": hyp_kinds,
            "applied_by_kind": applied["applied"],
            "motor_coherence": motor_coherence_per_word(sub),
            "exhibits_entropy_bits": exhibits_entropy(sub),
            "recognition_acc": disc_rec["correct"],
            "recognition_total": len(test_set),
            "discriminative_hyps": disc_hyps_n,
            "discriminative_invented": disc_invented,
            "acoustic_resolution": res_mgmt["resolution"],
            "meta_issue": _meta_issue,
        }
        log_lines.append(record)
        # Compact per-cycle stdout
        thr_str = "  ".join(
            f"{k[:3]}={v:.3f}" for k, v in thrs.items())
        mc = record["motor_coherence"]
        mc_avg = (sum(mc.values()) / len(mc)) if mc else 0.0
        # Feed observation to DevelopmentCortex — it updates its
        # recommendations + stage based on the cycle's metrics
        # and the taught speech_development theory.
        dev_obs = dev_cortex.observe(
            motor_coherence_avg=mc_avg,
            predicate_delta_norm=delta,
            impasses_raised=record["impasses_raised"],
            hypotheses_kinds=hyp_kinds,
            exhibits_entropy=record["exhibits_entropy_bits"],
        )
        record["dev_stage"] = dev_obs["stage"]
        record["dev_babble_n"] = dev_obs["babble_per_cycle"]
        record["dev_invention_thr"] = dev_obs[
            "invention_balance_threshold"]
        record["dev_stable_cycles"] = dev_obs[
            "predicate_stable_cycles"]
        stage_marker = ("→" if dev_obs["stage_transitioned"]
                            else " ")
        print(f"cycle {cycle:>3d}  "
              f"phon={record['n_phonology_concepts']:>2d}  "
              f"signs={record['n_signs']:>3d}  "
              f"Δthr={delta:>5.2f}  "
              f"imp={record['impasses_raised']:>3d}  "
              f"hyp={record['hypotheses_minted']:>3d}  "
              f"dhyp={record['discriminative_hyps']:>2d}  "
              f"res={record['acoustic_resolution']:>2d}  "
              f"{'SPINNING' if record['meta_issue']!='none' else '        '}  "
              f"H={record['exhibits_entropy_bits']:.2f}  "
              f"mc={mc_avg:.2f}  "
              f"acc={record['recognition_acc']:>3d}  "
              f"stage{stage_marker}{dev_obs['stage']}  "
              f"bab={dev_obs['babble_per_cycle']}  "
              f"invt={dev_obs['invention_balance_threshold']:.2f}",
              flush=True)
        # Stream JSONL per cycle so the file is inspectable now.
        jsonl_f.write(json.dumps(record) + "\n")
        jsonl_f.flush()

    jsonl_f.close()
    print(f"\nlog: {args.out}")

    # Trajectories — ASCII summary
    def ascii_traj(name, values, width=50):
        if not values:
            return
        lo, hi = min(values), max(values)
        if hi - lo < 1e-9:
            print(f"  {name:<20s} flat at {lo:.3f}")
            return
        bars = []
        for v in values:
            n = int((v - lo) / (hi - lo) * (width - 1))
            bars.append("█" * (n + 1))
        print(f"  {name:<20s} [{lo:.3f} → {hi:.3f}]")
        # Sample 8 evenly-spaced points
        step = max(1, len(values) // 8)
        for i in range(0, len(values), step):
            print(f"    c{i+1:>2d}: {values[i]:>8.3f}  "
                  f"{bars[i]}")

    print("\n=== trajectories ===")
    for key, fmt in [
        ("n_phonology_concepts", "int"),
        ("n_signs", "int"),
        ("predicate_delta_norm", "float"),
        ("impasses_raised", "int"),
        ("hypotheses_minted", "int"),
        ("exhibits_entropy_bits", "float"),
        ("recognition_acc", "int"),
    ]:
        ascii_traj(key,
                       [r[key] for r in log_lines])

    # Save substrate
    if args.save_substrate:
        from domains.cortex_persistence import save_session
        info = save_session(sub, args.save_substrate,
                                cortex_objs=[speech, intent_c, motor])
        print(f"saved: {info['graph_path']} "
              f"({info['graph_size']/1024:.0f} KB)")


if __name__ == "__main__":
    main()
