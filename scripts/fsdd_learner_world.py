"""Small learner world — FSDD digits.

Tight vocabulary (10 words: zero through nine), tight utterances
(~0.5s each, one digit per file), 6 speakers. The ideal sandbox
for stressing the substrate's full loop:

  - teach: each (audio, digit) pair grounds every produced sign
    to the digit's Concept and bumps vote counts.
  - recognise: held-out audio → predicted digit via vote majority.
    Compute classification accuracy + per-digit confusion.
  - self-coherence: substrate SPEAKS each of the 10 digits via
    the bidirectional lexicon → we feed the synthesised audio
    BACK into the recogniser. Does it recognise what it just
    said? This is the substrate's "self-consistency" check.

Reports: train wall, recognition accuracy, confusion matrix,
self-coherence accuracy.
"""
import argparse
import os
import re
import sys
import time
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key


DATA_DIR = '/tmp/fsdd/recordings'
_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five',
            'six', 'seven', 'eight', 'nine']
_FN_RE = re.compile(r'(\d)_([a-z]+)_(\d+)\.wav')


def load_wav(path):
    with wave.open(path, 'rb') as w:
        fs = w.getframerate()
        n = w.getnframes()
        buf = w.readframes(n)
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr * 0.7 / peak).astype(np.float32), fs


def gather_files(limit=None):
    out = []
    for fn in sorted(os.listdir(DATA_DIR)):
        m = _FN_RE.match(fn)
        if not m:
            continue
        digit, speaker, idx = m.groups()
        out.append((os.path.join(DATA_DIR, fn),
                      int(digit), speaker, int(idx)))
    return out[:limit] if limit else out


def _collect_signs_from_stream(sub, stream):
    """All AcousticSigns heard_as'd by Utterances on this stream.
    Includes compositional signs once the chunking compose rule
    has fired (which happens after sub.tick())."""
    out: list = []
    for utt in sub.in_neighbours(stream, "from_stream"):
        if sub.node(utt)["type"] != "Utterance":
            continue
        for s in sub.neighbours(utt, "heard_as"):
            out.append(s)
    return out


def teach_one(sub, pipe, samples, word, vote_counts):
    # Ingest produces base Utterances + signs. We tick BEFORE
    # grounding so compose_utterance can mint compositional
    # Utterances; then ground every sign (base + compositional)
    # to the word. Without the tick, compositional signs never
    # get grounded and we miss the chunking layer's word-specific
    # units at recognition time.
    pipe.ingest(sub, samples)
    sub.tick(50000)
    # Re-collect signs from the latest stream so compositional
    # ones (minted by compose_utterance) are included.
    latest_stream = None
    for s in sub.nodes("AudioStream"):
        latest_stream = s  # last in iter; AudioStreams are append-only
    signs = _collect_signs_from_stream(sub, latest_stream)
    if not signs:
        return 0
    nid = None
    for c in sub.nodes("Concept"):
        if sub.node(c)["attrs"].get("name") == word:
            nid = c
            break
    if nid is None:
        nid = sub.add_node("Concept", {"name": word,
                                          "origin": "fsdd_learner"})
    from substrate_rs import speech as _sp
    rust_sub = sub._inner if hasattr(sub, "_inner") else sub
    n_grounded = 0
    for sign in signs:
        key = (_node_sort_key(sign), word)
        vote_counts[key] = vote_counts.get(key, 0) + 1
        if nid not in list(sub.neighbours(sign, "denotes")):
            _sp.ground_sign(rust_sub, sign, nid)
            n_grounded += 1
    # Cross-cortex signal moved into SpeechCortex's
    # `phonology_propagate` reflex (K). The world adapter no
    # longer touches pending_intent; the cortex observes the new
    # denotes-edges and propagates the grounding event itself.
    return n_grounded


