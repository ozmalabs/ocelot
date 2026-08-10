"""PhonologyTeacher — LLM-backed (with expert fallback) teacher
that extends the phonology Mt with expert-curated word signatures.

The agent's hand-coded predicates cover 5 phonology concepts.
The signatures it learns from observation are noisy. A teacher
can provide:

  (a) richer per-word per-position signatures grounded in
      linguistic knowledge
  (b) [later] additional phonology concepts (manner, place,
      voicing as separable features) with their own predicates

This module is (a). Two paths:

  1. **LLM-driven** (if `OPENROUTER_API_KEY` set OR an Ollama
     backend reachable): prompt the LLM with the agent's current
     phonology vocabulary + word list, ask for per-word per-
     position signatures as JSON, parse, install via
     `teach_word_position_signature`.

  2. **Expert fallback** (always available): hardcoded
     linguistics-curated signatures for English digits zero-nine
     across the 5 phonology concepts. Same shape as the LLM
     would produce; lets the demo run offline.

Both paths produce graph data: per-word per-position
`<position>_marker_prob_<feature>` attrs on the word Concept.
The position-aware scoring (Q) reads these directly.
"""
from __future__ import annotations

import json

from .phonology import teach_word_position_signature


# Linguistics-curated signatures for English digit pronunciations.
# Format: {word: {position: {phonology_concept: P(exhibits)}}}
# Position keys: "first", "mid", "last".
# The 5 phonology concepts available: voicing, sibilant,
# sonorant, formant_present, noise_burst.
_EXPERT_DIGIT_SIGNATURES = {
    "zero":  {  # /ˈzɪroʊ/  z-i-r-o
        "first": {"voicing": 0.95, "sibilant": 0.6,
                    "sonorant": 0.3,  "formant_present": 0.3,
                    "noise_burst": 0.2},
        "last":  {"voicing": 1.0,  "sibilant": 0.0,
                    "sonorant": 1.0,  "formant_present": 0.95,
                    "noise_burst": 0.05},
    },
    "one":   {  # /wʌn/  w-uh-n
        "first": {"voicing": 0.95, "sibilant": 0.0,
                    "sonorant": 0.4,  "formant_present": 0.3,
                    "noise_burst": 0.05},
        "last":  {"voicing": 0.95, "sibilant": 0.0,
                    "sonorant": 0.95, "formant_present": 0.5,
                    "noise_burst": 0.05},
    },
    "two":   {  # /tu/  t-oo
        "first": {"voicing": 0.0,  "sibilant": 0.0,
                    "sonorant": 0.0,  "formant_present": 0.0,
                    "noise_burst": 0.9},
        "last":  {"voicing": 1.0,  "sibilant": 0.0,
                    "sonorant": 1.0,  "formant_present": 0.9,
                    "noise_burst": 0.0},
    },
    "three": {  # /θri/  th-r-ee
        "first": {"voicing": 0.0,  "sibilant": 0.4,
                    "sonorant": 0.0,  "formant_present": 0.1,
                    "noise_burst": 0.8},
        "last":  {"voicing": 1.0,  "sibilant": 0.0,
                    "sonorant": 1.0,  "formant_present": 0.9,
                    "noise_burst": 0.0},
    },
    "four":  {  # /fɔr/  f-or
        "first": {"voicing": 0.0,  "sibilant": 0.0,
                    "sonorant": 0.0,  "formant_present": 0.1,
                    "noise_burst": 0.8},
        "last":  {"voicing": 0.8,  "sibilant": 0.0,
                    "sonorant": 0.8,  "formant_present": 0.7,
                    "noise_burst": 0.1},
    },
    "five":  {  # /faɪv/  f-i-v
        "first": {"voicing": 0.0,  "sibilant": 0.0,
                    "sonorant": 0.0,  "formant_present": 0.1,
                    "noise_burst": 0.7},
        "last":  {"voicing": 0.8,  "sibilant": 0.0,
                    "sonorant": 0.5,  "formant_present": 0.3,
                    "noise_burst": 0.6},
    },
    "six":   {  # /sɪks/  s-i-k-s
        "first": {"voicing": 0.0,  "sibilant": 0.8,
                    "sonorant": 0.0,  "formant_present": 0.0,
                    "noise_burst": 0.6},
        "last":  {"voicing": 0.0,  "sibilant": 0.6,
                    "sonorant": 0.0,  "formant_present": 0.0,
                    "noise_burst": 0.8},
    },
    "seven": {  # /ˈsɛvən/  s-e-v-e-n
        "first": {"voicing": 0.0,  "sibilant": 0.9,
                    "sonorant": 0.0,  "formant_present": 0.0,
                    "noise_burst": 0.7},
        "last":  {"voicing": 0.95, "sibilant": 0.0,
                    "sonorant": 0.95, "formant_present": 0.5,
                    "noise_burst": 0.05},
    },
    "eight": {  # /eɪt/  ay-t
        "first": {"voicing": 0.95, "sibilant": 0.0,
                    "sonorant": 0.95, "formant_present": 0.95,
                    "noise_burst": 0.0},
        "last":  {"voicing": 0.0,  "sibilant": 0.0,
                    "sonorant": 0.0,  "formant_present": 0.0,
                    "noise_burst": 0.85},
    },
    "nine":  {  # /naɪn/  n-i-n
        "first": {"voicing": 0.95, "sibilant": 0.0,
                    "sonorant": 0.9,  "formant_present": 0.4,
                    "noise_burst": 0.05},
        "last":  {"voicing": 0.95, "sibilant": 0.0,
                    "sonorant": 0.9,  "formant_present": 0.4,
                    "noise_burst": 0.05},
    },
}


