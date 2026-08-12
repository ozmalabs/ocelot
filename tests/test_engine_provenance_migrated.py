"""test_engine_provenance_migrated — THE TWO-BINARY GATE.

*Everything this project measures is suspect if the process can silently
get the wrong Rust engine. This file makes that impossible to miss.*

THE HAZARD (found 2026-07-16 by the rung-6 agent, fixed 2026-07-17)
-------------------------------------------------------------------
Two `substrate_rs/_native.abi3.so` existed:

  * repo `runners/dsl/python/substrate_rs/` — Jul 16, CURRENT
    (byte-identical to `runners/dsl/target/release/libsubstrate_rs.so`);
  * `~/.local/lib/python3.14/site-packages/substrate_rs/` — Jul 13,
    STALE (a non-editable pip install of a Jul-3 wheel, `.so` later
    clobbered by a `maturin develop` build).

`conftest.py` puts only the repo ROOT on sys.path — NOT
`runners/dsl/python` — so bare `pytest` imported the STALE engine and
`PYTHONPATH=runners/dsl/python pytest` imported the CURRENT one. Two
agents, two engines, both reporting "green". Measured divergence on the
vision bench: **stale 3 failed / 38 passed, current 41 passed.**

The stale engine predated `vision_primitives.rs` entirely. Its failure
was only PARTLY loud: `ChangeDetect` raised `UnknownTermType`, but
`vf_temporal_diff` **silently never fired** — the dangerous kind, a rule
quietly not firing, corrupting a measurement without raising.

THE SECOND HAZARD — WRONG TREE (found 2026-07-17, this file's rewrite)
----------------------------------------------------------------------
The §10 fix made the `.pth` an ABSOLUTE path into the CANONICAL tree.
§11 then mandated one worktree per agent. Together: **every worktree
silently imports the canonical tree's engine**, because the artifact is
gitignored and the `.pth` is the only resolver a fresh worktree has.

Benign only while no rung added Rust. The standing directive is that
engine limits are BUILD TASKS, not vetoes — so a rung adding a Rust Term
is expected, and on that day it would have measured the canonical binary
while believing it measured its own.

WHY THESE TESTS
---------------
1. `test_exactly_one_native_artifact_is_resolvable` — the STALE hazard:
   two DISTINCT engines reachable from one sys.path. (Note it does NOT
   catch wrong-tree: in a worktree exactly one artifact resolves — the
   canonical one — so this test passes while the tree is wrong.)
2. `test_loaded_engine_is_a_build_of_THIS_TREES_rust_source` — the
   WRONG-TREE gate. Asks the only question that protects a number: is the
   engine a build of THIS tree's Rust source? Passes in canonical AND
   worktree when the source agrees; fails in BOTH when it diverges.
   Replaces an `loaded == REPO_NATIVE` check that was unconditionally red
   in every worktree — an always-red gate is one agents route around.
3. `test_a_worktree_that_builds_its_own_engine_gets_its_own` — the fix as
   a property: resolution is tree-relative, so a worktree that builds gets
   its own binary.
4. `test_source_fingerprint_is_content_not_location` — pins both halves of
   the fingerprint: same content/different path must AGREE (or worktrees
   could never share the canonical build), one changed byte must DISAGREE
   (or the wrong-tree gate cannot bite).
5. `test_engine_exposes_the_vision_terms` — a CAPABILITY pin on the exact
   Terms whose absence was the real symptom. The path/source checks would
   both pass on a stale binary at the RIGHT path with the RIGHT source
   fingerprint; only evaluating a Term catches that.

VERIFIED TO FAIL ON THE BROKEN SETUP, IN BOTH TREES. A gate that has never
failed is not a gate — and this exact defect has already recurred twice in
this arc. Verification, both recorded in the commit message:
  * STALE: restore the stale site-packages install -> (1) and (5) fail.
  * WRONG TREE: touch a `.rs` in a worktree -> (2) fails loudly in the
    worktree, passes in canonical. Before this rewrite the same change was
    silently ignored and the canonical answer returned.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import engine_provenance as ep  # noqa: E402
from domains.engine_provenance import (  # noqa: E402
    distinct_native_artifacts,
    engine_preamble,
    engine_provenance,
    loaded_native_path,
    provenance_line,
    resolvable_natives,
    rust_source_fingerprint,
    sha256_of,
    tree_of_native,
)

engine_preamble()

REPO_NATIVE = os.path.realpath(
    os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so"))
RELEASE_BUILD = os.path.join(ROOT, "runners", "dsl", "target", "release",
                             "libsubstrate_rs.so")


def test_no_stray_native_copy_is_resolvable():
    """THE STALE HAZARD: a `_native.abi3.so` that is NOT a tree build.

    The original form of this test was "exactly ONE artifact is
    resolvable". That was right for a one-tree world and WRONG under §11
    (one agent, one worktree): a worktree that builds its own engine
    legitimately makes TWO artifacts resolvable — its own (first on
    sys.path, and the one that loads) and the canonical one behind the
    `.pth`. Forbidding that would forbid the very per-worktree build that
    fixes the wrong-tree hazard.

    So the hazard is stated precisely instead. A **tree build** —
    `<tree>/runners/dsl/python/substrate_rs/_native.abi3.so` — can always
    be checked: it has Rust source next to it to fingerprint. A **stray
    copy** (the Jul-13 site-packages pip install that caused this whole
    section) cannot: there is no source to compare it against, so nothing
    about it can ever be verified. That is what must not exist.

    `test_resolution_is_deterministic` covers the other half — that among
    legitimate tree builds, the one that loads is not a matter of luck.
    """
    strays = [p for p in resolvable_natives() if tree_of_native(p) is None]
    if strays:
        pytest.fail(
            "STRAY ENGINE COPY resolvable — this is the artifact that made one "
            "session report six different answers for a suite with one:\n"
            + "\n".join(f"  {p}" for p in strays)
            + "\n\nIt is not a tree build, so it has no Rust source to "
            "fingerprint and can never be shown correct for anything. Delete "
            "it. Never `pip install` / `maturin develop` substrate_rs into "
            "site-packages (PROTOCOL §10 rule 2); build in place under "
            "runners/dsl/ instead.")
    assert resolvable_natives(), "no `_native.abi3.so` resolvable at all"


def test_resolution_is_deterministic():
    """The engine that loads must be the FIRST one on sys.path, not
    whichever import order happens to pick.

    With per-tree builds (§11) more than one legitimate engine can be
    resolvable. That is safe ONLY because resolution is ordered and
    `engine_preamble()` puts this tree's own build first. If the loaded
    engine were NOT the first resolvable, sys.path order would be doing
    something subtle and the next refactor would silently change which
    binary every number came from.
    """
    resolvable = resolvable_natives()
    loaded = loaded_native_path()
    assert resolvable, "no `_native.abi3.so` resolvable at all"
    assert os.path.realpath(resolvable[0]) == os.path.realpath(loaded), (
        "the loaded engine is NOT the first resolvable on sys.path — which "
        "one you get is an accident of import order:\n"
        f"  loaded         : {loaded}\n"
        f"  first on path  : {resolvable[0]}\n"
        f"  all resolvable : {resolvable}\n"
        "`engine_preamble()` should have put this tree's build first.")

    shadowed = [p for p in resolvable[1:]
                if sha256_of(p) != sha256_of(loaded)]
    if shadowed:
        # Not a failure: a worktree with its own build legitimately shadows
        # the canonical `.pth`. Report it, so the number's provenance is
        # readable in the log rather than inferred later.
        print(f"NOTE: {len(shadowed)} other engine(s) shadowed by this tree's "
              f"own build (correctly, and deterministically): {shadowed}")
        by_hash = distinct_native_artifacts()
        print(f"NOTE: {len(by_hash)} distinct artifacts resolvable; loaded "
              f"{sha256_of(loaded)[:12]} wins by sys.path order.")


def test_loaded_engine_is_a_build_of_THIS_TREES_rust_source():
    """THE WRONG-TREE GATE — the one that had to be rewritten.

    The old version asserted `loaded == REPO_NATIVE`: *"does the engine
    live in MY tree?"* That question is wrong twice over.

      * It FAILED IN EVERY WORKTREE. The `.pth` is an absolute path into
        the canonical tree and the artifact is gitignored, so a worktree
        has no engine of its own and this test was unconditionally red —
        which is worse than useless, because an always-red gate is one
        agents learn to route around. (PROTOCOL §11 mandates worktrees;
        §10 mandated the absolute `.pth`. They contradicted.)
      * It would PASS on a binary at the right PATH built from different
        SOURCE — the stale-in-place case §10 already knew it could not see.

    The question that actually protects a number is: **is the loaded
    engine a build of THIS TREE'S Rust source?** Location is irrelevant.
    Sharing the canonical build across worktrees is correct precisely
    when the `.rs` is byte-identical — the common case, since most rungs
    add no Rust — and wrong the instant a worktree touches Rust, which is
    the instant this fails.

    So this gate PASSES in both trees when the source agrees, and FAILS in
    both when it does not. It catches WRONG-TREE and STALE alike.
    """
    p = engine_provenance()
    print(provenance_line())

    assert p["source_match"] != "unknown", (
        f"engine at {p['native_path']} is not a tree build — it has no "
        "`runners/dsl/src` to fingerprint, so nothing about it can be "
        "verified. This is the site-packages COPY §10 forbids.")

    assert p["source_match"] != "DIVERGED", (
        "WRONG ENGINE — this process imported a build of a DIFFERENT tree's "
        "Rust source. Every number measured here is attributed to source "
        "that did not produce it.\n"
        f"  loaded      : {p['native_path']}\n"
        f"  engine tree : {p['engine_tree']}\n"
        f"    its src   : {(p['engine_source_fingerprint'] or '-')[:12]}\n"
        f"  this tree   : {p['this_tree']}\n"
        f"    its src   : {(p['source_fingerprint'] or '-')[:12]}\n\n"
        "This tree's Rust differs from the engine's. Build THIS tree:\n"
        "  cd runners/dsl && cargo build --release && \\\n"
        "    cp target/release/libsubstrate_rs.so "
        "python/substrate_rs/_native.abi3.so\n"
        "conftest.py's `engine_preamble()` then puts it first on sys.path.")

    assert not p["stale_rust"], (
        "STALE ENGINE — Rust source is NEWER than the binary built from it, "
        f"in the tree that built it ({p['engine_tree']}). The source "
        "fingerprint cannot see this: both trees can be equally un-rebuilt.\n"
        f"  newer than the .so: {p['stale_rust'][:5]}\n"
        "  cd runners/dsl && cargo build --release && cp "
        "target/release/libsubstrate_rs.so python/substrate_rs/_native.abi3.so")

    # A tree's OWN build must be the current release build of its own src.
    if p["source_match"] == "own" and os.path.isfile(RELEASE_BUILD):
        loaded = p["native_path"]
        assert sha256_of(loaded) == sha256_of(RELEASE_BUILD), (
            "the loaded engine is NOT the current release build of "
            f"runners/dsl/src.\n  loaded : {sha256_of(loaded)[:12]}\n"
            f"  release: {sha256_of(RELEASE_BUILD)[:12]}\n"
            "Rebuild and copy the artifact into runners/dsl/python/"
            "substrate_rs/ — otherwise results reflect older Rust than the "
            "source in this tree.")


def test_a_worktree_that_builds_its_own_engine_gets_its_own():
    """The FIX, stated as a property: resolution is TREE-RELATIVE.

    `engine_preamble()` puts a tree's own `runners/dsl/python` first on
    sys.path *iff* that tree has built an artifact. So a worktree that
    adds a Rust Term and builds gets ITS binary, not the canonical one —
    which is exactly what the absolute `.pth` silently prevented.
    """
    import domains.engine_provenance as ep

    tree = ep.THIS_TREE
    have_own = os.path.isfile(os.path.join(tree, "runners", "dsl", "python",
                                           "substrate_rs", "_native.abi3.so"))
    saved = list(sys.path)
    try:
        ep.engine_preamble(tree)
        if have_own:
            assert sys.path[0] == ep.tree_python_dir(tree), (
                "this tree HAS its own engine but `engine_preamble` did not "
                "put it first on sys.path — the .pth would win and the tree "
                "would measure another tree's binary.")
        else:
            # No artifact of its own: the .pth fallback is correct, and the
            # source-fingerprint gate above is what makes it safe.
            assert ep.tree_python_dir(tree) not in sys.path[:1], (
                "a tree with no built engine must not shadow the .pth with "
                "an empty directory — that would break the import entirely.")
    finally:
        sys.path[:] = saved


def test_source_fingerprint_is_content_not_location():
    """The fingerprint must be a function of Rust SOURCE only.

    Two trees at the same commit MUST agree (or the shared-build case
    would be unusable and every worktree would need a full cargo build);
    a single changed byte MUST disagree (or the wrong-tree gate above
    cannot bite). Both halves are load-bearing, so both are pinned.
    """
    import tempfile

    import domains.engine_provenance as ep

    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "runners", "dsl", "src")
        os.makedirs(src)
        with open(os.path.join(td, "runners", "dsl", "Cargo.toml"), "w") as fh:
            fh.write("[package]\nname='x'\n")
        rs = os.path.join(src, "lib.rs")
        with open(rs, "w") as fh:
            fh.write("fn a() {}\n")
        first = ep.rust_source_fingerprint(td)

        # A copy at a DIFFERENT path with identical content -> same print.
        other = os.path.join(td, "copy")
        os.makedirs(os.path.join(other, "runners", "dsl", "src"))
        with open(os.path.join(other, "runners", "dsl", "Cargo.toml"), "w") as fh:
            fh.write("[package]\nname='x'\n")
        with open(os.path.join(other, "runners", "dsl", "src", "lib.rs"), "w") as fh:
            fh.write("fn a() {}\n")
        assert ep.rust_source_fingerprint(other) == first, (
            "fingerprint depends on LOCATION — then a worktree could never "
            "share the canonical build and the fix collapses.")

        # One changed byte -> different print. This is what makes it a gate.
        with open(rs, "w") as fh:
            fh.write("fn a() { }\n")
        assert ep.rust_source_fingerprint(td) != first, (
            "fingerprint did not change on a changed .rs — the wrong-tree "
            "gate cannot bite and a worktree's Rust edit would evaporate.")


def test_engine_exposes_the_vision_terms():
    """CAPABILITY pin — the symptom the path checks cannot see.

    The stale engine lacked `vision_primitives.rs` altogether. `ChangeDetect`
    raised loudly; `TemporalDiff`'s rule just never fired. Evaluate both
    Terms for real, so a stale binary at the right path still fails here.
    """
    import numpy as np
    import substrate_rs
    from substrate_rs import Attr, Lit, Term, Vec

    print(provenance_line())

    s = substrate_rs.Substrate()
    image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=float)
    kernel = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]], dtype=float)

    nid = s.add_node("Kernel", {"weights": kernel.flatten().tolist(),
                                "kh": 3.0, "kw": 3.0})
    term = Term(
        "ChangeDetect",
        image_vals=Lit(image.flatten().tolist()),
        kernel_weights=Attr(Lit(nid), "weights"),
        dims=Vec([Lit(3), Lit(3), Lit(3), Lit(3), Lit(1)]),
    )
    resp = list(s.evaluate(term))
    assert len(resp) == 1, (
        f"ChangeDetect valid-response shape wrong: {resp} — this engine does "
        "not carry runners/dsl/src/vision_primitives.rs")

    # TemporalDiff — the SILENT one. Its absence made `vf_temporal_diff`
    # never fire, with no error raised anywhere.
    # `a_vals` = prior frame, `b_vals` = current; returns b[i] - a[i].
    diff = Term(
        "TemporalDiff",
        a_vals=Lit([1.0, 1.0, 1.0, 1.0]),
        b_vals=Lit([1.0, 2.0, 3.0, 4.0]),
    )
    out = list(s.evaluate(diff))
    assert out == pytest.approx([0.0, 1.0, 2.0, 3.0]), (
        f"TemporalDiff wrong/absent: {out} — the dorsal motion stream would "
        "silently not fire on this engine.")


def test_provenance_record_is_reportable():
    """PROTOCOL §10 — every result records which binary produced it. The
    record must be complete enough to identify the engine after the fact.
    """
    p = engine_provenance()
    assert p["native_path"] and os.path.isfile(p["native_path"])
    assert len(p["short"]) == 12
    assert p["short"] in provenance_line()

    # The record must name the TREE and the source verdict, not just the
    # binary. "engine X @ path" cannot answer the question that actually
    # protects a number — whether X was built from the source you are
    # attributing the number to.
    assert p["source_match"] in ("own", "shared"), (
        f"engine source verdict is {p['source_match']!r} — see "
        "test_loaded_engine_is_a_build_of_THIS_TREES_rust_source")
    assert p["engine_tree"] and p["source_fingerprint"]
    assert p["this_tree"] == os.path.realpath(ROOT)

    # `ambiguous` (>1 distinct artifact resolvable) is NOT an error under
    # §11: a worktree with its own build shadows the canonical `.pth` by
    # design. It must still be REPORTED, so a reader of the log can see
    # that another engine was present and which one won.
    if p["ambiguous"]:
        assert p["other_resolvable"], (
            "reported ambiguous but named no other engine — a provenance "
            "record that cannot be reconciled later")
        assert "shared" in provenance_line() or p["source_match"] == "own"


# --------------------------------------------------------------------------- #
#  STALENESS IS CONTENT, NOT MTIME (added 2026-08-12, red-test triage)
#
#  `build_is_stale` compared `os.path.getmtime`, documented as "meaningful here
#  and only here: this is the working tree where the build actually ran." The
#  premise is false for a tree GIT wrote: `git worktree add` stamps every file
#  with the checkout time in whatever order it writes them, so a brand-new
#  worktree gets `.rs` files microseconds newer than a `.so` neither of them
#  built. MEASURED at d239b7c: 85 false "STALE" `.rs` in a fresh worktree
#  (2 ms apart), 5 in the canonical tree — and because `assert_measuring_engine`
#  refuses on `stale_rust`, that FALSE ACCUSATION was the single largest red
#  class in the tree: 117 node ids across 88 files, on an engine that was
#  exactly the committed one.
#
#  Positive-controlled in BOTH directions, per protocol 12.3 — a gate you have
#  only ever seen pass is not a gate you have tested.
# --------------------------------------------------------------------------- #
def test_a_freshly_checked_out_tree_is_NOT_stale():
    """The regression this fix exists to prevent. THIS tree is a git checkout
    whose Rust source is clean at HEAD — whatever its mtimes say, no source has
    moved since the artifact was committed, so nothing is stale."""
    import subprocess
    dirty = subprocess.run(
        ["git", "-C", ROOT, "status", "--porcelain", "--",
         "runners/dsl/src", "runners/dsl/Cargo.toml"],
        capture_output=True, text=True).stdout.strip()
    if dirty:
        pytest.skip(f"this tree has uncommitted Rust source: {dirty.splitlines()[:3]}")
    assert ep.build_is_stale(ROOT) == [], (
        "a clean checkout was reported STALE — the mtime regression is back. "
        f"{ep.build_is_stale(ROOT)[:5]}")


def test_the_staleness_check_BITES_edited_rust(tmp_path):
    """...and it must still catch the real failure it was written for: source
    edited after the build. Content, so it bites through git, with no record."""
    import shutil
    tree = tmp_path / "tree"
    (tree / "runners" / "dsl" / "src").mkdir(parents=True)
    (tree / "runners" / "dsl" / "python" / "substrate_rs").mkdir(parents=True)
    (tree / "runners" / "dsl" / "src" / "a.rs").write_text("fn a() {}\n")
    (tree / "runners" / "dsl" / "Cargo.toml").write_text("[package]\n")
    (tree / "runners" / "dsl" / "python" / "substrate_rs"
     / "_native.abi3.so").write_bytes(b"\x7fELF-not-really")

    assert ep.build_is_stale(str(tree)) == [], \
        "no record and no git — UNKNOWN must return [], never a manufactured red"

    ep.record_build(str(tree))
    assert ep.build_is_stale(str(tree)) == [], "just-recorded build reported stale"

    (tree / "runners" / "dsl" / "src" / "a.rs").write_text("fn a() { 1; }\n")
    assert ep.build_is_stale(str(tree)) == [os.path.join("runners", "dsl", "src", "a.rs")], \
        "edited Rust after a recorded build was NOT caught — the real failure " \
        "this check exists for has been lost"

    # A source file DELETED since the build is equally a moved source.
    (tree / "runners" / "dsl" / "src" / "a.rs").unlink()
    assert ep.build_is_stale(str(tree)) == [os.path.join("runners", "dsl", "src", "a.rs")]
    shutil.rmtree(tree)


def test_the_staleness_check_IGNORES_mtime_alone(tmp_path):
    """The exact shape of the false accusation: source NEWER by mtime, identical
    by content. A checkout is nothing but this."""
    tree = tmp_path / "t2"
    (tree / "runners" / "dsl" / "src").mkdir(parents=True)
    (tree / "runners" / "dsl" / "python" / "substrate_rs").mkdir(parents=True)
    (tree / "runners" / "dsl" / "src" / "a.rs").write_text("fn a() {}\n")
    so = tree / "runners" / "dsl" / "python" / "substrate_rs" / "_native.abi3.so"
    so.write_bytes(b"\x7fELF-not-really")
    ep.record_build(str(tree))
    os.utime(tree / "runners" / "dsl" / "src" / "a.rs", (2 ** 31, 2 ** 31))
    assert ep.build_is_stale(str(tree)) == [], \
        "a source file merely TOUCHED (content unchanged) was reported stale — " \
        "the check is reading mtime again"