def predict_one(sub, pipe, samples, vote_counts,
                  phonology_weight: float | None = None):
    """Predict the digit-word for one audio. Two evidence streams:

    1. Naive-Bayes over per-sign vote-count distributions (the
       observation-trained DTW-cluster lookup):
         score_NB(w) = Σ_s log P(w | s)
    2. Phonological likelihood under each word's learned signature
       (the understanding side):
         score_phon(w) = Σ_s Σ_p Bernoulli-log-likelihood

    Blend: score(w) = score_NB(w) + phonology_weight * score_phon(w).

    With phonology_weight=0 (default), behaviour is identical to
    pure NB. >0 mixes the concept-level evidence in.
    """
    import math
    # phonology_weight is read from the graph (RecognitionRoot) when not
    # overridden, so the meta-monitor's do-contrast can toggle it as a graph attr.
    if phonology_weight is None:
        phonology_weight = 0.0
        for _rn in sub.nodes("RecognitionRoot"):
            phonology_weight = float(sub.node(_rn)["attrs"].get(
                "phonology_weight", 0.0))
            break
    pipe.ingest(sub, samples)
    sub.tick(50000)
    latest_stream = None
    for s in sub.nodes("AudioStream"):
        latest_stream = s
    signs = _collect_signs_from_stream(sub, latest_stream)
    if not signs:
        return None

    # Build per-sign vote distribution once (small).
    per_sign: dict = {}
    for (sign_key, word), cnt in vote_counts.items():
        d = per_sign.setdefault(sign_key, {})
        d[word] = d.get(word, 0) + cnt
    # Smoothing constant — keeps unseen words from log(0).
    smooth = 0.5

    score: dict[str, float] = {}
    for sign in signs:
        sk = _node_sort_key(sign)
        sign_votes = per_sign.get(sk)
        if not sign_votes:
            continue
        is_composed = bool(sub.node(sign)["attrs"].get("composed",
                                                            False))
        weight = 1.5 if is_composed else 1.0
        # Normalise: P(word|sign) = (count + smooth) / (total + smooth*V)
        total = sum(sign_votes.values())
        vocab = max(len(sign_votes), 1)
        denom = float(total + smooth * vocab)
        for word, c in sign_votes.items():
            p = (c + smooth) / denom
            score[word] = score.get(word, 0.0) + weight * math.log(p)
    if phonology_weight > 0.0:
        # Tag the freshly heard signs with phonology concepts so
        # the signature scoring layer sees their `exhibits` edges.
        # Q: prefer position-aware scoring when per-position
        # signatures exist; fall back to bag-of-features
        # otherwise.
        from domains.phonology import (
            classify_signs, score_signs_by_phonology,
            score_signs_by_position_phonology,
        )
        # If the agent has COMPOSED its own features (peak/formant or generated),
        # run those Term-trees on the observed signs so they exhibit them too —
        # the agent's own programs execute on the obs via the substrate evaluator.
        if any(sub.node(c)["attrs"].get("feature_kind") in ("peak", "generated")
               for c in sub.nodes("Concept")):
            from domains.acoustic_resolution import enrich_sign_bands
            from domains.feature_generator import evaluate_composed_features
            enrich_sign_bands(sub, signs=signs)
            evaluate_composed_features(sub, signs=signs)
        classify_signs(sub)
        # Use position signatures if any word has them.
        has_position_sigs = False
        for c in sub.nodes("Concept"):
            a = sub.node(c)["attrs"]
            if a.get("origin") == "phonology":
                continue
            if any(k.startswith("first_marker_prob_")
                       or k.startswith("last_marker_prob_")
                       for k in a):
                has_position_sigs = True
                break
        if has_position_sigs:
            phon_scores = score_signs_by_position_phonology(
                sub, signs)
        else:
            phon_scores = score_signs_by_phonology(sub, signs)
        for word, ll in phon_scores.items():
            score[word] = score.get(word, 0.0) + phonology_weight * ll
    if not score:
        return None
    # Route through the agent's DEPLOYED recogniser if it authored + compiled one
    # (no-op otherwise). It breaks confused top-2 pairs with the learned per-pair
    # feature — the agent's own authored fix for the global-signature limit.
    try:
        from domains import deployed_recogniser
        deployed_recogniser.apply(sub, score, signs)
    except Exception:
        pass
    return max(score.items(), key=lambda kv: kv[1])[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--test_speakers', nargs='+',
                        default=['jackson'])
    parser.add_argument('--report_every', type=int, default=200)
    parser.add_argument('--passes', type=int, default=1,
                        help='number of training passes; >1 re-trains '
                             'against the populated lexicon (HuBERT-style)')
    parser.add_argument('--distance_threshold', type=float, default=None,
                        help='override DTW distance threshold')
    parser.add_argument('--refine_merge_distance', type=float, default=0.06,
                        help='lexicon refinement merge distance; '
                             'set to 0 to skip refinement entirely')
    parser.add_argument('--delta_order', type=int, default=0,
                        help='augment trajectory frames with k derivative '
                             'channels (0=raw, 1=raw+Δ, 2=raw+Δ+ΔΔ)')
    parser.add_argument('--phonology', action='store_true',
                        help='install the phonology Microtheory + '
                             'classify signs by acoustic concepts after '
                             'training')
    parser.add_argument('--phonology_weight', type=float, default=0.0,
                        help='weight on the phonological likelihood '
                             'during recognition (added to NB log-score)')
    parser.add_argument('--llm_teacher', action='store_true',
                        help='install LLM-curated (or expert-fallback) '
                             'per-position phonology signatures for '
                             'each digit before recognition')
    parser.add_argument('--save_session', type=str, default=None,
                        help='after training, save substrate state + '
                             'cortex manifest to this path prefix '
                             '(creates <path>.graph.json + '
                             '<path>.session.json)')
    parser.add_argument('--resume_session', type=str, default=None,
                        help='resume from a previously-saved session '
                             '(<path> prefix). Skips training; just '
                             'loads + runs recognition.')
    args = parser.parse_args()

    files = gather_files(args.limit)
    speakers = sorted(set(f[2] for f in files))
    test_set = set(args.test_speakers)
    train = [f for f in files if f[2] not in test_set]
    test = [f for f in files if f[2] in test_set]
    print(f'speakers:  {speakers}')
    print(f'test speakers: {sorted(test_set)}')
    print(f'train: {len(train)} files from '
          f'{len(speakers) - len(test_set)} speakers')
    print(f'test:  {len(test)} files\n')

    sub = Substrate()
    # FSDD is 8 kHz mono — match sample rate so the cochlear bands
    # cover an appropriate range.
    pipe = STTPipeline(STTParams(sample_rate=8000))

    if args.resume_session is not None:
        # Resume from a saved session — load graph state +
        # rehydrate cortices. The pipe is still constructed
        # fresh because it's stateless; the lexicon lives in the
        # graph and gets loaded back.
        from domains.cortex_persistence import load_session
        loaded = load_session(sub, args.resume_session, pipe=pipe)
        pipe.attach(sub)
        speech_cortex = loaded.get("speech")
        intent_cortex = loaded.get("intent")
        motor_cortex = loaded.get("motor")
        scheduler = loaded.get("scheduler")
        print(f'resumed session from {args.resume_session}:')
        print(f'  cortices: speech={speech_cortex is not None} '
              f'intent={intent_cortex is not None} '
              f'motor={motor_cortex is not None}')
        n_signs = len(pipe.lexicon(sub))
        n_concepts = sum(1 for c in sub.nodes("Concept")
                            if sub.node(c)["attrs"].get("origin")
                                not in ("phonology",
                                          "phonology_variant"))
        print(f'  lexicon signs: {n_signs}, word concepts: '
              f'{n_concepts}')
        # Skip the training block — jump straight to recognition.
        vote_counts = {}  # vote_counts isn't persisted; recognition
                           # uses signs' denotes-edges instead via
                           # NB on per-sign top word.
        # Rebuild vote_counts from the persisted graph: for each
        # AcousticSign that denotes a word concept, register a
        # vote in proportion to its `hearings` attr.
        for s in pipe.lexicon(sub):
            a = sub.node(s)["attrs"]
            hearings = int(a.get("hearings", 1))
            for c in sub.neighbours(s, "denotes"):
                cname = sub.node(c)["attrs"].get("name")
                if cname:
                    key = (_node_sort_key(s), cname)
                    vote_counts[key] = vote_counts.get(key, 0) + hearings
        # Skip the training section by jumping to recognition.
        # The control flow below is structured around the training
        # block; the simplest fix: re-run with the loaded state
        # and the training loop becomes a no-op when train is empty.
        train = []  # makes the training loop iterate 0 times
    else:
        pipe.attach(sub)
        pipe._ensure_audio_pipeline(sub)
        if args.distance_threshold is not None or args.delta_order > 0:
            for op in sub.nodes("Operation"):
                if sub.node(op)["attrs"].get("kind") == "lexical_access":
                    if args.distance_threshold is not None:
                        sub.set_attr(op, "distance_threshold",
                                      float(args.distance_threshold))
                        print(f'distance_threshold override -> '
                              f'{args.distance_threshold}',
                              flush=True)
                    if args.delta_order > 0:
                        sub.set_attr(op, "delta_order", int(args.delta_order))
                        print(f'delta_order -> {args.delta_order}', flush=True)
                    break

    # Phonology cortices register early so they pulse alongside
    # training. The master clock is wall time (time.monotonic) so
    # cortex periods are real-world ms, not synthetic ticks.
    # Resume path may have already bound these. Only initialise
    # to None if the names aren't defined.
    if 'speech_cortex' not in dir():
        speech_cortex = None
    if 'intent_cortex' not in dir():
        intent_cortex = None
    if 'motor_cortex' not in dir():
        motor_cortex = None
    if 'scheduler' not in dir():
        scheduler = None
    if (args.resume_session is None
            and (args.phonology or args.phonology_weight > 0.0)):
        from domains.speech_cortex import SpeechCortex
        from domains.intent_cortex import IntentCortex
        from domains.motor_cortex import MotorCortex
        from domains.cortex_scheduler import CortexScheduler
        speech_cortex = SpeechCortex(sub, lexicon_name="stt",
                                          tick_period_ms=2000).install()
        intent_cortex = IntentCortex(sub,
                                          tick_period_ms=1000).install()
        # Synthesiser closure binds the pipe + substrate so the
        # cortex only needs to know about words.
        def _synth(word):
            try:
                return pipe.speak(sub, word, duration_s=0.4)
            except Exception:
                return None
        def _re_ingest(audio):
            # Self-monitor: feed the motor's audio back to the
            # speech pipeline. The lexicon is FROZEN during this
            # ingest so the agent's self-audio matches against
            # existing signs WITHOUT minting new ones or updating
            # the EMA-running trajectories. Self-perception
            # without polluting the external-lexicon's learned
            # state — biologically analogous to a separate
            # endophonic pathway (Broca's vs Wernicke's).
            pipe.set_frozen(sub, True)
            try:
                pipe.ingest(sub, audio)
                sub.tick(50000)
            finally:
                pipe.set_frozen(sub, False)
        motor_cortex = MotorCortex(sub, synthesise=_synth,
                                         re_ingest=_re_ingest,
                                         tick_period_ms=500).install()
        scheduler = CortexScheduler()
        scheduler.register(speech_cortex)
        scheduler.register(intent_cortex)
        scheduler.register(motor_cortex)
        # Teach textbook signatures before training starts so the
        # cortex's investigate/analyse layers have something to
        # contrast against.
        speech_cortex.teach("zero", {
            "voicing": 0.7, "sibilant": 0.5, "sonorant": 0.6,
            "formant_present": 0.6, "noise_burst": 0.4,
        })
        speech_cortex.teach("six", {
            "voicing": 0.5, "sibilant": 0.4, "sonorant": 0.5,
            "formant_present": 0.5, "noise_burst": 0.6,
        })

    print('--- training ---', flush=True)
    t0 = time.time()
    if 'vote_counts' not in dir():
        vote_counts: dict = {}
    grounded = 0
    n_cortex_fires = 0
    for i, (path, digit, sp, idx) in enumerate(train):
        samples, fs = load_wav(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs))
            pipe.attach(sub)
        word = _DIGITS[digit]
        grounded += teach_one(sub, pipe, samples, word, vote_counts)
        sub.tick(50000)
        if scheduler is not None:
            # Advance the master clock to current wall time. Each
            # cortex fires on its own period; pending-work
            # interrupts wake the relevant cortex.
            now_ms = int((time.time() - t0) * 1000)
            fires = scheduler.advance(now_ms=now_ms,
                                            vote_counts=vote_counts)
            for v in fires.values():
                n_cortex_fires += v["fires"]
        if (i + 1) % args.report_every == 0:
            n_signs = sum(1 for _ in sub.nodes('AcousticSign'))
            n_concepts = sum(1 for _ in sub.nodes('Concept'))
            cortex_note = ""
            if scheduler is not None:
                cortex_note = (f'  cortex_fires={n_cortex_fires}')
            print(f'  train {i+1}/{len(train)}  signs={n_signs}  '
                  f'concepts={n_concepts}  grounded_total={grounded}'
                  f'{cortex_note}  '
                  f'{(i+1) / (time.time() - t0):.1f} files/sec',
                  flush=True)
    train_wall = time.time() - t0
    print(f'\ntraining done: {train_wall:.1f}s, '
          f'cortex_fires_during_training={n_cortex_fires}\n')

    if args.save_session and scheduler is not None:
        from domains.cortex_persistence import save_session
        cortex_objs = [c for c in (speech_cortex, intent_cortex,
                                          motor_cortex) if c is not None]
        info = save_session(sub, args.save_session,
                                cortex_objs=cortex_objs)
        print(f'session saved:')
        print(f'  graph:   {info["graph_path"]} '
              f'({info["graph_size"]/1024:.1f} KB)')
        print(f'  session: {info["session_path"]} '
              f'({info["n_cortices"]} cortices)\n')

    # HuBERT-style pass-2: re-process training audio against the
    # populated lexicon. The matcher's running-mean updates refine
    # each sign's trajectory; vote counts reset so per-sign
    # word distributions reflect the converged lexicon (not the
    # alphabetic-order training bias of pass 1).
    if args.passes > 1:
        print(f'--- pass 2 (frozen-lexicon re-vote) ---', flush=True)
        # Freeze the lexicon: the Rust matcher always reuses the
        # closest existing sign, never mints. Same threshold as
        # pass 1 — frozen mode honours best-match regardless of
        # distance. The original `frozen` attr is graph data; the
        # agent could flip it via a Rule just as well.
        pipe.set_frozen(sub, True)
        vote_counts.clear()
        for i, (path, digit, sp, idx) in enumerate(train):
            samples, fs = load_wav(path)
            word = _DIGITS[digit]
            teach_one(sub, pipe, samples, word, vote_counts)
            sub.tick(50000)
            if (i + 1) % args.report_every == 0:
                n_signs = sum(1 for _ in sub.nodes('AcousticSign'))
                print(f'  pass2 {i+1}/{len(train)}  signs={n_signs}',
                      flush=True)
        # Unfreeze for the test phase. Test-time matching uses the
        # configured distance_threshold; frozen would force a
        # best-match-always even on noise, which is wrong for test.
        pipe.set_frozen(sub, False)

    # Iterative-refinement pass — HuBERT-style. Merge sign pairs
    # the in-streaming threshold left as separate but with
    # matching top-voted words. merge_distance should be ~2-3×
    # the in-streaming threshold; too loose merges genuinely
    # distinct signs.
    if args.refine_merge_distance > 0:
        refine_info = pipe.refine_lexicon(
            sub, vote_counts=vote_counts,
            merge_distance=args.refine_merge_distance,
        )
        print(f'lexicon refine: merged {refine_info["merged"]} pairs '
              f'({refine_info["before"]} → {refine_info["after"]} signs)',
              flush=True)

    use_phonology = args.phonology or args.phonology_weight > 0.0
    if use_phonology:
        from domains.speech_cortex import SpeechCortex
        from domains.phonology import (
            classify_signs, signs_by_concept, learn_word_signatures,
        )
        print('\n--- cortex flush to quiescence (wall-clock driven) ---',
                flush=True)
        # The cortices have been pulsing in real time alongside
        # training. Final flush: drive the master clock with
        # wall-clock time + 5ms real sleeps until no cortex has
        # pending work AND nothing fires.
        flush_t0 = time.time()
        quiescent_passes = 0
        flush_iters = 0
        while flush_iters < 400:
            now_ms = int((time.time() - t0) * 1000)
            f = scheduler.advance(now_ms=now_ms,
                                       vote_counts=vote_counts)
            flush_iters += 1
            any_pending = any(c.has_pending_work(
                vote_counts=vote_counts)
                for c in scheduler.registered())
            total_fires = sum(v["fires"] for v in f.values())
            if not any_pending and total_fires == 0:
                quiescent_passes += 1
                if quiescent_passes >= 3:
                    break
            else:
                quiescent_passes = 0
            time.sleep(0.005)
        flush_wall = time.time() - flush_t0
        print(f'  flush converged in {flush_iters} iterations / '
              f'{flush_wall*1000:.0f}ms wall')
        print(f'  scheduler status:')
        for st in scheduler.status():
            print(f'    {st["type"]:<14s} '
                  f'period={st["period_ms"]}ms '
                  f'next={st["next_fire_ms"]}ms '
                  f'fires_total={st["n_fires_total"]}')
        irep = intent_cortex.report()
        print(f'  intent cortex: {irep["n_intents_total"]} '
              f'intents minted total, '
              f'tick_count={irep["tick_count"]}, '
              f'wake_count={irep["wake_count"]}')
        if motor_cortex is not None:
            mrep = motor_cortex.report()
            print(f'  motor cortex: {mrep["n_plans_total"]} '
                  f'utterance plans minted, '
                  f'tick_count={mrep["tick_count"]}, '
                  f'wake_count={mrep["wake_count"]}')
            top_words = sorted(mrep["word_histogram"].items(),
                                  key=lambda kv: -kv[1])[:5]
            preview = ', '.join(f'{w}={n}'
                                    for w, n in top_words)
            print(f'    planned utterances: {preview}')

            # Self-coherence: of the signs MotorCortex produced
            # by re-ingesting its own audio, how many landed on a
            # sign denoting the same word the motor was trying to
            # say? "I said X and heard X" = coherent.
            coherent = 0
            incoherent = 0
            for s in sub.nodes("AcousticSign"):
                a = sub.node(s)["attrs"]
                if not a.get("from_self_motor", False):
                    continue
                expected = a.get("self_word")
                # Each self-sign should be matched against the
                # lexicon entries denoting `expected`. The lexical
                # matcher updates an existing sign if the audio
                # falls within distance_threshold, so the simplest
                # check: does this sign carry a `denotes` edge to
                # Concept(expected)?
                denoted_names = [
                    sub.node(c)["attrs"].get("name")
                    for c in sub.neighbours(s, "denotes")
                ]
                if expected in denoted_names:
                    coherent += 1
                else:
                    incoherent += 1
            total_self = coherent + incoherent
            if total_self:
                pct = 100.0 * coherent / total_self
                print(f'    self-coherence: {coherent}/'
                      f'{total_self} = {pct:.1f}% '
                      f'(I said the word AND heard a sign that '
                      f'denotes it)')
        cortex = speech_cortex

        rep = cortex.report()
        counts = classify_signs(sub)
        signatures = learn_word_signatures(sub, vote_counts)
        # H: sequence-level signatures — per-word first/last
        # position phonology exhibition probabilities.
        from domains.phonology import learn_sequence_signatures
        seq_sigs = learn_sequence_signatures(sub)

        # T: optional LLM/expert teacher overrides the learned
        # per-position signatures with curated phonology
        # knowledge.
        if args.llm_teacher:
            from domains.phonology_teacher import PhonologyTeacher
            try:
                from domains.llm_partner import LLMPartner
                llm = LLMPartner()
                if not llm.is_available():
                    llm = None
            except Exception:
                llm = None
            teacher = PhonologyTeacher(llm_partner=llm)
            outcome = teacher.teach(sub, list(_DIGITS))
            print(f'\n  phonology teacher: '
                  f'source={outcome["source"]}, '
                  f'taught {outcome["n_words_taught"]} words '
                  f'({outcome["n_positions_taught"]} positions)')

            # Post-teaching cortex flush — the per-position
            # signatures just changed; the cortex's hook-driven
            # wake routing detects this and the autopoietic loop
            # re-runs detect/investigate/analyse/act on the new
            # taught signatures. Predicate_too_lenient hypotheses
            # should mint where the agent's observation
            # disagrees with the textbook (e.g. voicing fires on
            # seven's /s/ onset).
            if scheduler is not None:
                t_flush = time.time()
                quiescent_passes = 0
                flush_iters_after = 0
                pre_hypotheses = sum(
                    1 for h in sub.nodes("MismatchHypothesis"))
                pre_impasses = sum(
                    1 for i in sub.nodes("Impasse"))
                while flush_iters_after < 200:
                    now_ms = int((time.time() - t0) * 1000)
                    f = scheduler.advance(now_ms=now_ms,
                                               vote_counts=vote_counts)
                    flush_iters_after += 1
                    any_pending = any(c.has_pending_work(
                        vote_counts=vote_counts)
                        for c in scheduler.registered())
                    total_fires = sum(v["fires"]
                                          for v in f.values())
                    if not any_pending and total_fires == 0:
                        quiescent_passes += 1
                        if quiescent_passes >= 3:
                            break
                    else:
                        quiescent_passes = 0
                    time.sleep(0.005)
                post_hyps = sum(
                    1 for h in sub.nodes("MismatchHypothesis"))
                post_imps = sum(
                    1 for i in sub.nodes("Impasse"))
                fl_dt = time.time() - t_flush
                print(f'  post-teaching flush: '
                      f'{flush_iters_after} iters / '
                      f'{fl_dt*1000:.0f}ms, '
                      f'impasses {pre_impasses}→{post_imps}, '
                      f'hypotheses {pre_hypotheses}→{post_hyps}')
                # Show which predicate thresholds shifted as a
                # result of the autopoietic loop closing on the
                # taught signatures.
                print(f'  predicate thresholds after autopoietic '
                      f'close:')
                for cname in ("voicing", "sibilant", "sonorant",
                                "formant_present", "noise_burst"):
                    for c in sub.nodes("Concept"):
                        ca = sub.node(c)["attrs"]
                        if (ca.get("origin") == "phonology"
                                and ca.get("name") == cname):
                            print(f'    {cname:<18s} '
                                  f'threshold={ca.get("threshold")}')
                            break
            # Re-pull seq_sigs from the graph so the report
            # shows the taught values.
            seq_sigs = {}
            for c in sub.nodes("Concept"):
                a = sub.node(c)["attrs"]
                if (a.get("origin") == "phonology"
                        or a.get("origin") == "phonology_variant"):
                    continue
                wname = a.get("name")
                if not wname:
                    continue
                pos_data = {}
                for position in ("first", "last"):
                    sig = {}
                    for pn in ("voicing", "sibilant", "sonorant",
                                  "formant_present", "noise_burst"):
                        key = f"{position}_marker_prob_{pn}"
                        if key in a:
                            sig[pn] = float(a[key])
                    if sig:
                        pos_data[position] = sig
                if pos_data:
                    seq_sigs[wname] = pos_data
        if seq_sigs:
            print(f'\n  sequence signatures (first/last position):')
            for w in sorted(seq_sigs):
                first = seq_sigs[w].get("first", {})
                last_ = seq_sigs[w].get("last", {})
                if not first and not last_:
                    continue
                top_first = sorted(first.items(),
                                          key=lambda kv: -kv[1])[:3]
                top_last = sorted(last_.items(),
                                         key=lambda kv: -kv[1])[:3]
                fst = ', '.join(f'{p}={pr:.2f}'
                                   for p, pr in top_first
                                   if pr > 0.05)
                lst = ', '.join(f'{p}={pr:.2f}'
                                   for p, pr in top_last
                                   if pr > 0.05)
                print(f'    {w:<8s} first: {fst or "(none)"}')
                print(f'           last:  {lst or "(none)"}')
        total_signs = rep["n_signs"]
        print(f'  signs in lexicon:     {total_signs}')
        print(f'  concepts (exhibits counts):')
        for name in ('voicing', 'sonorant', 'formant_present',
                       'sibilant', 'noise_burst'):
            n = counts.get(name, 0)
            pct = (100.0 * n / total_signs) if total_signs else 0.0
            print(f'    {name:<18s} {n:>4d}  ({pct:5.1f}%)')
        # Cross-tabulate concept exhibition × top-voted word.
        # For each concept, show the word distribution of signs that
        # exhibit it — answers "what does the agent think a sibilant
        # sounds like in word-terms?"
        print(f'\n  concept × word breakdown:')
        # Resolve phonology concept NodeIDs by name from the graph
        # (the cortex owns them; we don't carry a dict).
        info_by_name = {
            sub.node(c)["attrs"].get("name"): c
            for c in sub.nodes("Concept")
            if sub.node(c)["attrs"].get("origin") == "phonology"
        }
        for cname in ('voicing', 'sibilant', 'sonorant',
                        'formant_present', 'noise_burst'):
            cid = info_by_name.get(cname)
            if cid is None:
                continue
            sign_ids = list(sub.in_neighbours(cid, 'exhibits'))
            word_hist: dict = {}
            for s in sign_ids:
                # vote_counts is keyed by (sort_key, word). Find the
                # word with most votes for this sign.
                sk = _node_sort_key(s)
                per_sign = {w: c for (k, w), c in vote_counts.items()
                              if k == sk}
                if not per_sign:
                    continue
                top = max(per_sign.items(), key=lambda kv: kv[1])[0]
                word_hist[top] = word_hist.get(top, 0) + 1
            top_words = sorted(word_hist.items(),
                                  key=lambda kv: -kv[1])[:5]
            preview = ', '.join(f'{w}={n}' for w, n in top_words)
            print(f'    {cname:<18s} → {preview or "(no voted signs)"}')
        print(f'\n  word phonological signatures:')
        for w in sorted(signatures):
            sig = signatures[w]
            top = sorted(sig.items(), key=lambda kv: -kv[1])[:4]
            preview = ', '.join(f'{p}={pr:.2f}' for p, pr in top)
            print(f'    {w:<8s} → {preview}')

        # Surface the agent's converged state after the autonomous
        # Reflex loop has run.
        print(f'\n  final concept thresholds (agent-tuned):')
        for cname in ("voicing", "sibilant", "sonorant",
                        "formant_present", "noise_burst"):
            for c in sub.nodes("Concept"):
                ca = sub.node(c)["attrs"]
                if (ca.get("origin") == "phonology"
                        and ca.get("name") == cname):
                    thr = ca.get("threshold")
                    dflt = ca.get("threshold_min")  # not the init; just bound
                    n_ex = counts.get(cname, 0)
                    print(f'    {cname:<18s} threshold={thr}  '
                          f'exhibits={n_ex}')
                    break

        n_impasses = sum(1 for i in sub.nodes("Impasse")
                            if sub.node(i)["attrs"].get("kind")
                                == "phonology_divergence")
        n_resolved = sum(1 for i in sub.nodes("Impasse")
                            if sub.node(i)["attrs"].get("kind")
                                == "phonology_divergence"
                            and sub.node(i)["attrs"].get("investigated"))
        n_hyps = sum(1 for h in sub.nodes("MismatchHypothesis")
                        if sub.node(h)["attrs"].get("origin")
                            == "phonology")
        n_acted = sum(1 for h in sub.nodes("MismatchHypothesis")
                         if sub.node(h)["attrs"].get("origin")
                             == "phonology"
                         and sub.node(h)["attrs"].get("acted"))
        n_variants = sum(1 for c in sub.nodes("Concept")
                            if sub.node(c)["attrs"].get("origin")
                                == "phonology_variant")
        print(f'\n  final state:')
        print(f'    impasses (total/resolved): '
              f'{n_impasses}/{n_resolved}')
        print(f'    mismatch hypotheses (total/acted): '
              f'{n_hyps}/{n_acted}')
        print(f'    variants minted: {n_variants}')
        print('', flush=True)

    print('\n--- recognition (held-out) ---', flush=True)
    t0 = time.time()
    correct = 0
    total = 0
    confusion: dict[tuple[str, str], int] = {}
    for path, digit, sp, idx in test:
        samples, fs = load_wav(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs))
            pipe.attach(sub)
        ref = _DIGITS[digit]
        hyp = predict_one(sub, pipe, samples, vote_counts,
                              phonology_weight=args.phonology_weight) or '[?]'
        confusion[(ref, hyp)] = confusion.get((ref, hyp), 0) + 1
        if hyp == ref:
            correct += 1
        total += 1
    test_wall = time.time() - t0
    print(f'test wall: {test_wall:.1f}s  acc: {correct}/{total} = '
          f'{correct / max(total, 1):.3f}\n', flush=True)

    print('--- self-coherence (substrate speaks → hears itself) ---',
            flush=True)
    coherent = 0
    coherent_total = 0
    coherence_results = []
    for digit_word in _DIGITS:
        audio = pipe.speak(sub, digit_word, duration_s=0.5)
        if np.abs(audio).max() < 0.01:
            coherence_results.append((digit_word, '[silent]'))
            coherent_total += 1
            continue
        # Feed it back into the recogniser.
        hyp = predict_one(sub, pipe, audio, vote_counts) or '[?]'
        coherence_results.append((digit_word, hyp))
        if hyp == digit_word:
            coherent += 1
        coherent_total += 1

    print('\n===============================================')
    print('FSDD learner world — final')
    print('===============================================')
    print(f'training files:    {len(train)}')
    print(f'training wall:     {train_wall:.1f}s')
    print(f'test files:        {total}')
    print(f'recognition acc:   {correct}/{total} = '
          f'{correct / max(total, 1):.3f}')
    print()
    print('confusion matrix (rows ref / cols hyp, top-1 entries):')
    digit_names = _DIGITS + ['[?]']
    print('       ' + ''.join(f'{n[:5]:>6}' for n in digit_names))
    for ref in _DIGITS:
        row = []
        for hyp in digit_names:
            row.append(f'{confusion.get((ref, hyp), 0):>6}')
        print(f'{ref[:6]:>6} ' + ''.join(row))
    print()
    print('self-coherence (says → hears):')
    for spoken, heard in coherence_results:
        flag = ' ✓' if spoken == heard else ' ✗'
        print(f'  {spoken:>6} → {heard:>6}{flag}')
    print(f'self-coherence:    {coherent}/{coherent_total} = '
          f'{coherent / max(coherent_total, 1):.3f}')


if __name__ == "__main__":
    main()
