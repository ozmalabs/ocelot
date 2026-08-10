"""file_ingest — uploaded-file ingest (host I/O only, CLAUDE.md).

Mechanical translation of an on-disk upload into substrate mutations. The
boundary classifies by mime/extension only (no graph-state decisions), then:

  • text/markdown/json/csv/html  -> UploadedDocument + Mention tokenisation
  • source (.py/.rs/.lua)        -> UploadedDocument + CST/AST graph + code
                                    register facts + hub Program IR (P2)
  • image/*                      -> Image node(s) via substrate_rs.vision
  • application/pdf              -> rasterise pages (pdftoppm) -> Image nodes
  • audio/*                      -> ingest_audio_file (speech bridge)
  • other                        -> UploadedDocument metadata only (honest miss)

Each ingest mints an interlocutor Message (optional caption) with
`has_attachment` edges so the agent's conversation rules can treat the turn
like any other received utterance. Caller runs `agent.comprehend()` after.
"""
from __future__ import annotations

import mimetypes
import os
import subprocess
import tempfile
from typing import Any

_MENTION_STRIP = ".,?!;:()[]\"'"

_TEXT_EXTENSIONS = frozenset({
    ".txt", ".md", ".markdown", ".json", ".csv", ".tsv", ".log", ".yaml", ".yml",
    ".xml", ".html", ".htm", ".rst", ".tex",
})
# Source code takes a PARALLEL route, not the text route (P2,
# PROGRAM_SYNTHESIS_PLAN.md §4): the text pipeline mention-tokenises the
# body for the conversation rules — the wrong instrument for code (it would
# pollute referent resolution with identifiers). A source upload instead
# lands as a CST/AST graph + code-register facts + hub Program IR where the
# frame's reader covers it. Extension -> language (the parse dispatch is a
# mechanical extension table, not a graph-state decision).
_SOURCE_EXTENSIONS = {
    ".py": "python",
    ".rs": "rust",
    ".lua": "lua",
}
_IMAGE_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".pgm", ".ppm",
})
_AUDIO_EXTENSIONS = frozenset({
    ".wav", ".mp3", ".ogg", ".flac", ".webm", ".m4a", ".aac", ".opus",
})
_PDF_EXTENSIONS = frozenset({".pdf"})

_MAX_TEXT_CHARS = 200_000
_MAX_PDF_PAGES = 8


def _guess_mime(path: str, mime: str | None) -> str:
    if mime and str(mime).strip():
        return str(mime).strip().lower()
    guessed, _ = mimetypes.guess_type(path)
    return (guessed or "application/octet-stream").lower()


def classify_upload(mime: str, filename: str) -> str:
    """Mechanical kind from mime + extension. One of
    text|source|image|pdf|audio|binary. Source extensions are checked
    BEFORE the text/mime test (a .py file's mime is text/x-python — the
    extension names the frame)."""
    mime = (mime or "").lower()
    ext = os.path.splitext(str(filename or ""))[1].lower()
    if ext in _SOURCE_EXTENSIONS:
        return "source"
    if mime.startswith("text/") or ext in _TEXT_EXTENSIONS:
        return "text"
    if mime.startswith("image/") or ext in _IMAGE_EXTENSIONS:
        return "image"
    if mime == "application/pdf" or ext in _PDF_EXTENSIONS:
        return "pdf"
    if mime.startswith("audio/") or ext in _AUDIO_EXTENSIONS:
        return "audio"
    return "binary"


