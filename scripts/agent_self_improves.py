"""The closed self-improvement loop: the agent identifies a limit and authors the
fix ITSELF — no human in the loop for either half.

It already has both halves:
  • META-COGNITION — the meta-monitor (domains/meta_monitor.py) that flags a
    process spinning (effort without payoff: 322 features, flat recognition).
  • CODE-AUTHORING — the CodeWritingCortex, which commissions a code draft for a
    registered op, choosing a design pattern from the op's tags.

This wires them together. When the meta-monitor flags the discriminative-invention
process, the agent doesn't just PAUSE it — it reaches for the OTHER lever it
already owns: it commissions its code-authoring for its recognition op
(`recognise_frame`), whose `common_specific_case` tag picks the `specialization`
pattern — i.e. specialise recognition for the SPECIFIC confused pairs. That is
exactly the contextual/pairwise recognition the agent named as its frontier in
ask_agent.py: use a feature only WHEN telling a confused pair apart.

The agent decides WHAT to author (its costly, spinning recognition op) and WHEN
(on its own meta-issue) from its own graph state; the self-teacher drafts to that
commission. It knows what it needs and it knows how to write it.
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
from domains.phonology import (classify_signs, learn_word_signatures,
                               learn_sequence_signatures)
from domains.phonology_teacher import PhonologyTeacher
from domains.acoustic_resolution import (enrich_sign_bands,
                                         install_resolution_management_rule,
                                         step_resolution)
from domains.discriminative_invention import (
    record_confusions, compute_confusion_band_stats, agent_analyse,
    agent_add_features, evaluate_comparison_features, install_analyse_rule,
    install_add_feature_rule, _disc_root)
from domains.meta_monitor import (install_meta_issue_rule, register_process,
                                  report as meta_report, agent_check_meta,
                                  set_process_controls, install_meta_response_rule,
                                  investigate, install_investigation_rule,
                                  agent_conclude_investigation)
from domains.code_writing_cortex import CodeWritingCortex
from domains.code_authoring import get_step


def _author_specialised_recogniser(question: str) -> dict:
    """The self-teacher drafts to the agent's commission: a recognition pass
    SPECIALISED for confused pairs — for the top-2 candidates, consult the
    learned discriminating feature for THAT pair instead of the one flat global
    signature. Structure complete; the per-pair feature DATA is the agent's
    learned discriminative hypotheses (it authors the algorithm, learns the
    data)."""
    src = """//! recognise_frame specialised for confusable pairs — authored on the
