"""BigvilleDecisionWorld -- bigville DECISION CORE (block 279000): CONDUCT AS
ONE COLLAPSE (model-free / model-based RL, one principle, two faces).

The conduct decision is the substrate's ONE collapse operation applied to
conduct -- the same collapse the eye/perception and the sd loop already run.
The "four parts" are the FACES of one collapse, and RESIDUAL is the depth-driver:

  * ORDER-0 (the SHALLOW collapse / connectionist-descent face) = a genuinely
    COMPILED/CACHED net: the native `NetForward` Term over a `NetworkAssemblage`
    settles the held conduct state in ONE fast pass, over an availability-filtered
    consideration set (pruning lives here -- correction #3). NOT "a few live
    iterations of the symbolic decode" -- a compiled net lookup.
  * The RESIDUAL *is* the arbiter (correction #1). surprise = |cached value -
    grounded model value|. A collapse whose residual exceeds `settle_tol` has NOT
    settled, so it CONTINUES to higher order. No bolted-on "should I escalate?"
    rule; no depletion term; the scalar residual is logged, not a bit.
  * ORDER-N (the DEEPER collapse / symbolic-rewrite face) = a model-based Argmax
    that runs ONLY because the shallow pass left residual. It carries
    `rationalise_gain` so deliberation can RATIONALISE the impulse, not only
    override it (motivated reasoning rides UP -- correction #2).
  * INTERNALIZATION (the collapse settling BACK into the held state) =
    `net_collapse` writing the settled order-N result into the order-0 net (the
    SAME collapse at a slower timescale = Mattar & Daw MB->MF replay), so the
    shallow pass settles it directly next time -- the automation curve.

"yes... wait... no!" is ONE collapse trace: fast settle (yes) -> residual (wait,
not settled) -> deeper settle (no). Violence sits on BOTH faces.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md): this is a
WORLD ADAPTER. It holds NO agent decision. It does exactly mechanical I/O:
  * mint the order-0 net (a NetworkAssemblage + AssemblageStep + WeightTensors,
    wrapped in a ReflexNet so net_collapse can train it) -- an identity readout
    whose cached values ARE the situation's fast impulse appeal;
  * mint the conduct held-state (ConductState) with the situation's impulse-appeal
    feature vector (`input_vec`) and the WORLD's consequence model as the
    model-value target (`target_vec`) -- both are world config, exactly as
    af_choose_action's base_value / grief_affinity are Action config;
  * mint the conduct options (DecAction) with their appeal / plan_value / flags;
  * arm the collapse, run the Rust run_rules() fixpoint (the WHOLE collapse -- fast
    settle, residual, deepen, settle-back -- is ONE run_rules pass), and read back.
EVERY decision -- the fast pick, whether the collapse has settled (residual vs
tol), the deeper pick, whether to settle back -- is a seed RULE
(seeds/bigville_decision_core.json). It invokes no Python rule engine and holds no
if/else over an agent's graph valuation; conditionals here are over WORLD/config
state only. ZERO new Rust (composes NetForward + net_collapse + Argmax/IndexAt/
IfThenElse, all pre-existing).
"""
from __future__ import annotations
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.photon_eye import GraphEye              # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402

# ---- Tunable knobs (declared config -- the DIRECTION is the science, the
# MAGNITUDE is soft; every one is a graph attr the rules read). ----
KNOBS = dict(
    consideration_threshold=0.05,  # availability filter: appeal below this is pruned (never scored)
    settle_tol=0.15,               # collapse convergence tolerance (the depth/precision knob)
    deepen_enabled=1.0,            # FALSIFIER: 0 -> collapse capped at the shallow pass (pure order-0)
    rationalise_gain=0.0,          # correction #2: >0 -> order-N can rationalise the impulse (bias rides up)
    replay_gain=1.0,               # FALSIFIER: 0 -> the collapse never settles back (flat automation curve)
    replay_eta=0.35,               # the settle-back (net_collapse) learning rate
)


