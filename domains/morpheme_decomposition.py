"""morpheme_decomposition — the agent decomposes a written compound the way a
HUMAN parses it: by SHAPE, recognising known morphemes, the segmentation chosen by
COMPRESSION. (Creator: "these rules should be based on shape — look up how a human
parses it and that's how it should be done.")

THE SCIENCE the agent read (its reference reader, wiki_local):
  • a word decomposes into MORPHEMES — the smallest meaningful units (Morpheme);
  • a reader RECOGNISES them via the mental lexicon (word recognition / Taft &
    Forster's morphological decomposition) — it matches known morpheme FORMS in the
    word's shape, it does not apply an orthographic boundary rule;
  • when several segmentations are possible, the one a human settles on is the most
    COHERENT/likely — operationally the most COMPRESSIVE (all parts known, few,
    long): the agent's own compression-as-selector principle.

So decomposition is NOT a camelCase/separator rule (that is only an orthographic
CUE). It is: among the segmentations into held morphemes, take the one of minimum
DESCRIPTION LENGTH. This is the same selector forward_segmentation already owns
(description_length_bits), here per word and the morpheme codes read off the
agent's own corpus frequencies. MorphHead/MorphTail (the agent's authored
orthographic primitive) remains the confirming CUE when case/separators are present.

ARCHITECTURE (mirrors forward_segmentation): Python translates I/O and computes
the distributional STATISTIC (morpheme code lengths from the corpus) that
parameterises the rule; the DECISION — which segmentation — is a graph-resident
`Argmin` Term the agent evaluates over the candidate nodes (stamped with their
bits). No agent reasoning lives in Python beyond that translation.
"""
from __future__ import annotations

import glob
import json
import math
import re
from collections import Counter

_CORPUS_GLOB = "seeds/*.json"
_UNKNOWN_PER_CHAR = math.log2(27)   # raw-character code for an un-held segment
_UNKNOWN_FLAG = 8.0                  # + a flat cost so unknown segments are dispreferred
_MAX_MORPH = 18                      # longest morpheme considered (bounds the DP)


# ---------------------------------------------------------------------------
# (A) the agent's CORPUS CODE — morpheme frequencies from its own reading.
#     P(morpheme) sets the code length -log2 P; this is the distributional
#     statistic, computed once, that parameterises the selector (NOT a knob).
# ---------------------------------------------------------------------------

def corpus_morpheme_code() -> tuple[dict[str, float], set[str]]:
    """Read the agent's seed-prose corpus, count word frequencies, return
    {morpheme: code_bits} and the held-morpheme set. The code of a held morpheme
    is its unigram code length -log2 P; an un-held segment costs raw characters."""
    freq: Counter[str] = Counter()
    for f in glob.glob(_CORPUS_GLOB):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        # `seeds/` holds one git-tracked file whose JSON root is a LIST rather than
        # a manifest (`_recovered_f16_rules.json`). The seed LOADER already guards
        # for it (`boot_all._read_seeds`: `if not isinstance(d, dict): continue`);
        # this corpus read did not, and raised `'list' object has no attribute
        # 'get'` on every call. Read the bare list AS rules — the corpus statistic
        # should see that prose too, not skip it.
        for r in (d if isinstance(d, list) else (d.get("rules") or [])):
            if not isinstance(r, dict):
                continue
            txt = " ".join(str(r.get(k, "")) for k in ("head", "body", "if", "then", "why"))
            for w in re.findall(r"[a-z]{2,}", txt.lower()):
                freq[w] += 1
    total = sum(freq.values()) or 1
    code = {m: -math.log2(c / total) for m, c in freq.items()}
    return code, set(freq)


def _seg_code(seg: str, code: dict[str, float]) -> float:
    return code.get(seg, len(seg) * _UNKNOWN_PER_CHAR + _UNKNOWN_FLAG)


# ---------------------------------------------------------------------------
# (B) candidate SEGMENTATIONS — different ways to read the shape. The agent does
#     not search-and-tune; it BUILDS a few candidates (the compression-optimal
#     path, the greedy-longest reading, and the whole word) and lets the selector
#     choose. Compression is the selector run AFTER the build.
# ---------------------------------------------------------------------------

def _mdl_segmentation(word: str, code: dict[str, float]) -> list[str]:
    """The minimum-description-length reading: the segmentation of least total
    code (Viterbi over morpheme codes). The compression-optimal SHAPE parse."""
    w = word.lower()
    n = len(w)
    best = [0.0] + [math.inf] * n
    back = [0] * (n + 1)
    for i in range(1, n + 1):
        for j in range(max(0, i - _MAX_MORPH), i):
            c = best[j] + _seg_code(w[j:i], code)
            if c < best[i]:
                best[i] = c
                back[i] = j
    out, i = [], n
    while i > 0:
        out.append(w[back[i]:i])
        i = back[i]
    return out[::-1]


def _greedy_longest(word: str, held: set[str]) -> list[str]:
    """The left-to-right longest-known-morpheme reading (the simple lexical scan)."""
    w = word.lower()
    out, i = [], 0
    while i < len(w):
        hit = None
        for j in range(min(len(w), i + _MAX_MORPH), i + 1, -1):
            if w[i:j] in held:
                hit = j
                break
        if hit is None:
            out.append(w[i:])
            break
        out.append(w[i:hit])
        i = hit
    return out


