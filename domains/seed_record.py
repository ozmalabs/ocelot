"""seed_record — THE LEDGER'S MEASURED TRUTH, GENERATED NOT WRITTEN.

PROTOCOL §11 recommendation #4, made structural:

    "record MEASURED sub-ranges in ledger rows, not just the declared
     block"  -- assessed by the seed-claim rung as the highest-leverage of
     the five open recommendations, and NOT APPLIED.

WHY IT WAS NEVER APPLIED, AND WHY IT COULD NOT BE
--------------------------------------------------
It was written as a PROSE discipline: a human remembers to type the
measured sub-ranges into a markdown table cell. The seed-accounting rung
measured what that discipline actually produces across 108 declared
blocks:

    58 of 108 blocks measure ZERO.   Median fill 0.100.
    TWO FULL 100-SEED BLOCKS were consumed with NO DECLARATION AT ALL.

That is not carelessness; it is the predictable yield of a WRITE-SIDE
discipline with NO READ-SIDE ENFORCEMENT. And it cannot be fixed by
gating the prose, because gating prose means a substring selector -- and
this arc has now lost FOUR selectors to substring matching, the most
recent going red on a DOCSTRING.

SO: DO NOT GATE THE PROSE. GENERATE THE FACT.
---------------------------------------------
The measured occupancy of every declared block is DERIVABLE, mechanically
and deterministically, from an AST scan the tree already has
(`scripts/seed_audit.py`). This module derives it, and commits it as
`results/seed_ledger_measured.json`.

THE SEAM, and why it cannot be skipped: **the committed record is gated
for FRESHNESS.** Any seed added, moved, or removed anywhere in the tree
changes the derived report, the gate goes red, and the only way green is
to regenerate:

    python3 -m domains.seed_record --write

One command. No judgement, no prose, nothing to remember at the moment of
writing a ledger row -- which is the moment the old discipline reliably
failed. A rung cannot land seeds and leave their measured ranges
unrecorded, because leaving them unrecorded is now a red gate rather than
an omission nobody notices.

THE NUISANCE MODE, NAMED IN ADVANCE (it is real, and it is a TRUE
POSITIVE): a rung that adds a seed for an unrelated reason gets a red
gate it did not intend to trip. The failure message therefore carries the
regeneration command, and the diff it produces is exactly the record the
protocol asked for. A gate whose nuisance mode is undocumented reads as
noise; this one says what it is.

WHAT THIS IS NOT
----------------
It is not a collision check (`scripts/seed_claim.py` is), and it is not
an authority on what is FREE. It inherits every blind spot of
`seed_audit` -- 7 declared classes, hundreds of unresolved sink sites,
all COUNTED and reported here rather than discarded. **A CLEAN RECORD
MEANS "NOTHING DETECTED", NEVER "NOTHING THERE".**
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from seed_audit import analyse_tree  # noqa: E402
from seed_claim import DEFAULT_ROOTS, undeclared_runs  # noqa: E402
from seed_ledger_audit import LEDGER_FLOOR, parse_ledger  # noqa: E402

#: The committed artifact this module generates and the gate checks.
RECORD_PATH = os.path.join(ROOT, "results", "seed_ledger_measured.json")

#: The committed grandfather floor for the pre-registration claim gate.
PREREG_FLOOR_PATH = os.path.join(ROOT, "results", "prereg_claim_floor.json")

#: Pre-registrations live at the tree root as `VISION_*_PREREG.md`.
_PREREG_PREFIX = "VISION_"
_PREREG_SUFFIX = "_PREREG.md"


# ---- measured occupancy ----------------------------------------------------

def _scan(roots=DEFAULT_ROOTS) -> dict:
    scan = analyse_tree([os.path.join(ROOT, d) for d in roots])
    seed_files: dict[int, set[str]] = {}
    unknown = 0
    for f in scan["files"]:
        rel = os.path.relpath(f["file"], ROOT)
        unknown += f["unknown_sinks"]
        for s in f["seeds"]:
            seed_files.setdefault(s, set()).add(rel)
    return {"seed_files": seed_files, "unknown_sinks": unknown,
            "files_scanned": len(scan["files"]),
            "parse_errors": scan["parse_errors"]}


def subranges(seeds) -> list[list[int]]:
    """Sorted seeds -> contiguous [lo, hi] runs. THE thing rec #4 asks a
    ledger row to carry, computed instead of remembered."""
    out: list[list[int]] = []
    for s in sorted(set(seeds)):
        if out and s == out[-1][1] + 1:
            out[-1][1] = s
        else:
            out.append([s, s])
    return out


def measured_subranges(files, *, roots=DEFAULT_ROOTS) -> list[list[int]]:
    """Measured sub-ranges drawn by a specific set of files (repo-relative).

    This is the self-audit entry point: a rung asks what IT actually spent,
    rather than what it declared.
    """
    want = {os.path.normpath(f) for f in files}
    scan = _scan(roots)
    mine = [s for s, fs in scan["seed_files"].items()
            if any(os.path.normpath(f) in want for f in fs)]
    return subranges(mine)


def ledger_measured_report(*, roots=DEFAULT_ROOTS) -> dict:
    """Per declared §11 ledger block: what is ACTUALLY drawn inside it.

    Deterministic given a tree state -- sorted everywhere, no timestamps,
    no paths outside the repo. A record that varied run to run could not
    be gated for freshness, so it is built not to.
    """
    scan = _scan(roots)
    blocks, rows = parse_ledger()
    seed_files = scan["seed_files"]

    out_blocks = []
    for lo, hi, idx in sorted(blocks):
        inside = [s for s in seed_files if lo <= s <= hi]
        files = sorted({f for s in inside for f in seed_files[s]})
        width = hi - lo + 1
        out_blocks.append({
            "declared": [lo, hi],
            "declared_width": width,
            "measured_seeds": len(inside),
            "measured_subranges": subranges(inside),
            "fill": round(len(inside) / width, 4) if width else 0.0,
            "files": files,
        })

    fills = sorted(b["fill"] for b in out_blocks)
    n = len(fills)
    median = 0.0 if not n else (
        fills[n // 2] if n % 2 else round((fills[n // 2 - 1] + fills[n // 2]) / 2, 4))

    runs = undeclared_runs(roots=roots)
    return {
        "_README": (
            "GENERATED by `python3 -m domains.seed_record --write`. Do not "
            "hand-edit. PROTOCOL §11 rec #4: a ledger row's DECLARED block is "
            "a claim about the tree; this file is the tree. A CLEAN RECORD "
            "MEANS 'NOTHING DETECTED', NEVER 'NOTHING THERE' -- see "
            "unresolved_sinks."),
        "ledger_floor": LEDGER_FLOOR,
        "blocks_declared": len(out_blocks),
        "blocks_measuring_zero": sum(1 for b in out_blocks
                                     if b["measured_seeds"] == 0),
        "median_fill": median,
        "total_measured_in_declared_blocks": sum(b["measured_seeds"]
                                                 for b in out_blocks),
        "undeclared_runs": [
            {"lo": r["lo"], "hi": r["hi"], "n": r["n"], "files": sorted(r["files"])}
            for r in sorted(runs, key=lambda r: r["lo"])],
        "undeclared_seeds": sum(r["n"] for r in runs),
        "files_with_seed_sinks": scan["files_scanned"],
        "unresolved_sinks": scan["unknown_sinks"],
        "parse_errors": scan["parse_errors"],
        "blocks": out_blocks,
    }


def render(report: dict) -> str:
    """Canonical serialisation. Stable key order, trailing newline."""
    return json.dumps(report, indent=1, sort_keys=True) + "\n"


def read_record(path: str = RECORD_PATH) -> dict | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_record(path: str = RECORD_PATH, *, roots=DEFAULT_ROOTS) -> dict:
    rep = ledger_measured_report(roots=roots)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(rep))
    return rep


def record_is_fresh(path: str = RECORD_PATH, *, roots=DEFAULT_ROOTS):
    """(fresh, message). THE GATE for §11 rec #4."""
    committed = read_record(path)
    if committed is None:
        return False, (
            f"{os.path.relpath(path, ROOT)} is MISSING. The measured ledger "
            "record is not optional (PROTOCOL §11 rec #4).\n"
            "  Generate it:  python3 -m domains.seed_record --write")
    live = ledger_measured_report(roots=roots)
    if render(committed) == render(live):
        return True, "measured ledger record is current"

    diffs = []
    for key in ("blocks_declared", "blocks_measuring_zero", "median_fill",
                "total_measured_in_declared_blocks", "undeclared_seeds",
                "unresolved_sinks"):
        if committed.get(key) != live.get(key):
            diffs.append(f"    {key}: committed={committed.get(key)!r} "
                         f"live={live.get(key)!r}")
    # POSITIONAL, never keyed by declared range.
    #
    # Keying by `(lo, hi)` was the first version and it was WRONG: the §11
    # ledger legitimately carries REPEATED declared ranges ("0–13 (again)",
    # and 1900–1999 appears twice), so a dict keyed by range silently keeps
    # only the last row — and a perturbation of any earlier duplicate
    # produced a STALE verdict with an EMPTY diff list. Found by this
    # module's own positive control, which is the only reason it was found:
    # the top-level `render()` comparison was still correct, so the gate
    # fired, and only the LANDING CHECK ("the message must name the block I
    # broke") exposed that it could not say WHY. A gate that cannot name
    # what it caught is one nobody can act on.
    cbl, lbl = committed.get("blocks", []), live.get("blocks", [])
    if len(cbl) != len(lbl):
        diffs.append(f"    declared blocks: committed={len(cbl)} live={len(lbl)}"
                     " — a ledger row was added or removed")
    for i in range(max(len(cbl), len(lbl))):
        c = cbl[i] if i < len(cbl) else None
        l = lbl[i] if i < len(lbl) else None
        if c == l:
            continue
        rng = (l or c or {}).get("declared", ["?", "?"])
        diffs.append(
            f"    block {rng[0]}-{rng[1]}: committed="
            f"{(c or {}).get('measured_subranges')} live="
            f"{(l or {}).get('measured_subranges')}")
    return False, (
        "THE MEASURED SEED RECORD IS STALE — the tree draws seeds this "
        "committed record does not describe.\n"
        + "\n".join(diffs[:25])
        + ("\n    ... and more" if len(diffs) > 25 else "")
        + "\n  THIS IS THE NUISANCE MODE, AND IT IS A TRUE POSITIVE: you (or a\n"
          "  rung merged under you) changed which seeds this tree draws. §11\n"
          "  rec #4 asks that MEASURED sub-ranges be recorded, not just the\n"
          "  declared block. Regenerate — one command, no judgement:\n"
          "      python3 -m domains.seed_record --write\n"
          "  then read the diff: it IS the record the protocol asked for.")