def _read_text_bytes(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _summarize_text(filename: str, text: str) -> str:
    preview = (text or "").replace("\n", " ").strip()[:300]
    n = len(text or "")
    return (
        f"I hold your uploaded text file ({filename}, {n} characters). "
        f"It begins: {preview}"
    )


def _summarize_image(filename: str, arr) -> str:
    h, w = int(arr.shape[0]), int(arr.shape[1])
    mean = arr.mean(axis=(0, 1))
    r, g, b = int(mean[0]), int(mean[1]), int(mean[2])
    return (
        f"I hold your uploaded image ({filename}, {w}×{h} pixels). "
        f"Average colour is about RGB({r},{g},{b}). "
        f"Pixel data is in my graph; I have not run full object recognition yet."
    )


def _summarize_pdf(filename: str, page_count: int) -> str:
    return (
        f"I hold your uploaded PDF ({filename}, {page_count} page(s) rasterised). "
        f"Page images are in my graph; I have not run full document understanding yet."
    )


def _summarize_binary(filename: str, byte_length: int) -> str:
    return (
        f"I hold your uploaded file ({filename}, {byte_length} bytes) "
        f"but have no parser for this type yet."
    )


def _finish_ingest(agent, doc_id, out: dict) -> dict:
    """Track current attachment + tick comprehension — mechanical I/O only."""
    agent._set_current_attachment(doc_id)  # noqa: SLF001
    try:
        agent.comprehend()
    except Exception:  # noqa: BLE001 — ingest succeeded; comprehension is best-effort
        pass
    return out


def _tokenise_document(agent, doc_id, text: str) -> int:
    """Mention chain on a document node — same shape as fetch_dispatch."""
    S, I = agent.s, agent.inner
    prev = None
    count = 0
    for raw in (text or "").split():
        clean = raw.strip(_MENTION_STRIP).lower()
        if not clean:
            continue
        mn = S.add_node("Mention", {"text": clean})
        I.add_edge_unchecked(doc_id, "has_mention", mn)
        if prev is not None:
            I.add_edge_unchecked(prev, "next_mention", mn)
            I.add_edge_unchecked(mn, "prev_mention", prev)
        prev = mn
        count += 1
    return count


def _attach_message(agent, *, filename: str, kind: str, caption: str | None,
                    attachment_ids: list) -> Any:
    agent._ensure_intent_seeds()  # noqa: SLF001 — speech-act edges for comprehend
    S, I = agent.s, agent.inner
    label = (caption or "").strip() or f"[uploaded {kind}: {filename}]"
    mid = S.add_node("Message", {
        "from": "interlocutor",
        "source": "upload",
        "text": label,
        "upload_filename": str(filename),
        "upload_kind": str(kind),
    })
    I.add_edge_unchecked(agent.agent, "received", mid)
    statement = agent._concept_by_name("statement")  # noqa: SLF001 — mechanical ingest
    if statement is None:
        statement = S.add_node("Concept", {"name": "statement"})
    interlocutor = agent._interlocutor()  # noqa: SLF001
    I.add_edge_unchecked(mid, "has_speech_act", statement)
    I.add_edge_unchecked(mid, "sent_by", interlocutor)
    for att in attachment_ids:
        if att is not None and I.has_node(att):
            I.add_edge_unchecked(mid, "has_attachment", att)
    return mid


def _ingest_text(agent, path: str, filename: str, data: bytes, caption: str | None) -> dict:
    text = _read_text_bytes(data)
    if len(text) > _MAX_TEXT_CHARS:
        text = text[:_MAX_TEXT_CHARS]
    S, I = agent.s, agent.inner
    doc = S.add_node("UploadedDocument", {
        "filename": filename,
        "kind": "text",
        "mime": _guess_mime(path, None),
        "byte_length": len(data),
        "text": text,
        "summary": _summarize_text(filename, text),
    })
    n_mentions = _tokenise_document(agent, doc, text)
    mid = _attach_message(agent, filename=filename, kind="text", caption=caption,
                          attachment_ids=[doc])
    # DEEP READ (Wave 4, Deep-Reader unification): opt-in, same flag family as
    # shadow_read (see WorldAdapter.__init__) -- one-shot full deep-read of
    # the document text, register-routed (encyclopedic/narrative/casual BY
    # SHAPE) + the HeldAnswer bridge. A bench agent that never sets
    # deep_ingest/shadow_read is byte-unchanged (no flow, no HeldAnswers).
    if getattr(agent, "deep_ingest", False):
        agent._deep_read_document(doc, text)  # noqa: SLF001 -- mechanical ingest hook
    preview = text[:400].replace("\n", " ")
    return {
        "kind": "text",
        "message_id": mid,
        "document_id": doc,
        "n_mentions": n_mentions,
        "preview": preview,
        "byte_length": len(data),
    }


_PROG_READ_GAP_SEED = "prog_read_gap"


def _install_prog_read_gap_seed(agent) -> None:
    """Make the prog-read gap RULES available on this agent — idempotent
    mechanical seed I/O (the ts_ingest.install_correspondence_seed idiom;
    a fully-booted agent already holds it via load_all_seeds, detected by
    its SeedSummary). The seed's rule decides what is a gap; this only
    loads graph data."""
    S, I = agent.s, agent.inner
    try:
        for n in S.nodes("Seed"):
            if S.node(n)["attrs"].get("id") == _PROG_READ_GAP_SEED:
                return
        for n in S.nodes("SeedSummary"):
            if S.node(n)["attrs"].get("seed_id") == _PROG_READ_GAP_SEED:
                return
    except Exception:  # noqa: BLE001 — an unreadable graph falls through to load
        pass
    import json as _json

    from substrate.seed_loader import engine_rules_only
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "seeds", f"{_PROG_READ_GAP_SEED}.json")
    with open(path) as f:
        manifest = _json.load(f)
    I.load_seed_manifest(engine_rules_only(manifest), agent.agent)
    S.add_node("Seed", {"id": _PROG_READ_GAP_SEED,
                        "version": manifest.get("version", "1.0.0")})


