"""allographic_store — the ALLOGRAPHIC STORE: maps an ABSTRACT GRAPHEME (letter identity) to a
CONCRETE LETTER-FORM (allograph: case/style), graph-native, donkey=0.

THE MISSING LINK (the 3-level writing pipeline):
  graphemic BUFFER (1e66d484)  — abstract grapheme-IDENTITY at a POSITION
        |  (identity -> form)
  ALLOGRAPHIC STORE (here)     — identity + style -> a concrete letter-FORM (uppercase/lowercase/
        |                        print/cursive); selects among case/style variants of ONE identity
  MOTOR model (eae5048b)       — executes the form as a writer-physics trajectory

STYLE/CONTENT at the LETTER LEVEL (the held shape-math): a letter IDENTITY is a TEMPLATE (the
fixed content + WILD style slots); an ALLOGRAPH is Substitute(template, style-σ). The held
AntiUnifyWitness extracts (template, per-allograph σ) from exemplars of the same identity; Substitute
re-applies a chosen σ -> the form. Same identity, different form = same template, different σ. This
IS the writer-shape style residual (5695f2b3) at the per-letter grain.

ALL maps are HELD Terms (AntiUnifyWitness / Substitute / IndexAt) run by the Rust evaluator; the
tuple-keyed σ never leaves Rust (the witness is chained into Substitute as one Term tree). No LLM.
The DISSOCIATION (the test): lesion the allographic σ-selection -> RIGHT identity/order, WRONG FORM
(well-formed-but-wrong-allograph: case errors), NOT order errors, NOT ill-formed strokes.
"""
from __future__ import annotations
import substrate_rs as _srs

_S = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}
WILD = "·?·"


def _ev(term, env=None):
    return _S.evaluate(term, env or {})


def _witness_term(exemplars):
    """The held AntiUnifyWitness over allograph exemplars of ONE identity -> (template, sigmas).
    template = identity + WILD style slots (the CONTENT); sigmas = per-allograph style residuals."""
    return {"type": "AntiUnifyWitness", "values": _L([list(x) for x in exemplars]), "wild": WILD}


class AllographicStore:
    """identity -> concrete letter-FORM. For each grapheme identity it holds a TEMPLATE (content +
    WILD style slots) and a dict {style_name -> style-σ index}; selecting a style Substitutes that
    σ into the template -> the form. All via HELD shape-math Terms.

    An allograph exemplar = [identity, case, style, ...form-features]. AntiUnifyWitness factors the
    shared identity (template) from the varying style (σ). lesion='allographic' mis-selects the σ
    (wrong allograph, still well-formed); lesion=None is intact."""

    def __init__(self):
        self.templates = {}     # identity -> template tuple (held witness output)
        self.sigmas = {}        # identity -> list of style-σ (held)
        self.style_index = {}   # identity -> {style_name -> sigma position}

    def learn(self, identity, exemplars, style_names):
        """Learn an identity's template + its allograph σ from exemplars (same identity, different
        case/style). Held AntiUnifyWitness does the style/content split."""
        w = _ev(_witness_term(exemplars))
        self.templates[identity] = list(w[0])
        self.sigmas[identity] = [s for s in w[1]]
        self.style_index[identity] = {nm: i for i, nm in enumerate(style_names)}
        return self

    def form(self, identity, style, lesion=None):
        """Map identity + requested style -> the concrete letter-FORM (held Substitute of the chosen
        style-σ into the template). lesion='allographic' -> select the WRONG σ (a different style of
        the SAME identity): well-formed but wrong allograph (the allographic dissociation)."""
        if identity not in self.templates:
            return None
        idx_map = self.style_index[identity]
        want = idx_map.get(style, 0)
        if lesion == "allographic":
            # mis-select: pick a DIFFERENT allograph of the same identity (wrong case/style).
            n = len(self.sigmas[identity])
            want = (want + 1) % n if n > 1 else want
        # held chain: Substitute(template, sigmas[want]) — the tuple-keyed σ stays in Rust by
        # rebuilding the witness Term and indexing into it.
        # (we re-evaluate from stored template + a Lit-safe σ rebuilt as a held value)
        return self._substitute(identity, want)

    def _substitute(self, identity, sigma_idx):
        """Held Substitute of sigmas[identity][sigma_idx] into the template — chained so the
        tuple-keyed σ never round-trips through Python/JSON."""
        # rebuild the witness so the sigma is a live Rust value, then IndexAt + Substitute.
        # We stored the exemplars-derived witness implicitly; re-derive from template+sigmas is not
        # JSON-safe, so we keep the original exemplars to rebuild the witness Term.
        exs = self._exemplars.get(identity)
        if exs is None:
            return None
        witness = _witness_term(exs)
        tmpl = {"type": "IndexAt", "seq": witness, "index": _L(0)}
        sigs = {"type": "IndexAt", "seq": witness, "index": _L(1)}
        sig = {"type": "IndexAt", "seq": sigs, "index": _L(int(sigma_idx))}
        return tuple(_ev({"type": "Substitute", "template": tmpl, "sigma": sig, "wild": WILD}))

    _exemplars: dict = {}

    def learn_keep(self, identity, exemplars, style_names):
        """learn() + retain the exemplars (needed to rebuild the held witness for Substitute)."""
        self._exemplars = dict(self._exemplars)
        self._exemplars[identity] = [list(x) for x in exemplars]
        return self.learn(identity, exemplars, style_names)


def standard_allographs(identity):
    """A small allograph exemplar set for a letter identity: 4 case/style forms (the form-features
    are abstract tokens — domain-neutral; a renderer/motor turns them into strokes)."""
    return (
        [[identity, "upper", "print", "f0"], [identity, "lower", "print", "f1"],
         [identity, "upper", "cursive", "f2"], [identity, "lower", "cursive", "f3"]],
        ["upper_print", "lower_print", "upper_cursive", "lower_cursive"],
    )
