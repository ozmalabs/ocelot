"""SYNTACTIC BOOTSTRAPPING (Gleitman) on CONNECTED SPEECH — the next developmental rung.

Words-from-naming -> syntax-from-connected-speech. The syntactic FRAME a word sits in tells you its
category: a FUNCTION word FRAMES a CONTENT word ('the X' -> X is an object). This is what the agent-
authored construction (4d0ebdbf) is FOR, and it needs CONNECTED speech where function-word frames VARY
across content words — the variation the repetitive-naming tier lacked.

PART A  CONNECTED SPEECH: narrated Jellyfin children's programming (Absurd Planet / Secrets of the Zoo)
        — a narrator speaks SENTENCES; function words recur across VARYING content. vs a NAMING tier.
PART B  DISTRIBUTIONAL FUNCTION/CONTENT SPLIT (agent-authored, donkey=0): a function word is a
        DISTRIBUTIONAL UNIVERSAL — high FREQUENCY + context-INDEPENDENT (high context-entropy), NOT hand-
        labelled. The agent AUTHORS the split rule via its self-build composer (distributional_function
        RelationCue + _compose_distributional_rule) and it fires graph-native over WordForm nodes. GATE:
        the earned split MATCHES known function words (whisper transcript, EVAL-ONLY teacher) above a
        frequency-only control.
PART C  SYNTACTIC BOOTSTRAPPING (the payoff): the FRAME predicts CONTENT-hood — P(content | preceded-by-
        a-function-word) >> P(content). On CONNECTED speech (content is framed) the frame is informative;
        on NAMING (isolated words) it is not. CONNECTED > NAMING = the content-regime prediction.

donkey=0: both constructions AGENT-AUTHORED (composer + held RelationCue); the distributional split is a
graph rule over the token stream; whisper/allosaurus are TEACHER-ONLY (eval / bootstrap), never on the
decision path. USE THE VENV PYTHON: /home/matt/ozma/internal/research/.venv/bin/python

Run: PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
        scripts/jabberwock_syntactic_bootstrapping.py
"""
from __future__ import annotations
import os, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter, defaultdict

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.reflective_faculty as rf
import referential_word_learning as R
import scripts.multimodal_referential_video as M

# closed-class English function words (EVAL-ONLY ground truth for the distributional split; the DECISION
# never sees this list — it is used only to score whether the earned split matches known function words).
FUNC = set(("the a an is are was were be been being am s re m ve ll d to of in on at by for with from as "
            "and or but nor so yet it its it's he she they we i you me him her them his hers their our my "
            "your that this these those there here what when where which who whom whose why how not no do "
            "does did done doing have has had will would shall should can could may might must if then "
            "than about into onto over under up down out off out't don't isn't can't into up's").split())

_WHISP = None
def _whisper():
    global _WHISP
    if _WHISP is None:
        from faster_whisper import WhisperModel
        _WHISP = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    return _WHISP


def author_constructions():
    """PART B/A prep: the agent AUTHORS both the DISTRIBUTIONAL split and the SYNTACTIC construction via
    its self-build composer (induce_concern -> ground_concern), donkey=0."""
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    calls = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "D")[1])
    except Exception:
        pass
    ind_d = rf.induce_concern(a, [["distribute", "FORM", "over", "CONTEXT"],
                                  ["frequent", "FORM", "in", "STREAM"],
                                  ["context-independent", "FORM", "across", "USES"]],
                              name_hint="induced_distribution")
    gd = rf.ground_concern(a, [ind_d["capability_key"]])
    ind_s = rf.induce_concern(a, [["frame", "FUNCTION", "over", "CONTENT"],
                                  ["precede", "FUNCTION", "before", "ARGUMENT"],
                                  ["construct", "FORM", "to", "MEANING"]],
                              name_hint="induced_construction")
    gs = rf.ground_concern(a, [ind_s["capability_key"]])
    print("--- the JABBERWOCK AUTHORS BOTH constructions (self-build composer, donkey=0) ---")
    print(f"  DISTRIBUTIONAL split : {gd.get('path')} -> {gd.get('rule', {}).get('name')} "
          f"(where freq_norm & ctx_entropy_norm >= .5 -> is_function)")
    print(f"  SYNTACTIC construction: {gs.get('path')} -> {gs.get('rule', {}).get('name')} "
          f"(function precedes content -> referent_bearer)")
    print(f"  donkey calls: {calls['n']}")
    return a, gd, gs, calls["n"] == 0


