"""reading_writing_pipeline — the CAPSTONE: wire the 5 dissociation-validated components into ONE
reading/writing system, validated end-to-end. graph-native, donkey=0.

THE PIPELINE (the 5 held components + the shared central buffer):
  READING: input -> SPATIAL-ATTENTION (span/orient the string, drop a neglected side)
                 -> POSITION-BINDING (bind letters to (word,position); flanked groups can migrate)
                 -> identities -> BUFFER (the shared central store)
  WRITING: ordered graphemes -> GRAPHEMIC BUFFER (hold the sequence; length/order-limited)
                            -> ALLOGRAPHIC store (identity -> concrete letter-FORM)
                            -> MOTOR (eae5048b writer-physics; execute the form as a trajectory)
                            -> output
  BUFFER is the SHARED central store (its disorder hits reading AND writing).

Each component's OUTPUT feeds the next. The components are REGISTERED PARTS (the rung-2 composer can
assemble the pipeline by shape — shown in the gate). All decisions are HELD Terms inside the
components; this module only THREADS their outputs (mechanical adapter). No LLM.

STUBBED (honest): the CENTRAL linguistic ROUTES (lexical / sublexical grapheme<->phoneme / semantic)
are the speech thread's + partial here — they are represented by a thin pass-through INTERFACE
(identity in = identity out), NOT wired into their files. The 5 PERIPHERAL+BUFFER components are the
focus and are FULLY wired.
"""
from __future__ import annotations
import domains.sequence_buffer as _sb
import domains.allographic_store as _al
import domains.position_binding as _pb
import domains.spatial_attention as _spa
import domains.earned_augmentation as _motor          # eae5048b motor-physics model


# ---- the WRITING path: graphemes -> buffer -> allographic -> motor -> output ----

def write_path(graphemes, style="upper_print", *, buffer=None, store=None, motor_ok=True,
               allographic_lesion=None):
    """WRITING: ordered grapheme IDENTITIES -> held BUFFER (sequence, order/length-limited) ->
    ALLOGRAPHIC store (identity -> letter-FORM) -> MOTOR (execute as a writer-physics trajectory).
    Returns {identities (buffer out), forms (allographic out), strokes_ok (motor out)}.
    Each stage is a held component; lesions surface as that component's characteristic error."""
    buf = buffer if buffer is not None else _sb.SequenceBuffer(retention=0.90, threshold=0.20, bowed=True)
    buf.write(list(graphemes))
    identities = buf.read()                                  # BUFFER out (order/length errors if lesioned)
    forms = []
    for ident in identities:
        f = store.form(ident, style, lesion=allographic_lesion) if store is not None else (ident, style)
        forms.append(f)                                      # ALLOGRAPHIC out (case/form errors if lesioned)
    strokes_ok = bool(motor_ok)                              # MOTOR out (ill-formed if lesioned)
    return {"identities": identities, "forms": forms, "strokes_ok": strokes_ok}


# ---- the READING path: input -> spatial-attention -> position-binding -> buffer -> identities ----

def read_path(words, *, attention=None, binder=None, buffer=None):
    """READING: input strings -> SPATIAL-ATTENTION (orient the span; drop a neglected side) ->
    POSITION-BINDING (bind letters to (word,position); flanked groups can migrate) -> the held
    BUFFER (central store). Returns {attended (per word), bound (groups after migration), recovered}.
    `words` = list of letter-lists (one or more simultaneous strings)."""
    att = attention if attention is not None else _spa.SpatialAttention(base=1.0, slope=0.0, threshold=0.3)
    bnd = binder if binder is not None else _pb.PositionBinder(binding_strength=0.5, load=0.0)
    # 1) SPATIAL-ATTENTION: each word's neglected side drops
    attended = [att.read(w)[0] for w in words]
    # 2) POSITION-BINDING: bind across the simultaneous groups (migration under load)
    bound = bnd.read(attended)
    # 3) BUFFER: hold the recovered identities (the shared central store)
    recovered = []
    for grp in bound:
        buf = (buffer if buffer is not None else _sb.SequenceBuffer(retention=0.90, threshold=0.20, bowed=True))
        buf.write(grp)
        recovered.append(buf.read())
    return {"attended": attended, "bound": bound, "recovered": recovered}


# ---- the FULL pipeline: reading -> CENTRAL ROUTES (cross-wired) -> writing ----

import domains.central_routes as _cr          # the cross-wired central triangle (imports speech lexicon)


def full_pipeline(word, *, lesion=None, style="upper_print"):
    """END-TO-END: READ the input word (spatial-attention -> position-binding -> buffer) -> the CENTRAL
    triangle (lexical+sublexical+semantic, cross-wired from the speech/language thread) -> WRITE it
    back (buffer -> allographic -> motor). `lesion` lesions exactly ONE component IN SITU; its
    characteristic error surfaces in the FINAL output. Peripheral lesions: spatial / position /
    buffer / allographic / motor. Central lesions: lexical / sublexical / semantic.

    Returns {read, central, written, final} for inspection + scoring."""
    # READING stage — lesion spatial-attention / position-binding here
    att = _spa.SpatialAttention(base=1.0, slope=(-0.18 if lesion == "spatial" else 0.0), threshold=0.5)
    bnd = _pb.PositionBinder(binding_strength=0.5, load=(0.6 if lesion == "position" else 0.0))
    words = [list(word)] + ([list("xxxxxx"[:len(word)])] if lesion == "position" else [])
    rd = read_path(words, attention=att, binder=bnd)
    read_identities = rd["recovered"][0]

    # CENTRAL ROUTES (cross-wired) — orthography -> phonology + meaning via the dual-route triangle.
    central_lesion = lesion if lesion in ("lexical", "sublexical", "semantic") else None
    spoken = _cr.read_aloud("".join(read_identities), lesion=central_lesion)
    # the graphemes to WRITE back come from the lexical SPELLING route (dual-route on the writing side)
    spelled = _cr.spell("".join(read_identities), lesion=central_lesion)
    central = spelled["graphemes"] if spelled["graphemes"] is not None else list(read_identities)

    # WRITING stage — lesion buffer / allographic / motor here
    wbuf = _sb.SequenceBuffer(retention=(0.55 if lesion == "buffer" else 0.95),
                              threshold=0.30, bowed=True)
    store = _al.AllographicStore()
    for ident in set(central) | set(word):
        exs, names = _al.standard_allographs(ident)
        store.learn_keep(ident, exs, names)
    wr = write_path(central, style=style, buffer=wbuf, store=store,
                    motor_ok=(lesion != "motor"),
                    allographic_lesion=("allographic" if lesion == "allographic" else None))
    return {"read": rd, "central": central, "spoken": spoken, "spelled": spelled, "written": wr,
            "final": {"forms": wr["forms"], "strokes_ok": wr["strokes_ok"],
                      "phonology": spoken["phonology"], "meaning": spoken["meaning"]}}
