"""THE HEADLINE: the jabberwock closes a capability GAP ITSELF by READING a
method — read → ground → synthesise → SELF-VALIDATE (by running) → ADOPT — all
through its OWN autonomous self-authoring loop (code_writing_cortex). donkey=0 /
OZMA_NO_LLM=1: no model anywhere.

The read→implement path is plugged into `code_authoring` as a NEW teacher-free
DRAFT SOURCE (domains/read_method_draft.py), so the cortex's existing
identify → draft → validate → install reflexes drive the whole loop. The agent:

  1. HOLDS a gap (a capability/rule it lacks) — filed as a SelfConcern.
  2. READS a method describing the fix (procedural_reader — agent faculty).
  3. GROUNDS the binding against its OWN domain graph (binding_resolver — agent
     faculty; NOTHING hand-supplied).
  4. SYNTHESISES the rule (method_synthesis — agent faculty).
  5. SELF-VALIDATES by RUNNING the rule on a minimal instance built from the
     read model and checking the described effect (validate_by_running).
  6. ADOPTS (cortex reflex decides on the validation) — installs live + persists
     as seed `rules` data.
  7. The new capability RUNS on the real world; and SURVIVES a fresh boot.

Run:
  export TMPDIR=/home/matt/.claude/jobs/dec46f73/tmp \
         PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
  python3 scripts/jabberwock_reads_to_close_its_own_gap.py
"""
import json
import os
import tempfile

os.environ.setdefault("OZMA_NO_LLM", "1")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.code_writing_cortex import CodeWritingCortex


def hr(t):
    print("\n" + "=" * 76)
    print(t)
    print("=" * 76)


def who(stage, actor, detail=""):
    print("  [%-9s] %-34s %s" % (stage, actor, detail))


def show_draft(s, draft_nid):
    a = s.node(draft_nid)["attrs"]
    if a.get("wall"):
        print("    DRAFT WALL:", a["wall"]); return
    rules = json.loads(a.get("rule_json") or "[]")
    for r in rules:
        print("    SYNTHESISED RULE:", json.dumps(r))
    print("    HOW (the agent's own account):", a.get("how"))


# --------------------------------------------------------------------------- #
def _file_self_concern(s, content, kind="capability"):
    """Mint a SelfConcern the agent HOLDS — the same node shape gap_awareness /
    conversation_self_concern mint. (Mechanical mint; the concern→enqueue bridge
    below is the honest glue boundary.)"""
    return s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                      "kind": kind, "content": content})


def drive_gap(a, cortex, *, title, name, method_text, build_world, prove_absent,
              prove_present):
    hr(title)
    print("METHOD THE AGENT WILL READ:\n  " + method_text)

    # -- the domain world the agent already inhabits (its situation) ---------
    world = build_world(a)

    # -- 1. the GAP: prove the capability is ABSENT --------------------------
    absent = prove_absent(a, world)
    who("GAP", "the world (agent's own graph)",
        "capability ABSENT before reading: %s" % absent)
    concern = _file_self_concern(a.s, name)
    who("GAP", "agent holds it (SelfConcern)",
        "#%s status=noted content=%r" % (concern, name))

    # -- 2. hand the agent the gap+method; its loop does the rest ------------
    #    binding=None => the agent GROUNDS the binding itself (nothing supplied).
    tgt = cortex.enqueue_read_method(name, method_text, binding=None)
    who("ENQUEUE", "glue (concern -> target)",
        "ReplacementTarget #%s carries the method text; binding UNSUPPLIED" % tgt)

    # -- 3. drive the AGENT'S OWN autonomous loop ---------------------------
    audit = []
    for _ in range(8):
        fired = cortex.tick()
        audit += fired
        if not fired:
            break
    who("LOOP", "cortex reflexes (existing machinery)", " -> ".join(audit))

    # inspect what the loop produced
    draft_nid = None
    for d in a.s.nodes("CodeDraft"):
        da = a.s.node(d)["attrs"]
        if da.get("kind") == "read_method_rule" and da.get("method_name") == name:
            draft_nid = d
    if draft_nid is not None:
        who("READ+GRND+SYNTH", "agent faculties",
            "draft #%s (read_method_draft.draft_from_reading)" % draft_nid)
        show_draft(a.s, draft_nid)
        val = None
        for vn in a.s.neighbours(draft_nid, "validated_by"):
            val = a.s.node(vn)["attrs"]
        if val is not None:
            who("VALIDATE", "validate_by_running (ran the rule)",
                "tests_pass=%s :: %s" %
                (val.get("tests_pass"), val.get("notes")))
        inst = None
        for it in a.s.neighbours(draft_nid, "installed_as"):
            inst = a.s.node(it)["attrs"]
        if inst is not None:
            who("ADOPT", "reflex cw_install_if_better decided",
                "installed live + persisted -> %s" % inst.get("seed_path"))

    # -- 4. the capability now RUNS on the real world -----------------------
    present = prove_present(a, world)
    who("CLOSED", "the adopted rule (runs in Rust)",
        "capability PRESENT after adoption: %s" % present)
    ok = (not absent) and present
    print("  RESULT:", "GAP CLOSED BY THE AGENT ITSELF" if ok else "*** FAILED ***")
    assert ok, "%s: gap not closed" % name
    return draft_nid


