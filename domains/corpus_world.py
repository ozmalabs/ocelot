"""corpus_world — self-learn from a Hugging Face CONVERSATION corpus.

A WORLD ADAPTER (CLAUDE.md): it FETCHES an external corpus
(``google/Synthetic-Persona-Chat``) and feeds each utterance through the
agent's EXISTING comprehension + reference-grounding stack
(``ConversationWorld.turn`` -> ``LanguageWorld._parse_with_grounded`` ->
WordNet/Wiktionary grounding -> ``KnownFact`` storage). The LEARNING is the
graph mutating as the agent comprehends; this module only sequences the corpus
into turns and reads the growth back out. NO ML training, NO agent decisions in
Python — the comprehension/grounding rules that grow the lexicon and mint facts
are all graph-resident.

This is the BABBLE LOOP at corpus scale: comprehend -> ground -> keep, run
cumulatively over hundreds of real utterances so the lexicon and the KnownFact
store grow from genuine exposure.

What genuinely learns (HONEST):
  * VOCABULARY — every content word the comprehension stack can ground (via
    WordNet) becomes a Concept + LexEntry. The lexicon grows cumulatively
    across the corpus. This is the reliable win.
  * SIMPLE FACTS — two kinds:
      - PERSONA first-person facts ("I am 32." / "I play video games.") are
        attributed to the speaker (a KnownFact with agent=<speaker>), grounded
        once per conversation from the persona block.
      - SVO statements in the dialogue ground to KnownFacts by the normal
        comprehension path (frame -> _store_fact).
  * DISCOURSE REFERENTS — the conversation world's reference-resolution store
    accumulates the entities in play.

What is capped / noisy (HONEST — reported, not hidden):
  * Comprehension is lemma-level with limited grammar: long, clause-heavy, or
    elliptical turns parse partially or not at all. Pronoun-heavy turns, the
    "[user 1's name]" placeholders, and questions ground vocabulary but yield
    no clean SVO fact.
  * WordNet sense-1 / category mis-picks happen (reported by the sense layer).
  * "Learning" here = cumulative vocabulary + simple-fact grounding, NOT deep
    reading or inference over the dialogue.

The corpus slice is cached to ``data/corpus/`` (gitignored) so a re-run is
offline. Only the parquet rows are cached — never an in-RAM agent dict.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
_CACHE_DIR = _ROOT / "data" / "corpus"

_HF_DATASET = "google/Synthetic-Persona-Chat"

# A turn line looks like "User 1: ...". Capture the speaker tag + the text.
_TURN_RE = re.compile(r"^\s*(User\s*\d+)\s*:\s*(.*)$", re.I)
# The dialogue uses "[user 1's name]" placeholders — strip them (no real name).
_NAME_PLACEHOLDER = re.compile(r"\[[^\]]*name[^\]]*\]", re.I)


# ---------------------------------------------------------------------------
# Load + cache the corpus slice.
# ---------------------------------------------------------------------------


def load_conversations(n: int = 300, *, force: bool = False
                       ) -> list[dict[str, Any]]:
    """Load + cache the first ``n`` conversations from the HF persona-chat set.

    Returns a list of ``{personas: {speaker: [facts]}, turns: [(speaker,
    text)]}`` dicts. The raw slice is cached to ``data/corpus/persona_chat_
    <n>.json`` (gitignored); a re-run reads the cache with no HF hit.

    Mechanical I/O only — splits the ``Best Generated Conversation`` string
    into turns and the persona blocks into first-person fact lines."""
    cache = _CACHE_DIR / f"persona_chat_{n}.json"
    if cache.exists() and not force:
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            pass  # corrupt cache — reload below.

    from datasets import load_dataset
    ds = load_dataset(_HF_DATASET, split=f"train[:{n}]")
    convs: list[dict[str, Any]] = []
    for row in ds:
        personas = {
            "User 1": _split_personas(row.get("user 1 personas", "")),
            "User 2": _split_personas(row.get("user 2 personas", "")),
        }
        turns = _split_turns(row.get("Best Generated Conversation", ""))
        convs.append({"personas": personas, "turns": turns})

    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(convs), encoding="utf-8")
    except Exception:
        pass
    return convs


def _split_personas(block: str) -> list[str]:
    """Split a persona block ("\\n"-separated first-person facts) into lines."""
    return [ln.strip() for ln in (block or "").split("\n") if ln.strip()]


def _split_turns(conv: str) -> list[tuple[str, str]]:
    """Split a ``Best Generated Conversation`` string into (speaker, text)
    turns. Placeholder names ("[user 1's name]") are stripped to a bare token
    so the comprehension parse isn't derailed by the bracketed literal."""
    out: list[tuple[str, str]] = []
    for line in (conv or "").split("\n"):
        m = _TURN_RE.match(line)
        if not m:
            continue
        speaker = re.sub(r"\s+", " ", m.group(1)).strip().title()
        text = _NAME_PLACEHOLDER.sub("someone", m.group(2)).strip()
        if text:
            out.append((speaker, text))
    return out


# ---------------------------------------------------------------------------
# Persona first-person facts -> KnownFact attributed to the speaker.
# ---------------------------------------------------------------------------

# A first-person persona line ("I am 32." / "I play video games all day.").
# We attribute it to the speaker: a KnownFact carrying the raw predicate text
# + agent=<speaker label>. This is a deliberately SHALLOW grounding — the
# persona sentence isn't fully parsed into SVO (many are copular / stative);
# it records the attributed self-description as a referenceable fact.
_FIRST_PERSON = re.compile(r"^\s*i\s+(.*)$", re.I)


