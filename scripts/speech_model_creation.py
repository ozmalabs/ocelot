"""Speech development WITH the agent's model-creation faculty in the loop.

The speech agent (cortex harness: speech / intent / motor / development cortices
on a substrate_rs.Substrate) develops by babbling + training on FSDD, the way it
always does. The new thing: the CodeWritingCortex is ALSO installed, and the
agent MEASURES its own op costs as it lives — recognition (`lexical_access`,
trajectory matching) and perception (`categorical_perception`, per-frame
clustering). Once it has lived enough to know what's expensive, its code-writing
cortex surveys its ops and, entirely through its own machinery
(`identify_target` by cost → `pick_design_pattern` by computational shape →
author), reaches for a MODEL where one fits.

This is "put the agent in the world and see how it goes": no one tells it to make
a net; it decides, from its own measured world, that its recognition op is a
fuzzy classifier and authors a softmax_classifier for it. It AUTHORS — it does
not train (the net ships unfitted); what it gains is a graph-resident parametric
model of its own recognition it can reason from. See memory
[[ozma_agent_authors_not_trains]] / [[ozma_net_authoring_speech_bridge]].
"""
from __future__ import annotations

import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

import scripts.develop as dev
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.intent_cortex import IntentCortex
from domains.motor_cortex import MotorCortex
from domains.development_cortex import DevelopmentCortex
from domains.speech_development import install_speech_development
from domains.model_understanding import install_model_understanding
from domains.phonology import (
    classify_signs, learn_word_signatures, learn_sequence_signatures,
    detect_phonology_impasses, investigate_phonology_impasses,
    analyse_persistent_mismatches, apply_top_hypotheses, _reset_detect_gate,
)
from domains.phonology_teacher import PhonologyTeacher
from domains.code_writing_cortex import CodeWritingCortex
from domains.code_authoring import get_step


# The net the agent's self-teacher drafts to the commissioned spec. Structure is
# real + complete; weights ship UNFITTED (the agent authors, it does not train).
def _author_net(question: str) -> dict:
    pattern = "softmax_classifier" if "softmax" in question else "linear_layer"
    src = f"""//! {pattern} draft for the op the agent targeted, AUTHORED by its
//! code-writing cortex from its own measured op costs + the design pattern it
//! picked. Structure complete; weights UNFITTED (the agent authors, not trains).
pub const FEAT_DIM: usize = 800;   // 32 traj frames x 25 A1 patches
pub const N_CLASSES: usize = 11;   // ten digits + unknown
pub static W: [[f32; FEAT_DIM]; N_CLASSES] = [[0.0; FEAT_DIM]; N_CLASSES];
pub static B: [f32; N_CLASSES] = [0.0; N_CLASSES];
#[no_mangle]
pub extern "C" fn recognise(feats: *const f32, len: usize) -> i32 {{
    if feats.is_null() || len < FEAT_DIM {{ return -1; }}
    let x = unsafe {{ std::slice::from_raw_parts(feats, FEAT_DIM) }};
    let mut best = 0usize; let mut best_logit = f32::NEG_INFINITY;
    for c in 0..N_CLASSES {{
        let mut acc = B[c];
        for i in 0..FEAT_DIM {{ acc += W[c][i] * x[i]; }}
        if acc > best_logit {{ best_logit = acc; best = c; }}
    }}
    best as i32   // softmax argmax; with W=0 every logit equal -> class 0
}}
"""
    return {"answer": src}


class SpeechAgent:
    """The minimal agent surface the CodeWritingCortex reads: measured op_stats
    (its sense of what's expensive in its world) + a self-teacher (the drafter)."""

    def __init__(self):
        self._op_stats: dict = {}
        self._self_teacher = _author_net

    def op_stats(self, name=None):
        if name is None:
            return {k: dict(v) for k, v in self._op_stats.items()}
        return dict(self._op_stats.get(name, {"count": 0, "total_ms": 0.0}))

    def record_op(self, name: str, ms: float):
        st = self._op_stats.setdefault(name, {"count": 0, "total_ms": 0.0})
        st["count"] += 1
        st["total_ms"] += float(ms)


