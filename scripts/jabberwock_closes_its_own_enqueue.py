"""THE HEADLINE: the last hand-holding is GONE — the concern->target ENQUEUE is
now a GRAPH RULE, so the agent's OWN gap detection drives read -> ground ->
synthesise -> validate -> adopt with NO human in the enqueue. donkey=0 /
OZMA_NO_LLM=1: no model anywhere.

Before: a human called cortex.enqueue_read_method(name, method) to turn a held
SelfConcern into a ReplacementTarget the loop picks up.
Now: seeds/concern_to_target_bridge.json's `bridge_concern_to_target` rule DECIDES
that — from a SelfConcern{kind:'capability'} carrying a method_text, it MINTS the
ReplacementTarget and wires it into the code-authoring root, in the agent's own
run_rules fixpoint. The human never touches the enqueue.

This driver proves:

  A. THE FILLS (the agent authors NEW effect kinds by reading):
     · add_node with attr-propagation (Batch -> Record) — a NEW effect the reader
       parses, the synthesiser builds, validate-by-running checks, the loop adopts.
     · Mean aggregate (gauge average) — COMPOSED as Sum/Count via Div (no new Rust).
     These are the recursion CAPABILITY: the agent can now read-and-adopt the very
     add_node-with-attr-propagation shape a self-authored bridge is made of.

  B. THE CLOSED ENQUEUE (the full loop, no human enqueue):
     agent holds SelfConcern{capability, method} -> [bridge rule] mints target ->
     [loop] reads -> grounds -> synthesises -> validates -> adopts -> capability RUNS.
     Each stage prints WHO did it.

  C. THE HONEST NEGATIVES:
     · a capability concern with NO method -> the bridge does NOT fire (no target).
     · a concern with an UNBINDABLE method -> bridge fires -> draft WALL -> validate
       rejects -> NOT adopted.

Run:
  export TMPDIR=... PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
  python3 scripts/jabberwock_closes_its_own_enqueue.py
"""
import json
import os
import tempfile

os.environ.setdefault("OZMA_NO_LLM", "1")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.code_writing_cortex import CodeWritingCortex


def hr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


def who(stage, actor, detail=""):
    print("  [%-11s] %-32s %s" % (stage, actor, detail))


# --------------------------------------------------------------------------- #
#  file a SelfConcern the agent HOLDS — the SAME node shape gap_awareness /
#  conversation_self_concern mint (status/source/kind/content), plus the method
#  it carries. The DETECTION is the agent's gap_awareness machinery; the METHOD
#  it carries is the method-sourcing boundary (taught / carried — donkey=0 offline
#  can't fetch it). op_name names the capability the loop will author.
# --------------------------------------------------------------------------- #
def file_capability_concern(a, *, op_name, method_text):
    sc = a.s.add_node("SelfConcern", {
        "status": "noted", "source": "implicit", "kind": "capability",
        "content": op_name, "op_name": op_name, "method_text": method_text})
    a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
    return sc


def _target_for(a, op_name):
    for rt in a.s.nodes("ReplacementTarget"):
        if a.s.node(rt)["attrs"].get("op_name") == op_name:
            return rt
    return None


def _attach_method(a, sc, *, op_name, method_text):
    """Attach a TAUGHT method to a held SelfConcern (op_name + method_text). This
    is the METHOD-SOURCING boundary made explicit: donkey=0 offline can't fetch a
    method, so it is taught/carried. Mechanical host I/O (set_attr), no decision."""
    a.s.set_attr(sc, "op_name", op_name)
    a.s.set_attr(sc, "method_text", method_text)


