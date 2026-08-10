"""capture.py — Wave 2 (Deep-Reader) divergence-fixture capture.

Runs BOTH comprehension paths over one shared corpus and freezes, per
utterance, a straight field-by-field comparison — this is the input Wave 3's
cutover decision reads:

  * ``comp_*``    — the CURRENT front end (`comprehend_text.comprehend_text` +
    `WorldAdapter._write_comprehension_to_graph`), the SAME no-rule-pass capture
    idiom `tests/fixtures/speech_act_parity/capture.py` already uses (no network
    I/O, no search dispatch — a pure parse-and-write).
  * ``shadow_*``  — the NEW light deep-read gateway (`WorldAdapter.
    _shadow_read_turn`, Wave 2 Task 2): `reading_drive.run_reading_flow` under
    the `conversational` register's aperture (Wave 2 Task 1 — `stages=['spine']`
    only) plus `reading_collapse.read_clause`'s own turn-grain fields (Wave 1B).

Both are written onto the SAME inbound Message in the SAME turn (one
`receive_utterance` call), so the comparison is apples-to-apples — no
state drift between two separate runs.

Each utterance runs on its OWN fresh `WorldAdapter` (not one substrate shared
across the whole corpus): a few conversation-tracking utterances lose their
preceding-turn context this way (an isolated "Tell me more about it." has no
current_topic to resolve against — an honest, disclosed limitation of this
capture methodology, not a defect in either comprehension path), but it keeps
per-utterance cost bounded and independent of corpus position/order.

Corpus:
  (a) all 133 utterances in `tests/fixtures/speech_act_parity/speech_act.json`
      (read-only fixture — texts only, never its frozen kind/predicate values,
      which were captured under a DIFFERENT harness with no shadow_* pass);
  (b) the literal `.converse(...)` inputs mined from the conversation gates
      this Wave's mission names (test_instruction_gap / test_nl_steering /
      test_qa / test_topic_* migrated) — deduplicated, in first-seen order.

This script does NOT modify any source file; it only reads current code and
writes the fixture. Idempotent. Side-effect-free on seeds/ (`_shadow_read_turn`
calls `read_clause` with write=False, learn=False; `run_reading_flow`'s own
mutations are confined to the throwaway corpus substrate this script boots,
never seeds/).

Run:  cd gamma-substrate && PYTHONPATH=runners/dsl/python:. python3 \
        tests/fixtures/comprehension_divergence/capture.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "comprehension_divergence")
_SPEECH_ACT_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "speech_act_parity",
                                   "speech_act.json")

from substrate.world_adapter import WorldAdapter                    # noqa: E402
from substrate.boot_all import load_all_seeds                       # noqa: E402
from domains import comprehend_text as ct                           # noqa: E402
from domains import dictionary_lexicon as dl                        # noqa: E402


# --------------------------------------------------------------------------- #
#  CORPUS (b) — the literal inputs the mission's own conversation gates drive,
#  mined verbatim from their `.converse(...)` call sites, first-seen order,
#  deduplicated. Kept as a hardcoded list (not a live import of the test
#  modules) so this script has no test-suite dependency.
# --------------------------------------------------------------------------- #
CONVERSATION_GATE_UTTERANCES = [
    # test_instruction_gap_migrated.py
    "Summarise the report.",
    "Read this: The sky is blue.",
    "Run the script.",
    "Fix your grammar.",
    "Improve your florbnax.",
    "Juggle the plates.",
    "Juggle the plates again.",
    "Describe yourself.",
    # test_nl_steering_migrated.py
    "Work on the summarise report gap.",
    "Transmogrify the data.",
    "Drop the transmogrify data gap.",
    "Pursue the flurble gap.",
    # test_qa_migrated.py
    "what is a graph",
    "what is xyz",
    "hello",
    "the sky is blue",
    # test_topic_grounding_migrated.py / test_topic_tracking_migrated.py /
    # test_topic_route_selfheal_migrated.py
    "What do you know about the moon?",
    "Tell me more about it.",
    "How big is it?",
    "What about volcanoes?",
    "What are you?",
    "How do you learn?",
    "How does your collapse function work?",
    "What is the moon made of?",
    "Do you know what dancing is?",
    "Can you dance?",
    "Can you navigate 3D spaces?",
    "Can you play chess?",
    "Could you dance if you had a body?",
]


def _load_speech_act_corpus() -> list:
    with open(_SPEECH_ACT_FIXTURE) as f:
        data = json.load(f)
    out = []
    for _cat, items in data["corpus"].items():
        for it in items:
            out.append(it["text"])
    return out


def _norm(v):
    """Loose textual normalisation for the agreement compare — case-fold a
    string, leave None/other types alone. Not a decision — just so 'LLM' and
    'llm' (comp_topic vs shadow_focus casing conventions differ) count as
    agreement rather than a spurious mismatch."""
    return v.lower().strip() if isinstance(v, str) else v


# --------------------------------------------------------------------------- #
#  CAPTURE — one turn, both paths. `comp_agent` is the ONE shared full-seed
#  WorldAdapter the comp_* pass accumulates conversation state on (matching
#  `tests/fixtures/speech_act_parity/capture.py`'s own proven-stable pattern —
#  a single `load_all_seeds` agent driven through the whole 133-row corpus).
#  The shadow_* pass runs on its OWN FRESH, LIGHT `WorldAdapter()` (default
#  CORE_SEEDS, no `load_all_seeds`) per utterance: `_shadow_read_turn` only
#  needs `reading_drive`/`register_source`/`coref_entities` (ensured on demand,
#  Wave 2 Task 1's own aperture), so it needs none of the full seed closure,
#  and a fresh light substrate per call is CHEAP (~5ms boot + ~30-70ms shadow
#  read) — this also keeps the two passes' node-mint volumes independent, so
#  neither pass's accumulation can affect the other's.
# --------------------------------------------------------------------------- #
def capture_utterance(comp_agent, text: str) -> dict:
    mid = comp_agent.receive_utterance(text, speech_act=comp_agent.classify_speech_act(text))
    comp = ct.comprehend_text(comp_agent, text)
    comp_agent._write_comprehension_to_graph(mid, comp)
    comp_attrs = comp_agent.s.node(mid)["attrs"]
    comp_kind = comp_attrs.get("comp_kind")
    comp_predicate = comp_attrs.get("comp_predicate")
    comp_topic = comp_attrs.get("comp_topic")

    shadow_agent = WorldAdapter()
    smid = shadow_agent.receive_utterance(text, speech_act=shadow_agent.classify_speech_act(text))
    shadow_agent._shadow_read_turn(smid, text)
    shadow_attrs = shadow_agent.s.node(smid)["attrs"]
    shadow_speech_act = shadow_attrs.get("shadow_speech_act")
    shadow_predicate = shadow_attrs.get("shadow_predicate")
    shadow_focus = shadow_attrs.get("shadow_focus")

    return {
        "text": text,
        "comp_kind": comp_kind,
        "shadow_speech_act": shadow_speech_act,
        "agree_kind": _norm(comp_kind) == _norm(shadow_speech_act),
        "comp_predicate": comp_predicate,
        "shadow_predicate": shadow_predicate,
        "agree_predicate": _norm(comp_predicate) == _norm(shadow_predicate),
        "comp_topic": comp_topic,
        "shadow_focus": shadow_focus,
        "agree_topic": _norm(comp_topic) == _norm(shadow_focus),
        "shadow_error": shadow_attrs.get("shadow_error"),
        "shadow_latency_ms": shadow_attrs.get("shadow_latency_ms"),
    }


def _rate(rows: list, key: str, *, require_present_field: str | None = None) -> dict:
    """agree/total, plus the SAME rate restricted to rows where
    `require_present_field` (a comp_*/shadow_* pair name) is non-null on BOTH
    sides — a None==None pair trivially 'agrees' and would inflate the
    headline rate on fields many utterances simply don't carry (comp_topic /
    shadow_focus are the sparse ones: only question/instruction turns set
    them). All the numbers are reported; none is hidden:
      * rate           — over ALL rows (None==None counts as agreement);
      * present_rate   — over rows where EITHER side set the field (the
                         harshest read: a one-sided write counts as a miss);
      * both_rate      — over rows where BOTH sides set it (the semantic
                         head-to-head: do the two parsers extract the SAME
                         value when they both extract one?);
      * comp_only / shadow_only — the coverage asymmetry itself."""
    total = len(rows)
    agree = sum(1 for r in rows if r[key])
    out = {"agree": agree, "total": total,
          "rate": round(agree / total, 4) if total else None}
    if require_present_field:
        c_key, s_key = require_present_field
        present = [r for r in rows if r[c_key] is not None or r[s_key] is not None]
        p_agree = sum(1 for r in present if r[key])
        out["present_agree"] = p_agree
        out["present_total"] = len(present)
        out["present_rate"] = round(p_agree / len(present), 4) if present else None
        both = [r for r in rows if r[c_key] is not None and r[s_key] is not None]
        b_agree = sum(1 for r in both if r[key])
        out["both_agree"] = b_agree
        out["both_total"] = len(both)
        out["both_rate"] = round(b_agree / len(both), 4) if both else None
        out["comp_only"] = sum(1 for r in rows
                               if r[c_key] is not None and r[s_key] is None)
        out["shadow_only"] = sum(1 for r in rows
                                 if r[c_key] is None and r[s_key] is not None)
    return out


def main() -> int:
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    dl.warm_wordnet("en")
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    speech_act_texts = _load_speech_act_corpus()
    seen = set()
    conv_texts = []
    for t in CONVERSATION_GATE_UTTERANCES:
        if t not in seen:
            seen.add(t)
            conv_texts.append(t)

    rows = []
    for t in speech_act_texts:
        rows.append(dict(capture_utterance(agent, t), source="speech_act_parity"))
    for t in conv_texts:
        rows.append(dict(capture_utterance(agent, t), source="conversation_gates"))

    summary = {
        "n_utterances": len(rows),
        "n_speech_act_parity": len(speech_act_texts),
        "n_conversation_gates": len(conv_texts),
        "kind": _rate(rows, "agree_kind"),
        "predicate": _rate(rows, "agree_predicate",
                           require_present_field=("comp_predicate", "shadow_predicate")),
        "topic": _rate(rows, "agree_topic",
                       require_present_field=("comp_topic", "shadow_focus")),
        "shadow_errors": sum(1 for r in rows if r.get("shadow_error")),
        "shadow_latency_ms_mean": round(
            sum(r.get("shadow_latency_ms") or 0.0 for r in rows) / len(rows), 2) if rows else None,
    }

    out = {"summary": summary, "rows": rows}
    path = os.path.join(FIXTURE_DIR, "divergence.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {path} ({len(rows)} utterances)")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
