"""Mechanical world-control basis and cognitive ControlBundle readback."""
from __future__ import annotations
from substrate.seed_loader import manifest_for
from domains.information_commitment import assess


def _control_attrs(spec, ordinal):
    """Normalize mechanical actuator metadata; make no control decision."""
    if isinstance(spec, dict):
        token = str(spec.get("token", spec.get("name", "")))
        attrs = {
            key: value for key, value in spec.items()
            if key not in ("token", "name")
        }
    else:
        token, attrs = str(spec), {}
    attrs.update({
        "name": token, "token": token, "n_trials": 0.0,
        "last_trial_epoch": -1.0,
    })
    # motor_core's generic attention term rotates the current heading by this
    # actuator's measured/declared angular effect. Non-angular actuators are
    # mechanically calibrated at zero rather than interpreted by Python.
    attrs.setdefault("dtheta_ema", 0.0)
    attrs.setdefault("control_ordinal", int(ordinal))
    return token, attrs


class ControlBundleAdapter:
    def __init__(self,agent,game,basis,*,intent_horizon_ticks=6):
        self.agent=agent;self.s=agent.s;self.inner=agent.inner;self.game=game
        # Direct adapter construction is used by small worlds/tests as well as
        # normal load-all boot. Seed manifests declare dependencies, but the
        # low-level native loader intentionally installs only the given
        # manifest, so make the graph-resident attention evaluator available.
        if not list(self.inner.neighbours(agent.agent, "attention_value_term")):
            self.inner.load_seed_manifest(
                manifest_for("motor_core"), agent.agent)
        names={r.get("name") for r in self.inner.export_rules()}
        if "control_bundle_from_selected_primitives" not in names:
            self.inner.load_seed_manifest(manifest_for("control_bundle"),agent.agent)
        self.inner.add_edge_unchecked(game,"for_agent",agent.agent)
        # Actuator transport calibration is graph data. A world whose
        # cognition spans several actuator ticks can publish a longer horizon
        # without moving the expiry decision out of the seed.
        self.inner.set_attr(
            game, "intent_horizon_ticks", max(1, int(intent_horizon_ticks)))
        self.controls={}
        control_ordinal = 0
        for axis_spec in basis:
            axis=self.s.add_node("ControlAxis",{
                "name":axis_spec["axis"],"role":axis_spec.get("role","motor")})
            self.inner.add_edge_unchecked(game,"has_control_axis",axis)
            axis_controls=[]
            for spec in axis_spec["controls"]:
                token, attrs = _control_attrs(spec, control_ordinal)
                control_ordinal += 1
                control=self.s.add_node("Control", attrs)
                self.inner.add_edge_unchecked(axis,"has_control",control)
                self.inner.add_edge_unchecked(game,"has_control",control)
                self.controls[token]=control
                axis_controls.append(control)
            for control in axis_controls:
                for other in axis_controls:
                    if control!=other:
                        self.inner.add_edge_unchecked(control,"exclusive_with",other)

    def deliberate(self,world_tick:int,footprint_fn):
        """Run existing cognition and return one proposed bundle intent."""
        self.inner.set_attr(self.game,"world_tick",int(world_tick))
        self.inner.set_attr(self.game,"bundle_open",1.0)
        self.inner.set_attr(self.game,"chosen_control","")
        for control in list(self.inner.neighbours(self.game,"selected_control")):
            self.inner.remove_edge(self.game,"selected_control",control)
        self.agent.tick();self.agent.master_tick();self.agent.tick()
        bundles=[b for b in self.inner.neighbours(self.game,"has_control_bundle")
                 if int(self.s.node(b)["attrs"].get("world_tick",-1))==int(world_tick)]
        if len(bundles)!=1:return None
        bundle=bundles[0]
        if self.s.node(bundle)["attrs"].get("status")!="proposed":return None
        intents=list(self.inner.neighbours(bundle,"has_intent"))
        if len(intents)!=1:return None
        intent=intents[0]
        tokens=tuple(self.s.node(c)["attrs"]["token"]
                     for c in self.inner.neighbours(bundle,"includes_control"))
        footprint=footprint_fn(tokens)
        gate=assess(self.agent,
            commit={"name":"control_bundle",
                    "expected_goal_work":float(footprint.get("expected_goal_work",1.0)),
                    "expected_information_gain":float(footprint.get("expected_information_gain",0.0)),
                    "uncertainty":float(footprint.get("uncertainty",0.0)),
                    "footprint":{k:float(footprint.get(k,v)) for k,v in (
                        ("deleted_facts",0.0),("overwritten_facts",0.0),
                        ("recoverability",0.0),("externality",0.0))}},
            wait={"delay_cost":0.1},
            refine={"expected_information_gain":max(
                        0.0,float(footprint.get("uncertainty",0.0))),
                    "decision_relevance":1.0,"refinement_cost":0.2},
            retain_trace=False)
        status="authorized" if gate["decision"]=="commit" and gate["authorized"] else "deferred"
        self.inner.set_attr(intent,"status",status)
        return intent

    def enact(self,intent,world_tick:int):
        if intent is None or not self.s.has_node(intent):return ()
        attrs=self.s.node(intent)["attrs"]
        if attrs.get("status")!="authorized":return ()
        if int(world_tick)>int(attrs.get("expires_tick",-1)):
            self.inner.set_attr(intent,"status","expired");return ()
        bundles=list(self.inner.neighbours(intent,"enacts_bundle"))
        if len(bundles)!=1:return ()
        controls=list(self.inner.neighbours(bundles[0],"includes_control"))
        self.agent.snapshot_self_attrs_at_decision()
        self.inner.set_attr(intent,"status","enacted")
        self.inner.set_attr(intent,"enacted_tick",int(world_tick))
        tokens=tuple(self.s.node(c)["attrs"]["token"] for c in controls)
        self.inner.set_attr(self.game,"action_epoch",int(world_tick))
        self.inner.set_attr(self.game,"last_action",tokens[0] if len(tokens)==1 else "")
        self.inner.set_attr(self.game,"bundle_open",0.0)
        # The enacted status is graph evidence.  Settle it before the next
        # deliberation so the graph-resident trial memory can influence that
        # deliberation instead of observing every primitive one epoch late.
        # This is cadence only: bundle membership and the learning update
        # remain rule decisions in control_bundle.json.
        self.inner.run_rules()
        return tokens
