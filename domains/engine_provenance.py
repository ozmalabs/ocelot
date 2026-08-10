"""engine_provenance — WHICH Rust binary produced this number?

A mechanical, read-only reporter (no agent decisions, no graph state): it
answers one question — *which `_native.abi3.so` is this process actually
running?* — and answers it the only way that cannot be fooled, by reading
the loaded module's own `__file__` rather than by re-deriving a path.

WHY THIS EXISTS (2026-07-17, the two-binary hazard)
---------------------------------------------------
There were TWO `substrate_rs/_native.abi3.so` on this machine:

  * `runners/dsl/python/substrate_rs/_native.abi3.so` (Jul 16) — current,
    built from `runners/dsl/src`, byte-identical to
    `runners/dsl/target/release/libsubstrate_rs.so`;
  * `~/.local/lib/python3.14/site-packages/substrate_rs/_native.abi3.so`
    (Jul 13) — a STALE non-editable pip install of a Jul-3 wheel whose
    `.so` had later been clobbered by a `maturin develop` build.

`conftest.py` inserts only the gamma-substrate ROOT on `sys.path`, not
`runners/dsl/python`. So `pytest tests/...` imported the STALE
site-packages engine, while
`PYTHONPATH=runners/dsl/python pytest tests/...` imported the CURRENT
repo engine. **Two agents could measure two different engines and both
report "green".**

The stale engine predated `runners/dsl/src/vision_primitives.rs`
entirely (no `kernel_wH`/`kernel_wI` symbols). Its failure mode was only
*partly* loud — `ChangeDetect` raised `UnknownTermType`, but
`vf_temporal_diff` simply **never fired**: a rule silently not firing,
which corrupts a measurement without ever raising.

THE FIRST FIX (2026-07-17, machine-level): the site-packages copy was
deleted and a `site-packages/substrate_rs.pth` made to point at the
CANONICAL tree's `runners/dsl/python`, so *every* process — any cwd, with
or without PYTHONPATH — resolved to ONE artifact. "A copy goes stale; a
pointer cannot."

THE CONTRADICTION THAT FIX CREATED (2026-07-17, this module's rewrite)
----------------------------------------------------------------------
PROTOCOL §11 then mandated that every concurrent agent work in its own
git WORKTREE. But the `.pth` is an ABSOLUTE path into the canonical tree,
and `runners/dsl/python/substrate_rs/_native.abi3.so` is gitignored — so
a fresh worktree has NO built artifact and the `.pth` is the only thing
that resolves `substrate_rs` at all.

**Consequence: every worktree silently imports the CANONICAL tree's
engine — and, worse than first understood, the canonical tree's entire
`substrate_rs` PYTHON PACKAGE too.** A pointer cannot go stale, but it
CAN point somewhere other than where you are standing.

This was benign only because no rung had added Rust. The standing
directive is that engine limits are BUILD TASKS, not vetoes — so a rung
adding a Rust Term is expected. The moment one does, it silently measures
the canonical binary and its own `.rs` edit evaporates.

THE ROOT FIX — THE INVARIANT IS ABOUT SOURCE, NOT LOCATION
-----------------------------------------------------------
The old gate asked *"does the engine live in MY tree?"* — which is the
wrong question twice over: it fails in every worktree (so it reads as
"worktrees are just broken, ignore it" — an always-red signal agents route
around), and it would pass on a binary that lives in the right place while
being built from different source.

The question that actually protects a number is:

    **Is the loaded engine a build of THIS TREE'S Rust source?**

Location is irrelevant. Sharing the canonical binary across worktrees is
correct and cheap *precisely when* the Rust source is byte-identical —
which is the common case, since most rungs add no Rust. It becomes wrong
the instant a worktree touches `.rs`, and that is the instant this module
makes it fail loudly. (Rung 7 verified this by hand with an md5 of every
`.rs`; that manual check is what `rust_source_fingerprint` automates.)

So resolution is now TREE-RELATIVE and the check is CONTENT-BASED:

  * `conftest.py` (and `engine_preamble()`) put THIS tree's
    `runners/dsl/python` FIRST on sys.path, so a tree that has built its
    own artifact always gets its own — the `.pth` is only a fallback.
  * A tree with no artifact of its own falls back to the `.pth`, and the
    gate then requires `rust_source_fingerprint(this_tree) ==
    rust_source_fingerprint(engine_tree)`. Identical source ⇒ the shared
    binary IS correct for this source, and the number is attributable.
    Divergent source ⇒ LOUD FAILURE naming the build command.

THE GATE (durable, in-repo): `tests/test_engine_provenance_migrated.py`
— verified to FAIL on the broken setup and PASS on the fixed one, IN BOTH
TREES, and to catch WRONG-TREE as well as STALE.

PROTOCOL: `VISION_PROTOCOL.md` §10 (engine on every result) + §11
(one agent, one worktree) — this module is what makes the two consistent.
"""
from __future__ import annotations

