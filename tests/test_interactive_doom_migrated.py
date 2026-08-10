"""Honest paced Doom world plus generic graph-native affordance control."""
from __future__ import annotations
import os,sys
import inspect
import numpy as np
import pytest

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(ROOT,"scripts") not in sys.path:sys.path.insert(0,os.path.join(ROOT,"scripts"))
import doom_world as dw
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.control_bundle import ControlBundleAdapter
from domains.spatial_belief import SpatialBeliefAdapter

class State:
    screen_buffer=np.zeros((24,32,3),np.uint8)
    labels_buffer=None;depth_buffer=None
    @property
    def labels(self): raise AssertionError("labels oracle was read")

class FakeGame:
    def __init__(self):self.calls=[];self.running=True;self.dead=False;self.finished=False;self.state=State()
    def __getattr__(self,name):
        if name.startswith("set_") or name.startswith("add_"):
            return lambda *a:self.calls.append((name,a))
        raise AttributeError(name)
    def init(self):self.calls.append(("init",()))
    def new_episode(self):self.calls.append(("new_episode",()));self.dead=False;self.finished=False
    def get_state(self):return self.state
    def get_game_variable(self,var):return {dw.vzd.GameVariable.POSITION_X:64,dw.vzd.GameVariable.POSITION_Y:128,dw.vzd.GameVariable.POSITION_Z:0,dw.vzd.GameVariable.ANGLE:90,dw.vzd.GameVariable.HEALTH:100,dw.vzd.GameVariable.ARMOR:0,dw.vzd.GameVariable.SELECTED_WEAPON_AMMO:20,dw.vzd.GameVariable.KILLCOUNT:0,dw.vzd.GameVariable.DAMAGE_TAKEN:0}.get(var,0)
    def is_player_dead(self):return self.dead
    def is_episode_finished(self):return self.finished
    def is_running(self):return self.running
    def make_action(self,buttons,tics):self.calls.append(("make_action",(list(buttons),tics)))
    def set_action(self,buttons):self.calls.append(("set_action",(list(buttons),)))
    def close(self):self.calls.append(("close",()));self.running=False

@pytest.fixture
def fake(monkeypatch):
    games=[]
    def make():g=FakeGame();games.append(g);return g
    monkeypatch.setattr(dw.vzd,"DoomGame",make)
    return games

def test_visible_player_is_configured_before_init_without_oracles(fake):
    world=dw.DoomWorld(visible=True,realtime=False,oracle_buffers=False)
    calls=fake[0].calls; names=[n for n,_ in calls]
    assert names.index("set_window_visible")<names.index("init")
    assert ("set_window_visible",(True,)) in calls
    assert ("set_mode",(dw.vzd.Mode.PLAYER,)) in calls
    assert ("set_depth_buffer_enabled",(False,)) in calls
    assert ("set_labels_buffer_enabled",(False,)) in calls
    sub,_=world.reset()
    assert sub.vision_screen is not None and sub.vision_frame is None
    assert all(n.type not in ("DoomPlayer","Zombieman") for n in sub.graph.nodes())
    world.close()

def test_one_tic_pulse_pause_and_button_mapping(fake):
    world=dw.DoomWorld(visible=False,realtime=False)
    sub,ctx=world.reset()
    assert world.step_tic(("forward","attack"))
    action=[c for c in fake[0].calls if c[0]=="make_action"][-1][1]
    assert action[1]==1
    assert action[0][0]==1 and action[0][4]==1
    before=len([c for c in fake[0].calls if c[0]=="make_action"])
    world.pause()
    assert len([c for c in fake[0].calls if c[0]=="make_action"])==before
    world.close();world.close()
    assert len([c for c in fake[0].calls if c[0]=="close"])==1