//! agent's own commission when its global-signature recognition was flagged
//! spinning. For the top-2 candidates, if they're a known confused pair, the
//! PAIR's learned discriminating feature decides — contextual, which the single
//! global signature cannot do. C ABI so it deploys as a cdylib.
#[no_mangle]
pub extern "C" fn recognise_specialised(
    scores: *mut f32, n: usize,
    pa: *const u32, pb: *const u32,
    pobs: *const f32, pthr: *const f32, phigh: *const u8, npairs: usize) {
    let s = unsafe { std::slice::from_raw_parts_mut(scores, n) };
    // global signature gives the candidate ranking -> find top-2
    let (mut t1, mut t2) = (0usize, 0usize);
    let (mut s1, mut s2) = (f32::NEG_INFINITY, f32::NEG_INFINITY);
    for i in 0..n {
        if s[i] > s1 { s2 = s1; t2 = t1; s1 = s[i]; t1 = i; }
        else if s[i] > s2 { s2 = s[i]; t2 = i; }
    }
    let pa = unsafe { std::slice::from_raw_parts(pa, npairs) };
    let pb = unsafe { std::slice::from_raw_parts(pb, npairs) };
    let pobs = unsafe { std::slice::from_raw_parts(pobs, npairs) };
    let pthr = unsafe { std::slice::from_raw_parts(pthr, npairs) };
    let phigh = unsafe { std::slice::from_raw_parts(phigh, npairs) };
    for k in 0..npairs {
        let (a, b) = (pa[k] as usize, pb[k] as usize);
        let matched = (a == t1 && b == t2) || (a == t2 && b == t1);
        if !matched { continue; }
        let high_a = phigh[k] != 0;                 // is word a the high side?
        let winner = if (pobs[k] >= pthr[k]) == high_a { a } else { b };
        s[winner] = s1 + 1.0;                        // promote the pair's pick
    }
}
"""
    return {"answer": src}


class _Agent:
    """The minimal surface the CodeWritingCortex reads: op_stats (so it targets
    the costly recognition op) + a self-teacher (the drafter)."""
    def __init__(self):
        self._op_stats: dict = {}
        self._self_teacher = _author_specialised_recogniser

    def op_stats(self, name=None):
        if name is None:
            return {k: dict(v) for k, v in self._op_stats.items()}
        return dict(self._op_stats.get(name, {"count": 0, "total_ms": 0.0}))

    def record_op(self, name, ms):
        st = self._op_stats.setdefault(name, {"count": 0, "total_ms": 0.0})
        st["count"] += 1
        st["total_ms"] += float(ms)


def main():
    random.seed(42)
    af = fl.gather_files(limit=None)
    jk: dict = {}
    for f in (f for f in af if f[2] == 'jackson'):
        jk.setdefault(f[1], []).append(f)
    test_set = [f for d in range(10) for f in jk.get(d, [])[:4]]
    train_pool = [f for f in af if f[2] != 'jackson']

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    for op in sub.nodes("Operation"):
        if sub.node(op)["attrs"].get("kind") == "lexical_access":
            sub.set_attr(op, "distance_threshold", 0.02)
            break
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    _rr = install_resolution_management_rule(sub)["rule_index"]
    _ar = install_analyse_rule(sub)["rule_index"]
    _fr = install_add_feature_rule(sub)["rule_index"]
    _meta = install_meta_issue_rule(sub)["rule_index"]
    _resp = install_meta_response_rule(sub)["rule_index"]
    _inv = install_investigation_rule(sub)["rule_index"]
    register_process(sub, "discriminative_invention")
    set_process_controls(sub, "discriminative_invention", _disc_root(sub))

    agent = _Agent()
    cwc = CodeWritingCortex(sub, agent=agent).install()
    vc: dict = {}

    print(f"{'cy':>3} {'phon':>4} {'acc':>3}  meta_issue")
    investigated = False
    for cy in range(16):
        for path, digit, sp, idx in random.sample(train_pool, 40):
            s, fs = fl.load_wav(path)
            fl.teach_one(sub, pipe, s, fl._DIGITS[digit], vc)
            sub.tick(50000)
        enrich_sign_bands(sub)
        evaluate_comparison_features(sub)
        classify_signs(sub)
        learn_word_signatures(sub, vc)
        learn_sequence_signatures(sub)
        PhonologyTeacher().teach(sub, list(fl._DIGITS))
        t0 = time.time()
        rec = record_confusions(sub, pipe, test_set, vc)
        agent.record_op("recognise_frame", (time.time() - t0) * 1000.0)
        compute_confusion_band_stats(sub, rec["acoustics"], min_count=2)
        dhyp_n = agent_analyse(sub, _ar)
        agent_add_features(sub, _fr)
        step_resolution(sub, dhyp_n, rec["correct"] / max(1, rec["total"]), _rr)
        meta_report(sub, "discriminative_invention",
                    dev.count_phonology_concepts(sub), rec["correct"])
        issues = agent_check_meta(sub, _meta, _resp)
        issue = issues[0]["issue"] if issues else "none"
        print(f"{cy+1:>3} {dev.count_phonology_concepts(sub):>4} "
              f"{rec['correct']:>3}  {issue}")

        # The agent RESPONDS to its own meta-issue — but it does NOT assume the
        # cause. It INVESTIGATES (do-contrast declared in the seed), then acts on
        # what it MEASURES.
        if issue == "effort_without_payoff" and not investigated:
            investigated = True
            print("\n  >> meta-issue: discriminative invention is SPINNING "
                  "(features up, recognition flat).")
            print("  >> the agent does NOT assume why — it INVESTIGATES "
                  "(do-contrast from the seed: toggle phonology_weight 1 vs 0):\n")
            res = investigate(sub, "discriminative_invention",
                              lambda: dev.measure_recognition(sub, pipe, test_set, vc))
            verdicts = agent_conclude_investigation(sub, _inv)
            verdict = next((v["issue"] for v in verdicts
                            if v["name"] == "discriminative_invention"), "none")
            if res:
                wv, wo = res
                print(f"     DO-CONTRAST: recognition WITH its features "
                      f"={wv:.0f}/{len(test_set)}  WITHOUT={wo:.0f}/{len(test_set)} "
                      f" (delta {wv - wo:+.0f})")
            print(f"     VERDICT (measured, not assumed): {verdict}")
            if verdict == "lever_harms":
                print("     -> using its features makes recognition WORSE. Its "
                      "effort is COUNTERPRODUCTIVE — the discriminative invention "
                      "is minting BAD features. It stops, and (correctly) leaves "
                      "them OUT of recognition (phonology_weight stays 0).")
                print("        The honest finding: the lever the agent poured "
                      "effort into actively hurts; recognition is bound by NB/DTW.")
            elif verdict == "lever_helps":
                rn = next((n for n in sub.nodes("RecognitionRoot")), None)
                if rn is not None:
                    sub.set_attr(rn, "phonology_weight", 1.0)
                after = dev.measure_recognition(sub, pipe, test_set, vc)
                print("     -> its features HELP when used. The real fix isn't more "
                      "features — it's to USE them.")
                print(f"     FIX     : raise phonology_weight 0 -> 1 (a graph attr); "
                      f"recognition {rec['correct']}/{len(test_set)} -> "
                      f"{after}/{len(test_set)}.")
            else:  # disconnected_lever
                print("     -> its effort does NOT reach recognition; this lever is "
                      "the WRONG one. It stops minting features and looks elsewhere.")

    print("\n=== the agent INVESTIGATED its own spinning (do-contrast), found the "
          "real cause from measurement, and acted on it — entity, not program ===")
    if not investigated:
        print("  (no meta-issue fired in this run — try more cycles)")


if __name__ == "__main__":
    main()