def _record_read_blocked(inner, node_id, frame: str, blockers) -> None:
    """Record the FACT of a blocked read as attrs on the ingested node —
    a datum, never a decision. The DECISION that a blocked read is a gap
    (SelfConcern{kind:'prog_read'}) lives in seeds/prog_read_gap.json."""
    inner.set_attr(node_id, "read_blocked", 1.0)
    inner.set_attr(node_id, "read_blockers",
                   ",".join(sorted({str(b) for b in blockers})))
    inner.set_attr(node_id, "frame", frame)


def _summarize_source(filename: str, language: str, n_functions: int,
                      n_ok: int) -> str:
    return (
        f"I hold your uploaded {language} source file ({filename}): "
        f"{n_functions} function(s) parsed into my code graph, "
        f"{n_ok} fully read into my program IR."
    )


def _ingest_source(agent, path: str, filename: str, data: bytes,
                   caption: str | None) -> dict:
    """Source upload → CST/AST graph + code-register facts + hub Program IR
    (P2, PROGRAM_SYNTHESIS_PLAN.md §4). Mechanical translation only:

      · parse via the frame's reader (python → stdlib ast ingest; rust/lua
        → the tree-sitter world adapter) and wire the code graph under the
        document (`has_code_root` edges);
      · fold rust/lua functions into hub Program IR by applying the
        correspondence SEEDS (the walkers decide nothing — the table does);
        ok functions land as reflected IR subgraphs (`has_prog_ir` edges),
        blocked ones record their honest blocker lists;
      · record the code REGISTER verdict (register_source.decode_register —
        the ShapeDecode collapse decides; this only writes the read-back).
    """
    text = _read_text_bytes(data)
    if len(text) > _MAX_TEXT_CHARS:
        text = text[:_MAX_TEXT_CHARS]
    language = _SOURCE_EXTENSIONS[os.path.splitext(filename)[1].lower()]
    S, I = agent.s, agent.inner
    doc = S.add_node("UploadedDocument", {
        "filename": filename,
        "kind": "source",
        "language": language,
        "mime": _guess_mime(path, None),
        "byte_length": len(data),
        "text": text,
    })

    # 1) the code graph (CST/AST) — mechanical parse + dump.
    n_functions = n_ok = 0
    blockers: list = []
    if language == "python":
        import ast as _pyast

        from domains import ast_to_term, prog_ir_emit
        ast_to_term.open_ast_productions(S)
        try:
            rec = ast_to_term.ingest_ast(S, text, root_label=filename)
            for fname, root in sorted(rec.get("func_roots", {}).items()):
                I.add_edge_unchecked(doc, "has_code_root", root)
                n_functions += 1
            I.set_attr(doc, "n_code_nodes", int(rec.get("n_nodes", 0)))
            # hub IR per TOP-LEVEL function via the P2-Python track's
            # emitter (domains/prog_ir_emit) — attached exactly the way the
            # rust/lua branch below attaches its reads: an ok function
            # lands as a reflected Term subgraph (`has_prog_ir`, ProgEval-
            # runnable); a blocked one records its honest blocker FACTS on
            # its own code-root node (the rule decides if that is a gap).
            for fn_def in rec["tree"].body:
                if not isinstance(fn_def, _pyast.FunctionDef):
                    continue
                emitted = prog_ir_emit.emit_prog_ir(fn_def)
                if emitted["ok"]:
                    n_ok += 1
                    ir_root = I.add_term_subgraph(emitted["ir"])
                    I.set_attr(ir_root, "prog_name", fn_def.name)
                    I.add_edge_unchecked(doc, "has_prog_ir", ir_root)
                else:
                    blockers.extend(emitted["blockers"])
                    froot = rec.get("func_roots", {}).get(fn_def.name)
                    if froot is not None:
                        _record_read_blocked(I, froot, "python",
                                             emitted["blockers"])
        except SyntaxError as e:
            I.set_attr(doc, "parse_error", str(e))
    else:
        from domains import prog_ir_lua, prog_ir_rust, ts_ingest
        ts_ingest.open_cst_productions(S)
        reader = prog_ir_rust if language == "rust" else prog_ir_lua
        rec = reader.read_source(S, text)
        I.add_edge_unchecked(doc, "has_code_root", rec["root"])
        I.set_attr(doc, "n_code_nodes", int(rec.get("n_cst_nodes", 0)))
        for fn in rec["functions"]:
            n_functions += 1
            if fn["ok"]:
                n_ok += 1
                # 2) hub IR, graph-resident (the reflected Term subgraph).
                ir_root = I.add_term_subgraph(fn["ir"])
                I.set_attr(ir_root, "prog_name", fn["name"] or "")
                I.add_edge_unchecked(doc, "has_prog_ir", ir_root)
            else:
                blockers.extend(fn["blockers"])
    I.set_attr(doc, "n_functions", n_functions)
    I.set_attr(doc, "n_ir_ok", n_ok)
    if blockers:
        import json as _json
        I.set_attr(doc, "ir_blockers", _json.dumps(sorted(set(blockers))))
        # blocked-read FACTS on the source document (frame + blocker
        # summary); seeds/prog_read_gap.json's rule reads these and DECIDES
        # whether to file a SelfConcern{kind:'prog_read'}.
        _record_read_blocked(I, doc, language, blockers)
    _install_prog_read_gap_seed(agent)

    # 3) code-register facts — the register decode's own verdict, recorded.
    try:
        from domains import register_source as _rs
        verdict = _rs.decode_register(agent, text)
        if verdict.get("register"):
            I.set_attr(doc, "register", verdict["register"])
            I.set_attr(doc, "register_family", verdict.get("family") or "")
    except Exception:  # noqa: BLE001 — register facts are best-effort I/O
        pass

    I.set_attr(doc, "summary",
               _summarize_source(filename, language, n_functions, n_ok))
    mid = _attach_message(agent, filename=filename, kind="source",
                          caption=caption, attachment_ids=[doc])
    return {
        "kind": "source",
        "language": language,
        "message_id": mid,
        "document_id": doc,
        "n_functions": n_functions,
        "n_ir_ok": n_ok,
        "ir_blockers": sorted(set(blockers)),
        "byte_length": len(data),
        "preview": text[:400].replace("\n", " "),
    }


