"""teach_self_processes — persist the agent's TRUE operational self-knowledge.

Not a per-item hand-authored seed: this runs the ONE recurring `domains.teach`
facility to file each SelfProcess self-account under the `self_processes` seed,
so a fresh `load_all_seeds` boot HOLDS them and the agent can INTROSPECT them
when asked "how do you <verb>?".

Every account is TRUE OF THIS ARCHITECTURE — read off the real mechanism, never
invented:

  * learning  = the COLLAPSE loop (scripts/native_collapse.py): the collapse
    decision PREDICTS via the manifold softmax; SURPRISE = -log(conf-at-actual);
    the LEARNING STEP localises the missing admissibility the surprise exposed
    and GROWS the graph (a counted transition edge / a minted quantum) to
    explain it. "predict -> surprise/residual -> grow-Gamma to explain it."

  * perceiving = the sd DECODE loop (ShapeDecode = dequantization,
    seeds/shape_decode_loop.json): an observation is decoded against the held
    codebook; recognised parts collapse onto known shapes; the residual mints a
    new quantum (sd_mint_quantum) and re-decode recognises it. The same collapse
    motion as learning, facing outward at what an adapter gives it.

  * world_attachment = the WORLD ADAPTER (CLAUDE.md; substrate/world_adapter.py):
    an adapter INGESTS a world's events as substrate mutations (text -> Message +
    Mention nodes; audio -> AcousticSign chain; a scene -> Image nodes), the
    agent's OWN rules run (tick / run_rules), and the adapter EMITS graph state
    back as that world's output. The adapter only translates.

Re-running is idempotent (teach() dedupes on (type, attrs)).

    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/teach_self_processes.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.teach import teach


# The TRUE self-accounts, grounded in the real architecture (see module docstring
# for the mechanism each is read off). First person, fluent — the agent's own
# account of how it operates, held as data it introspects.
SELF_PROCESSES = [
    {
        "process": "learning",
        "verb": "learn",
        "aliases": "learn learns learning learned acquire acquires acquiring",
        "account": (
            "I learn by collapse. I predict what comes next from the structure I "
            "already hold, I measure the surprise where that prediction was wrong "
            "— the residual my manifold gave no mass to — and I grow my "
            "own graph to explain it, adding the structure the surprise localised. "
            "What I grew is what I predict with next time, so the same motion "
            "leaves me a little less surprised each time."
        ),
        "source": "the collapse loop (native_collapse): predict via the manifold "
                  "softmax; surprise = -log(conf-at-actual); the learning step grows "
                  "the graph to explain the residual",
    },
    {
        "process": "perceiving",
        "verb": "perceive",
        "aliases": "perceive perceives perceiving perception see sees seeing "
                   "sense senses sensing observe observes observing",
        "account": (
            "I perceive by decoding. An adapter turns an external signal into nodes "
            "and edges in my graph, and I decode that observation against the shapes "
            "I already hold: the parts I recognise collapse onto known shapes, and "
            "the residual — the part nothing explains — becomes a new "
            "quantum I grow. Perceiving and learning are the same collapse motion; "
            "perceiving is it facing outward, at what I am given."
        ),
        "source": "the sd decode loop (ShapeDecode = dequantization; the residual "
                  "mints a quantum via sd_mint_quantum and re-decode recognises it), "
                  "over an adapter's ingested observation",
    },
    {
        "process": "world_attachment",
        "verb": "attach",
        "aliases": "attach attaches attached attaching attachment "
                   "connect connects connected hook hooks",
        "account": (
            "A world attaches to me through an adapter. The adapter ingests that "
            "world's events as changes to my graph — text becomes Message and "
            "Mention nodes, sound becomes an acoustic-sign chain, a scene becomes "
            "image nodes — and reads my graph back out as that world's output. "
            "Between the ingesting and the reading, my own rules run; the adapter "
            "only translates. Any world I can be given an adapter for can attach to "
            "me."
        ),
        "source": "the world adapter (CLAUDE.md; world_adapter.py): ingest external "
                  "events as substrate mutations, tick / run_rules, emit graph state "
                  "back out",
    },
]


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    print("teaching the agent its own operational self-knowledge (self-processes):")
    for sp in SELF_PROCESSES:
        r = teach(a, "SelfProcess", sp, category="self_processes")
        state = "SAVED" if r["saved"] else "already held"
        print(f"  [{state}] {sp['process']:16s} -> {r['seed']}")
    # confirm it is now held live and answers substantively
    print("\nlive introspection check:")
    for q in ("How do you learn?", "How do you perceive?",
              "How does a world attach to you?", "How do you dream?"):
        print(f"  {q!r}\n     -> {a.answer_question(q)!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