def drive_closed_loop(a, cortex, *, title, op_name, method_text,
                      build_world, prove_absent, prove_present,
                      detect_via_converse=None):
    hr(title)
    print("METHOD THE AGENT HOLDS (carried on the concern):\n  " + method_text)
    world = build_world(a)

    absent = prove_absent(a, world)
    who("GAP", "the world (agent's own graph)",
        "capability ABSENT before: %s" % absent)

    # -- 1. the agent DETECTS + HOLDS the gap as a SelfConcern ------------------
    if detect_via_converse:
        before = set(a.s.nodes("SelfConcern"))
        reply = a.converse(detect_via_converse)
        sc = next((n for n in a.s.nodes("SelfConcern") if n not in before), None)
        who("DETECT", "gap_awareness RULE fired (real)",
            "converse(%r) -> SelfConcern #%s kind=%r; reply=%r"
            % (detect_via_converse, sc, a.s.node(sc)["attrs"].get("kind"), reply))
        _attach_method(a, sc, op_name=op_name, method_text=method_text)
        who("METHOD", "taught + attached (the ceiling)",
            "op_name=%r + method_text attached to the held gap" % op_name)
    else:
        sc = file_capability_concern(a, op_name=op_name, method_text=method_text)
        who("DETECT", "agent holds it (gap_awareness shape)",
            "#%s SelfConcern content=%r carries a method" % (sc, op_name))

    # -- 2. THE CLOSED ENQUEUE: the bridge RULE mints the target (no human) ------
    before = _target_for(a, op_name)
    a.inner.run_rules(10000)
    tgt = _target_for(a, op_name)
    who("ENQUEUE", "bridge_concern_to_target (RULE)",
        "minted ReplacementTarget #%s + wired current_target — NO human enqueue"
        % tgt if (tgt and before is None) else "NO target (bridge declined)")
    assert tgt is not None, "bridge failed to mint a target"
    assert cortex.current_target() == tgt, "target not wired into the cortex root"

    # -- 3. the agent's OWN autonomous loop: read+ground+synth -> validate -> adopt
    audit = []
    for _ in range(8):
        fired = cortex.tick()
        audit += fired
        if not fired:
            break
    who("LOOP", "cortex reflexes (existing loop)", " -> ".join(audit))

    draft_nid = None
    for d in a.s.nodes("CodeDraft"):
        da = a.s.node(d)["attrs"]
        if da.get("kind") == "read_method_rule" and da.get("method_name") == op_name:
            draft_nid = d
    if draft_nid is not None:
        da = a.s.node(draft_nid)["attrs"]
        who("READ+GRND+SYNTH", "agent faculties", "draft #%s" % draft_nid)
        for r in json.loads(da.get("rule_json") or "[]"):
            print("    SYNTHESISED RULE:", json.dumps(r))
        print("    HOW:", da.get("how"))
        for vn in a.s.neighbours(draft_nid, "validated_by"):
            va = a.s.node(vn)["attrs"]
            who("VALIDATE", "validate_by_running (ran it)",
                "tests_pass=%s :: %s" % (va.get("tests_pass"), va.get("notes")))
        for it in a.s.neighbours(draft_nid, "installed_as"):
            who("ADOPT", "cw_install_if_better reflex",
                "installed live + persisted -> %s"
                % a.s.node(it)["attrs"].get("seed_path"))

    present = prove_present(a, world)
    who("CLOSED", "the adopted rule (runs in Rust)",
        "capability PRESENT after adoption: %s" % present)
    ok = (not absent) and present
    print("  RESULT:", "GAP CLOSED — NO HUMAN IN THE ENQUEUE" if ok else "*** FAILED ***")
    assert ok, "%s: loop did not close the gap" % op_name


# --------------------------------------------------------------------------- #
#  GAP worlds (distinctive `kind`s so role resolution grounds to THESE nodes).
# --------------------------------------------------------------------------- #
def build_task_world(a):
    s, inner = a.s, a.inner
    owner = s.add_node("Person", {"kind": "owner", "name": "alice"})
    task = s.add_node("Task", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "owned_by", owner)
    return {"task": task, "owner": owner}


def task_absent(a, w):
    a.s.set_attr(w["task"], "done", 1.0)
    a.inner.run_rules(10000)
    return w["owner"] in a.inner.neighbours(w["task"], "completed")


def task_present(a, w):
    a.inner.run_rules(10000)
    return w["owner"] in a.inner.neighbours(w["task"], "completed")


def build_gauge_world(a):
    s, inner = a.s, a.inner
    gauge = s.add_node("Gauge", {"kind": "gauge", "avg": -1.0})
    feed = s.add_node("Feed", {"kind": "feed"})
    inner.add_edge_unchecked(gauge, "depends_on", feed)
    for x in (2.0, 4.0, 6.0):                       # mean = 4
        inner.add_edge_unchecked(feed, "has_sample", s.add_node("Sample", {"value": x}))
    return {"gauge": gauge, "expect": 4.0}


def gauge_absent(a, w):
    a.inner.run_rules(10000)
    return a.s.node(w["gauge"])["attrs"]["avg"] == w["expect"]


def gauge_present(a, w):
    a.inner.run_rules(10000)
    return a.s.node(w["gauge"])["attrs"]["avg"] == w["expect"]


def build_batch_world(a):
    s, inner = a.s, a.inner
    line = s.add_node("Line", {"kind": "line"})
    batch = s.add_node("Batch", {"kind": "batch", "ready": 0.0, "weight": 5.0})
    inner.add_edge_unchecked(line, "has_batch", batch)
    return {"line": line, "batch": batch}


def batch_absent(a, w):
    a.s.set_attr(w["batch"], "ready", 1.0)
    a.inner.run_rules(10000)
    return len(a.s.nodes("Record")) > 0


def batch_present(a, w):
    a.inner.run_rules(10000)
    recs = a.s.nodes("Record")
    if not recs:
        return False
    # the minted Record carries the batch's data (attr-propagation)
    ra = a.s.node(recs[0])["attrs"]
    return ra.get("weight") == 5.0