def ground_persona_facts(world, speaker: str, persona_lines: list[str]
                         ) -> int:
    """Ground a speaker's persona block as ``PersonaFact`` KnownFacts.

    Each first-person line "I <predicate>" becomes a KnownFact{agent=speaker,
    predicate=<text>, origin='persona'} — the speaker's grounded
    self-description. Mechanical translation: no decision over graph state, just
    one node per first-person line. Returns the number grounded.

    Also runs the line's content words through comprehension grounding (below,
    in ``learn_turn``) — handled by the caller — so the vocabulary in the
    persona is grounded too; here we only mint the attributed fact."""
    n = 0
    for line in persona_lines:
        m = _FIRST_PERSON.match(line)
        if not m:
            continue
        predicate = m.group(1).strip().rstrip(".")
        if not predicate:
            continue
        try:
            world.s.add_node("KnownFact", {
                "language": "en",
                "agent": speaker,
                "predicate": predicate,
                "origin": "persona",
            })
            n += 1
        except Exception:
            pass
    return n


# ---------------------------------------------------------------------------
# learn_turn / learn_conversation — drive comprehension over the corpus.
# ---------------------------------------------------------------------------


def learn_turn(cw, speaker: str, text: str) -> dict[str, Any]:
    """Comprehend ONE corpus turn through the conversation world, growing the
    graph. Returns a small trace ({speaker, reply, frame, act}).

    Pure sequencing: hands the text to ``ConversationWorld.turn`` (the real
    comprehend -> ground -> store loop) and reads the resulting frame back out.
    The grounding (Concept / LexEntry / KnownFact creation) all happens inside
    the graph-resident comprehension stack."""
    try:
        reply = cw.turn(text, "en")
    except Exception as exc:  # a turn that the parser can't handle at all
        return {"speaker": speaker, "reply": None, "frame": {},
                "act": "error", "error": str(exc)}
    rec = cw.transcript[-1] if cw.transcript else {}
    return {"speaker": speaker, "reply": reply,
            "frame": dict(rec.get("frame", {})),
            "act": rec.get("speech_act", "")}


def learn_conversation(cw, conv: dict[str, Any]) -> dict[str, Any]:
    """Self-learn from one corpus conversation: ground both speakers' persona
    blocks, then comprehend every dialogue turn. Returns a per-conversation
    trace (persona facts grounded, turns processed, frames with a clean SVO).

    The cumulative grounding (lexicon growth + KnownFacts) lands on the shared
    substrate; this returns only the per-conversation deltas for reporting."""
    world = cw.world
    persona_facts = 0
    for speaker, lines in conv.get("personas", {}).items():
        persona_facts += ground_persona_facts(world, speaker, lines)
        # Also comprehend the persona lines so their vocabulary grounds (the
        # facts above are attribution; this grows the lexicon from the text).
        for line in lines:
            learn_turn(cw, speaker, line)

    turn_traces: list[dict[str, Any]] = []
    svo = 0
    for speaker, text in conv.get("turns", []):
        tr = learn_turn(cw, speaker, text)
        turn_traces.append(tr)
        f = tr.get("frame") or {}
        # A "clean SVO" = an assertion frame with event + agent + patient.
        if (tr.get("act") == "assertion" and f.get("event")
                and f.get("agent") and f.get("patient")):
            svo += 1
    return {"persona_facts": persona_facts,
            "turns": len(turn_traces),
            "clean_svo": svo,
            "traces": turn_traces}


# ---------------------------------------------------------------------------
# Graph counts — measure cumulative grounding growth.
# ---------------------------------------------------------------------------


def graph_counts(world) -> dict[str, int]:
    """Snapshot the learning-relevant graph counts (for before/after deltas):
    Concept / LexEntry / KnownFact (split by origin) / lexicon-cache size."""
    s = world.s
    persona = svo = banked = other = 0
    for fid in s.nodes("KnownFact"):
        origin = s.node(fid)["attrs"].get("origin", "")
        if origin == "persona":
            persona += 1
        elif origin == "banked_resolution":
            banked += 1
        elif origin:
            other += 1
        else:
            svo += 1  # the comprehension _store_fact path sets no origin.
    return {
        "concepts": sum(1 for _ in s.nodes("Concept")),
        "lex_entries": sum(1 for _ in s.nodes("LexEntry")),
        "lexicon_cache": sum(len(d) for d in world._lexicon_cache.values()),
        "known_facts": sum(1 for _ in s.nodes("KnownFact")),
        "facts_persona": persona,
        "facts_svo": svo,
        "facts_banked": banked,
        "facts_other": other,
    }


def example_groundings(world, before_lex: set[str], limit: int = 10
                       ) -> list[dict[str, Any]]:
    """Return up to ``limit`` example NEW lexicon groundings (surfaces grounded
    during this run, i.e. not in ``before_lex``), each with its concept +
    category + source — for an honest sample of what the corpus taught."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for eid in world.s.nodes("LexEntry"):
        a = world.s.node(eid)["attrs"]
        surface = a.get("surface")
        concept = a.get("concept")
        if not surface or surface in before_lex or surface in seen:
            continue
        seen.add(surface)
        cat = ""
        cid = world._concept_nodes.get(concept)
        if cid is not None:
            cat = world.s.node(cid)["attrs"].get("category", "")
        out.append({"surface": surface, "concept": concept,
                    "category": cat, "source": a.get("source", "")})
        if len(out) >= limit:
            break
    return out


def current_surfaces(world) -> set[str]:
    """The set of surface forms currently grounded (across languages) — used to
    snapshot the lexicon BEFORE a run so new groundings can be isolated."""
    out: set[str] = set()
    for d in world._lexicon_cache.values():
        out |= set(d.keys())
    return out


__all__ = [
    "load_conversations", "ground_persona_facts",
    "learn_turn", "learn_conversation",
    "graph_counts", "example_groundings", "current_surfaces",
]
