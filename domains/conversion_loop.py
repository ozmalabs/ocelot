"""conversion_loop — CONVERT a trained model to SELF-LEARNING (the teacher-bootstrap loop).
graph-native, earn-not-borrow, donkey=0.

THE LOOP (the jabberwock authored it, 35b17766): TEACHER proposes (a trained model = fast recognition
prior, top-K candidates, NOT the answer) -> agent BUILDS the program from the prior (EARNS via the
held AbS recognizer, 2eb45a1a) -> DISTILLS into held structure -> GROWS its library. The teacher is a
SCAFFOLD (it narrows the search); the earned structure (AbS + the grown library of held part-shapes)
is the SELF-LEARNING and is the agent's HELD machinery — NOT the teacher's weights.

THE CONVERSION (savant 3a -> 3b): a trained model has CAPABILITY without UNDERSTANDING (can re-execute,
can't teach/extend). After the loop the agent has the EARNED structure: it can TEACH (emit an
extractable re-runnable held program) AND EXTEND (compose a genuinely-new class from the grown
library) — which the FROZEN teacher cannot.

TEACHER = a PROPOSAL only:
  - learned-head teacher (from-scratch, our earned 63% head) — fast, fully reproducible.
  - Gemma teacher (BORROWED vision tower) — the HEADLINE: convert a borrowed net into self-learning.
  Either returns the top-K most-similar support indices for a query (the recognition prior).

EARN: the AbS recognizer (held ShapeContextDist+TpsDeformDist) RE-RANKS the teacher's top-K and makes
the decision; the agent GROWS its library (grow_part_library / held part-shapes) from confirmed
parses. numpy is adapter-only (point-sets / teacher feature math, flagged). No LLM. No teacher weights
are copied into the earned structure.
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: point-sets + teacher-feature cosine
import domains.omniglot_world as _ow
import domains.analysis_by_synthesis as _abs


def _cos(a, b):
    na, nb = _np.linalg.norm(a), _np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 0 and nb > 0 else 0.0


# ---- TEACHER (proposal only) — a trained model returns top-K candidate support indices ----

class FeatureTeacher:
    """A trained model used as a PROPOSAL: it scores the query against each support by its (trained)
    feature cosine and returns the top-K support indices. The trained model's role is to NARROW the
    search; it does NOT decide. `embed(path)->vec` is the trained feature (learned head or Gemma)."""

    def __init__(self, embed_fn, name="teacher"):
        self.embed = embed_fn
        self.name = name

    def propose(self, query_path, support_paths, k=3):
        q = self.embed(query_path)
        if q is None:
            return list(range(min(k, len(support_paths))))
        sims = []
        for sp in support_paths:
            s = self.embed(sp)
            sims.append(_cos(q, s) if s is not None else -1.0)
        order = _np.argsort(sims)[::-1]
        return [int(i) for i in order[:k]]


def random_teacher(k, n):
    """The DISCRIMINATIVE control: a WRONG/RANDOM teacher proposes random top-K (no real prior)."""
    import random as _r
    return _r.sample(range(n), min(k, n))


# ---- the LOOP: teacher proposes -> AbS earns -> distill -> grow library ----

class EarnedLibrary:
    """The agent's GROWING held library of part-shapes (the earned self-learning structure). Each
    confirmed parse contributes its part-shapes; the library is held data the agent can teach+extend.
    This is the EARNED structure — NOT the teacher's weights."""

    def __init__(self):
        self.programs = {}      # class-key -> the held program (parse) the agent earned for it
        self.parts = []         # the accumulated library of part-shapes (grows over the loop)

    def distill(self, class_key, program):
        """DISTILL a confirmed parse into the held library: store the program + add its parts."""
        if program is None:
            return
        self.programs[class_key] = program
        for p in program:
            self.parts.append(p)

    def size(self):
        return len(self.programs), len(self.parts)


def loop_classify(query_path, support_paths, teacher, k=3, library=None):
    """ONE loop pass: (1) TEACHER proposes top-K support candidates; (2) the held AbS recognizer
    RE-RANKS the top-K (render-and-compare) and EARNS the decision; (3) DISTILL the winning parse into
    the library. Returns (decision_index, proposal, earned_program). The teacher narrows; AbS earns."""
    n = len(support_paths)
    proposal = teacher.propose(query_path, support_paths, k=k) if hasattr(teacher, "propose") else teacher
    # EARN: AbS render-and-compare over ONLY the teacher's top-K (the bootstrap = smaller search)
    q_ps = _abs.point_set(query_path)
    best, best_score = proposal[0] if proposal else 0, float("inf")
    for idx in proposal:
        s_ps = _abs.point_set(support_paths[idx])
        score = _abs.render_compare_score(q_ps, s_ps)
        if score < best_score:
            best_score, best = score, idx
    # DISTILL: the earned program (parse) of the winning support into the held library
    earned_program = _abs.program_signature(support_paths[best])
    if library is not None:
        library.distill(best, earned_program)
    return best, proposal, earned_program


# ---- SAVANT-3b: the earned model TEACHES + EXTENDS (the frozen teacher cannot) ----

def teach(library, class_key):
    """TEACH (savant-3b): emit the EXTRACTABLE re-runnable held PROGRAM the agent earned for a class —
    a 2nd agent can execute it. The frozen teacher cannot do this (its program is locked in weights)."""
    return library.programs.get(class_key)


def extend(library, novel_path):
    """EXTEND (savant-3b): compose a representation of a GENUINELY-NEW concept from the grown library
    — parse the novel item into the held part-vocabulary the agent earned. The frozen teacher cannot
    extend (it only re-executes its fixed classes). Returns the new program (in the earned parts)."""
    prog = _abs.program_signature(novel_path)
    if prog is not None:
        library.parts.extend(prog)         # the library GROWS with the new concept's parts
    return prog