class BigvilleDecisionWorld:
    """A conduct decision as ONE collapse: an order-0 net + residual-driven depth
    + settle-back, in ONE substrate, ONE run_rules() per decision."""

    def __init__(self, actions, **knob):
        """`actions` = list of (name, impulse_appeal, plan_value, is_transgressive).

        impulse_appeal is the situation's FAST pull (the order-0 net's initial
        cached value -- an identity readout passes it through); plan_value is the
        WORLD's model value (the grounded consequence the deep collapse scores by
        and the target the settle-back trains toward). Both are world config."""
        self.actions = list(actions)
        self.knobs = dict(KNOBS)
        self.knobs.update(knob)
        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("bigville_decision_core"),
                                      self.eye._agent)
        self._build()

    # ------------------------------------------------------------------ ingest
    def _build(self):
        s, AE = self.s, self.inner.add_edge_unchecked
        n = len(self.actions)
        appeal = [float(a[1]) for a in self.actions]
        plan = [float(a[2]) for a in self.actions]
        # The order-0 net: an identity readout whose cached values ARE the fast
        # impulse appeal. NetForward(input_vec) = ReLU(I*x) = x initially; the
        # settle-back (net_collapse) edits these weights toward the model values.
        asm = s.add_node("NetworkAssemblage", {"input_dim": n, "output_dim": n})
        sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
        AE(asm, "has_step", sid)
        ident = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        for role, dat in {"W1": ident, "b1": [0.0] * n,
                          "W2": ident, "b2": [0.0] * n}.items():
            AE(sid, "has_weight", s.add_node("WeightTensor",
                                             {"role": role, "data": dat}))
        rn = s.add_node("ReflexNet", {"name": "order0_conduct", "status": "idle",
                                      "enabled": 1.0, "eta": 0.5})
        AE(rn, "net_assemblage", asm)
        # The conduct held-state (what collapses). input_vec = situation appeal;
        # target_vec = the world's consequence model (the settled-state target).
        attrs = {"input_vec": list(appeal), "target_vec": list(plan)}
        attrs.update(self.knobs)
        m = s.add_node("ConductState", attrs)
        AE(m, "has_net", rn)
        for i, (nm, ap, pl, tr) in enumerate(self.actions):
            a = s.add_node("DecAction", {
                "name": nm, "code": float(i), "index": i,
                "base_value": float(ap), "plan_value": float(pl),
                "is_transgressive": float(tr), "impulse": float(ap)})
            AE(m, "in_scene", a)
        self.m, self.rn, self.asm = m, rn, asm

    # -------------------------------------------------------------------- tick
    def decide(self):
        """Arm and run ONE collapse (the whole loop is ONE run_rules fixpoint):
        shallow settle -> residual -> (deepen if not settled) -> settle back."""
        for f in ("collapse_armed", "settle_check_armed", "writeback_armed",
                  "done", "deepened", "s2_choice_name", "s2_choice_code"):
            self.s.set_attr(self.m, f, 0.0)
        self.s.set_attr(self.m, "collapse_armed", 1.0)
        self.inner.run_rules()
        return self.trace()

    def set_knob(self, key, value):
        """Mechanically edit a collapse knob on the held state (a config write)."""
        self.knobs[key] = float(value)
        self.s.set_attr(self.m, key, float(value))

    # -------------------------------------------------------------------- read
    def trace(self):
        """Glass-box read-off of the collapse: the shallow candidate, the residual
        that drove depth, whether the collapse deepened, and the settled choice."""
        at = self.s.node(self.m)["attrs"]
        return dict(
            cand=at.get("cand_name"),
            cand_val=round(float(at.get("cand_val", 0.0)), 4),
            cand_transgressive=bool(round(float(at.get("cand_transg", 0.0)))),
            residual=round(float(at.get("residual", 0.0)), 4),
            settle_tol=round(float(at.get("settle_tol", 0.0)), 4),
            order=int(round(float(at.get("order", 0.0)))),
            deepened=int(round(float(at.get("deepened", 0.0)))),
            chosen=at.get("chosen_name"),
            chosen_via=at.get("chosen_via"),
            s2_choice=(at.get("s2_choice_name") if at.get("s2_choice_name") else None),
            considered=self.consideration_set(),
        )

    def consideration_set(self):
        """The order-0 availability filter's set (a pure read: appeal > threshold).
        This is the pruning the SHALLOW collapse does -- pruned options are never
        scored by the deeper collapse."""
        thr = self.knobs["consideration_threshold"]
        return [a[0] for a in self.actions if float(a[1]) > thr]

    def net_values(self):
        """Read the order-0 net's current cached values (NetForward over the held
        assemblage) -- how the settle-back has reshaped the fast path over reps."""
        try:
            asm_id = self.asm.value if hasattr(self.asm, "value") else int(self.asm)
            iv = list(self.s.node(self.m)["attrs"]["input_vec"])
            out = self.inner.net_forward(asm_id, iv)
            return [round(float(v), 4) for v in out]
        except Exception:
            return None

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