# ---- §11 rec #7: a prereg must record its check_claim output ---------------

def prereg_files(root: str = ROOT) -> list[str]:
    return sorted(f for f in os.listdir(root)
                  if f.startswith(_PREREG_PREFIX) and f.endswith(_PREREG_SUFFIX))


def _claim_verdicts(text: str) -> list[tuple[int, int]]:
    """Ranges for which this document records a `check_claim` VERDICT.

    Matched on the TOOL'S OWN emitted header — `SEED CLAIM <lo>-<hi>:` —
    not on a keyword anyone might mention in passing. A document that
    merely says the words "seed claim" does not satisfy this; a document
    that pasted the tool's output does, and pasting the output is the
    entire ask of §11 rec #7.
    """
    found: list[tuple[int, int]] = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("`").strip()
        if not line.startswith("SEED CLAIM "):
            continue
        rest = line[len("SEED CLAIM "):]
        head = rest.split(":", 1)[0].strip()
        for dash in ("-", "–", "—"):
            if dash in head:
                a, _, b = head.partition(dash)
                if a.strip().isdigit() and b.strip().isdigit():
                    found.append((int(a), int(b)))
                break
    return found


def read_prereg_floor(path: str = PREREG_FLOOR_PATH) -> set[str]:
    """The GRANDFATHER SET: pre-registrations that predate this gate.

    An explicit, committed floor — never a date, never an mtime, never
    "files older than X". A gate that is red on arrival for work nobody
    can now go back and redo is a gate agents route around (§10.1 says so
    in those words about the old always-red provenance test). This binds
    every rung AFTER it and none before, and the floor is a list you can
    read.
    """
    if not os.path.isfile(path):
        return set()
    with open(path, "r", encoding="utf-8") as fh:
        return set(json.load(fh)["grandfathered"])