_LLM_PROMPT_TEMPLATE = """\
You are a phonology expert teaching a substrate-based AI agent.

The agent has 5 phonology concepts it can detect in audio:
  voicing         — periodic glottal source (F0 in 50-400 Hz)
  sibilant        — high-band energy >> low+mid bands (/s/, /z/, /ʃ/, /ʒ/)
  sonorant        — voiced + low-band dominant (vowels, nasals, liquids)
  formant_present — concentrated mid-band energy (vowels, glides)
  noise_burst     — high-band > low-band (unvoiced fricatives, bursts)

For each of these spoken English words, give per-position
probability estimates that an audio observation at that position
will exhibit each phonology concept.

Words: {words}

Respond with EXACTLY this JSON shape, no other text:

{{
  "word_one": {{
    "first": {{"voicing": 0.x, "sibilant": 0.x, "sonorant": 0.x,
              "formant_present": 0.x, "noise_burst": 0.x}},
    "last":  {{"voicing": 0.x, "sibilant": 0.x, "sonorant": 0.x,
              "formant_present": 0.x, "noise_burst": 0.x}}
  }},
  ...
}}

Use linguistic knowledge of IPA/English phonology. Probabilities
∈ [0.0, 1.0]. 'first' = first sign of the utterance; 'last' = last
sign. Numbers should reflect that, e.g., "seven" begins with /s/
(no voicing, high sibilant, high noise_burst at first position)
and ends with /n/ (full voicing, sonorant).
"""


class PhonologyTeacher:
    """Bridge between an external teacher (LLM or expert) and the
    substrate's phonology Mt. Calls teach_word_position_signature
    per (word, position) for the curated signatures."""

    def __init__(self, llm_partner=None):
        """llm_partner: an LLMPartner instance (optional). If
        unavailable or unset, falls back to hardcoded expert
        signatures."""
        from .no_llm import no_llm
        if no_llm():
            llm_partner = None   # OZMA_NO_LLM: skip the LLM path; the expert
            #                      fallback IS the non-LLM link of this chain.
        self.llm = llm_partner

    def teach(self, substrate, words: list[str]) -> dict:
        """Install per-word per-position signatures. Returns:
            {"source": "llm" | "expert",
             "n_words_taught": int,
             "n_positions_taught": int}
        """
        signatures = self._fetch_signatures(words)
        n_words = 0
        n_positions = 0
        for word, per_pos in signatures.items():
            touched = False
            for position, sig in per_pos.items():
                ok = teach_word_position_signature(
                    substrate, word, position, sig)
                if ok:
                    n_positions += 1
                    touched = True
            if touched:
                n_words += 1
        source = "llm" if (self.llm is not None
                                and self._used_llm) else "expert"
        return {
            "source": source,
            "n_words_taught": n_words,
            "n_positions_taught": n_positions,
        }

    def _fetch_signatures(self, words: list[str]) -> dict:
        """Try the LLM path; on any failure (no key, parse error,
        transport), fall back to expert. Returns the same shape
        as _EXPERT_DIGIT_SIGNATURES."""
        self._used_llm = False
        if self.llm is not None:
            try:
                if not self.llm.is_available():
                    raise RuntimeError("LLM not available")
                prompt = _LLM_PROMPT_TEMPLATE.format(
                    words=", ".join(words))
                reply = self.llm.ask(prompt)
                if not reply:
                    raise RuntimeError("empty LLM reply")
                # Strip code fences if present.
                txt = reply.strip()
                if txt.startswith("```"):
                    txt = txt.split("```")[1]
                    if txt.startswith("json"):
                        txt = txt[4:]
                parsed = json.loads(txt)
                # Validate shape.
                if isinstance(parsed, dict):
                    self._used_llm = True
                    return parsed
            except Exception:
                pass
        # Expert fallback — filter to the requested words.
        return {w: _EXPERT_DIGIT_SIGNATURES[w]
                  for w in words
                  if w in _EXPERT_DIGIT_SIGNATURES}


__all__ = ["PhonologyTeacher", "_EXPERT_DIGIT_SIGNATURES"]