def test_no_restart_when_disabled_or_window_closed(fake):
    world=dw.DoomWorld(realtime=False,auto_restart=False)
    sub,ctx=world.reset();fake[0].dead=True
    _,out=world.apply_action(sub,ctx,("noop",))
    assert out["terminal"] and not out["respawned"]
    assert len([c for c in fake[0].calls if c[0]=="new_episode"])==1
    fake[0].running=False
    assert not world.is_running()

def test_observation_packet_roundtrip_is_rgb_and_proprioception_only(fake):
    world=dw.DoomWorld(realtime=False,oracle_buffers=False)
    sub,ctx=world.reset();packet=dw.observation_packet(sub,ctx,0)
    rebuilt,cell,pose=dw.substrate_from_packet(packet)
    assert rebuilt.vision_screen is not None and rebuilt.vision_frame is None
    body=next(n for n in rebuilt.graph.nodes() if n.type=="Body")
    assert body.attrs["angle"]==90
    assert all(n.type not in ("Zombieman","DoomPlayer") for n in rebuilt.graph.nodes())
    world.close()

def test_live_runner_has_no_doom_policy_or_oracle_path():
    import jabberwock_plays_doom as runner
    source=inspect.getsource(runner)
    assert "choose_action_meta_curious" not in source
    assert "doom_live_motor" not in source
    assert "doom_ingraph_map" not in source
    assert "AffordanceController" not in source
    assert "sensorimotor_affordance_control" not in source
    assert "ControlBundleAdapter" in source
    assert not os.path.exists(os.path.join(ROOT,"domains","affordance_control.py"))
    assert not os.path.exists(os.path.join(ROOT,"seeds","sensorimotor_affordance_control.json"))
    assert "describe_affordance" not in inspect.getsource(dw)
    world_source=inspect.getsource(dw.DoomWorld._build_substrate)
    assert "depth_buffer" not in world_source

def _control_agent(basis):
    a=WorldAdapter(seeds=())
    spatial=SpatialBeliefAdapter(a)
    controls=ControlBundleAdapter(a,spatial.space,basis)
    return a,spatial,controls

def test_least_tried_control_is_cognitive_not_action_list_weighting():
    basis=[{"axis":"a","controls":["zeta","alpha"]},
           {"axis":"b","controls":["omega"]}]
    a,spatial,controls=_control_agent(basis)
    a.inner.set_attr(controls.controls["zeta"],"n_trials",4.0)
    a.inner.set_attr(controls.controls["alpha"],"n_trials",2.0)
    a.inner.set_attr(controls.controls["omega"],"n_trials",3.0)
    intent=controls.deliberate(1,lambda _:{"recoverability":1.0})
    assert intent is not None
    bundle=a.inner.neighbours(intent,"enacts_bundle")[0]
    tokens={a.s.node(c)["attrs"]["token"]
            for c in a.inner.neighbours(bundle,"includes_control")}
    assert tokens=={"alpha"}

def test_distinct_axes_compose_and_same_axis_is_rejected():
    basis=[{"axis":"move","controls":["fwd","back"]},
           {"axis":"weapon","role":"operate","controls":["fire"]}]
    a,spatial,controls=_control_agent(basis)
    game=spatial.space
    for token in ("fwd","fire"):
        a.inner.add_edge_unchecked(game,"selected_control",controls.controls[token])
    a.inner.set_attr(game,"world_tick",3);a.inner.set_attr(game,"bundle_open",1.0)
    a.tick()
    bundle=[b for b in a.inner.neighbours(game,"has_control_bundle")
            if a.s.node(b)["attrs"].get("world_tick")==3][0]
    assert a.s.node(bundle)["attrs"]["status"]=="proposed"
    intent=a.inner.neighbours(bundle,"has_intent")[0]
    a.inner.set_attr(intent,"status","authorized")
    assert set(controls.enact(intent,3))=={"fwd","fire"}
    assert controls.enact(intent,3)==()

    a.inner.set_attr(game,"world_tick",4);a.inner.set_attr(game,"bundle_open",1.0)
    for token in ("fwd","back"):
        a.inner.add_edge_unchecked(game,"selected_control",controls.controls[token])
    a.tick()
    bad=[b for b in a.inner.neighbours(game,"has_control_bundle")
         if a.s.node(b)["attrs"].get("world_tick")==4][0]
    assert a.s.node(bad)["attrs"]["status"]=="inadmissible"