def _ingest_image(agent, path: str, filename: str, caption: str | None) -> dict:
    import numpy as np
    from substrate_rs import vision as _vision

    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("Pillow is required for image ingest") from e

    img = Image.open(path)
    img.load()
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:  # noqa: BLE001
        pass
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg
    else:
        img = img.convert("RGB")
    arr = np.asarray(img)
    image_id = _vision.image_from_array(agent.inner, arr, origin="upload")
    S, I = agent.s, agent.inner
    I.set_attr(image_id, "upload_filename", filename)
    doc = S.add_node("UploadedDocument", {
        "filename": filename,
        "kind": "image",
        "mime": _guess_mime(path, None),
        "width": int(arr.shape[1]),
        "height": int(arr.shape[0]),
        "channels": int(arr.shape[2]) if arr.ndim == 3 else 1,
    })
    I.add_edge_unchecked(doc, "has_image", image_id)
    agent.perceive_upload_image(arr, doc)  # noqa: SLF001 — sets vision_summary
    # Pixel fallback if GraphEye produced no summary (best-effort).
    if not S.node(doc)["attrs"].get("summary"):
        I.set_attr(doc, "summary", _summarize_image(filename, arr))
    mid = _attach_message(agent, filename=filename, kind="image", caption=caption,
                          attachment_ids=[doc, image_id])
    return {
        "kind": "image",
        "message_id": mid,
        "document_id": doc,
        "image_ids": [image_id],
        "width": int(arr.shape[1]),
        "height": int(arr.shape[0]),
        "preview": f"image {arr.shape[1]}×{arr.shape[0]}",
    }


