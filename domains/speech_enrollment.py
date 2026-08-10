"""speech_enrollment — the CAREGIVER side of speech grounding.

Per CLAUDE.md's developmental ethos: the creator TEACHES the jabberwock a word
through the console (an utterance + a label), and thereafter the agent's OWN
held machinery (the `sg_denote_best_dist` / `sg_denote_ground` Rules installed
by `domains/voice_world.py`) recognises held-out utterances of that word —
no cloud ASR, no Python matcher in the loop.

This module is a world adapter (mechanical host I/O, per CLAUDE.md):

  ENROLL   ingest the caregiver's utterance through the SAME chain
           `VoiceWorld.hear()` uses (ffmpeg decode -> cochlea -> AcousticSign),
           get-or-create a Concept named after the label, `ground_sign`-style
           `denotes` edge from the resulting sign(s) to that Concept — this
           IS the ground truth (a teacher assigns it, exactly the shape
           `substrate_rs.speech.ground_sign` documents: "called separately by
           teaching code") — then persist via `teach()` (idempotent) so the
           word survives a reboot.

  PERSIST  `teach()` only appends to a seed manifest's `nodes` array; it has
           no notion of the manifest's `rules` array (genuine engine Rules,
           installed by `Substrate.load_seed_manifest` at boot — see
           substrate/seed_loader.py). This module owns that missing half
           itself (`_persist_rules`, same idempotent-JSON-write shape as
           `teach()`, applied to `rules` instead of `nodes`) rather than
           editing `domains/teach.py`.

  REHYDRATE `materialize_enrollments` turns the taught `AcousticExemplar`
           records (inert data nodes after a FRESH `load_all_seeds` boot —
           the AcousticLexicon/AcousticSign graph shape they describe is
           runtime state, not seed-loadable as such) back into a live
           AcousticSign wired into the target AcousticLexicon (`has_entry`
           + `denotes`) — the exact shape `enroll()` builds live in a
           running session, and what a checkpoint `WorldAdapter.save()`/
           `.load()` round-trip already preserves without any of this
           (it's just graph state).

RECOGNITION itself is NOT here — it is the two graph Rules
`domains.voice_world.install_recognition_rules` installs (DtwTo over the
sign's own cochlear frame trajectory, argmin-then-threshold, run by
`run_rules()`). This module only ever ADDS exemplars and their ground truth;
it never decides which exemplar a held-out sign matches.

COMPOSER NOTE: the task considered authoring `sg_denote_*` via the self-build
composer (`domains.reflective_faculty.induce_concern` -> `ground_concern`,
the `_compose_*_rule` dispatch table) instead of a hand-seeded Rule. Checked
(read-only): every `_compose_*_rule` path grounds relations through the held
`RelationCue` lexicon (`seeds/relation_vocabulary.json`) via
`domains/reflective_faculty.py`'s `ground_concern`/`_ground_relation_predicates`
— a genuinely-new "match acoustic form" concern has no existing RelationCue
for it, so authoring it would mean adding one to `relation_vocabulary.json`
(and possibly `seeds/composer_dispatch.json`) — both explicitly owned by a
concurrent agent this session. Per the task's own fallback instruction, this
uses the seeded-rule path instead (via the persistence shape above, filed
under the `speech_enrollment` seed — a speech seed, matching `teach()`'s own
category convention) and reports the wall here rather than editing those files.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

import numpy as np

from domains.teach import teach, SEEDS as _SEEDS_DIR
from domains.voice_world import (
    FS, N_BANDS, N_TIME_WINDOWS, VoiceWorld, load_audio_any,
    DENOTE_THRESHOLD, recognition_rules, install_recognition_rules,
    ensure_sign_frames,
)

SEED_CATEGORY = "speech_enrollment"
DEFAULT_LEXICON = "enrolled"
# Strict on purpose (near 1.0): acquire_sign's own cosine pre-merge (a Python
# primitive inside the off-limits runners/dsl/* package) should essentially
# never short-circuit a held-out hearing into an existing exemplar node before
# the graph-native DTW recognition Rules get a chance to run — the whole
# point of this module is that THOSE Rules (not cosine pre-merge) do the
# per-turn recognition. Calibrated empirically (see
# tests/test_speech_grounding.py / domains/voice_world.py's DENOTE_THRESHOLD
# docstring): below ~0.999 the flattened-energy cosine similarity between
# two jittered renderings of the SAME synthetic word already exceeds the
# threshold often enough to merge before DtwTo ever runs.
DEFAULT_MATCH_THRESHOLD = 0.999


# --------------------------------------------------------------------------- #
#  small mechanical queries shared by enroll()/materialize_enrollments()
# --------------------------------------------------------------------------- #
def _concept_by_name(agent, name: str):
    for n in agent.s.nodes("Concept"):
        if agent.s.node(n)["attrs"].get("name") == name:
            return n
    return None


def _get_or_create_concept(agent, name: str):
    return _concept_by_name(agent, name) or agent.s.add_node("Concept", {"name": name})


def _lexicon_node(agent, name: str):
    for n in agent.s.nodes("AcousticLexicon"):
        if agent.s.node(n)["attrs"].get("name") == name:
            return n
    return None


# --------------------------------------------------------------------------- #
#  PERSIST — the half of teach()'s job teach() itself doesn't do (rules).
# --------------------------------------------------------------------------- #
def _persist_rules(rules: list[dict], *, seed_id: str = SEED_CATEGORY,
                   seeds_dir: Path = _SEEDS_DIR, depends_on: Optional[list] = None) -> str:
    """Idempotently append `rules` (each a `{name, match, where, effects}` dict
    — the exact `add_rule` dialect) to `seeds/<seed_id>.json`'s `rules` array,
    creating the manifest if absent. Same idempotent-JSON-write shape as
    `domains.teach.teach`, applied to the one manifest key `teach()` doesn't
    touch. Returns the seed file path."""
    path = Path(seeds_dir) / f"{seed_id}.json"
    if path.exists():
        m = json.loads(path.read_text())
    else:
        m = {
            "id": seed_id, "version": "1.0.0", "depends_on": depends_on or ["speech"],
            "description": "Speech enrollment: caregiver-taught words (Concept + LexEntry, "
                           "via domains.teach.teach) plus the graph-native per-turn "
                           "recognition Rules (sg_denote_best_dist / sg_denote_ground — DtwTo "
                           "argmin-then-threshold over enrolled AcousticSign exemplars, run by "
                           "run_rules) that mint a held-out AcousticSign's `denotes` edge. No "
                           "Python matcher; see domains/speech_enrollment.py + "
                           "domains/voice_world.py.",
            "microtheory": {"name": seed_id,
                            "description": "taught words + the per-turn recognition rules"},
            "nodes": [], "edges": [], "productions": [], "rules": [],
        }
    m.setdefault("rules", [])
    existing = {r.get("name") for r in m["rules"] if isinstance(r, dict)}
    changed = False
    for r in rules:
        if r.get("name") not in existing:
            m["rules"].append(r)
            existing.add(r.get("name"))
            changed = True
    if changed:
        path.write_text(json.dumps(m, indent=1))
    return str(path)


def _ensure_rules_persisted(threshold: float = DENOTE_THRESHOLD) -> str:
    return _persist_rules(recognition_rules(threshold))


# --------------------------------------------------------------------------- #
#  ENROLL — the caregiver teaches one word.
# --------------------------------------------------------------------------- #
def enroll(agent, wav_or_samples: Union[str, "np.ndarray"], label: str, *,
          fs: int = FS, lexicon_name: str = DEFAULT_LEXICON,
          match_threshold: float = DEFAULT_MATCH_THRESHOLD,
          n_bands: int = N_BANDS, n_time_windows: int = N_TIME_WINDOWS) -> dict:
    """The interlocutor says `label` (a word) once; ingest it through the SAME
    chain `VoiceWorld.hear()` uses, ground the resulting AcousticSign(s) to a
    Concept named `label` (the caregiver's word IS the ground truth —
    mechanical, like `substrate_rs.speech.ground_sign`), and persist (via
    `teach()`, idempotent) so the word — and the recognition Rules themselves —
    survive a reboot. Supports multiple exemplars per word: call `enroll()`
    again with another recording of the same `label`.

    `wav_or_samples`: a path to an audio file (any format — ffmpeg-decoded via
    `load_audio_any`, so a browser's webm/opus MediaRecorder blob works too)
    OR an already-decoded float32 sample array (paired with `fs`).

    Returns {"concept", "label", "signs": [...], "n_exemplars", "seed_path"}.
    """
    install_recognition_rules(agent)          # live (idempotent)
    seed_path = _ensure_rules_persisted()      # + persisted (idempotent)

    vw = VoiceWorld(agent, lexicon_name=lexicon_name, fs=fs, n_bands=n_bands,
                    n_time_windows=n_time_windows, match_threshold=match_threshold)

    if isinstance(wav_or_samples, (str, Path)):
        samples, sr = load_audio_any(str(wav_or_samples), fs=fs)
    else:
        samples = np.asarray(wav_or_samples, dtype=np.float32)
        sr = fs

    results = vw.hear(samples, fs=sr)
    concept = _get_or_create_concept(agent, label)

    signs = []
    for r in results:
        sign = r["sign"]
        if sign is None:
            continue
        ensure_sign_frames(agent, sign, n_bands=n_bands, n_time_windows=n_time_windows)
        if concept not in set(agent.inner.neighbours(sign, "denotes")):
            agent.inner.add_edge_unchecked(sign, "denotes", concept)
        frames = agent.s.node(sign)["attrs"].get("frames")
        if frames is not None:
            teach(agent, "AcousticExemplar",
                 {"word": label, "lexicon": lexicon_name, "frames": frames,
                  "n_bands": n_bands, "n_time_windows": n_time_windows},
                 category=SEED_CATEGORY)
        signs.append(sign)

    teach(agent, "LexEntry",
         {"surface": label, "concept": label, "language": "en", "status": "confirmed"},
         category=SEED_CATEGORY)
    teach(agent, "Concept", {"name": label}, category=SEED_CATEGORY)

    agent.tick()   # let sg_denote_* + the speech-bridge settle on the fresh exemplar(s)
    return {"concept": concept, "label": label, "signs": signs,
            "n_exemplars": len(signs), "seed_path": seed_path}


# --------------------------------------------------------------------------- #
#  REHYDRATE — after a fresh seed boot (no checkpoint), turn taught
#  AcousticExemplar records back into a live, wired AcousticLexicon.
# --------------------------------------------------------------------------- #
def materialize_enrollments(agent, lexicon_name: str = DEFAULT_LEXICON,
                            match_threshold: float = DEFAULT_MATCH_THRESHOLD) -> int:
    """Rehydrate every taught `AcousticExemplar` node not yet mirrored into the
    named AcousticLexicon: mint an AcousticSign carrying the SAME `features`/
    `frames` recorded at enrollment time, wire `lexicon -has_entry-> sign`, and
    `sign -denotes-> Concept(word)`. Mechanical reconstruction of exactly the
    shape `enroll()` builds live, from the same taught data — no decision, no
    recognition (that's still the Rules). Idempotent per boot: a word already
    present as an entry's `label` in the target lexicon is skipped, so calling
    this more than once in the same running session is a no-op after the
    first. Returns how many exemplars were (re)materialised."""
    install_recognition_rules(agent)
    lex = _lexicon_node(agent, lexicon_name)
    if lex is None:
        lex = agent.s.add_node(
            "AcousticLexicon",
            {"name": lexicon_name, "match_threshold": float(match_threshold), "n_signs": 0})

    existing_words = set()
    for sid in agent.inner.neighbours(lex, "has_entry"):
        lbl = agent.s.node(sid)["attrs"].get("label")
        if lbl:
            existing_words.add(lbl)

    n = 0
    for ex in agent.s.nodes("AcousticExemplar"):
        a = agent.s.node(ex)["attrs"]
        word, frames = a.get("word"), a.get("frames")
        if not word or not frames or word in existing_words:
            continue
        n_bands = int(a.get("n_bands", N_BANDS))
        n_time_windows = int(a.get("n_time_windows", N_TIME_WINDOWS))
        arr = np.asarray(frames, dtype=np.float32)              # (n_time_windows, n_bands)
        flat = arr.T.reshape(-1).astype(np.float32)              # -> band-major, matches
                                                                   # extract_features's own layout
        sign = agent.s.add_node("AcousticSign", {
            "label": word, "features": flat.tobytes(), "feature_length": int(flat.size),
            "hearings": 1, "origin": "enrolled"})
        agent.s.set_attr(sign, "frames", frames)
        agent.inner.add_edge_unchecked(lex, "has_entry", sign)
        cur = int(agent.s.node(lex)["attrs"].get("n_signs", 0))
        agent.s.set_attr(lex, "n_signs", cur + 1)
        concept = _get_or_create_concept(agent, word)
        agent.inner.add_edge_unchecked(sign, "denotes", concept)
        existing_words.add(word)
        n += 1
    return n


__all__ = [
    "SEED_CATEGORY", "DEFAULT_LEXICON", "DEFAULT_MATCH_THRESHOLD",
    "enroll", "materialize_enrollments",
]