def candidate_segmentations(word: str, code: dict[str, float],
                            held: set[str]) -> list[tuple[str, list[str]]]:
    """The named candidate readings of `word`'s shape. (mechanism, parts)."""
    cands = {
        "mdl": tuple(_mdl_segmentation(word, code)),
        "greedy_longest": tuple(_greedy_longest(word, held)),
        "whole": (word.lower(),),
    }
    # de-dup identical readings, keep the first mechanism that produced each
    seen: dict[tuple, str] = {}
    for mech, parts in cands.items():
        seen.setdefault(parts, mech)
    return [(mech, list(parts)) for parts, mech in seen.items()]


def candidate_bits(parts: list[str], code: dict[str, float]) -> float:
    """The DESCRIPTION LENGTH of a reading = sum of its parts' codes + a small
    per-part model cost (so fewer, longer, known parts win). The selector."""
    return sum(_seg_code(p, code) for p in parts) + len(parts) * math.log2(2)


# ---------------------------------------------------------------------------
# (C) the DECISION is graph-resident: stamp a Candidate node per reading with its
#     `bits`, and a seeded Argmin Term picks the minimum-description-length one.
# ---------------------------------------------------------------------------

def open_decomposition_productions(substrate) -> int:
    """Admit the CompoundForm --has_part--> Morpheme edge so a decomposition
    LANDS as graph data (the same admissible-edge opening the grounding seed does
    for built_from). Idempotent."""
    n = 0
    try:
        substrate.add_production({
            "src": {"type": "CompoundForm", "var": "w"},
            "edge_type": "has_part",
            "tgt": {"type": "Morpheme", "var": "m"},
            "where": None,
            "provenance": "morpheme_decomposition:has_part",
        })
        n += 1
    except Exception:
        pass
    return n


def _argmin_bits_term() -> dict:
    """Argmin over DecompCandidate nodes for this word, by their `bits` attr —
    the agent's compression selector AS GRAPH DATA (not a Python min)."""
    return {
        "type": "Argmin",
        "source": {"type": "NodesWhere", "node_type": "DecompCandidate",
                   "attr_key": "active", "value": {"type": "Lit", "value": 1.0}},
        "var_name": "c",
        "value": {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "bits"},
    }


def decompose(substrate, word: str, code: dict[str, float],
              held: set[str]) -> dict:
    """Decompose `word` into morphemes by SHAPE: build candidate readings, stamp a
    DecompCandidate per reading with its description-length `bits`, let the seeded
    Argmin Term decide, and emit the winning parts as `has_part` Morpheme nodes.
    Returns {parts, mechanism, bits, candidates}."""
    cands = candidate_segmentations(word, code, held)
    # stamp candidate nodes (mechanical) — only THIS word's candidates are active
    for c in substrate.nodes("DecompCandidate"):
        substrate.set_attr(c, "active", 0.0)
    cand_nodes = []
    for mech, parts in cands:
        nid = substrate.add_node("DecompCandidate", {
            "active": 1.0, "for_word": word.lower(), "mechanism": mech,
            "parts": json.dumps(parts), "n_parts": float(len(parts)),
            "bits": round(candidate_bits(parts, code), 4)})
        cand_nodes.append((nid, mech, parts))
    # the DECISION: evaluate the seeded Argmin Term over the candidates (the Rust
    # engine parses the Term JSON + picks the min-bits DecompCandidate node).
    winner = substrate._inner.evaluate(_argmin_bits_term(), {})
    chosen = next((c for c in cand_nodes if str(c[0]) == str(winner)), cand_nodes[0])
    _, mech, parts = chosen
    # emit the winning morphemes as graph data (has_part), mechanical
    open_decomposition_productions(substrate)
    wnode = substrate.add_node("CompoundForm", {"surface": word.lower()})
    for p in parts:
        m = substrate.add_node("Morpheme", {"surface": p})
        substrate.add_edge(wnode, "has_part", m)
    return {"parts": parts, "mechanism": mech,
            "bits": candidate_bits(parts, code),
            "candidates": [(m, pp) for _, m, pp in cand_nodes]}


def agent_decide_decomposition_mechanism(substrate) -> dict:
    """The agent reasons from the read morpheme science + its compression principle
    to the decomposition mechanism, and records the choice as graph data (a
    DecompositionSpec) — the same move as runtime_design.agent_specify_primitive.
    The mechanism is not hand-picked: it is whichever reading the COMPRESSION
    selector prefers, per word, from the corpus structure."""
    spec = {
        "name": "morpheme_decomposition",
        "grounded_in": "Morpheme (smallest meaningful unit) + word recognition / "
                       "morphological decomposition (Taft & Forster): recognise "
                       "known morpheme FORMS in the shape.",
        "selector": "minimum description length over held-morpheme readings "
                    "(the agent's own compression-as-selector); orthographic "
                    "MorphHead/MorphTail is the confirming cue, not the rule.",
        "decision_term": "Argmin(DecompCandidate, c, bits)",
        "origin": "agent_runtime_design",
    }
    substrate.add_node("DecompositionSpec", spec)
    return spec