def _ingest_pdf(agent, path: str, filename: str, caption: str | None) -> dict:
    import numpy as np
    from substrate_rs import vision as _vision

    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("Pillow is required for PDF page rasterisation") from e

    with tempfile.TemporaryDirectory(prefix="jbw_pdf_") as tmp:
        prefix = os.path.join(tmp, "page")
        try:
            subprocess.run(
                ["pdftoppm", "-png", "-f", "1", "-l", str(_MAX_PDF_PAGES), path, prefix],
                check=True, capture_output=True, timeout=120)
        except FileNotFoundError as e:
            raise RuntimeError("pdftoppm not found — install poppler for PDF ingest") from e
        except subprocess.CalledProcessError as e:
            err = (e.stderr or b"").decode("utf-8", errors="replace")[:200]
            raise RuntimeError(f"pdftoppm failed: {err or e}") from e

        pages = sorted(
            f for f in os.listdir(tmp)
            if f.startswith("page") and f.endswith(".png"))
        if not pages:
            raise RuntimeError("pdftoppm produced no pages")

        S, I = agent.s, agent.inner
        doc = S.add_node("UploadedDocument", {
            "filename": filename,
            "kind": "pdf",
            "mime": "application/pdf",
            "page_count": len(pages),
        })
        image_ids = []
        for i, name in enumerate(pages):
            page_path = os.path.join(tmp, name)
            arr = np.asarray(Image.open(page_path).convert("RGB"))
            iid = _vision.image_from_array(agent.inner, arr, origin="upload")
            I.set_attr(iid, "upload_filename", filename)
            I.set_attr(iid, "page_index", float(i))
            I.add_edge_unchecked(doc, "has_page", iid)
            image_ids.append(iid)

        I.set_attr(doc, "summary", _summarize_pdf(filename, len(image_ids)))

    mid = _attach_message(agent, filename=filename, kind="pdf", caption=caption,
                          attachment_ids=[doc, *image_ids])
    return {
        "kind": "pdf",
        "message_id": mid,
        "document_id": doc,
        "image_ids": image_ids,
        "page_count": len(image_ids),
        "preview": f"pdf {len(image_ids)} page(s) rasterised",
    }


def _ingest_audio(agent, path: str, filename: str, caption: str | None) -> dict:
    heard = agent.ingest_audio_file(path, comprehend=True)
    S, I = agent.s, agent.inner
    doc = S.add_node("UploadedDocument", {
        "filename": filename,
        "kind": "audio",
        "mime": _guess_mime(path, None),
        "utterance_count": len(heard),
    })
    attachment_ids = [doc]
    for item in heard:
        sign = item.get("sign")
        if sign is not None:
            I.add_edge_unchecked(doc, "has_utterance", sign)
            attachment_ids.append(sign)
    mid = _attach_message(agent, filename=filename, kind="audio", caption=caption,
                          attachment_ids=attachment_ids)
    signs = [agent.s.node(h["sign"])["attrs"].get("text", "")
             for h in heard if h.get("sign") is not None]
    return {
        "kind": "audio",
        "message_id": mid,
        "document_id": doc,
        "n_utterances": len(heard),
        "heard": [s for s in signs if s],
        "preview": ", ".join(signs[:5]) if signs else "audio (no recognised signs)",
    }


def _ingest_binary(agent, path: str, filename: str, data: bytes, mime: str,
                   caption: str | None) -> dict:
    S = agent.s
    doc = S.add_node("UploadedDocument", {
        "filename": filename,
        "kind": "binary",
        "mime": mime,
        "byte_length": len(data),
        "summary": _summarize_binary(filename, len(data)),
    })
    mid = _attach_message(agent, filename=filename, kind="binary", caption=caption,
                          attachment_ids=[doc])
    return {
        "kind": "binary",
        "message_id": mid,
        "document_id": doc,
        "byte_length": len(data),
        "preview": f"binary file ({len(data)} bytes) — no parser for this type",
    }


def ingest_file(agent, path: str, *, filename: str | None = None,
                mime: str | None = None, caption: str | None = None) -> dict:
    """Ingest one uploaded file from disk. Mechanical I/O only — no routing."""
    path = str(path)
    filename = os.path.basename(filename or path)
    mime = _guess_mime(path, mime)
    kind = classify_upload(mime, filename)
    with open(path, "rb") as f:
        data = f.read()

    if kind == "text":
        out = _ingest_text(agent, path, filename, data, caption)
    elif kind == "source":
        out = _ingest_source(agent, path, filename, data, caption)
    elif kind == "image":
        out = _ingest_image(agent, path, filename, caption)
    elif kind == "pdf":
        out = _ingest_pdf(agent, path, filename, caption)
    elif kind == "audio":
        out = _ingest_audio(agent, path, filename, caption)
    else:
        out = _ingest_binary(agent, path, filename, data, mime, caption)

    out["filename"] = filename
    out["mime"] = mime
    return _finish_ingest(agent, out.get("document_id"), out)


__all__ = ["ingest_file", "classify_upload"]
