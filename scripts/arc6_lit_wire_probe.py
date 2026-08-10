#!/usr/bin/env python
"""arc6_lit_wire_probe — LW1/LW2/LW3, measured live, on WHATEVER engine is loaded.

Run it twice (baseline `.so`, then the fixed `.so`) and diff. That pairing IS
the control A7 minted: *a control must be shown capable of detecting the
difference it is used to rule out.* Every probe below is therefore reported
together with a CAPABILITY row that the probe is known to resolve on BOTH
engines -- the engine's own shipped tagged form (`{"__list__": ...}` /
`{"__tuple__": ...}`), which decodes distinctly at `persist::decode_value` on
the baseline binary too. A path whose capability row reads `list`/`tuple`
distinctly is a path whose "bare list arrives as a tuple" reading is a real
measurement and not a blind channel.

  OZMA_NO_LLM=1 python scripts/arc6_lit_wire_probe.py --out results/x.json
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from substrate_rs import Substrate  # noqa: E402
import substrate_rs._native as _native  # noqa: E402


def engine_sha() -> str:
    h = hashlib.sha256()
    with open(_native.__file__, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tname(v) -> str:
    return type(v).__name__


# The four probe values. `bare_*` are what a Python caller writes; `tag_*`
# are the engine's own wire form and are the CAPABILITY control.
PROBES = [
    ("bare_list", [1, 2]),
    ("bare_tuple", (1, 2)),
    ("tag_list", {"__list__": [1, 2]}),
    ("tag_tuple", {"__tuple__": [1, 2]}),
]


def lit(v):
    return {"type": "Lit", "value": v}


def _try(fn):
    try:
        return {"ok": True, "value": fn()}
    except Exception as e:  # noqa: BLE001 — the exception IS the reading
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])}


# ---------------------------------------------------------------- LW1
def probe_evaluate() -> dict:
    out = {}
    for name, v in PROBES:
        n = Substrate()._inner
        r = _try(lambda v=v: tname(n.evaluate(lit(v), None)))
        out[name] = r
    return out


def probe_add_term_subgraph() -> dict:
    out = {}
    for name, v in PROBES:
        n = Substrate()._inner

        def go(v=v, n=n):
            nid = n.add_term_subgraph(lit(v))
            return tname(n.node(nid)["attrs"]["value"])
        out[name] = _try(go)
    return out


def probe_relax_to_fixpoint() -> dict:
    """`relax_to_fixpoint` IS wired to the type-faithful encoder, but it has
    NO READOUT for LW1 and this probe says so rather than claiming a pass.

    Read at `py.rs::relax_to_fixpoint`: the per-cell eval commits only
    `Value::Float` / `Value::Int` into the register (`_ => None` discards
    everything else), so a `Lit` list can never reach a graph attr through
    this path. The A7 discipline applies in the direction that hurts: the
    CAPABILITY row below (a numeric `Lit`, which the path does commit)
    passes, so the probe is not simply broken -- and the four container
    rows still return nothing, which is a property of the PATH, not of the
    wire. Reported as NO_READOUT.
    """
    out = {}
    for name, v in PROBES + [("capability_numeric_lit", 7)]:
        n = Substrate()._inner

        def go(v=v, n=n):
            c = n.add_node("Cell", {})
            n.relax_to_fixpoint(lit(v), [c.value], "reg", 1)
            return tname(n.node(c)["attrs"]["reg"])
        out[name] = _try(go)
    out["_verdict"] = (
        "NO_READOUT — the path commits only Float/Int registers, so no "
        "container type is observable here; the numeric capability row "
        "shows the probe itself works.")
    return out


def probe_search() -> dict:
    """`search`'s `accept` Term gates a complete leaf, so with an EMPTY
    `open` collection the returned solution count is exactly
    `1 if accept else 0`. `accept = Eq(Lit(x), Lit((1,2)))` therefore reads
    out whether `x` arrived as a `Value::Tuple` (equal -> 1) or as anything
    else (-> 0).

    The CAPABILITY control is the `tag_*` pair, which resolves 0/1 on the
    BASELINE binary too — so a "bare list reads as tuple" result here is a
    measurement of the wire and not of a blind channel.

    NOTE, recorded not absorbed: a `search` whose `open` term does not
    SHRINK as options are assigned recurses without bound and takes the
    process down with a stack overflow. That is PRE-EXISTING (the baseline
    binary `8311d435` dumps core on the identical call, with no `Lit`
    container anywhere in the term) and is not touched by this rung. The
    empty-`open` form below terminates by construction.
    """
    out = {}
    for name, v in PROBES:
        n = Substrate()._inner

        def go(v=v, n=n):
            n.add_node("Opt", {})
            r = n.search(lit(()), {"type": "NodesOfType", "node_type": "Opt"},
                         "assigned", None, None,
                         {"type": "Eq", "a": lit(v), "b": lit((1, 2))}, None)
            return {"solutions": r,
                    "reads_as": "Value::Tuple" if r == 1 else "NOT Value::Tuple"}
        out[name] = _try(go)
    return out


def probe_shape_paths() -> dict:
    """`shape_of_term` / `add_shape_node_for_term` return a SHAPE, which by
    construction cannot express a `Lit`'s value type -- so LW1 has no direct
    readout there. What IS observable is WHICH ENCODER the path uses: a
    Python `set` in a `Lit` is not JSON-serialisable, so the legacy
    `json.dumps` path raises `TypeError` and the type-faithful path (which
    tags a set as `__set__`) does not. That differential is the reading."""
    out = {}
    for path in ("shape_of_term", "add_shape_node_for_term", "add_term_subgraph",
                 "evaluate"):
        n = Substrate()._inner
        fn = getattr(n, path)

        def go(fn=fn):
            if fn.__name__ == "evaluate" or path == "evaluate":
                fn(lit({1, 2}), None)
            else:
                fn(lit({1, 2}))
            return "encoded"
        out[path] = _try(go)
    return out


# ---------------------------------------------------------------- LW2
def probe_seed_resident() -> dict:
    """LW2 -- a FILE-resident `Lit` array must still decode as `Value::Tuple`.

    Measured end to end against real seeds: `json.load(seed)` ->
    `load_seed_manifest` -> `export_rules`, which re-emits every installed
    rule through `persist::encode_value`, so a `Value::Tuple` comes back
    tagged `__tuple__` and a `Value::List` comes back tagged `__list__`.
    That readout is the capability control for this probe: it distinguishes
    the two tags by construction.
    """
    def find_lits(o, path=""):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), (list, dict)):
                yield path, o["value"]
            for k, v in o.items():
                yield from find_lits(v, path + "/" + str(k))
        elif isinstance(o, (list, tuple)):
            for i, v in enumerate(o):
                yield from find_lits(v, path + "/%d" % i)

    seeds = []
    for f in sorted(glob.glob(os.path.join(ROOT, "seeds", "*.json"))):
        try:
            m = json.load(open(f))
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        arr = [(p, v) for p, v in find_lits(m) if isinstance(v, list)]
        if arr:
            seeds.append((os.path.basename(f), m, arr))

    total_file_arrays = sum(len(a) for _, _, a in seeds)
    per_seed = []
    tags_seen = {}
    for name, m, arr in seeds:
        n = Substrate()._inner
        try:
            n.load_seed_manifest(m, None)
        except Exception as e:  # noqa: BLE001
            per_seed.append({"seed": name, "file_array_lits": len(arr),
                             "load_error": "%s: %s" % (type(e).__name__, str(e)[:100])})
            continue
        try:
            ex = n.export_rules()
        except Exception as e:  # noqa: BLE001
            per_seed.append({"seed": name, "file_array_lits": len(arr),
                             "export_error": "%s: %s" % (type(e).__name__, str(e)[:100])})
            continue
        tags = {"__tuple__": 0, "__list__": 0, "__set__": 0, "__fset__": 0, "bare": 0}
        for _p, v in find_lits(ex):
            if isinstance(v, dict):
                for t in ("__tuple__", "__list__", "__set__", "__fset__"):
                    if t in v:
                        tags[t] += 1
                        break
            elif isinstance(v, list):
                tags["bare"] += 1
        for k, c in tags.items():
            tags_seen[k] = tags_seen.get(k, 0) + c
        per_seed.append({"seed": name, "file_array_lits": len(arr),
                         "exported_lit_container_tags": tags})
    return {
        "seeds_with_array_lits": len(seeds),
        "file_resident_array_lits": total_file_arrays,
        "exported_tag_totals": tags_seen,
        "per_seed": per_seed,
    }


# ---------------------------------------------------------------- LW3
def probe_wire_rows_redundant() -> dict:
    """LW3 -- is `domains.prog_synthesis._wire_rows` now redundant?

    Not asserted: MEASURED, by running every MBPP spec's rows through BOTH
    the `_wire_rows` path and the plain path and comparing what the engine
    reads back. Equivalence means: for every row value, the Value the
    engine decodes is identical (same Python type AND same content) either
    way.
    """
    from domains.prog_synthesis import _wire_rows  # noqa: PLC0415
    from domains import mbpp_spec as ms  # noqa: PLC0415

    fixture = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
    tasks = json.load(open(fixture))
    n = Substrate()._inner

    checked = 0
    rows_checked = 0
    mismatches = []
    both_error = []
    for t in tasks:
        try:
            spec = ms.parse_asserts(t)
        except Exception:
            continue
        rows = (spec or {}).get("rows") or []
        if not rows:
            continue
        checked += 1

        def one(x):
            try:
                v = n.evaluate(lit(x), None)
                return ("ok", repr(v), type(v).__name__)
            except Exception as e:  # noqa: BLE001
                return ("err", "%s: %s" % (type(e).__name__, str(e)[:80]), "")

        plain = one(rows)
        wired = one(_wire_rows(rows))
        rows_checked += len(rows)
        if plain != wired:
            mismatches.append({"task_id": t.get("task_id"),
                               "plain": plain[:2], "wired": wired[:2]})
        elif plain[0] == "err":
            both_error.append({"task_id": t.get("task_id"), "error": plain[1]})
    return {"specs_checked": checked, "rows_checked": rows_checked,
            "mismatches": mismatches, "equivalent": not mismatches,
            "identically_unserialisable_both_paths": both_error,
            "_note": ("`identically_unserialisable_both_paths` are specs whose "
                      "rows contain a value neither path can put on the wire "
                      "(complex numbers, tuple dict keys). Both paths raise the "
                      "SAME exception, so they are EQUIVALENT — they are listed "
                      "rather than hidden, and they are a pre-existing wire "
                      "limit, not something this rung introduced.")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="unlabelled")
    args = ap.parse_args()
    rec = {
        "_README": __doc__,
        "label": args.label,
        "engine_sha256": engine_sha(),
        "engine_file": _native.__file__,
        "LW1_evaluate": probe_evaluate(),
        "LW1_add_term_subgraph": probe_add_term_subgraph(),
        "LW1_relax_to_fixpoint": probe_relax_to_fixpoint(),
        "LW1_search": probe_search(),
        "LW1_encoder_reached_set_differential": probe_shape_paths(),
        "LW2_seed_resident": probe_seed_resident(),
        "LW3_wire_rows_redundant": probe_wire_rows_redundant(),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(rec, fh, indent=2, sort_keys=True)
    print(json.dumps({k: v for k, v in rec.items()
                      if k.startswith("LW1")}, indent=2, sort_keys=True))
    print("LW2 tag totals:", rec["LW2_seed_resident"]["exported_tag_totals"],
          "over", rec["LW2_seed_resident"]["file_resident_array_lits"],
          "file-resident array Lits in",
          rec["LW2_seed_resident"]["seeds_with_array_lits"], "seeds")
    print("LW3:", {k: v for k, v in rec["LW3_wire_rows_redundant"].items()
                   if k != "mismatches"},
          "n_mismatch=", len(rec["LW3_wire_rows_redundant"]["mismatches"]))
    print("engine", rec["engine_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