#: The pre-registration of the rung that INSTALLED the gate. Deliberately
#: NOT grandfathered.
#:
#: I generated the floor from `os.listdir` after writing my own
#: pre-registration, so my own document landed in the exempt set — the gate
#: would have been green on me for the reason that it never looked at me.
#: That is the SAME shape as the failure the seed-claim rung recorded (its
#: first positive control passed silently because it planted in an
#: already-declared block) and as the supervisor's injection test that
#: passed because it planted in the wrong subtree. **A gate that exempts
#: its own author has not been tested**, so this rung is inside its own
#: gate and must satisfy it like every rung after it.
_GATE_AUTHOR_PREREG = "VISION_INSTRUMENT_SEAMS_PREREG.md"


def write_prereg_floor(path: str = PREREG_FLOOR_PATH, root: str = ROOT) -> list[str]:
    files = [f for f in prereg_files(root) if f != _GATE_AUTHOR_PREREG]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({
            "_README": (
                "GRANDFATHER FLOOR for the §11 rec #7 prereg claim gate. "
                "Pre-registrations listed here predate the gate and are "
                "exempt. NEVER add to this list to silence a failure — add "
                "the check_claim output to your pre-registration instead. "
                "Generated once by `python3 -m domains.seed_record "
                "--write-floor`. NOTE: the pre-registration of the rung that "
                "INSTALLED this gate is deliberately absent from the list — "
                "a gate that exempts its own author has not been tested."),
            "grandfathered": files,
        }, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return files


def preregs_missing_claim(root: str = ROOT, *, floor_path: str = PREREG_FLOOR_PATH):
    """Pre-registrations, not grandfathered, that record NO claim verdict."""
    floor = read_prereg_floor(floor_path)
    missing = []
    for name in prereg_files(root):
        if name in floor:
            continue
        with open(os.path.join(root, name), "r", encoding="utf-8",
                  errors="replace") as fh:
            if not _claim_verdicts(fh.read()):
                missing.append(name)
    return missing


def main(argv) -> int:
    if "--write" in argv:
        rep = write_record()
        print(f"wrote {os.path.relpath(RECORD_PATH, ROOT)}: "
              f"{rep['blocks_declared']} declared blocks, "
              f"{rep['blocks_measuring_zero']} measuring zero, "
              f"median fill {rep['median_fill']}, "
              f"{rep['undeclared_seeds']} undeclared seeds, "
              f"{rep['unresolved_sinks']} unresolved sinks.")
        return 0
    if "--write-floor" in argv:
        files = write_prereg_floor()
        print(f"grandfathered {len(files)} pre-registrations.")
        return 0
    if "--preregs" in argv:
        missing = preregs_missing_claim()
        print(json.dumps({"missing_claim": missing}, indent=1))
        return 1 if missing else 0
    fresh, msg = record_is_fresh()
    print(msg)
    return 0 if fresh else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