def test_learned_response_goal_and_held_operate_term_drive_one_bundle():
    a=WorldAdapter(seeds=());load_all_seeds(a)
    spatial=SpatialBeliefAdapter(a,cell_size=1.0)
    controls=ControlBundleAdapter(a,spatial.space,[
        {"axis":"opaque-motion","controls":["mystery"]},
        {"axis":"opaque-operation","role":"operate","controls":["zap"]}])
    spatial.record_action("mystery")
    spatial.ingest((0,0,0),[]);spatial.ingest((2,0,0),[])
    a.master_tick()
    responses=[r for r in a.inner.neighbours(spatial.self_region,"responds_via")
               if a.s.node(r)["attrs"].get("cname")=="mystery"]
    assert responses and a.s.node(responses[0])["attrs"]["dr"]>0

    target=a.s.add_node("Region",{
        "is_goal_kind":1.0,"cy":5.0,"cx":0.0,"dist_to_self":3.0})
    a.inner.add_edge_unchecked(spatial.space,"has_region",target)
    a.inner.set_attr(a.agent,"control_ahead",3.0)
    a.inner.set_attr(spatial.space,"world_tick",9)
    a.inner.set_attr(spatial.space,"bundle_open",1.0)
    a.inner.set_attr(spatial.space,"chosen_control","")
    a.master_tick();a.tick()
    bundles=[b for b in a.inner.neighbours(spatial.space,"has_control_bundle")
             if a.s.node(b)["attrs"].get("world_tick")==9]
    assert len(bundles)==1
    tokens={a.s.node(c)["attrs"]["token"]
            for c in a.inner.neighbours(bundles[0],"includes_control")}
    assert tokens=={"mystery","zap"}

def test_bundle_enactment_feeds_existing_action_and_resource_learning():
    a,spatial,controls=_control_agent([{"axis":"x","controls":["opaque"]}])
    game=spatial.space
    a.inner.add_edge_unchecked(game,"selected_control",controls.controls["opaque"])
    a.inner.set_attr(game,"world_tick",2);a.inner.set_attr(game,"bundle_open",1.0)
    a.tick()
    bundle=a.inner.neighbours(game,"has_control_bundle")[0]
    intent=a.inner.neighbours(bundle,"has_intent")[0]
    a.inner.set_attr(a.agent,"my_resource",10.0)
    a.inner.set_attr(intent,"status","authorized")
    assert controls.enact(intent,2)==("opaque",)
    a.inner.set_attr(a.agent,"my_resource",8.0)
    a.record_action_outcome_observed(
        "opaque",novelty_delta=2.0,failure_delta=0.0,boredom_delta=0.0,
        frontier_after=2.0)
    a.record_self_attr_deltas("opaque",alpha=1.0)
    stat=a.action_stat("opaque")
    assert stat["n"]==1 and stat["novelty_sum"]==2.0
    assert stat["delta_my_resource_ema"]==-2.0

def test_intent_expiry_uses_graph_visible_transport_horizon():
    a=WorldAdapter(seeds=())
    game=a.s.add_node("WorldInstance",{})
    controls=ControlBundleAdapter(
        a,game,[{"axis":"x","controls":["opaque"]}],
        intent_horizon_ticks=35)
    intent=controls.deliberate(11,lambda _:{"recoverability":1.0})
    assert intent is not None
    assert a.s.node(game)["attrs"]["intent_horizon_ticks"]==35
    assert a.s.node(intent)["attrs"]["created_tick"]==11
    assert a.s.node(intent)["attrs"]["expires_tick"]==46
    a.close()