# --------------------------------------------------------------------------- #
def main():
    print("donkey=0 / OZMA_NO_LLM =", os.environ.get("OZMA_NO_LLM"))
    seeds_dir = tempfile.mkdtemp(prefix="enqueue_close_seeds_")
    os.environ["OZMA_READ_METHOD_SEEDS_DIR"] = seeds_dir

    a = WorldAdapter(seeds=())
    load_all_seeds(a)                                     # loads the bridge seed
    cortex = CodeWritingCortex(a.s, agent=a).install()
    # confirm the enqueue bridge is RESIDENT (a boot-loaded rule, not glue).
    ex = a.inner.export_rules()
    names = [r.get("name") for r in (ex if isinstance(ex, list) else json.loads(ex))]
    hr("THE BRIDGE IS CORTEX-SCOPED — installed with the code-authoring cortex")
    who("SEED", "seeds/code_authoring/... (non-resident)",
        "bridge_concern_to_target installed by CodeWritingCortex.install(): %s"
        % ("bridge_concern_to_target" in names))
    assert "bridge_concern_to_target" in names

    # B + A: the full closed loop over three effect kinds, incl. the two FILLS.
    drive_closed_loop(
        a, cortex,
        title="LOOP 1 — add_edge (task completion), enqueue CLOSED by the bridge",
        op_name="task_completion",
        method_text=("When a task is marked done, add a completed edge from the "
                     "task to its owner."),
        build_world=build_task_world, prove_absent=task_absent,
        prove_present=task_present,
        detect_via_converse="You cannot complete tasks.")

    drive_closed_loop(
        a, cortex,
        title="LOOP 2 — FILL: Mean aggregate (gauge average), enqueue CLOSED",
        op_name="gauge_average",
        method_text=("A gauge holds the average of its feed's samples. "
                     "A gauge depends on its feed. When the feed changes, the "
                     "gauge becomes stale. Recompute a stale gauge from its feed."),
        build_world=build_gauge_world, prove_absent=gauge_absent,
        prove_present=gauge_present)

    drive_closed_loop(
        a, cortex,
        title="LOOP 3 — FILL: add_node + attr-propagation (batch->record), CLOSED",
        op_name="batch_record",
        method_text=("When a batch is marked ready, create a record from the batch."),
        build_world=build_batch_world, prove_absent=batch_absent,
        prove_present=batch_present)

    # C1 — a capability concern with NO method -> the bridge REFUSES to enqueue.
    hr("NEGATIVE 1 — a capability concern with NO method: bridge does NOT enqueue")
    before = {n for n in a.s.nodes("ReplacementTarget")}
    sc = a.s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                      "kind": "capability", "content": "no_method_here",
                                      "op_name": "no_method_here"})
    a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
    a.inner.run_rules(10000)
    new_t = [n for n in a.s.nodes("ReplacementTarget") if n not in before]
    who("ENQUEUE", "bridge_concern_to_target (RULE)",
        "target minted? %s (method_text absent -> guard blocks)" % bool(new_t))
    assert not new_t, "bridge minted a target for a method-less concern"
    print("  RESULT: no method -> no enqueue (correct).")

    # C2 — an UNBINDABLE method -> bridge enqueues, but the loop refuses to adopt.
    hr("NEGATIVE 2 — an UNBINDABLE method: bridge enqueues, loop REFUSES to adopt")
    method = ("When a widget is marked ready, add a shipped edge from the widget "
              "to its vendor.")
    print("  (no widget/vendor in the world -> binding cannot ground)")
    inst_before = {n for n in a.s.nodes("CodeInstallation")}
    file_capability_concern(a, op_name="widget_shipping", method_text=method)
    a.inner.run_rules(10000)
    tgt = _target_for(a, "widget_shipping")
    who("ENQUEUE", "bridge_concern_to_target (RULE)",
        "target minted #%s (concern carries a method)" % tgt)
    assert tgt is not None
    for _ in range(8):
        if not cortex.tick():
            break
    walled = [a.s.node(d)["attrs"].get("wall") for d in a.s.nodes("CodeDraft")
              if a.s.node(d)["attrs"].get("wall")]
    who("DRAFT", "agent synthesis", "WALL: %s" % (walled[-1] if walled else None))
    new_inst = [n for n in a.s.nodes("CodeInstallation") if n not in inst_before]
    who("GATE", "validate + reflex", "adopted? %s" % bool(new_inst))
    assert not new_inst, "an unvalidated read was adopted"
    print("  RESULT: unbindable -> enqueued but NOT adopted (correct).")

    hr("DONE — the concern->target ENQUEUE is CLOSED (a graph rule), donkey=0")
    installs = [a.s.node(n)["attrs"] for n in a.s.nodes("CodeInstallation")
                if a.s.node(n)["attrs"].get("kind") == "read_method_rule"]
    for it in installs:
        print("  adopted:", it.get("op_name"), "->", it.get("rule_name"))
    assert len(installs) == 3, "expected three adopted read-method rules"
    print("\n  WHO closed the enqueue: the SEEDED bridge rule "
          "(bridge_concern_to_target).")
    print("  WHO detected the gap: gap_awareness RULE (LOOP 1 fired it for real via "
          "converse); loops 2-3 hold the same-shape concern directly.")
    print("  WHO read/ground/synth/validate/adopt: the agent's faculties + reflexes.")
    print("  METHOD-SOURCING (the ceiling): carried on the concern (taught) — "
          "donkey=0 offline cannot fetch it.")


if __name__ == "__main__":
    main()
