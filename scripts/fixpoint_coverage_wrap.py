"""Run a measuring script IN-PROCESS and dump the engine's trigger counters.

The counters are process-global atomics in the REVERTED engine, so they must be
read inside the same process that ran the workload. `atexit` fires on a normal
return AND on `SystemExit`, so a script that calls `sys.exit(2)` still reports
its exposure -- the predecessor lost `codebook_axis_measure`'s count exactly
there.

The read goes through `fixpoint_trigger_counts()`, which loads two atomics and
does NOT boot a `Substrate`: the instrument cannot contribute to its own reading.
"""
import atexit
import json
import runpy
import sys

target, ctrfile = sys.argv[1], sys.argv[2]
_state = {"dumped": False}


def _dump():
    if _state["dumped"]:
        return
    _state["dumped"] = True
    try:
        import substrate_rs._native as nat
        h, c = nat.fixpoint_trigger_counts()
    except Exception as e:                                # FIX engine: absent
        h, c, = None, None
        err = repr(e)
    else:
        err = None
    with open(ctrfile, "w") as f:
        json.dump({"harmful_skips": h, "run_rules_calls": c, "err": err}, f)


atexit.register(_dump)
sys.argv = [target] + sys.argv[3:]
runpy.run_path(target, run_name="__main__")
