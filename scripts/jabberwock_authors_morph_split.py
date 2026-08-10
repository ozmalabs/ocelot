"""The jabberwock AUTHORS its own compound-split primitive — by ASKING, not by
being told. (Creator: "it should author its own primitives… did you ask it first?")

The agent's flow, end to end:
  1. INTROSPECT — it reads its own native string vocabulary (StringIndexOf /
     StringSlice / StringConcat) and finds the gap: none tests a CHARACTER CLASS,
     so a camelCase boundary (lowercase→uppercase) is INEXPRESSIBLE. Records a
     PrimitiveSpec.
  2. MIRROR its sibling — a new single-child TermNode has the SAME boilerplate at
     every match site as the agent's existing single-child `Tokenize { text }`.
     The agent reads Tokenize's arm at each of the 8 exhaustive `TermNode` sites
     (term.rs ×3, jsonio.rs ×3, reflect.rs ×2) and CLONES it (Tokenize→MorphHead
     / MorphTail) — deterministic, always compiles. This is the same
     anchor-from-sibling discipline `self_extend` uses, applied to every site.
  3. CONSULT the Claude-teacher (scripts/claude_teacher, `claude -p`) for the ONLY
     novel parts — the two EVAL arms + the `first_morph_boundary` helper — handing
     it the agent's verbatim StringConcat eval arm as the type/idiom template.
     Records the reply as a TaughtHint.
  4. SELF-EXTEND under the keystone's ALL-OR-NOTHING guard — snapshot every touched
     file, apply clones+eval+helper, `cargo check`, rebuild (capped jobs), VERIFY
     in a fresh subprocess that MorphHead("actionSpace")=="action", and on ANY
     failure restore the snapshot byte-for-byte. A repair loop feeds a compiler
     error back to the teacher up to a small cap.

The boilerplate is the agent mirroring its own held primitive; only the genuinely
new logic is asked of the teacher. This driver only sequences it.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter
from domains.self_modification import DSL, SelfModification
from scripts.claude_teacher import make_ask

SRC = DSL / "src"
TERM = SRC / "term.rs"
JSONIO = SRC / "jsonio.rs"
REFLECT = SRC / "reflect.rs"
FILES = (TERM, JSONIO, REFLECT)

# The agent's SIBLING single-child Term. A new single-child TermNode slots in
# identically beside it at every exhaustive-match site; only the evaluator body
# (and a helper) differ. (file, verbatim Tokenize arm to clone).
CLONE_SITES = [
    (TERM, "    Tokenize { text: TermIdx },"),
    (TERM, "        TermNode::Tokenize { text } => TermNode::Tokenize { text: copy_subtree(src, dst, text) },"),
    (TERM, "        TermNode::Tokenize { text } => out.push(*text),"),
    (JSONIO, '        TermNode::Tokenize { .. } => "Tokenize",'),
    (JSONIO, '        TermNode::Tokenize { text } => {\n            m.insert("text".into(), child(*text, arena, interner));\n        }'),
    (JSONIO, '        "Tokenize" => TermNode::Tokenize {\n            text: child_of("text", obj, arena, interner, variant)?,\n        },'),
    (REFLECT, '        TermNode::Tokenize { text } => ("Tokenize", vec![Child { name: "text", child: *text }]),'),
    (REFLECT, '        "Tokenize" => TermNode::Tokenize { text: take_child!("text") },'),
]

# the eval arms go just before this (unique) line in term.rs
EVAL_ANCHOR = "        TermNode::Verify { term, env: env_term, expected } => {"


def _introspect_gap(wa) -> dict:
    src = TERM.read_text()
    held = [n for n in ("StringIndexOf", "StringSlice", "StringConcat")
            if f"    {n} " in src or f"    {n} {{" in src]
    spec = {
        "name": "MorphHead/MorphTail",
        "held_string_primitives": json.dumps(held),
        "semantic_kind": "morphological_segmentation",
        "why_new": "I split on a separator with StringIndexOf+StringSlice, but no "
                   "held primitive tests a CHARACTER CLASS, so a camelCase boundary "
                   "(lowercase/digit -> uppercase) is inexpressible: 'actionSpace' "
                   "cannot be decomposed. A morphological split is INEXPRESSIBLE.",
        "already_present": "MorphHead {" in src,
        "origin": "agent_runtime_design",
    }
    wa.s.add_node("PrimitiveSpec", spec)
    return spec


def _extract_arm(src: str, header: str) -> str:
    """Verbatim arm from `header` through its matching closing brace."""
    i = src.find(header)
    if i < 0:
        return ""
    arrow = src.find("=>", i)
    br = src.find("{", arrow) if arrow >= 0 else -1
    if br < 0:
        nl = src.find("\n", i)
        return src[i:nl if nl > 0 else len(src)]
    depth, k = 0, br
    while k < len(src):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                end = k + 1
                if end < len(src) and src[end] == ",":
                    end += 1
                return src[i:end]
        k += 1
    return src[i:]


def _ask_teacher_eval(ask, eval_example, prior_error="") -> dict | None:
    """Ask the teacher ONLY for the novel parts: the two eval arms + the helper."""
    err = (f"\n\nYour LAST patch FAILED `cargo check`. Fix EXACTLY:\n{prior_error[-1800:]}"
           if prior_error else "")
    q = f"""You are extending a Rust DSL (substrate-rs). I have already added two single-child