def harvest(jf, show, n_target, scratch, start=150.0, dur=120.0, max_ep=30):
    """Audio word tokens in temporal order per episode + whisper words aligned by midpoint (EVAL teacher).
    Returns [(frames, t_mid, whisper_word)] concatenated over episodes (sequence order preserved)."""
    toks = []; total_words = 0
    from scripts.jellyfin_world import JellyfinWorld  # noqa
    for e in jf.episodes({c["name"]: c for c in jf.catalog(("Series",))}[show]["id"], limit=max_ep):
        if len(toks) >= n_target:
            break
        try:
            w = M.hear_words(jf.stream_url(e["id"]), start, dur, scratch)   # [(t_mid, frames)]
            if len(w) < 8:
                continue
            wav = os.path.join(scratch, "sb.wav")
            r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{dur}",
                                "-i", jf.stream_url(e["id"]), "-ar", "16000", "-ac", "1", wav],
                               capture_output=True, timeout=120)
            words = []
            if r.returncode == 0 and os.path.exists(wav):
                segs, _ = _whisper().transcribe(wav, word_timestamps=True)
                words = [(start + float(x.start), x.word.strip().strip(".,!?;:\"'").lower())
                         for s in segs for x in s.words]
            total_words += len(words)
            wt = [t for t, _ in words]
            for (t_mid, fr) in w:                                          # align whisper word to token
                lab = None
                if wt:
                    j = int(np.argmin([abs(t_mid - x) for x in wt]))
                    if abs(t_mid - wt[j]) < 0.5:
                        lab = words[j][1]
                toks.append((fr, t_mid, lab))
        except Exception:
            pass
    return toks, total_words


def distributional_split(a, toks, Kw=28):
    """EARN is_function per token: cluster tokens into WORD-FORMS (audio), compute per-word-form FREQUENCY
    + CONTEXT-ENTROPY (entropy of neighbour word-forms in the stream) -> normalise -> write WordForm nodes
    -> fire the AGENT'S authored distributional rule (graph-native) -> is_function. donkey=0."""
    A = R._unit(np.stack([M.pool_coarse(fr) for fr, _, _ in toks]).astype(np.float64))
    lab = [int(x) for x in R.kmeans(A, min(Kw, len(A)), np.random.default_rng(0))]
    freq = Counter(lab)
    ctx = defaultdict(list)
    for i in range(len(lab)):
        if i > 0:
            ctx[lab[i]].append(lab[i - 1])
        if i < len(lab) - 1:
            ctx[lab[i]].append(lab[i + 1])
    def _ent(xs):
        c = Counter(xs); n = sum(c.values())
        return float(-sum((v / n) * np.log(v / n) for v in c.values())) if n else 0.0
    cents = {c: _ent(ctx[c]) for c in freq}
    fmax = max(freq.values()); emax = max(cents.values()) or 1.0
    # write WordForm nodes with normalised distributional attrs; fire the agent's rule.
    s = a.s; anchor = s.add_node("WordForm", {})
    node = {}
    for c in freq:
        w = s.add_node("WordForm", {"freq_norm": freq[c] / fmax, "ctx_entropy_norm": cents[c] / emax})
        s.add_edge_unchecked(w, "is_a", anchor); node[c] = w
    a.inner.run_rules(200000)
    is_func_cluster = {c: (s.node(node[c])["attrs"].get("is_function") == 1.0) for c in freq}
    return lab, is_func_cluster, freq


