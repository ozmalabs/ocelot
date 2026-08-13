"""Surgical JSON-Term wrap tool for seeds/composer_experiment_graph.json.

Extracts the existing collapsed-pick block verbatim (by brace-counting,
never by hand-retyping), wraps it in a new named Let, and replaces its
abstain sentinel branch with a structural-fallback Argmax over the same
candidate Filter, scored by where_signature_json instead of keywords_text.
"""
import json
import sys


def find_matching_brace(text, open_idx):
    assert text[open_idx] == '{', text[open_idx]
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while text[i] != '"':
                if text[i] == '\\':
                    i += 1
                i += 1
            i += 1
            continue
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("no matching brace found")


def line_col_to_offset(text, line_idx_1based, needle):
    """Return absolute char offset of `needle` on the given 1-based line."""
    lines = text.split('\n')
    line = lines[line_idx_1based - 1]
    col = line.index(needle)
    abs_off = sum(len(l) + 1 for l in lines[:line_idx_1based - 1]) + col
    return abs_off


def extract_block(text, anchor_line_1based, key_marker):
    """key_marker e.g. '"value": {' or '"__term__": {' -- locate the '{'
    that starts the block to extract, on the given line, and return
    (start_offset, end_offset_inclusive, block_text)."""
    brace_off = line_col_to_offset(text, anchor_line_1based, key_marker)
    open_off = brace_off + len(key_marker) - 1  # position of the '{'
    assert text[open_off] == '{', repr(text[open_off:open_off + 20])
    close_off = find_matching_brace(text, open_off)
    block_text = text[open_off:close_off + 1]
    json.loads(block_text)  # validate standalone-parseable
    return open_off, close_off, block_text


def build_fallback_node_or_null(candidate_node_type, extra_filter_items,
                                 words_var, struct_var, cand_var):
    """Fallback Argmax that resolves to a NODE or null (A7 shape)."""
    def V(n): return {"type": "Var", "name": n}
    def L(v): return {"type": "Lit", "value": v}
    def Attr(nd, k): return {"type": "Attr", "node": nd, "key": k}
    def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
    def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
    def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
    def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
    def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
    def And(*items): return {"type": "And", "items": list(items)}
    def Argmax(src, var, val, default): return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": default}
    def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
    def Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var, "value": val}
    def StrIdx(h, n): return {"type": "StringIndexOf", "haystack": h, "needle": n}
    def LetT(nm, val, body): return {"type": "Let", "name": nm, "value": val, "body": body}

    words = Attr(V(words_var[0]), words_var[1])

    def struct_overlap(node_t):
        return Sum(words, "w", Ite(Gte(StrIdx(Attr(node_t, "where_signature_json"), V("w")), L(0)), L(1), L(0)))

    predicate = extra_filter_items
    candidates = Filter(NodesOfType(candidate_node_type), cand_var, predicate) if predicate else \
        NodesOfType(candidate_node_type)

    struct_best = Argmax(candidates, cand_var, struct_overlap(V(cand_var)), None)
    fallback = LetT(struct_var, struct_best,
        Ite(Eq(V(struct_var), L(None)), L(None),
            Ite(Gt(struct_overlap(V(struct_var)), L(0.0)), V(struct_var), L(None))))
    return fallback


def build_fallback_seedid_or_empty(words_var, struct_var, cand_var):
    """Fallback Argmax that resolves to seed_id STRING or "" (A9 shape)."""
    def V(n): return {"type": "Var", "name": n}
    def L(v): return {"type": "Lit", "value": v}
    def Attr(nd, k): return {"type": "Attr", "node": nd, "key": k}
    def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
    def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
    def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
    def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
    def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
    def Argmax(src, var, val, default): return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": default}
    def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
    def Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var, "value": val}
    def StrIdx(h, n): return {"type": "StringIndexOf", "haystack": h, "needle": n}
    def LetT(nm, val, body): return {"type": "Let", "name": nm, "value": val, "body": body}

    words = Attr(V(words_var[0]), words_var[1])

    def struct_overlap(node_t):
        return Sum(words, "w", Ite(Gte(StrIdx(Attr(node_t, "where_signature_json"), V("w")), L(0)), L(1), L(0)))

    candidates = Filter(NodesOfType("SeedSummary"), cand_var,
                         Eq(Attr(V(cand_var), "skippable"), L(1.0)))
    struct_best = Argmax(candidates, cand_var, struct_overlap(V(cand_var)), None)
    fallback = LetT(struct_var, struct_best,
        Ite(Eq(V(struct_var), L(None)), L(""),
            Ite(Gt(struct_overlap(V(struct_var)), L(0.0)), Attr(V(struct_var), "seed_id"), L(""))))
    return fallback


def wrap_site(filepath, anchor_line_1based, key_marker, primary_var, sentinel,
              fallback_expr, dry_run=False):
    text = open(filepath, 'r').read()
    open_off, close_off, block_text = extract_block(text, anchor_line_1based, key_marker)

    cond = {"type": "Eq", "a": {"type": "Var", "name": primary_var}, "b": {"type": "Lit", "value": sentinel}}
    other = {"type": "Var", "name": primary_var}

    # Build the wrapper with a placeholder for the (verbatim) extracted block
    # and for the fallback, so both get spliced in as raw text (no re-dump
    # of the parts we want to preserve byte-for-byte or already built via
    # the ordinary dict path -- the fallback IS built as a dict so dump it
    # normally; only the extracted primary block is spliced as raw text).
    placeholder = "@@PRIMARY_BLOCK@@"
    wrapper = {
        "type": "Let",
        "name": primary_var,
        "value": placeholder,
        "body": {
            "type": "IfThenElse",
            "cond": cond,
            "then": fallback_expr,
            "other": other,
        },
    }
    dumped = json.dumps(wrapper, indent=1)
    marker_line_idx = None
    lines = dumped.split('\n')
    for i, l in enumerate(lines):
        if placeholder in l:
            marker_line_idx = i
            break
    assert marker_line_idx is not None
    prefix = lines[marker_line_idx].split('"' + placeholder + '"')[0]
    assert prefix.rstrip().endswith(':'), repr(prefix)
    # replace the placeholder line with prefix + block_text (verbatim) + trailing comma
    new_line = prefix + block_text + ','
    new_lines = lines[:marker_line_idx] + [new_line] + lines[marker_line_idx + 1:]
    new_wrapper_text = '\n'.join(new_lines)

    json.loads(new_wrapper_text)  # validate the new subtree standalone

    new_text = text[:open_off] + new_wrapper_text + text[close_off + 1:]
    json.loads(new_text)  # validate whole file

    if not dry_run:
        open(filepath, 'w').write(new_text)
    return new_text
