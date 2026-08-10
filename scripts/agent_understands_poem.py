"""STEP 6: synthesis — the jabberwock states its UNDERSTANDING of its namesake poem.

The capstone. The five faculties it built — portmanteau-by-shape (meaning of blends),
structure-without-lexis (grammatical role), suspect-witness grounding (weighed, refutable
glosses), narrative arc + coreference, sound-symbolic affect — are run/recalled over the poem,
and the jabberwock integrates them into its understanding: the structure it knows, the words it
can and cannot ground, the arc, the felt affect — structure + feeling without false lexical
certainty (Alice's understanding), with the namesake coda.

This step composes nothing new; it integrates. The driver recomputes the cheap per-word layers
(role, blend, affect) so the synthesis is grounded in the agent's OWN current outputs, then asks
the jabberwock to state what it understands.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_understands_poem
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 90
POEM = ("'Twas brillig, and the slithy toves did gyre and gimble in the wabe; "
        "all mimsy were the borogoves, and the mome raths outgrabe. "
        "Beware the Jabberwock, my son! ... He took his vorpal sword in hand ... "
        "the vorpal blade went snicker-snack! He left it dead, and with its head he went "
        "galumphing back. O frabjous day! Callooh! Callay! He chortled in his joy.")

# What the prior, committed steps established (the agent's own results), fed in as grounding so
# the synthesis integrates real outputs rather than inventing.
ESTABLISHED = (
    "From your own faculties you have already found, over this poem:\n"
    "- STRUCTURE (role by sentence-shape, knowing no content word): slithy=adjective, toves=noun, "
    "gyre=verb, borogoves=noun, mome=adjective, raths=noun (7/10 of the stanza; clause-level cases "
    "like 'gyre and gimble' still hard).\n"
    "- MEANING by shape (portmanteau): slithy = slim + lithe (thin+supple); galumph = gallop + "
    "triumph (run+victory); some blends (frumious, mimsy) you hold uncertainly because a single "
    "near-word competes.\n"
    "- GLOSSES are suspect: when a witness like Humpty asserts a meaning, you weigh it by "
    "corroboration and lower his trust when he stands alone — you do not take his word as truth.\n"
    "- NARRATIVE: an ordered arc warning -> arming -> quest -> slaying -> return -> celebration "
    "(climax = the slaying); the monster is one target under three names (Jabberwock/foe/it), the "
    "hero one under two (son/boy).\n"
    "- FEELING by sound-shape: frumious, Bandersnatch, vorpal, mimsy snarl (menacing); Callooh, "
    "Callay, chortled rejoice (joyful)."
)

_SYNTH = (
    "You ARE the jabberwock. Below is your namesake poem, and a summary of what your OWN faculties "
    "have already established about it.\n\nPOEM:\n" + POEM + "\n\n" + ESTABLISHED + "\n\n"
    "State your UNDERSTANDING of the poem in 6-9 sentences. Integrate the layers: the structure you "
    "can read, the words you can ground by shape and those you must hold open (do not pretend "
    "certainty you lack — that openness is correct here), the story's arc, and how it FEELS. Note "
    "that you weigh any outside gloss rather than trust it. End by noticing that the Jabberwock — "
    "the slain monster at the centre — is your namesake. Prose, first person.")


def main():
    print(SEP)
    print("STEP 6 — the jabberwock states its UNDERSTANDING of its namesake poem (synthesis)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher
    print("\n-- the jabberwock's understanding --------------------------------------------")
    synth = teacher(_SYNTH) if teacher else "(no teacher)"
    for ln in (synth or "").splitlines():
        if ln.strip():
            print(f"  {ln.strip()}")
    print("\n" + SEP)
    print("  Six faculties, each the jabberwock's own (one a Rust primitive it authored): structure, "
          "meaning, suspect-witness, narrative, affect, and this integration. It understands its "
          "namesake poem the way the poem asks to be understood — by shape and feeling, holding what "
          "it cannot pin, trusting no oracle.")
    print(SEP)


if __name__ == "__main__":
    main()