import hashlib
import os
import sys

_NATIVE_REL = os.path.join("substrate_rs", "_native.abi3.so")

# `<tree>/runners/dsl/python/substrate_rs/_native.abi3.so` — the path shape
# every engine artifact in this project has. Used to recover the TREE a
# loaded engine was built in, so its Rust source can be fingerprinted.
_ENGINE_REL = os.path.join("runners", "dsl", "python", _NATIVE_REL)
_RUST_SRC_REL = os.path.join("runners", "dsl", "src")
_CARGO_REL = os.path.join("runners", "dsl", "Cargo.toml")

# This module lives at `<tree>/domains/engine_provenance.py`.
THIS_TREE = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def tree_python_dir(tree: str = THIS_TREE) -> str:
    """Where `substrate_rs` lives inside a tree. What must go on sys.path
    FIRST for resolution to be tree-relative rather than `.pth`-relative."""
    return os.path.join(tree, "runners", "dsl", "python")


def ensure_tree_engine(tree: str = THIS_TREE) -> str | None:
    """Give a tree an engine at its OWN path when it legitimately may share
    one — by symlinking a source-identical build. Returns the path, or None.

    THE HEADLESS-PACKAGE TRAP (the third face of the §10/§11 contradiction,
    and the sharpest). `runners/dsl/python/substrate_rs/*.py` is TRACKED but
    `_native.abi3.so` is GITIGNORED. So a fresh worktree ships the package
    WITHOUT its binary — and every script following the convention §10 rule
    4 called "safe" (`sys.path.insert(0, runners/dsl/python)`) pins that
    HEADLESS package, which SHADOWS the canonical `.pth` and dies with
    `cannot import name '_native' ... (most likely due to a circular
    import)` — a misleading message for a path problem.

    Measured: this breaks 3 of the 16 vision bench files in EVERY worktree,
    before any change of mine. In the canonical tree the same preamble pins
    the right engine; in a worktree it pins a package with no engine at all.
    **The convention is not portable, and that is why this exists.**

    So: if the source is byte-identical to a resolvable tree's, link that
    tree's build to our own path. Every existing preamble then works
    unchanged, in every tree, and provenance stays honest — `realpath`
    resolves the symlink, so the record names the REAL artifact and the
    verdict reads `shared`, never pretending the build was ours.

    If the source DIVERGES we deliberately do NOT link: the tree must build
    its own (that is the whole point), and it fails loudly instead.
    """
    own = os.path.join(tree, _ENGINE_REL)
    if os.path.exists(own):
        return own
    pkg = os.path.join(tree_python_dir(tree), "substrate_rs")
    if not os.path.isdir(pkg):
        return None  # tree ships no package; the .pth resolves everything

    mine = rust_source_fingerprint(tree)
    for cand in resolvable_natives():
        ctree = tree_of_native(cand)
        if ctree is None or os.path.realpath(ctree) == os.path.realpath(tree):
            continue
        if mine is not None and rust_source_fingerprint(ctree) == mine:
            try:
                os.symlink(cand, own)
            except FileExistsError:  # another process won the race — fine
                pass
            except OSError:
                return None
            return own

    print(
        f"engine_provenance: {tree} ships substrate_rs but has NO engine, and "
        "no resolvable build matches its Rust source. Scripts that insert "
        "runners/dsl/python will fail with a misleading '_native / circular "
        "import' error.\n  This tree's Rust differs from every available "
        "build — BUILD IT:\n    cd runners/dsl && cargo build --release && "
        "cp target/release/libsubstrate_rs.so "
        "python/substrate_rs/_native.abi3.so",
        file=sys.stderr)
    return None


class EngineProvenanceError(RuntimeError):
    """The process that is about to take a number is on the wrong engine.

    Raised IN the measuring process, from the verdict computed off the
    module resident in ITS `sys.modules` — never from a tree inspection
    performed somewhere else.
    """