TermNode variants `MorphHead {{ text: TermIdx }}` and `MorphTail {{ text: TermIdx }}` and ALL their
boilerplate (enum, copy, json, reflect). I need ONLY two things: their EVAL match arms and one
helper fn.

Behaviour: split a string at the FIRST morphological boundary — a '-'/'_' separator (dropped) OR a
camelCase transition (a lowercase/digit immediately followed by an uppercase, KEPT). MorphHead =
part BEFORE the boundary (whole string if none). MorphTail = part AFTER (leading separators
skipped; camelCase kept; EMPTY if no boundary). So MorphHead("actionSpace")="action",
MorphTail("actionSpace")="Space", MorphHead("action_space")="action", MorphTail("action_space")="space".

Mirror this EXACT existing eval arm (same types/idioms — Value, SurfaceKind, ctx.interner,
evaluate(arena, *x, env, ctx), std::sync::Arc::from). Your arms go in the SAME `match`:
{eval_example}

Add a module-level `fn first_morph_boundary(s: &str) -> Option<(usize, usize)>` returning
(head_end_byte, tail_start_byte); the eval arms call it and slice `s` (Value::Str via
ctx.interner.resolve(sym), or Value::Surface(SurfaceKind::Text, b)).

Output ONLY raw Rust between markers (no backticks, no prose):
@@@eval
<the two full eval match arms: TermNode::MorphHead {{ text }} => {{ ... }} and TermNode::MorphTail {{ text }} => {{ ... }}>
@@@helper
<the full fn first_morph_boundary>
@@@end{err}"""
    reply = ask(q)
    if not reply:
        return None
    out = {}
    parts = re.split(r"(?m)^@@@(\w+)\s*$", reply)
    for idx in range(1, len(parts) - 1, 2):
        k, body = parts[idx], parts[idx + 1]
        if k in ("eval", "helper"):
            out[k] = body.strip("\n")
    return out if out.get("eval") and out.get("helper") else None


def _apply(eval_arms: str, helper: str) -> tuple[bool, str]:
    """Clone the sibling boilerplate at every site + splice the taught eval/helper,
    onto a snapshot. All-or-nothing. (caller builds + verifies + may roll back.)"""
    snap = {p: p.read_text() for p in FILES}

    def restore():
        for p, t in snap.items():
            p.write_text(t)

    try:
        bufs = {p: snap[p] for p in FILES}
        for fp, anchor in CLONE_SITES:
            if anchor not in bufs[fp]:
                restore(); return False, f"clone anchor missing in {fp.name}: {anchor[:50]!r}"
            head = anchor.replace("Tokenize", "MorphHead")
            tail = anchor.replace("Tokenize", "MorphTail")
            bufs[fp] = bufs[fp].replace(anchor, anchor + "\n" + head + "\n" + tail, 1)
        # eval arms (term.rs) + helper (append term.rs)
        if EVAL_ANCHOR not in bufs[TERM]:
            restore(); return False, "eval anchor missing"
        bufs[TERM] = bufs[TERM].replace(EVAL_ANCHOR, eval_arms.strip("\n") + "\n\n" + EVAL_ANCHOR, 1)
        bufs[TERM] = bufs[TERM].rstrip() + "\n\n" + helper.strip("\n") + "\n"
        for p, t in bufs.items():
            p.write_text(t)
        return True, "applied"
    except Exception as e:
        restore(); return False, f"apply error: {type(e).__name__}: {e}"


_CARGO = (
    "import os,subprocess\n"
    "from domains.self_modification import DSL\n"
    "env={**os.environ,'CARGO_BUILD_JOBS':'2'}\n"
    "r=subprocess.run(['cargo','check','-j','2','--message-format=short'],cwd=DSL,"
    "capture_output=True,text=True,timeout=1200,env=env)\n"
    "print('RC',r.returncode); print(r.stderr[-1800:])"
)
_VERIFY = (
    "from substrate.boot_core import CORE_SEEDS\n"
    "from substrate.world_adapter import WorldAdapter\n"
    "wa=WorldAdapter(seeds=CORE_SEEDS)\n"
    "h=wa.inner.evaluate({'type':'MorphHead','text':{'type':'Lit','value':'actionSpace'}},None)\n"
    "t=wa.inner.evaluate({'type':'MorphTail','text':{'type':'Lit','value':'action_space'}},None)\n"
    "h=h.decode() if isinstance(h,(bytes,bytearray)) else str(h)\n"
    "t=t.decode() if isinstance(t,(bytes,bytearray)) else str(t)\n"
    "print('RESULT', repr(h), repr(t))"
)


def _cargo_check() -> tuple[bool, str]:
    try:
        r = subprocess.run([sys.executable, "-c", _CARGO], capture_output=True,
                           text=True, timeout=1300)
        out = (r.stdout or "") + (r.stderr or "")
        return ("RC 0" in (r.stdout or ""), out[-1800:])
    except Exception as e:
        return False, f"cargo check failed to run: {e}"


def _verify() -> tuple[bool, str]:
    try:
        r = subprocess.run([sys.executable, "-c", _VERIFY], capture_output=True,
                           text=True, timeout=600)
        out = (r.stdout or "").strip()
        m = re.search(r"RESULT (.+)", out)
        if not m:
            return False, f"no result: {(out + r.stderr)[-400:]}"
        body = m.group(1)
        return ("'action'" in body and "'space'" in body), body
    except Exception as e:
        return False, f"verify raised: {type(e).__name__}: {e}"


def run(max_repair: int = 2):
    mod = SelfModification()
    wa = WorldAdapter(seeds=CORE_SEEDS)
    spec = _introspect_gap(wa)
    print("GAP:", spec["why_new"], flush=True)
    if spec["already_present"]:
        print("MorphHead/MorphTail already present — nothing to author.")
        return

    ask = make_ask(timeout=300.0,
                   preamble="You are a Rust compiler expert helping an agent extend its own DSL. ")
    eval_example = _extract_arm(TERM.read_text(), "TermNode::StringConcat { parts } => {")
    snap = {p: p.read_text() for p in FILES}

    def restore_all():
        for p, t in snap.items():
            p.write_text(t)

    prior_error = ""
    for attempt in range(1, max_repair + 2):
        print(f"\n--- consult attempt {attempt} ---", flush=True)
        taught = _ask_teacher_eval(ask, eval_example, prior_error)
        if not taught:
            print("teacher reply unusable", flush=True)
            continue
        wa.s.add_node("TaughtHint", {"question": "author MorphHead/MorphTail eval+helper",
                                     "answer": json.dumps(taught)[:4000], "grounded": 0})
        applied, detail = _apply(taught["eval"], taught["helper"])
        if not applied:
            print("apply failed:", detail, flush=True)
            prior_error = detail
            continue
        ok_chk, msg = _cargo_check()
        if not ok_chk:
            restore_all()
            print("cargo check FAILED -> rolled back. errors:\n" + msg[-1000:], flush=True)
            prior_error = msg
            continue
        print("cargo check PASSED; rebuilding native (capped)…", flush=True)
        rb = mod.rebuild_native()
        if not rb["ok"]:
            restore_all(); mod.rebuild_native()
            print("rebuild FAILED -> rolled back", flush=True)
            prior_error = rb.get("tail", "")
            continue
        ok, vdetail = _verify()
        print("VERIFY:", vdetail, flush=True)
        if ok:
            mod._done("MorphHead/MorphTail", "author", "OK_BUILT",
                      "agent cloned sibling boilerplate + teacher eval; verified", ok=True)
            print("\n✓ the jabberwock AUTHORED MorphHead/MorphTail — mirrored its sibling "
                  "for boilerplate, asked the teacher for the novel logic, applied under "
                  "guard, verified live.", flush=True)
            return
        restore_all(); mod.rebuild_native()
        print("verify FAILED -> rolled back", flush=True)
        prior_error = vdetail

    print("\n✗ did not land a compiling+verified primitive; tree restored.", flush=True)


if __name__ == "__main__":
    run()
    sys.exit(0)