def main():
    # NB: recognition accuracy is seed-dependent NOISE (some seeds → 0, some →
    # ~35/40) — the developmental SIGNAL is motor coherence, which climbs on
    # every seed. (Verified: develop.py --seed 7 also gives acc=0.)
    random.seed(int(os.environ.get("SEED", "42")))
    cycles = int(os.environ.get("CYCLES", "12"))
    all_files = fl.gather_files(limit=None)
    # Balanced test set: jackson files are filename-sorted, so a plain [:40] is
    # ALL digit 0 — which would make an unfitted net (always predicts one class)
    # look perfect. Take 4 of each digit so recognition is measured across digits.
    _jackson: dict = {}
    for f in (f for f in all_files if f[2] == 'jackson'):
        _jackson.setdefault(f[1], []).append(f)
    test_set = [f for d in range(10) for f in _jackson.get(d, [])[:4]]
    train_pool = [f for f in all_files if f[2] != 'jackson']
    print(f"train pool: {len(train_pool)}  test: {len(test_set)}  cycles: {cycles}")

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    for op in sub.nodes("Operation"):
        if sub.node(op)["attrs"].get("kind") == "lexical_access":
            sub.set_attr(op, "distance_threshold", 0.02)
            break

    agent = SpeechAgent()
    speech = SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    IntentCortex(sub, tick_period_ms=99999).install()

    def _synth(word):
        try:
            return pipe.speak(sub, word, duration_s=0.4)
        except Exception:
            return None

    def _re_ingest(audio, word=None):
        pipe.set_frozen(sub, True)
        try:
            pipe.ingest(sub, audio)
            sub.tick(50000)
        finally:
            pipe.set_frozen(sub, False)

    motor = MotorCortex(sub, synthesise=_synth, re_ingest=_re_ingest,
                        tick_period_ms=99999).install()
    dev_cortex = DevelopmentCortex(sub).install()
    install_speech_development(sub)
    # The agent's graph-resident understanding of what a MODEL is: static (does
    # not adapt), has a cost to balance, and its failures are surprise.
    mu = install_model_understanding(sub)
    print("Installed cortices: speech, intent, motor, development. The agent "
          "lives + measures its op costs; the model-creation faculty is brought "
          "in once it knows its world (its install adds NN/pattern vocabulary "
          "that would otherwise pollute the speech lexicon).")

    vote_counts: dict = {}
    print(f"\n{'cy':>3} {'phon':>4} {'signs':>5} {'mc':>5} {'acc':>4} "
          f"{'percept_ms':>10} {'recog_ms':>9}  (op the agent feels as costly)")
    for cycle in range(1, cycles + 1):
        babble_n = int(dev_cortex.report().get("babble_per_cycle", 1))
        # --- live + measure perception cost (audio → phonemes pipeline) ---
        t0 = time.time()
        for path, digit, sp, idx in random.sample(train_pool, 30):
            samples, fs = fl.load_wav(path)
            fl.teach_one(sub, pipe, samples, fl._DIGITS[digit], vote_counts)
            sub.tick(50000)
        percept_ms = (time.time() - t0) * 1000.0
        agent.record_op("categorical_perception", percept_ms)

        classify_signs(sub)
        learn_word_signatures(sub, vote_counts)
        learn_sequence_signatures(sub)
        PhonologyTeacher().teach(sub, list(fl._DIGITS))
        dev.babble_pass(sub, motor, list(fl._DIGITS), n_per_word=babble_n)
        _reset_detect_gate(sub)
        detect_phonology_impasses(sub, divergence_threshold=1.0)
        investigate_phonology_impasses(sub, learning_rate=0.3)
        hyps = analyse_persistent_mismatches(sub, min_impasses_per_pair=3)
        apply_top_hypotheses(sub, min_score=0.5)
        classify_signs(sub)
        learn_word_signatures(sub, vote_counts)
        learn_sequence_signatures(sub)

        # --- live + measure recognition cost (trajectory matching) ---
        t0 = time.time()
        acc = dev.measure_recognition(sub, pipe, test_set, vote_counts)
        recog_ms = (time.time() - t0) * 1000.0
        agent.record_op("lexical_access", recog_ms)

        mc = dev.motor_coherence_per_word(sub)
        mc_avg = (sum(mc.values()) / len(mc)) if mc else 0.0
        dev_cortex.observe(motor_coherence_avg=mc_avg, predicate_delta_norm=0.0,
                           impasses_raised=0, hypotheses_kinds={},
                           exhibits_entropy=dev.exhibits_entropy(sub))
        costliest = max(agent.op_stats().items(),
                        key=lambda kv: kv[1]["total_ms"])[0]
        print(f"{cycle:>3} {dev.count_phonology_concepts(sub):>4} "
              f"{len(pipe.lexicon(sub)):>5} {mc_avg:>5.2f} {acc:>4} "
              f"{percept_ms:>10.0f} {recog_ms:>9.0f}  {costliest}")

    # ---- the agent now KNOWS its world; bring in the model-creation faculty ----
    cwc = CodeWritingCortex(sub, agent=agent).install()
    print("\n=== the agent reads its own world (op_stats it MEASURED) ===")
    for name, st in sorted(agent.op_stats().items(),
                           key=lambda kv: -kv[1]["total_ms"]):
        print(f"  {name:>24}  total={st['total_ms']:>8.0f} ms  "
              f"calls={st['count']}")
    print("\n=== its model-creation survey (pick_design_pattern over its ops) ===")
    for row in cwc.survey_pattern_opportunities():
        mark = "  <== a NET" if row["pattern_origin"] == "neural_networks" else ""
        print(f"  {row['op_name']:>24} -> {str(row['chosen_pattern']):<22}"
              f" [{row['pattern_origin']}]{mark}")

    print("\n=== it AUTHORS for its costliest op (its own autonomous chain) ===")
    audit = []
    for step_name in ("cw_identify_target", "cw_select_design_pattern",
                      "cw_request_author", "cw_drain_teacher"):
        if get_step(step_name)(cwc):
            audit.append(step_name)
    print("  fired:", " -> ".join(audit))
    tgt = cwc.current_target()
    if tgt is not None:
        a = sub.node(tgt)["attrs"]
        pat = cwc.chosen_design_pattern()
        pa = sub.node(pat)["attrs"] if pat else {}
        print(f"  TARGETED  : {a.get('op_name')}  (its costliest authorable op)")
        print(f"  PICKED    : {pa.get('name')!r}  [{pa.get('origin')}]")
        draft = cwc.current_draft()
        if draft is not None:
            d = sub.node(draft)["attrs"]
            sub.set_attr(draft, "parameters_fitted", False)
            sub.set_attr(draft, "learned",
                         "recognition = argmax(W.x); competence lives in W, which "
                         "only training fills; the agent authored the STRUCTURE "
                         "from its world, did not train it. Both this net and the "
                         "1-NN recogniser are bounded by the SAME features -> the "
                         "ceiling is upstream (feature coverage).")
            print(f"  AUTHORED  : CodeDraft {draft}, "
                  f"{len(d.get('source',''))} chars of net code (UNFITTED)")
            print(f"  LEARNED   : {sub.node(draft)['attrs']['learned'][:130]}...")

            # --- the agent HANDLES the model via its model_understanding Mt ----
            print("\n=== the agent handles its model "
                  "(model_understanding: static / cost / surprise) ===")
            fitted = bool(sub.node(draft)["attrs"].get("parameters_fitted"))
            # Unfitted softmax (W=0) predicts ONE class for every input.
            n_zero = sum(1 for _p, dgt, _s, _i in test_set if dgt == 0)
            model_correct = n_zero if not fitted else acc
            print(f"  the model is fitted? {fitted} -> a static softmax predicts "
                  f"one class for ALL inputs")
            print(f"  model recognises ~{model_correct}/{len(test_set)} (only the "
                  f"one class); its ADAPTIVE recogniser got {acc}/{len(test_set)}")
            print("  applies model_is_static        : re-running the model can't "
                  "improve it — it's frozen, the agent does NOT train; not a tuning "
                  "problem")
            keep = model_correct > acc
            print(f"  applies model_cost_balance     : model {model_correct} < "
                  f"adaptive {acc} AND cannot adapt -> "
                  f"{'KEEP' if keep else 'DROP it (stop paying its per-call cost)'}")
            misses = len(test_set) - model_correct
            print(f"  applies model_failure_is_surprise: each of the {misses} model "
                  "misses is a SURPRISE -> fall back to the adaptive recogniser, "
                  "which DOES learn; the surprise feeds the adaptive core, not the "
                  "frozen model")
            print("\n  DECISION: keep the adaptive recognition. The authored model "
                  "is a frozen artifact the agent now UNDERSTANDS — to reason FROM, "
                  "not (yet) to rely ON. It does not adapt; the babble loop does.")


if __name__ == "__main__":
    main()