def assert_measuring_engine(tree: str = THIS_TREE) -> dict:
    """REFUSE to measure on an engine that is provably not this tree's.

    WHY THIS EXISTS — THE DEFECT IT CLOSES (2026-07-19, surface-assignment)
    -----------------------------------------------------------------------
    A concurrent rung rebuilt the CANONICAL tree's engine from changed Rust
    source mid-pilot. In the SAME MINUTE:

        pytest tests/test_engine_provenance_migrated.py   ->  7 PASSED
        a plain script in the same tree                   ->  ** WRONG ENGINE **

    Both readings were correct. **The gate certifies the TREE'S CONFIG
    UNDER ITS OWN PREAMBLE; it does not certify that the process you are
    about to measure in loaded the engine you think it did.** A bare
    `python -c` with `sys.path.insert(0, '.')` picks up the canonical
    `.pth` first, and the gate is silent about it — a green gate in a
    DIFFERENT PROCESS IS NOT PROVENANCE.

    The surface-assignment rung applied the fix locally (print
    `provenance_line()` from inside the measuring process; abort on
    divergence) and offered it upward. This is that fix, made structural:
    attached to the call §10 rule 3 ALREADY REQUIRES of every non-pytest
    entrypoint, so no rung has to remember it.

    Refuses on:
      * ``DIVERGED`` — a foreign build from DIFFERENT Rust source. Every
        number from this process would be attributed to source that did
        not produce it.
      * ``unknown``  — the engine is not a tree build (a stray copy).
        Nothing can be verified about it, and an UNVERIFIABLE ENGINE IS
        NOT A PASS.

    Does NOT refuse on ``own`` or ``shared``: a shared build from
    byte-identical Rust source is CORRECT for this source (§10.1 — the
    invariant is CONTENT, not LOCATION). Refusing it would make the check
    unconditionally red in every worktree, which is the failure mode that
    turns a gate into something agents route around.

    Returns the provenance record so a caller can stamp it.
    """
    p = engine_provenance(tree)
    if p["source_match"] in ("DIVERGED", "unknown"):
        raise EngineProvenanceError(
            "REFUSING TO MEASURE — " + provenance_line(tree) + "\n"
            f"  verdict:      {p['source_match']}\n"
            f"  loaded:       {p['native_path']}\n"
            f"  engine tree:  {p['engine_tree']}\n"
            f"  this tree:    {p['this_tree']}\n"
            "  A green provenance gate in a DIFFERENT PROCESS is not\n"
            "  provenance (PROTOCOL §10). Build this tree's engine:\n"
            "      bash scripts/engine_build.sh\n"
            "  If you are deliberately not measuring the engine, call\n"
            "  engine_preamble(strict=False) — and say so in your results.")
    if p["stale_rust"]:
        raise EngineProvenanceError(
            "REFUSING TO MEASURE — " + provenance_line(tree) + "\n"
            f"  {len(p['stale_rust'])} .rs file(s) are NEWER than the binary: "
            f"{p['stale_rust'][:5]}\n"
            "  Edited Rust, forgot to rebuild:  bash scripts/engine_build.sh")
    return p


def engine_preamble(tree: str = THIS_TREE, *, strict: bool = True) -> None:
    """Make `import substrate_rs` resolve to THIS TREE's engine, THEN
    verify in-process that it did. Mechanical sys.path work + a refusal —
    the fix for the `.pth`/worktree contradiction, in the one place every
    entrypoint can call.

    A tree that built its own artifact gets its own. A tree that may share
    one (identical Rust source) gets it linked at its own path, so the
    tree is self-consistent for every script. A tree whose source diverges
    gets nothing, and fails loudly rather than silently measuring another
    tree's binary.

    THE SEAM (2026-07-19). `strict=True` is the default because THIS CALL
    IS ALREADY MANDATORY for every non-pytest entrypoint (§10 rule 3). The
    check therefore costs NO new ceremony and cannot be forgotten
    separately from the thing it guards: you cannot pin the engine without
    also certifying what you pinned. A rung has to actively pass
    `strict=False` to get the old silent behaviour, and that is a visible
    choice in a diff rather than an omission.

    `conftest.py` passes `strict=False` DELIBERATELY: pytest already has a
    dedicated gate (`tests/test_engine_provenance_migrated.py`) that
    reports DIVERGED as two named test failures, and turning that into a
    collection-time abort would move the ORACLE's protocol number
    (§9 — defaults preserve committed results). The gate reports; the
    preamble refuses; neither was made to do the other's job.

    A tree with no resolvable engine at all is NOT refused here: the
    ImportError that follows at the real import site is already loud, and
    raising a provenance error instead would only mislabel it.
    """
    ensure_tree_engine(tree)
    if os.path.exists(os.path.join(tree, _ENGINE_REL)):
        pydir = tree_python_dir(tree)
        if sys.path[:1] != [pydir]:
            while pydir in sys.path:
                sys.path.remove(pydir)
            sys.path.insert(0, pydir)
    if strict:
        try:
            assert_measuring_engine(tree)
        except ImportError:
            # No engine resolvable at all. Loud at the use site already.
            pass


