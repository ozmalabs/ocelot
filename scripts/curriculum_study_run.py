"""curriculum_study_run — WHOLE-CURRICULUM WAVE 1, PART D: THE RUN.

Drives the standing study loop (`domains.curriculum_study.study_tick`) over
a WHOLE bundled book (`data/think_python_2e/`, 21 real chapters fetched
verbatim from the free Think Python 2e HTML edition -- see
`data/think_python_2e/provenance.json`, CC BY-NC, research use) on a
full-seed, OZMA_NO_LLM=1 agent, sequentially, with flow retirement LIVE the
whole time (part A) -- so the substrate's node count stays bounded across a
book-length run instead of accumulating every chapter's reading scaffolding
forever.

A whole chapter (up to ~25K chars) as ONE StudyLesson makes a single flow's
peak node count (before it can be retired -- retirement only fires AFTER a
lesson's own extraction completes, part A) too large to process in bounded
time (measured: chapter 1 alone did not finish a full deep-read pass in
5 minutes at chapter grain). So each chapter is instead SPLIT into several
StudyLessons at PARAGRAPH boundaries (`--max-lesson-chars`, default 3000;
a ```-fenced code block is kept atomic -- never split mid-function), written
to small chunk files under `<out-dir>/chunks/`, and installed with
FRACTIONAL `order` (`chapter_order + 0.001*chunk_index`) so the whole book's
reading order is preserved across the split. Every chunk is still routed
through the UNCHANGED `code_curriculum.learn_from_lesson` path -- this is
purely a grain change, not a different reading mechanism.

Resumable: `--ckpt-path` (default `<out-dir>/checkpoint.json`) is a
`WorldAdapter.save()` blob (the SAME mechanism the daemon checkpoints with);
if it exists at start, the run RESUMES from it (the Curriculum/StudyLesson
graph state, already-taught shapes, and already-filed gaps all persist
across a resume -- `install_curriculum` is idempotent by title, so re-running
this script against an existing checkpoint never re-installs duplicate
lessons). Checkpointed after every lesson (small, cheap, and this run may be
long).

Captures, per lesson: shapes learned, gaps filed, exercises attempted/
answered, the flow's own node count before/after sweep (the flow-GC proof),
and the running total node count (the "roughly flat" trajectory). At the
end (or when interrupted / time-bounded): the ranked emitter roadmap
(part C) and the agent's own account of what it can do and what blocks it.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     python3 scripts/curriculum_study_run.py [--out-dir results/curriculum_study] \
     [--max-lessons N] [--time-budget-s N]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import curriculum_study as cs                # noqa: E402

BOOK_DIR = os.path.join(ROOT, "data", "think_python_2e")
CURRICULUM_TITLE = "Think Python 2e"


def _log(f, msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    if f is not None:
        f.write(line + "\n")
        f.flush()


def _targeted_seed_rule_refresh(adapter, seed_id: str) -> int:
    """Refresh ONLY `seeds/<seed_id>.json`'s changed executable rule bodies
    on a resumed graph (tombstone via remove_rule + reinstall from file) --
    the `jabberwock_daemon._reconcile_seed_rules` move (same
    `_canon_rule_body` comparison, same leak-free real-diff-only firing),
    scoped to ONE seed instead of sweeping every seed file. Mechanical
    host I/O; the rule BODY comes from the seed file verbatim."""
    import jabberwock_daemon as _jd
    with open(os.path.join(ROOT, "seeds", f"{seed_id}.json")) as f:
        manifest = json.load(f)
    live_by_name = {}
    for i, r in enumerate(adapter.inner.export_rules()):
        if r.get("active") and r.get("name") and r["name"] not in live_by_name:
            live_by_name[r["name"]] = (i, _jd._canon_rule_body(r))
    refresh = []
    for r in (manifest.get("rules") or []):
        if (isinstance(r, dict) and r.get("name") and r.get("match")
                and (r.get("effects") or r.get("effect"))
                and r["name"] in live_by_name):
            idx, live_body = live_by_name[r["name"]]
            seed_body = _jd._canon_rule_body(r)
            if seed_body and live_body and seed_body != live_body:
                refresh.append((idx, r))
    for idx, _r in refresh:
        adapter.inner.remove_rule(idx)
    if refresh:
        adapter.inner.load_seed_manifest(
            {"id": seed_id, "rules": [r for _i, r in refresh]}, adapter.agent)
    return len(refresh)


def _n_all(agent) -> int:
    return len(list(agent.s.nodes(None)))


def _split_text_into_chunks(text: str, max_chars: int) -> list:
    """Split `text` at paragraph (blank-line) boundaries into chunks no
    larger than `max_chars`, treating a ```-fenced code block as ONE atomic
    unit (a function is never split mid-body). Mechanical text prep, the
    same status `code_curriculum._function_sources`'s AST split has -- never
    a decision about MEANING, purely a size-bounding step so one flow's
    working-node peak stays tractable."""
    parts = re.split(r"(```.*?```)", text, flags=re.S)
    units = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            units.append(part.strip("\n"))
        else:
            for para in re.split(r"\n\s*\n", part):
                para = para.strip("\n")
                if para.strip():
                    units.append(para)
    chunks, cur, cur_len = [], [], 0
    for u in units:
        if cur and cur_len + len(u) > max_chars:
            chunks.append("\n\n".join(cur))
            cur, cur_len = [], 0
        cur.append(u)
        cur_len += len(u)
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def _load_book_lessons(out_dir: str, max_lesson_chars: int) -> list:
    with open(os.path.join(BOOK_DIR, "provenance.json")) as f:
        prov = json.load(f)
    chunk_dir = os.path.join(out_dir, "chunks")
    os.makedirs(chunk_dir, exist_ok=True)
    lessons = []
    for ch in sorted(prov["chapters"], key=lambda c: c["order"]):
        text = open(os.path.join(BOOK_DIR, ch["file"]), encoding="utf-8").read()
        chunks = _split_text_into_chunks(text, max_lesson_chars)
        for k, chunk_text in enumerate(chunks):
            fname = f"ch{ch['order']:02d}_part{k:02d}.txt"
            path = os.path.join(chunk_dir, fname)
            if not os.path.exists(path):   # idempotent across a resume
                with open(path, "w", encoding="utf-8") as f:
                    f.write(chunk_text)
            title = f"Ch{ch['order']:02d} {ch['title']} (part {k + 1}/{len(chunks)})"
            lessons.append((ch["order"] + 0.001 * k, title, path))
    lessons.sort(key=lambda t: t[0])
    return lessons


def run(out_dir: str, *, max_lessons: int | None, time_budget_s: float | None,
       ckpt_path: str | None, max_lesson_chars: int = 3000) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    ckpt_path = ckpt_path or os.path.join(out_dir, "checkpoint.json")
    log_path = os.path.join(out_dir, "run.log")
    logf = open(log_path, "a")

    started_fresh = not os.path.exists(ckpt_path)
    if started_fresh:
        _log(logf, "== BOOT (fresh, full seed set) ==")
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    else:
        _log(logf, f"== RESUME from {ckpt_path} ==")
        a = WorldAdapter.load(ckpt_path)
        # WAVE 2: a resumed CHECKPOINT carries its RULES as graph data too --
        # `seeds/curriculum_study.json`'s `study_lesson_reopen_on_growth` rule
        # was edited (now watches the READ codebook as well as the WRITE
        # one) AFTER this checkpoint was saved, so the live graph is still
        # running the STALE pre-edit rule body (the exact CLAUDE.md-
        # documented "resumed daemon runs stale rule bodies" gotcha).
        # TARGETED refresh -- only THIS seed's changed rule bodies, never a
        # sweep over every seed file (a generic sweep also INSTALLS any
        # missing foreign rules other sessions committed since the
        # checkpoint -- unknown match cost on a 400K-node graph, and none
        # of this run's business).
        n_rules_refreshed = _targeted_seed_rule_refresh(a, "curriculum_study")
        # Reconcile the read-construction codebook (installs any newly-
        # seeded ShapeSignature by name -- no codebook_epoch bump, see the
        # helper's note) and backfill the pre-WAVE-2 read_decoded_epoch
        # tracking attr: stale (-1.0) iff a construction actually landed,
        # so the NOW-CURRENT reopen rule re-arms every blocked lesson on
        # THIS run's very first tick.
        recon = cs.reconcile_code_construction_seed(a)
        epoch_recon = cs.reconcile_lesson_epoch_tracking(
            a, stale=bool(recon["installed"]))
        _log(logf, f"reconcile: rules refreshed={n_rules_refreshed} "
                  f"installed constructions={recon['installed']} "
                  f"epoch-tracking backfilled on {epoch_recon['fixed']} lesson(s) "
                  f"(value {epoch_recon['value']})")

    lessons = _load_book_lessons(out_dir, max_lesson_chars)
    _log(logf, f"book split into {len(lessons)} lessons "
              f"(max {max_lesson_chars} chars/lesson)")
    inst = cs.install_curriculum(a, CURRICULUM_TITLE, lessons, source=str(BOOK_DIR))
    _log(logf, f"curriculum install: reused={inst['reused']} "
              f"n_lessons_minted={len(inst['lessons'])}")

    trajectory = []
    n_processed = 0
    t0 = time.monotonic()
    while True:
        if max_lessons is not None and n_processed >= max_lessons:
            _log(logf, f"stopping: reached --max-lessons {max_lessons}")
            break
        if time_budget_s is not None and (time.monotonic() - t0) > time_budget_s:
            _log(logf, f"stopping: reached --time-budget-s {time_budget_s}")
            break
        before_n = _n_all(a)
        r = cs.study_tick(a)
        if r.get("picked") is None:
            _log(logf, "no lesson queued (all done/blocked-not-reopenable) -- run complete")
            break
        after_n = _n_all(a)
        swept = r.get("swept", {}).get("total_deleted", 0)
        row = {"title": r.get("title"), "status": r.get("status"),
              "shapes_learned": r.get("shapes_learned"),
              "exercises_attempted": r.get("exercises_attempted"),
              "exercises_answered": r.get("exercises_answered"),
              "flow_id": r.get("flow_id"), "swept": swept,
              "node_count_before": before_n, "node_count_after": after_n,
              "node_delta": after_n - before_n}
        trajectory.append(row)
        n_processed += 1
        _log(logf, f"lesson {n_processed:3d}  {str(r.get('title'))[:40]:40s}  "
                  f"status={r.get('status'):9s}  shapes={r.get('shapes_learned')}  "
                  f"exercises={r.get('exercises_answered')}/{r.get('exercises_attempted')}  "
                  f"swept={swept:4d}  nodes={after_n:6d} (Δ{after_n - before_n:+d})")
        a.save(ckpt_path)

    # ---- final report ----
    _log(logf, "== FINAL REPORT ==")
    lesson_rows = []
    for n in a.s.nodes("StudyLesson"):
        at = a.s.node(n)["attrs"]
        lesson_rows.append({"title": at.get("title"), "order": at.get("order"),
                            "status": at.get("status"),
                            "shapes_learned": at.get("shapes_learned"),
                            "exercises_attempted": at.get("exercises_attempted"),
                            "exercises_answered": at.get("exercises_answered")})
    lesson_rows.sort(key=lambda r: r["order"])
    n_done = sum(1 for r in lesson_rows if r["status"] == "done")
    n_blocked = sum(1 for r in lesson_rows if r["status"] == "blocked")
    n_error = sum(1 for r in lesson_rows if r["status"] == "error")
    n_queued = sum(1 for r in lesson_rows if r["status"] in ("queued", "reading"))
    _log(logf, f"lessons: {len(lesson_rows)} total, {n_done} done, {n_blocked} blocked, "
              f"{n_error} error, {n_queued} queued/in-progress")

    roadmap = cs.emitter_roadmap(a)
    with open(os.path.join(out_dir, "emitter_roadmap.json"), "w") as f:
        json.dump(roadmap, f, indent=1, default=str)
    _log(logf, f"emitter roadmap: {len(roadmap['reasons'])} distinct open reasons "
              f"(written to emitter_roadmap.json)")
    for row in roadmap["reasons"][:10]:
        _log(logf, f"  blocked={row['lessons_blocked']:2d}  count={row['count']:2d}  "
                  f"{row['reason'][:90]!r}")

    cap_note = a.converse("What can you do with code now?")
    blocks_note = a.converse("What blocks your learning?")
    _log(logf, f"self-account (capabilities): {cap_note}")
    _log(logf, f"self-account (blockers): {blocks_note}")

    report = {
        "book": CURRICULUM_TITLE, "n_lessons_total": len(lesson_rows),
        "n_done": n_done, "n_blocked": n_blocked, "n_queued": n_queued,
        "n_processed_this_run": n_processed,
        "lessons": lesson_rows, "trajectory": trajectory,
        "emitter_roadmap": roadmap,
        "self_account": {"capabilities": cap_note, "blockers": blocks_note},
        "final_node_count": _n_all(a),
        "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(os.path.join(out_dir, "curriculum_study_report.json"), "w") as f:
        json.dump(report, f, indent=1, default=str)
    a.save(ckpt_path)
    _log(logf, f"report written: {os.path.join(out_dir, 'curriculum_study_report.json')}")
    logf.close()
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "results", "curriculum_study"))
    ap.add_argument("--ckpt-path", default=None)
    ap.add_argument("--max-lessons", type=int, default=None)
    ap.add_argument("--time-budget-s", type=float, default=None)
    ap.add_argument("--max-lesson-chars", type=int, default=3000)
    args = ap.parse_args()
    run(args.out_dir, max_lessons=args.max_lessons, time_budget_s=args.time_budget_s,
       ckpt_path=args.ckpt_path, max_lesson_chars=args.max_lesson_chars)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
