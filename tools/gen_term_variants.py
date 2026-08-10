#!/usr/bin/env python3
"""Generate `TermNode::variant_index` + the name table from term.rs's enum body.

MECHANICAL. The enum body is parsed at brace depth 1 of `pub enum TermNode {`;
every `Ident {` / `Ident(` / `Ident,` at that depth is a variant, in DECLARATION
ORDER. Emitted as a Rust source block for term.rs. Re-run after any variant is
added; the `variant_count_is_exhaustive` test fails if the table drifts.
"""
import re
import sys

SRC = sys.argv[1]
DEST = sys.argv[2] if len(sys.argv) > 2 else None
src = open(SRC).read()
start = src.index("pub enum TermNode {")
i = src.index("{", start)
depth = 0
body_start = i + 1
j = i
while True:
    ch = src[j]
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            break
    j += 1
body = src[body_start:j]

variants = []
depth = 0
line_start = True
buf = ""
k = 0
# Walk the body, tracking depth; collect identifiers that begin a variant at depth 0.
tok = ""
pending = ""
in_line_comment = False
in_block_comment = False
n = len(body)
cur = []
while k < n:
    ch = body[k]
    two = body[k:k + 2]
    if in_line_comment:
        if ch == "\n":
            in_line_comment = False
        k += 1
        continue
    if in_block_comment:
        if two == "*/":
            in_block_comment = False
            k += 2
            continue
        k += 1
        continue
    if two == "//":
        in_line_comment = True
        k += 2
        continue
    if two == "/*":
        in_block_comment = True
        k += 2
        continue
    if ch == "#" and depth == 0:
        # attribute — skip to end of line
        while k < n and body[k] != "\n":
            k += 1
        continue
    if depth == 0 and (ch.isalpha() or ch == "_"):
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", body[k:])
        ident = m.group(0)
        k += len(ident)
        # what follows (skipping whitespace) decides
        p = k
        while p < n and body[p].isspace():
            p += 1
        if p < n and body[p] in "{(," and ident[0].isupper():
            variants.append(ident)
        continue
    if ch in "{([<":
        if ch in "{([":
            depth += 1
    elif ch in "})]":
        depth -= 1
    k += 1

assert variants, "no variants parsed"
assert len(variants) == len(set(variants)), "duplicate variant names parsed"

out = []
out.append("//! GENERATED — do not hand-edit.")
out.append("//!")
out.append("//! Produced by `tools/gen_term_variants.py runners/dsl/src/term.rs`.")
out.append("//! Regenerate after adding a `TermNode` variant; the")
out.append("//! `variant_table_covers_the_enum` test in `scale_audit.rs` fails if this")
out.append("//! table drifts from the enum.")
out.append("//!")
out.append("//! The per-variant Term-evaluation counter (`scale_audit::term_eval`)")
out.append("//! indexes into a table of this exact length. `NUM_TERM_VARIANTS` is")
out.append("//! therefore the enum's OWN ARITY — a number that FALLS OUT of the")
out.append("//! structure being counted, not a chosen constant (PROTOCOL §13).")
out.append("")
out.append("use crate::term::TermNode;")
out.append("")
out.append(f"pub const NUM_TERM_VARIANTS: usize = {len(variants)};")
out.append("")
out.append("/// Variant names in DECLARATION ORDER. Index == `variant_index()`.")
out.append(f"pub static TERM_VARIANT_NAMES: [&str; NUM_TERM_VARIANTS] = [")
for v in variants:
    out.append(f'    "{v}",')
out.append("];")
out.append("")
out.append("impl TermNode {")
out.append("    /// Dense index of this node's variant, for the per-variant counter")
out.append("    /// table. Exhaustive by construction: the generator reads the enum.")
out.append("    #[inline]")
out.append("    pub fn variant_index(&self) -> u16 {")
out.append("        match self {")
for n_, v in enumerate(variants):
    out.append(f"            TermNode::{v} {{ .. }} => {n_},")
out.append("        }")
out.append("    }")
out.append("}")
rendered = "\n".join(out) + "\n"
if DEST is None:
    print(rendered, end="")
else:
    with open(DEST, "w") as f:
        f.write(rendered)
sys.stderr.write(f"{len(variants)} variants\n")
