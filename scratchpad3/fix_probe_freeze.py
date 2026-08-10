p = "domains/dorsal_world.py"
src = open(p).read()

old_freeze = '''    eta0 = float(s.node(dp)["attrs"]["oja_eta"])
    prop0 = float(s.node(wp)["attrs"]["propagate"])
    s.set_attr(dp, "oja_eta", 0.0)
    s.set_attr(wp, "propagate", 0.0)'''
new_freeze = '''    eta0 = float(s.node(dp)["attrs"]["oja_eta"])
    bi0 = float(s.node(dp)["attrs"].get("bi_eta", 0.0))
    prop0 = float(s.node(wp)["attrs"]["propagate"])
    s.set_attr(dp, "oja_eta", 0.0)
    s.set_attr(dp, "bi_eta", 0.0)
    s.set_attr(wp, "propagate", 0.0)'''
assert old_freeze in src
src = src.replace(old_freeze, new_freeze)

old_restore = '''        s.set_attr(dp, "oja_eta", eta0)
        s.set_attr(wp, "propagate", prop0)'''
new_restore = '''        s.set_attr(dp, "oja_eta", eta0)
        s.set_attr(dp, "bi_eta", bi0)
        s.set_attr(wp, "propagate", prop0)'''
assert old_restore in src
src = src.replace(old_restore, new_restore)

old_doc = '''    NO LEARNING HAPPENS DURING A PROBE. `oja_eta` is set to 0 for the duration
    (Oja's update degenerates to w <- w*1 + 0 = w, exactly the identity) and
    `propagate` to 0 so no wave contaminates the response. Both are restored
    afterwards. Configuration writes, not decisions.
    """'''
new_doc = '''    NO LEARNING HAPPENS DURING A PROBE. `oja_eta` AND `bi_eta` are BOTH set to 0
    for the duration (dv_oja_learn's update is a SUM of an Oja part scaled by
    oja_eta and a rung-3B bistable part scaled by bi_eta; zeroing both degenerates
    the whole rule to w <- w*1 + 0 + 0 = w, exactly the identity) and `propagate`
    to 0 so no wave contaminates the response. All three are restored afterwards.
    Configuration writes, not decisions.

    ZEROING bi_eta TOO IS A MEASURED INSTRUMENT FIX, found by the rung-3B positive
    control BEFORE any arm was run. The freeze originally zeroed only `oja_eta`, on
    the reasoning that Oja then degenerates to the identity. That reasoning was
    correct for rung 3 and FALSE the moment the bistable term was added: the term
    is scaled by `bi_eta`, NOT by `oja_eta`, so the probe went on training the unit
    ON THE PROBE STIMULUS -- the measure was manufacturing the thing it measured.

    It shows up in the one place it cannot hide: the positive control's step-0
    column is taken BEFORE ANY TRAINING STEP and must therefore equal the 0.111
    floor in every row. It did not. It rose monotonically with bi_eta -- 0.112,
    0.118, 0.136, and 0.339 at bi_eta=1e-1, a 3x floor jump produced entirely by
    measuring. Every armed number in that table was training on the test set, and
    the apparent bi_eta=1e-1 "win" was almost all of it.

    The gate that should have caught this (test_the_probe_does_not_let_the_agent_learn)
    PASSED throughout, because it booted with bistable=0: it checked the freeze's
    CONSTANTS while being blind to the AXIS they parameterise, which is exactly the
    defect PROTOCOL section 1 names ("a gate that checks a rule's CONSTANTS but not
    the AXIS they parameterise is not a gate"). It is now run with the term ARMED,
    which is the only version of it that could have failed.
    """'''
assert old_doc in src
src = src.replace(old_doc, new_doc)
open(p, "w").write(src)
print("patched probe_dsi freeze")