def provenance_stamp(tree: str = THIS_TREE, *, strict: bool = True) -> dict:
    """The record §10 rule 1 wants in every results artifact — and the
    refusal that makes recording it mean something.

    `provenance_line()` and `engine_provenance()` are PURE REPORTERS and
    stay that way: the existing gate reads them to describe a broken
    setup, so making them raise would break the instrument that diagnoses
    the fault. This is the WRITE-side entry point instead — call it where
    the number is written down:

        rec["engine_provenance"] = provenance_stamp()

    Returns the full record plus its one-line form under ``"line"``.
    """
    p = assert_measuring_engine(tree) if strict else engine_provenance(tree)
    p = dict(p)
    p["line"] = provenance_line(tree)
    return p


def tree_of_native(native_path: str) -> str | None:
    """The TREE a loaded engine was built in, recovered from its path.

    `<tree>/runners/dsl/python/substrate_rs/_native.abi3.so` -> `<tree>`.
    Returns None for an artifact that is not in that shape (e.g. a
    site-packages COPY — which §10 forbids and which has no Rust source
    to fingerprint, so it can never be shown correct for this tree).
    """
    real = os.path.realpath(native_path)
    suffix = os.sep + _ENGINE_REL
    if not real.endswith(suffix):
        return None
    return real[: -len(suffix)]


def rust_source_fingerprint(tree: str = THIS_TREE) -> str | None:
    """Content hash of a tree's Rust source — `runners/dsl/src/**/*.rs`
    plus `Cargo.toml`. THE identity a binary must match to be correct for
    this tree.

    Content, never mtime: a git checkout rewrites every mtime, so mtimes
    are meaningless ACROSS trees. (Within the build tree they still catch
    a forgotten rebuild — see `build_is_stale`.)
    """
    src = os.path.join(tree, _RUST_SRC_REL)
    if not os.path.isdir(src):
        return None
    h = hashlib.sha256()
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames.sort()
        for name in sorted(filenames):
            if name.endswith(".rs"):
                files.append(os.path.join(dirpath, name))
    for path in sorted(files):
        h.update(os.path.relpath(path, tree).encode())
        h.update(sha256_of(path).encode())
    cargo = os.path.join(tree, _CARGO_REL)
    if os.path.isfile(cargo):
        h.update(b"Cargo.toml")
        h.update(sha256_of(cargo).encode())
    return h.hexdigest()


def build_is_stale(tree: str) -> list[str]:
    """`.rs` files NEWER than the built artifact, within the tree that
    BUILT it. Catches "edited Rust, forgot to rebuild" — the failure the
    source fingerprint alone cannot see, because it compares this tree to
    the engine's tree and both can be equally un-rebuilt.

    mtime is meaningful here and only here: this is the working tree where
    the build actually ran.
    """
    native = os.path.join(tree, _ENGINE_REL)
    if not os.path.isfile(native):
        return []
    built = os.path.getmtime(native)
    newer: list[str] = []
    src = os.path.join(tree, _RUST_SRC_REL)
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames.sort()
        for name in sorted(filenames):
            if not name.endswith(".rs"):
                continue
            path = os.path.join(dirpath, name)
            if os.path.getmtime(path) > built:
                newer.append(os.path.relpath(path, tree))
    return newer