# --------------------------------------------------------------------------- #
#  GAP 1 — task completion (an add_edge rule the agent lacks)
# --------------------------------------------------------------------------- #
def build_task_world(a):
    s, inner = a.s, a.inner
    # `kind` names each node so the agent's binding resolver grounds the read
    # role nouns ("task"/"owner") to THESE nodes (kind is matched before a stray
    # seed Concept that merely shares the name).
    owner = s.add_node("Person", {"kind": "owner", "name": "alice"})
    task = s.add_node("Task", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "owned_by", owner)
    return {"task": task, "owner": owner}


def task_absent(a, w):
    s, inner = a.s, a.inner
    s.set_attr(w["task"], "done", 1.0)          # the trigger is already true
    inner.run_rules(10000)
    return w["owner"] in inner.neighbours(w["task"], "completed")


def task_present(a, w):
    a.inner.run_rules(10000)                     # same world, new capability
    return w["owner"] in a.inner.neighbours(w["task"], "completed")


# --------------------------------------------------------------------------- #
#  GAP 2 — materialized-view maintenance (a recompute rule the agent lacks)
# --------------------------------------------------------------------------- #
def build_view_world(a):
    s, inner = a.s, a.inner
    src = s.add_node("Source", {"kind": "source"})
    view = s.add_node("View", {"kind": "view", "val": -1.0})
    inner.add_edge_unchecked(view, "depends_on", src)
    for wtok in ("alpha", "beta", "gamma", "delta"):
        inner.add_edge_unchecked(src, "has_mention", s.add_node("Mention", {"text": wtok}))
    return {"view": view, "src": src, "expect": 4}


def view_absent(a, w):
    a.inner.run_rules(10000)
    return a.s.node(w["view"])["attrs"]["val"] == w["expect"]


def view_present(a, w):
    a.inner.run_rules(10000)
    return a.s.node(w["view"])["attrs"]["val"] == w["expect"]


# --------------------------------------------------------------------------- #
#  GAP 3 — richer aggregate: SUM (the op is read from the method, not Count)
# --------------------------------------------------------------------------- #
def build_ledger_world(a):
    s, inner = a.s, a.inner
    feed = s.add_node("Feed", {"kind": "feed"})
    ledger = s.add_node("Ledger", {"kind": "ledger", "total": -1.0})
    inner.add_edge_unchecked(ledger, "depends_on", feed)
    for x in (2.0, 5.0, 3.0):                 # sum = 10
        inner.add_edge_unchecked(feed, "has_reading", s.add_node("Reading", {"value": x}))
    return {"ledger": ledger, "feed": feed, "expect": 10.0}


def ledger_absent(a, w):
    a.inner.run_rules(10000)
    return a.s.node(w["ledger"])["attrs"]["total"] == w["expect"]


def ledger_present(a, w):
    a.inner.run_rules(10000)
    return a.s.node(w["ledger"])["attrs"]["total"] == w["expect"]


# --------------------------------------------------------------------------- #
def persistence_proof(seeds_dir, category="read_method_rules"):
    hr("PERSISTENCE — the adopted rule survives a FRESH BOOT (durable seed)")
    path = os.path.join(seeds_dir, category + ".json")
    if not os.path.exists(path):
        print("  (no persisted seed written)"); return
    manifest = json.load(open(path))
    names = [r.get("name") for r in manifest.get("rules", [])]
    print("  persisted seed %s carries rules: %s" % (path, names))

    b = WorldAdapter(seeds=())
    load_all_seeds(b)
    b.inner.load_seed_manifest(manifest, b.agent)     # re-install the adopted rules
    s, inner = b.s, b.inner
    # rebuild the task world on the fresh agent
    owner = s.add_node("Person", {"name": "bob"})
    task = s.add_node("Task", {"done": 1.0})
    inner.add_edge_unchecked(task, "owned_by", owner)
    inner.run_rules(10000)
    got = owner in inner.neighbours(task, "completed")
    print("  fresh boot + re-loaded seed: task.done=1 -> completed edge? %s" % got)
    assert got, "adopted rule did not survive a fresh boot"
    print("  RESULT: the read-and-adopted capability is DURABLE.")


