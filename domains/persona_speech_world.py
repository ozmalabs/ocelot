"""A WORLD the agent inhabits: multiple speaking PERSONAS it controls.

The agent has ears (its speech stack) and a voice (STTPipeline.speak). This world
gives it several VOICES — personas, each a distinct speaker (pitch f0, resonance q,
and a vocal-tract scale) — and lets it choose WHO says WHAT. When the agent speaks
through a persona, the world voices it and re-ingests the audio, so the agent HEARS
its own speech through its own ears.

Why this is the right world for learning language: the agent can say the same word
through different speakers and hear them all — so the speaker-invariant identity of
a word (its MEANING, the thing that's constant across voices) is something it can
GROUND by doing, not be told. And with several personas it controls, it can stage a
conversation between them — turn-taking, reference, reply — the social ground of
language, all driven by the one mind.

Faithful to the architecture: this is a WORLD ADAPTER. Python only voices the
personas and moves audio (the I/O boundary). The CONTROL — which persona speaks
what, and when — is the agent's, expressed as graph intents it acts on. The world
executes; it does not decide. See [[ozma_babble_grounding]] / [[ozma_boundary_as_relations]].
"""
from __future__ import annotations

import numpy as np


def install_personas(substrate, specs) -> dict:
    """Install the speaking personas as graph nodes the agent controls + can sense.
    `specs`: list of (name, f0_hz, q_factor, vtl_scale). The agent_root `controls`
    each persona (the boundary relation — it is a voice the agent acts through).
    Returns {name: node_id}."""
    root = next((n for n in substrate.nodes("AgentRoot")), None)
    if root is None:
        root = next((n for n in substrate.nodes("DevelopmentRoot")), None)
    ids = {}
    for name, f0, q, vtl in specs:
        p = substrate.add_node("Persona", {
            "name": name, "f0_hz": float(f0), "q_factor": float(q),
            "vtl_scale": float(vtl), "origin": "persona_world"})
        ids[name] = p
        if root is not None:
            try:
                substrate.add_edge(root, "controls", p)
            except Exception:
                pass
    return ids


def speak_as(substrate, pipe, persona, word: str, hear: bool = True,
             projection=None):
    """The agent makes `persona` say `word`. The world voices it in the persona's
    voice (pitch + resonance + vocal-tract scale) and, if `hear`, re-ingests the
    audio so the agent perceives its own speech. Returns (audio, heard_signs).

    SPEAK PATH (the projection fix). When `projection` is supplied (a
    domains.projection.Projection), the world voices the word by running that
    projection FORWARD — project(word) = config -> signal — instead of the
    most-heard-sign voicebox. The projection's forward is the SAME owned forward
    model the agent recognises through (its inverse), so the agent speaks
    word-DISCRIMINATIVELY in the space it hears in (ozma_order_n_analysis_by_synthesis).
    When `projection` is None the legacy voicebox speak is used (regression bench).
    The vtl speaker knob is baked INTO project() (formant scaling) when projecting,
    so no post-hoc waveform resample is needed in that path."""
    a = substrate.node(persona)["attrs"]
    f0 = float(a.get("f0_hz", 120.0))
    q = float(a.get("q_factor", 4.0))
    vtl = float(a.get("vtl_scale", 1.0))
    if projection is not None:
        # FORWARD through the projection (config -> signal); vtl baked into the
        # forward model's formant scaling = the speaker knob, done in projection.
        fs = int(getattr(pipe.params, "sample_rate", 8000))
        audio = projection.project(word, sub=substrate, fs=fs,
                                   f0_hz=f0, vtl_scale=vtl)
        audio = np.asarray(audio, dtype=np.float32)
    else:
        audio = pipe.speak(substrate, word, f0_hz=f0, q_factor=q)
        audio = np.asarray(audio, dtype=np.float32)
        if vtl != 1.0 and audio.size:                   # vocal-tract length: resample
            # a longer tract (vtl>1) lowers formants; resampling the waveform shifts
            # the spectrum, the cheap speaker-difference the agent must hear past.
            n = max(1, int(round(audio.size / vtl)))
            idx = np.clip((np.arange(n) * vtl).astype(int), 0, audio.size - 1)
            audio = np.ascontiguousarray(audio[idx])
    heard = []
    if hear:
        heard = pipe.ingest(substrate, audio)
        substrate.tick(50000)
    return audio, heard


DEFAULT_PERSONAS = [
    # name        f0     q     vtl    (a child, a woman, a man, a deep voice)
    ("pip",      230.0, 6.0,  0.85),
    ("ada",      190.0, 5.0,  0.95),
    ("milo",     120.0, 4.0,  1.05),
    ("bertram",   95.0, 3.0,  1.15),
]


__all__ = ["install_personas", "speak_as", "DEFAULT_PERSONAS"]
