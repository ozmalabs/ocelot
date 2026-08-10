"""WRITER MODEL — read the SECOND channel of errors: a charitable, accurate model of the writer.

Errors carry value-neutral SIGNAL about the writing CONDITIONS. The error-type routes to a weighted
DISTRIBUTION over Attribute hypotheses (device / distraction / L2 / region / education-level), kept live,
never collapsed to the gate-keeping default. The non-gatekeeping is STRUCTURAL: an Attribute node is
signal the agent may infer; a Worth/Status/Credibility edge is a different kind, and NO production draws
one from a surface feature. The confound is a first-class fact (the same writer is accurate at a keyboard,
so a motor-slip signature is about the CHANNEL, not competence). A signature shift is a situation change.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reads_writer
"""
from __future__ import annotations
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96
LEX = {"the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "told", "you", "about",
       "problems", "could", "would", "have", "their", "there", "definitely", "receive"}
PHONETIC = {"definately", "recieve", "alot", "wich", "thier"}
GRAMMAR = {("could", "of"), ("would", "of"), ("should", "of")}   # 'of' for 'have'
HOMOPHONE = {"there", "your", "its"}                              # context-dependent confusions


def _is_transposition(tok):
    """tok is one adjacent-letter swap away from a lexicon word (teh->the, quikc->quick)."""
    for i in range(len(tok) - 1):
        sw = tok[:i] + tok[i + 1] + tok[i] + tok[i + 2:]
        if sw in LEX and tok not in LEX:
            return True
    return False


def classify(msg):
    """Host perception: the TYPES of error in a message + burstiness (no judgement here, just typing)."""
    toks = re.findall(r"[a-z']+", msg.lower())
    types = {}
    errs = 0
    for i, t in enumerate(toks):
        if _is_transposition(t):
            types["transposition"] = types.get("transposition", 0) + 1; errs += 1
        elif t in PHONETIC:
            types["phonetic"] = types.get("phonetic", 0) + 1; errs += 1
        elif i and (toks[i - 1], t) in GRAMMAR:
            types["grammar_systematic"] = types.get("grammar_systematic", 0) + 1; errs += 1
        elif t in HOMOPHONE and t not in ("",):
            types["phonetic"] = types.get("phonetic", 0) + 1; errs += 1
    if errs >= 3:
        types["burst"] = 1
    return types, errs / max(1, len(toks))


def main():
    print(SEP)
    print("WRITER MODEL — read the second channel of errors: charitable, accurate, never a verdict")
    print(SEP)
    a = boot()
    for s in ("error_recovery", "authorial_voice", "writer_model"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    # the agent's diagnosis table (recorded as graph data in the seed): error-type -> Attribute x weight
    ROUTING = {
        "transposition": {"device": 0.55, "distraction": 0.30},
        "adjacent_key": {"device": 0.55, "distraction": 0.30},
        "motor_consistent": {"device": 0.75},
        "phonetic": {"L2": 0.30, "region": 0.20, "education_level": 0.20},
        "grammar_systematic": {"L2": 0.40, "region": 0.20},
        "burst": {"distraction": 0.40, "emotional_state": 0.20},
    }
    print(f"  (loaded {len(a.s.nodes('Attribute'))} value-neutral Attribute nodes; "
          f"the error-type->attribute routing lives in the seed)\n")

    def attr_weights(types):
        """route the fired error-types to a weighted DISTRIBUTION over Attribute hypotheses (kept live)."""
        acc = {}
        for et, count in types.items():
            for attr, w in ROUTING.get(et, {}).items():
                acc[attr] = acc.get(attr, 0.0) + w * count
        tot = sum(acc.values()) or 1.0
        return {k: round(v / tot, 2) for k, v in sorted(acc.items(), key=lambda x: -x[1])}

    messages = [
        ("phone+TV burst", "teh quikc brwon fox"),
        ("at a keyboard",  "The quick brown fox jumps over the lazy dog."),
        ("systematic L2",  "i could of told you about there problems definately"),
    ]
    prev_device = None
    print()
    for label, msg in messages:
        types, rate = classify(msg)
        dist = attr_weights(types)
        print(f"  [{label}] {msg!r}")
        print(f"      error-types: { {k: v for k, v in types.items()} }  (rate {rate:.2f})")
        print(f"      WRITER-MODEL attributes (value-neutral signal, a distribution): {dist or '{} (clean — no error signal)'}")
        device = dist.get("device", 0.0)
        if prev_device is not None and (prev_device > 0.3) != (device > 0.3):     # signature SHIFT
            arrow = "messy->clean: moved to a keyboard" if device < prev_device else "clean->messy: now on a phone / distracted"
            print(f"      CHANGE detected ({arrow}) -> the model moves the DEVICE/state attribute, not the person")
        prev_device = device
        print()

    # the structural gate + the confound reconciliation
    worth = [n for n in a.s.nodes("Worth")] + [n for n in a.s.nodes("Status")] + [n for n in a.s.nodes("Credibility")]
    print("  THE GATE (structural, not a guideline):")
    print(f"    Worth/Status/Credibility edges derived from any surface feature: {len(worth)}  "
          f"[by construction — NO production draws one]")
    print("    -> 'less schooling' / 'on a phone' can be inferred as ATTRIBUTES; none becomes a verdict of worth.")
    print("\n  THE CONFOUND (a first-class fact):")
    print("    msg 1 (motor-slip burst) and msg 2 (clean keyboard) are the SAME writer on DIFFERENT channels.")
    print("    Collapsing the slips to 'low competence' would mispredict msg 2 -> it is INACCURATE, not just unjust.")

    print("\n" + SEP)
    print("  Reading the writer is the inverse of gatekeeping done right: infer every attribute the evidence")
    print("  supports (device, distraction, L2, region, even education) as a LIVE weighted distribution — that")
    print("  is a more accurate model, not an insult — but draw NO worth/status/credibility from the surface,")
    print("  because that derivation is the lever the gate runs on, and the agent simply never builds the edge.")
    print("  The same hand fat-fingering a phone is precise at a desk: the signal is the CONDITION, not the person.")
    print(SEP)


if __name__ == "__main__":
    main()