# --------------------------------------------------------------------------- #
def main():
    print("donkey=0 / OZMA_NO_LLM =", os.environ.get("OZMA_NO_LLM"))
    seeds_dir = tempfile.mkdtemp(prefix="read_method_seeds_")
    os.environ["OZMA_READ_METHOD_SEEDS_DIR"] = seeds_dir

    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cortex = CodeWritingCortex(a.s, agent=a).install()
    print("cortex installed; reflexes:", len(cortex._reflexes))

    drive_gap(
        a, cortex,
        title="GAP 1 — TASK COMPLETION (the agent reads an add_edge method it lacks)",
        name="task_completion",
        method_text=("When a task is marked done, add a completed edge from the "
                     "task to its owner."),
        build_world=build_task_world,
        prove_absent=task_absent, prove_present=task_present)

    drive_gap(
        a, cortex,
        title="GAP 2 — MATERIALIZED VIEW (the agent reads a recompute method it lacks)",
        name="view_maintenance",
        method_text=("A view holds the count of its source's mentions. "
                     "A view depends on its source. "
                     "When the source changes, the view becomes stale. "
                     "Recompute a stale view from its source."),
        build_world=build_view_world,
        prove_absent=view_absent, prove_present=view_present)

    drive_gap(
        a, cortex,
        title="GAP 3 — RICHER AGGREGATE: the method says SUM, not count (read-driven Term)",
        name="ledger_maintenance",
        method_text=("A ledger holds the sum of its feed's readings. "
                     "A ledger depends on its feed. "
                     "When the feed changes, the ledger becomes stale. "
                     "Recompute a stale ledger from its feed."),
        build_world=build_ledger_world,
        prove_absent=ledger_absent, prove_present=ledger_present)

    # ---- the GATE: an unbindable read must NOT be adopted -----------------
    hr("GATE — the loop REFUSES to adopt a read it cannot validate")
    name = "widget_shipping"
    method = ("When a widget is marked ready, add a shipped edge from the "
              "widget to its vendor.")
    print("READS (no widget/vendor in its world -> binding cannot ground):\n  " + method)
    before = {n for n in a.s.nodes("CodeInstallation")}
    cortex.enqueue_read_method(name, method, binding=None)
    for _ in range(8):
        if not cortex.tick():
            break
    draft_nid = None
    for d in a.s.nodes("CodeDraft"):
        da = a.s.node(d)["attrs"]
        if da.get("kind") == "read_method_rule" and da.get("wall") \
                and name.split("_")[0] in (da.get("source") or ""):
            draft_nid = d
    walled = [a.s.node(d)["attrs"].get("wall") for d in a.s.nodes("CodeDraft")
              if a.s.node(d)["attrs"].get("wall")]
    who("DRAFT", "agent faculties (synthesis)",
        "WALL raised (unbindable): %s" % (walled[-1] if walled else None))
    new_inst = [n for n in a.s.nodes("CodeInstallation") if n not in before]
    who("GATE", "validate_by_running + reflex",
        "adopted? %s  (NO CodeInstallation minted -> rule NOT adopted)"
        % bool(new_inst))
    assert not new_inst, "GATE FAILED: an unvalidated read was adopted"
    print("  RESULT: unvalidated read correctly REFUSED (no adoption).")

    hr("GENERALITY — two different read methods -> two different adopted rules, "
       "one loop")
    installs = [a.s.node(n)["attrs"] for n in a.s.nodes("CodeInstallation")
                if a.s.node(n)["attrs"].get("kind") == "read_method_rule"]
    for it in installs:
        print("  adopted:", it.get("op_name"), "->", it.get("rule_name"))
    assert len(installs) == 3, "expected three adopted read-method rules"

    persistence_proof(seeds_dir)

    hr("DONE — the jabberwock closed its own gaps by reading, donkey=0")
    print("  Every DECISION (read parse, binding, rule shape, effect match, "
          "adopt) was the agent's faculty/reflex; the glue only routed data.")


if __name__ == "__main__":
    main()