def sha256_of(path: str) -> str:
    """Full content hash of a file. Mechanical I/O."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def loaded_native_path() -> str:
    """The `_native` extension THIS process actually imported.

    Read off the imported module itself — never re-derived from sys.path,
    which is exactly the ambiguity this module exists to detect.
    """
    import substrate_rs  # noqa: PLC0415 — deliberate: report what loads

    return os.path.realpath(substrate_rs._native.__file__)


def resolvable_natives() -> list[str]:
    """Every distinct `_native.abi3.so` reachable from this `sys.path`.

    Returns realpaths, deduplicated, in sys.path order. More than one
    DISTINCT artifact here (by content) is the two-binary hazard.
    """
    found: list[str] = []
    seen: set[str] = set()
    for entry in sys.path:
        if not entry:
            entry = os.getcwd()
        cand = os.path.realpath(os.path.join(entry, _NATIVE_REL))
        if cand in seen:
            continue
        if os.path.isfile(cand):
            seen.add(cand)
            found.append(cand)
    return found


def distinct_native_artifacts() -> dict[str, list[str]]:
    """sha256 -> [paths]. One key == one engine. Two keys == the hazard."""
    by_hash: dict[str, list[str]] = {}
    for path in resolvable_natives():
        by_hash.setdefault(sha256_of(path), []).append(path)
    return by_hash


def engine_provenance(tree: str = THIS_TREE) -> dict:
    """The provenance record every result must carry (PROTOCOL §10).

    Mechanical: what loaded, its hash, WHICH TREE built it, and — the
    question that actually protects the number — whether that tree's Rust
    source is identical to THIS tree's.

    `source_match` is the verdict:
      * "own"     — the engine is this tree's own build. Ideal.
      * "shared"  — a foreign tree's build, but byte-identical Rust
                    source ⇒ correct for this source, and attributable.
      * "DIVERGED"— a foreign build from DIFFERENT Rust source. Every
                    number from this process is measuring the wrong
                    engine. THE failure §10/§11 exist to prevent.
      * "unknown" — the engine is not in a tree shape (a stray copy);
                    nothing can be verified about it.
    """
    path = loaded_native_path()
    digest = sha256_of(path)
    others = [p for p in resolvable_natives() if os.path.realpath(p) != path]
    etree = tree_of_native(path)
    mine = rust_source_fingerprint(tree)
    theirs = rust_source_fingerprint(etree) if etree else None

    if etree is None or theirs is None or mine is None:
        match = "unknown"
    elif os.path.realpath(etree) == os.path.realpath(tree):
        match = "own"
    elif theirs == mine:
        match = "shared"
    else:
        match = "DIVERGED"

    return {
        "native_path": path,
        "sha256": digest,
        "short": digest[:12],
        "mtime": os.path.getmtime(path),
        "other_resolvable": others,
        "ambiguous": len(distinct_native_artifacts()) > 1,
        "this_tree": os.path.realpath(tree),
        "engine_tree": etree,
        "source_fingerprint": mine,
        "engine_source_fingerprint": theirs,
        "source_match": match,
        "stale_rust": build_is_stale(etree) if etree else [],
    }


def provenance_line(tree: str = THIS_TREE) -> str:
    """One-line human/log form: paste into any results file or log.

    Carries the engine hash, the path, AND the source verdict — because
    "engine X @ path" alone does not say whether X is a build of the tree
    whose numbers you are about to record.
    """
    p = engine_provenance(tree)
    notes = []
    # A STRAY copy (not a tree build) is the §10 hazard: unverifiable, and
    # it can win in any process that skips `engine_preamble()`. A shadowed
    # TREE build is not — under §11 a worktree's own build legitimately
    # shadows the canonical `.pth`, deterministically. Distinguish them, or
    # the loud flag fires on the correct configuration and stops being read.
    strays = [q for q in p["other_resolvable"] if tree_of_native(q) is None]
    if strays:
        notes.append(f"** STRAY ENGINE COPY RESOLVABLE — {strays} **")
    elif p["other_resolvable"]:
        notes.append(f"[{len(p['other_resolvable'])} other tree build(s) shadowed]")
    if p["source_match"] == "DIVERGED":
        notes.append(
            "** WRONG ENGINE — built from DIFFERENT Rust source than this tree "
            f"({p['engine_tree']}) — REBUILD, see engine_provenance **")
    elif p["source_match"] == "shared":
        notes.append(f"[shared build from {p['engine_tree']} — Rust source identical]")
    elif p["source_match"] == "unknown":
        notes.append("** UNVERIFIABLE — engine is not a tree build **")
    if p["stale_rust"]:
        notes.append(f"** STALE — {len(p['stale_rust'])} .rs newer than the binary **")
    suffix = ("  " + "  ".join(notes)) if notes else ""
    return f"engine {p['short']} @ {p['native_path']}{suffix}"


if __name__ == "__main__":
    # `engine_preamble()` FIRST — before anything can import substrate_rs.
    # Reporting the engine without it would report whatever the `.pth`
    # resolves, which is the very bug this module exists to catch. (Caught
    # exactly that way: this entrypoint printed the canonical engine while
    # this tree had its own build sitting next to it.)
    engine_preamble()
    print(provenance_line())