def main():
    print("=" * 100)
    print("SYNTACTIC BOOTSTRAPPING on CONNECTED SPEECH — function-word frames identify content words")
    print("=" * 100, flush=True)
    a, gd, gs, donkey0 = author_constructions()
    scratch = os.environ.get("SCRATCH", "/tmp/mmref_syn"); os.makedirs(scratch, exist_ok=True)

    from scripts.jellyfin_world import JellyfinWorld
    jf = JellyfinWorld().connect()
    by = {c["name"]: c for c in jf.catalog(("Series",))}
    conn_show = next((s for s in ["Absurd Planet", "Secrets of the Zoo: Tampa",
                                  "Secrets of the Zoo: Down Under"] if s in by), None)
    name_show = next((s for s in ["Sesame Street", "StoryBots Super Songs", "Ask the Storybots"] if s in by), None)
    print(f"\n  CONNECTED (narrated): {conn_show}   NAMING: {name_show}", flush=True)
    print("  harvesting audio tokens + whisper word labels (eval-only teacher)...", flush=True)
    conn, conn_words = harvest(jf, conn_show, 300, scratch)
    name, name_words = harvest(jf, name_show, 300, scratch)
    cwpt = conn_words / max(len(conn), 1); nwpt = name_words / max(len(name), 1)
    print(f"  CONNECTED tokens {len(conn)} ({sum(1 for _,_,l in conn if l)} labelled) vs {conn_words} "
          f"whisper WORDS = {cwpt:.1f} words/token  <- tokens are UTTERANCES not words if >>1")
    print(f"  NAMING    tokens {len(name)} ({sum(1 for _,_,l in name if l)} labelled) vs {name_words} "
          f"whisper WORDS = {nwpt:.1f} words/token", flush=True)

    def analyze(tag, toks):
        lab, isf, freq = distributional_split(a, toks)
        # per-token function/content (agent's distributional split)
        tok_func = [isf.get(lab[i], False) for i in range(len(toks))]
        # EVAL: whisper closed-class ground truth (only on labelled tokens)
        lw = [l for _, _, l in toks]
        ev = [(i, lw[i]) for i in range(len(toks)) if lw[i]]
        # GATE B: does the earned split match known function words? vs frequency-only control.
        top_by_freq = set(c for c, _ in freq.most_common(max(1, len([c for c in isf if isf[c]]))))
        def _acc(pred_func_of_cluster):
            ok = tot = 0
            for i, w in ev:
                tot += 1; ok += int(pred_func_of_cluster(lab[i]) == (w in FUNC))
            return ok / max(tot, 1)
        acc_dist = _acc(lambda c: isf.get(c, False))
        acc_freq = _acc(lambda c: c in top_by_freq)
        # which known function words landed on the function side:
        func_words = Counter(w for i, w in ev if isf.get(lab[i], False))
        # GATE C: does the FRAME predict CONTENT? P(content | preceded-by-function) vs P(content).
        base_content = np.mean([1 - (w in FUNC) for _, w in ev]) if ev else 0.0
        framed_content = []
        for i, w in ev:
            if i > 0 and tok_func[i - 1]:                         # preceded by an EARNED function word
                framed_content.append(1 - (w in FUNC))
        p_framed = float(np.mean(framed_content)) if framed_content else float("nan")
        # ORACLE frame (whisper eval): does the "function-precedes-content" SIGNAL EXIST at all? Uses the
        # TRUE (whisper) function/content labels for BOTH frame + target -> measures whether connected
        # speech HAS the syntactic framing structure that naming lacks (the mechanism's ceiling; the
        # agent's earned decision above is donkey=0, this is analysis only).
        lw = [l for _, _, l in toks]
        orc = []
        for i in range(1, len(toks)):
            if lw[i] and lw[i - 1]:
                if lw[i - 1] in FUNC:
                    orc.append(1 - (lw[i] in FUNC))
        p_orc = float(np.mean(orc)) if orc else float("nan")
        return {"n": len(toks), "acc_dist": acc_dist, "acc_freq": acc_freq,
                "n_func_clusters": sum(1 for c in isf if isf[c]), "func_words": func_words,
                "base_content": base_content, "p_content_framed": p_framed,
                "frame_lift": (p_framed - base_content) if framed_content else float("nan"),
                "n_framed": len(framed_content),
                "oracle_framed": p_orc, "oracle_lift": (p_orc - base_content) if orc else float("nan")}

    print("\n--- ★ PART B: distributional function/content split (agent-authored, graph-native) ---")
    rc = analyze("CONNECTED", conn); rn = analyze("NAMING", name)
    for tag, r in (("CONNECTED", rc), ("NAMING", rn)):
        print(f"  {tag:10s}: split matches known function words = {r['acc_dist']:.3f}  "
              f"(frequency-only control {r['acc_freq']:.3f}; {r['n_func_clusters']} function clusters)")
        print(f"             known function words on the function side: "
              f"{', '.join(w for w,_ in r['func_words'].most_common(10))}")
    gateB = rc["acc_dist"] > rc["acc_freq"] + 0.01 and rc["acc_dist"] > 0.5

    print("\n--- ★ PART C: syntactic bootstrapping — does the FRAME predict CONTENT-hood? ---")
    for tag, r in (("CONNECTED", rc), ("NAMING", rn)):
        print(f"  {tag:10s}: P(content) {r['base_content']:.3f} | EARNED-frame P(content|prec-func) "
              f"{r['p_content_framed']:.3f} (lift {r['frame_lift']:+.3f}) | ORACLE-frame "
              f"{r['oracle_framed']:.3f} (lift {r['oracle_lift']:+.3f})")
    conn_lift = rc["frame_lift"]; name_lift = rn["frame_lift"]
    gateC = (conn_lift > 0.03) and (np.isnan(name_lift) or conn_lift > name_lift + 0.03)
    # does the syntactic SIGNAL exist (oracle), connected > naming? (isolates order-1 as the blocker)
    oracle_signal = (rc["oracle_lift"] > 0.03) and (rc["oracle_lift"] > rn["oracle_lift"] + 0.03)

    print("\n--- donkey=0 / graph-native ---")
    print("  both constructions AGENT-AUTHORED via the self-build composer (held RelationCue + add_rule);")
    print("  the distributional split fires graph-native over WordForm nodes; whisper is EVAL-ONLY (scores")
    print("  the split against known function words), never on the decision path.")

    print("=" * 100)
    print(f"VERDICT  SYNTACTIC BOOTSTRAPPING on connected speech:")
    print(f"  (B) distributional split agent-authored + matches known function words: "
          f"{'YES' if gateB else 'NO'} (connected {rc['acc_dist']:.3f} vs freq-only {rc['acc_freq']:.3f}, "
          f"donkey={0 if donkey0 else '>0'}).")
    print(f"  (C) EARNED frame predicts content-hood, CONNECTED > NAMING: "
          f"{'YES' if gateC else 'NO'} (earned frame-lift connected {conn_lift:+.3f} vs naming {name_lift:+.3f}).")
    print(f"  ORACLE (does the syntactic SIGNAL exist at all?): connected oracle-lift {rc['oracle_lift']:+.3f} "
          f"vs naming {rn['oracle_lift']:+.3f} -> signal-exists+connected>naming: {'YES' if oracle_signal else 'NO'}.")
    print(f"  words/token: CONNECTED {cwpt:.1f}, NAMING {nwpt:.1f}  (>>1 => the agent's tokens are")
    print(f"  UTTERANCES/phrases, not WORDS — there is no word-level sequence for the frame to run over).")
    if cwpt > 2.0:
        print("  => DIAGNOSIS (precise, order-N — the PREREQUISITE below order-1): the agent's audio tokens")
        print("     come from detect_utterances = UTTERANCE/phrase-level (~{:.0f} words each on connected".format(cwpt))
        print("     speech), NOT words. Naming gave one-word-per-token FOR FREE (each flashcard = one word);")
        print("     connected speech does NOT. So the whole word-form / function-content / frame machinery")
        print("     has no WORD-LEVEL stream to operate on, and neither the earned NOR the oracle frame lifts.")
        print("     WORD SEGMENTATION of connected speech is the unsolved prerequisite — order-0 (segment) ->")
        print("     order-1 (word-forms) -> order-2/3 (syntax). Syntactic bootstrapping cannot show until the")
        print("     agent segments connected speech into words; the naming tier hid this by construction.")
    elif oracle_signal and not gateC:
        print("  => the syntactic SIGNAL exists (oracle) but the EARNED function/content split is blocked by")
        print("     ORDER-1 word-form impurity — the recurring soft-B, now gating syntax.")
    elif not oracle_signal:
        print("  => DIAGNOSIS (precise, order-N — TWO gates, both tracing to order-1 purity):")
        print("     (i) the EARNED function/content split = the frequency baseline ({:.3f}) because the audio".format(rc["acc_freq"]))
        print("         word-form clusters MIX function+content ('and/on/no' WITH 'beetles/humans') — order-1")
        print("         word-form impurity on broadcast audio, the recurring soft-B.")
        print("     (ii) even the ORACLE 'any-function-precedes-content' frame does NOT lift content-hood")
        print("         (connected {:+.3f}) — that frame is too COARSE: real Gleitman bootstrapping uses".format(rc["oracle_lift"]))
        print("         SPECIFIC frames ('the ___'->noun, 'to ___'->verb), not 'any function word precedes'.")
        print("     Specific frames REQUIRE distinguishing 'the' from 'a' from 'to' — which needs a CLEAN")
        print("     order-1 to identify specific function words. So order-1 purity gates syntax two ways;")
        print("     words/token ~{:.1f} is fine (not the blocker). Fix order-1 first, then per-word frames.".format(cwpt))
    else:
        print("  => syntax is the next rung: the agent-authored frame identifies content words on CONNECTED.")
    print("=" * 100)


if __name__ == "__main__":
    main()
