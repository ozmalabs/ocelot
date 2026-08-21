#!/usr/bin/env python3
"""Figure IN-1 -- the chain, from a boring meeting to a theory of collapse.

Conceptual, and the introduction's only figure. Ten links, each a real
artefact. Its job is to make one point visible that the prose can only assert:
every arrow is the SAME move -- ask what the unnamed assumption is, and follow
the answer -- applied at a larger scale each time.

Dates are from public git history and the documents named in BOOK_SOURCES.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "intro_1_chain.svg")

LINKS = [
    ("a boring meeting", "play games through it; blend both audio streams",
     "", sp.NULLC),
    ("no good KVM+A exists", "hardware is clunky, software is duct tape",
     "", sp.NULLC),
    ("so build one", "a software-defined KVMA router; the USB never moves",
     "2026-04-01", sp.ARM_A),
    ("the problem keeps growing", "keyboard = video = audio = network = power",
     "", sp.ARM_A),
    ("one typed map", "labelled things, labelled connections, any scale",
     "77k-word spec", sp.ARM_A),
    ("the tooling bill", "every model-to-model link needs bespoke glue",
     "", sp.ARM_A),
    ("a semiotic layer for models",
     "a protocol; the shared knowledge base is, again, a map", "", sp.ARM_A),
    ("THE COLLISION", "the KVMA map and the model map are the SAME map",
     "unplanned", sp.ARM_B),
    ("the key is not the graph — it is Γ",
     "what matters is what the map is ALLOWED to become", "", sp.ARM_B),
    ("so the model was scaffolding",
     "if Γ generates and the substrate realises, no LLM is needed", "",
     sp.ARM_B),
    ("then physics",
     "the tick was already possibility-then-realise; QM is where the "
     "distinction is irreducible", "2026-04-25", sp.ACCENT),
    ("collapse leaves residual", "which is the spine of everything after this",
     "", sp.ACCENT),
]


def main():
    W, H = 780, 636
    f = sp.Fig(W, H)
    f.title(46, 34, "How I got here",
            "Twelve links. Every arrow is the same question asked again, one "
            "scale up.")

    x, y = 60, 74
    for i, (name, gloss, stamp, col) in enumerate(LINKS):
        f.circle(x, y + 9, 5.4, fill=col if col != sp.NULLC else "none",
                 stroke=col, sw=1.6)
        if i < len(LINKS) - 1:
            f.line(x, y + 16, x, y + 38, sp.RULE, 1.4)
        f.text(x + 18, y + 8, name, cls="lbl")
        f.text(x + 18, y + 23, gloss, cls="note")
        if stamp:
            f.text(734, y + 8, stamp, cls="val", anchor="end", fill=sp.MUTED)
        y += 38

    f.line(46, 542, 734, 542, sp.RULE, 0.8)
    f.text(46, 564, "The method, which is the point", cls="lbl")
    f.text(46, 582,
           "\"What are the unnamed assumptions here?\" — asked of the answer, "
           "repeatedly, until the answer stops", cls="note")
    f.text(46, 596,
           "changing. It took about ten passes to believe the word "
           "\"everything\", because every scope word", cls="note")
    f.text(46, 610,
           "smuggled in a boundary: in computing, on the planet. Ten passes is "
           "a mint, not a delay.", cls="note")

    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
