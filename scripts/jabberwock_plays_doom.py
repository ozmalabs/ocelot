"""Interactive autonomous Doom through the Jabberwock's photon eye.

The much-richer, seed-booted jabberwock is dropped into DOOM E1M1. The split is
strict (CLAUDE.md) and the cognition is ALL in the graph:

The visible PLAYER world advances at 35 one-tic pulses. RGB is the only visual
input; pose/resources are proprioception. The async photon retina and main
cognitive runtime settle independently. A generic sensorimotor-affordance
faculty exposes legal Control nodes. Each settled visual epoch mechanically
mints raw Doom/PSI observations plus one candidate per control. The native
dual-process cycle scores those candidates through the canonical affective
state, recruits scoped active cognition when warranted, and graph-authorizes
an epoch-bound ControlBundle intent. The host enacts exactly one fresh
authorized pulse or zero control. The following raw observation verifies the
prior deliberative outcome and graph learning persists on the Control node.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_plays_doom.py \
      --steps 400 --out recordings/doom_jabberwock_understands.mp4
  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_plays_doom.py --steps 40 --debug
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import signal
import queue
import multiprocessing as mp
from collections import deque

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import doom_world as dw


PHOTON_EYE_PROFILE = {
    # The measured real-Doom 2-D photon eye: event-native graph semantics with
    # the shipped byte-identical transduction accelerator.  The fixed event
    # window is sensor framing; motion/carve/salience decisions remain rules.
    "synchronous": True,
    "retina_accel": True,
    "retina_dirty": True,
    "retina_dirty_stamp_epoch": True,
    "top_down_world_view": True,
    "event_native": True,
    "visual_motion": True,
    "visual_salience": True,
    "event_window_epochs": 6,
    "adapt_rate": 0.4,
    "held_prediction": "decay",
    "onset_threshold_db": 6.0,
    "onset_refractory_epochs": 0.0,
    "carve_min_coherence": 0.5,
    "carve_min_events": 2.5,
    "fov_h_deg": 90.0,
    "fov_v_deg": 60.0,
}

FOVEATED_RETINA_WIDTH = 96
FOVEATED_FOVEA_WIDTH = 96
FOVEATED_FOVEA_HEIGHT = 72
# One sparse scout row (96 receptors) around a 6,912-receptor native fovea.
# Physical ring adjacency, not packed row/column proximity, remains authority.
FOVEATED_PERIPHERAL_RECEPTORS = 96
FOVEATED_RETINA_HEIGHT = (
    FOVEATED_FOVEA_WIDTH * FOVEATED_FOVEA_HEIGHT
    + FOVEATED_PERIPHERAL_RECEPTORS
) // FOVEATED_RETINA_WIDTH


class Recorder:
    """Streams RGB24 screen frames to ffmpeg -> mp4."""
    def __init__(self, path, w, h, fps=35):
        self.w, self.h = w, h
        self.closed = False
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.proc = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
             "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", path],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.n = 0

    def __call__(self, frame):
        try:
            self.proc.stdin.write(np.ascontiguousarray(frame).tobytes())
            self.n += 1
        except (BrokenPipeError, ValueError):
            pass

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()

def _replace(q,item):
    try:q.get_nowait()
    except queue.Empty:pass
    try:q.put_nowait(item)
    except queue.Full:pass


def _action_pulse(
        action, *, authored_world_tick, expires_world_tick, action_id=None):
    """Mechanical, pickle-safe envelope for one graph-authored pulse."""
    action = tuple(action or ())
    if not action or action == ("noop",):
        raise ValueError("only authored non-noop pulses belong in the FIFO")
    return {
        "action": action,
        "action_id": int(
            authored_world_tick if action_id is None else action_id),
        "authored_world_tick": int(authored_world_tick),
        "expires_world_tick": int(expires_world_tick),
    }


def _drain_action_fifo(action_queue, pending, *, world_tick):
    """Append every arrived action without overwriting or reordering."""
    while True:
        try:
            envelope = action_queue.get_nowait()
        except queue.Empty:
            break
        if isinstance(envelope, dict):
            action = tuple(envelope.get("action") or ())
            action_id = int(envelope.get(
                "action_id",
                envelope.get("authored_world_tick", world_tick)))
            authored = int(envelope.get("authored_world_tick", world_tick))
            expires = int(envelope.get("expires_world_tick", world_tick))
        else:
            # Compatibility for old mechanical callers: a bare pulse is valid
            # only for the world tick on which the boundary receives it.
            action = tuple(envelope or ())
            authored = expires = int(world_tick)
            action_id = authored
        if action and action != ("noop",):
            pending.append({
                "action": action,
                "action_id": action_id,
                "authored_world_tick": authored,
                "expires_world_tick": expires,
            })


def _action_receipt(envelope, status, world_tick):
    """Lossless child-process acknowledgement for one authored pulse."""
    return {
        "action_id": int(envelope["action_id"]),
        "action": tuple(envelope["action"]),
        "status": str(status),
        "authored_world_tick": int(envelope["authored_world_tick"]),
        "expires_world_tick": int(envelope["expires_world_tick"]),
        "receipt_world_tick": int(world_tick),
        "applied_world_tick": (
            int(world_tick) if status == "applied" else -1),
    }


def _take_action_envelope_for_world_tick(pending, world_tick):
    """Return the oldest live envelope plus receipts for stale predecessors."""
    expired = []
    while pending:
        envelope = pending[0]
        if int(envelope["expires_world_tick"]) < int(world_tick):
            expired.append(_action_receipt(
                pending.popleft(), "expired_stale", world_tick))
            continue
        if int(envelope["authored_world_tick"]) > int(world_tick):
            return None, expired
        return pending.popleft(), expired
    return None, expired


def _take_action_for_world_tick(pending, world_tick):
    """Compatibility readout: oldest live action and number expired."""
    envelope, expired = _take_action_envelope_for_world_tick(
        pending, world_tick)
    action = (
        tuple(envelope["action"]) if envelope is not None else ("noop",))
    return action, len(expired)


def _latest(q):
    """Drain a latest-state channel; unlike action pulses, history is irrelevant."""
    latest = None
    while True:
        try:
            latest = q.get_nowait()
        except queue.Empty:
            return latest


def _drain_action_receipts(receipt_queue):
    """Drain the lossless action-event channel without collapsing history."""
    receipts = []
    while True:
        try:
            receipts.append(receipt_queue.get_nowait())
        except queue.Empty:
            return receipts


def _reconcile_transport_telemetry(
        authored, applied, expired_stale, expired_world_end):
    """Classify sender-side pulses left behind after the world has ended."""
    authored = int(authored)
    applied = int(applied)
    expired_stale = int(expired_stale)
    expired_world_end = int(expired_world_end)
    accounted = applied + expired_stale + expired_world_end
    # A pulse authored from a final observation can enter the sender queue
    # after the Doom process has exited. With no future world tick it is
    # expired at world end even though the receiver could not count it.
    expired_world_end += max(0, authored - accounted)
    return {
        "expired_stale_actions": expired_stale,
        "expired_world_end_actions": expired_world_end,
        "expired_actions": expired_stale + expired_world_end,
    }


_EYE_MOTOR_DEFAULTS = {
    "eye_motor_active": 0.0,
    "eye_motor_source_epoch": -1,
    "eye_motor_target_column": -1,
    "eye_motor_target_row": -1,
    "eye_motor_target_az_deg": 0.0,
    "eye_motor_target_el_deg": 0.0,
    "eye_motor_fixation_epoch": -1,
    "eye_motor_duration_tics": 0,
    "eye_motor_status": "refused",
}


def _eye_motor_command(agent):
    """Copy the graph's single authoritative eye command to the actuator."""
    attrs = agent.s.node(agent.agent)["attrs"]
    return {
        key: attrs.get(key, default)
        for key, default in _EYE_MOTOR_DEFAULTS.items()
    }


def _doom_process(
        config, actions, eye_commands, frames, result, stop,
        action_receipts=None):
    world=None;recorder=None;acts={};deaths=0
    pending_actions=deque()
    applied_actions=0;expired_stale_actions=0;doom_ticks=0
    try:
        world=dw.DoomWorld(**{
            k:v for k,v in config.items() if k not in ("tics","record_path")})
        sub,ctx=world.reset()
        if config.get("record_path"):
            frame=world.screen()
            recorder=Recorder(config["record_path"],frame.shape[1],frame.shape[0],
                              fps=config["ticrate"])
            world.recorder=recorder
        _replace(frames,dw.observation_packet(sub,ctx,0))
        for tic in range(config["tics"]):
            if stop.is_set() or not world.is_running():break
            world_tick=tic+1
            _drain_action_fifo(
                actions,pending_actions,world_tick=world_tick)
            envelope,expired_receipts=_take_action_envelope_for_world_tick(
                pending_actions,world_tick)
            expired_stale_actions += len(expired_receipts)
            if action_receipts is not None:
                for receipt in expired_receipts:
                    action_receipts.put(receipt)
            action=(
                tuple(envelope["action"])
                if envelope is not None else ("noop",))
            world.apply_eye_motor_command(_latest(eye_commands))
            sub,ctx=world.apply_action(sub,ctx,action)
            if envelope is not None and action_receipts is not None:
                action_receipts.put(
                    _action_receipt(envelope, "applied", world_tick))
            _replace(frames,dw.observation_packet(sub,ctx,tic+1))
            deaths += 1 if ctx.get("respawned") else 0
            acts[action]=acts.get(action,0)+1
            doom_ticks += 1
            if action != ("noop",):
                applied_actions += 1
    except BaseException as exc:
        result.put({"error":f"{type(exc).__name__}: {exc}"})
    finally:
        # Once the world stops there is no future tick on which a queued pulse
        # can be enacted. Account for every received pulse honestly.
        _drain_action_fifo(
            actions,pending_actions,world_tick=doom_ticks+1)
        expired_world_end_actions=len(pending_actions)
        if action_receipts is not None:
            for envelope in pending_actions:
                action_receipts.put(_action_receipt(
                    envelope, "expired_world_end", doom_ticks + 1))
        pending_actions.clear()
        if world is not None:
            try:world.release_action()
            except Exception:pass
        if recorder is not None:recorder.close()
        if world is not None:world.close()
        result.put({
            "acts":acts,"deaths":deaths,"doom_ticks":doom_ticks,
            "applied_actions":applied_actions,
            "expired_stale_actions":expired_stale_actions,
            "expired_world_end_actions":expired_world_end_actions,
            "expired_actions":(
                expired_stale_actions+expired_world_end_actions),
        })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tics", type=int, default=1400)
    ap.add_argument("--map", default="E1M1")
    ap.add_argument("--out", default="")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--unpaced", action="store_true")
    ap.add_argument("--ticrate", type=int, default=35)
    ap.add_argument("--cognition-hz", type=float, default=30.0)
    ap.add_argument("--workers", type=int, default=4)
    # Current full-cognition budget floor from the committed real-Doom fixture:
    # 20x15 settles at about 12 ms p90.  Larger uniform sheets remain explicit
    # experiment options until foveation removes their global-fixpoint cost.
    ap.add_argument("--retina-width", type=int, default=20)
    ap.add_argument("--retina-height", type=int, default=15)
    ap.add_argument(
        "--foveated-eye", action="store_true",
        help=("use the explicit native-detail fovea plus persistent log-polar "
              "peripheral scout"))
    ap.add_argument(
        "--fovea-width", type=int, default=FOVEATED_FOVEA_WIDTH)
    ap.add_argument(
        "--fovea-height", type=int, default=FOVEATED_FOVEA_HEIGHT)
    ap.add_argument(
        "--no-predictive-fovea", action="store_true",
        help=("ablate allocentric latent reconstruction and residual-selected "
              "dense settlement while retaining identical foveated optics"))
    ap.add_argument(
        "--no-global-illumination", action="store_true",
        help=("ablate foveal-lead/broad-field illumination inference while "
              "retaining identical foveated photon measurements"))
    ap.add_argument("--peripheral-rings", type=int, default=4)
    ap.add_argument("--peripheral-spokes", type=int, default=24)
    ap.add_argument(
        "--saccades", action="store_true",
        help="enable graph-native eye-motor commands (implied by --foveated-eye)")
    ap.add_argument(
        "--retinal-focus", action="store_true",
        help=("opt into graph-directed bounded event settlement; the whole-sheet "
              "path remains the conservative default"))
    ap.add_argument("--no-restart", action="store_true")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    stop = mp.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())

    t0 = time.time()
    print("booting the jabberwock ...", flush=True)
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    # self-identification: the marine's Body carries id 'agent_self'; tell the
    # agent that IS itself, so its self-attrs (my_angle, my_health, ...) — which
    # the motor faculty reads — populate from what it observes.
    agent.inner.set_attr(agent.agent, "my_world_id", "agent_self")
    from domains.control_bundle import ControlBundleAdapter
    from domains.doom_dual_process_ingest import DoomDualProcessAdapter
    from domains.spatial_belief import SpatialBeliefAdapter
    from domains.allocentric_world_view_ingest import (
        ingest_current_optic_evidence)
    spatial = SpatialBeliefAdapter(agent, cell_size=64.0, fov_deg=90.0)
    controls = ControlBundleAdapter(
        agent,spatial.space,dw.control_basis(),
        # One second of actuator time is the graph-visible transport
        # calibration. A full cognition pass currently spans several Doom
        # tics, so the old six-tic envelope expired before IPC delivery.
        intent_horizon_ticks=max(1,int(args.ticrate)))
    doom_cognition = DoomDualProcessAdapter(agent, controls)
    saccades_enabled = bool(args.saccades or args.foveated_eye)
    for controller in agent.s.nodes("SaccadeController"):
        agent.inner.set_attr(
            controller, "enabled", 1.0 if saccades_enabled else 0.0)
    for params in agent.s.nodes("TranssaccadicMemoryParams"):
        agent.inner.set_attr(
            params, "enabled", 1.0 if args.foveated_eye else 0.0)
    for params in agent.s.nodes("AllocentricWorldViewParams"):
        agent.inner.set_attr(
            params, "enabled", 1.0 if args.foveated_eye else 0.0)
    for params in agent.s.nodes("FovealPredictiveParams"):
        agent.inner.set_attr(
            params, "enabled",
            1.0 if (
                args.foveated_eye and not args.no_predictive_fovea)
            else 0.0)
    for params in agent.s.nodes("GlobalIlluminationParams"):
        agent.inner.set_attr(
            params, "enabled",
            1.0 if (
                args.foveated_eye and not args.no_global_illumination)
            else 0.0)
    print(f"booted in {time.time()-t0:.1f}s. dropping into DOOM {args.map}.", flush=True)

    retina_width = (
        FOVEATED_RETINA_WIDTH if args.foveated_eye
        else int(args.retina_width))
    retina_height = (
        FOVEATED_RETINA_HEIGHT if args.foveated_eye
        else int(args.retina_height))
    # Authored non-noop pulses are events: retain FIFO history. Eye commands
    # and frames are state snapshots and intentionally remain latest-only.
    actions=mp.Queue(maxsize=max(1,args.tics+1))
    action_receipts=mp.Queue(maxsize=max(1,2*(args.tics+1)))
    eye_commands=mp.Queue(maxsize=1)
    frames=mp.Queue(maxsize=1);result=mp.Queue()
    config={"wad":dw.DEFAULT_WAD,"doom_map":args.map,"ticks_per_action":1,
        "visible":not args.headless,"realtime":not args.unpaced,
        "ticrate":args.ticrate,"auto_restart":not args.no_restart,
        # The foveated profile's native-detail contract is the canonical Doom
        # 320x240 field used by the eye ceiling fixtures.
        **({"res":dw.vzd.ScreenResolution.RES_320X240}
           if args.foveated_eye else {}),
        "oracle_buffers":False,"ingest_oracle_objects":False,
        "worker_capacity":max(1,args.workers),"retina_tick_hz":args.cognition_hz,
        "photon_sheet":True,
        "photon_n_az":max(1,retina_width),
        "photon_n_el":max(1,retina_height),
        "photon_eye_context":{
            **PHOTON_EYE_PROFILE,
            "retinal_focus":bool(args.retinal_focus or args.foveated_eye),
            # Absent when disabled so the legacy uniform build remains exact,
            # rather than merely constructing an equivalent explicit layout.
            **({"retinal_layout":"foveated"} if args.foveated_eye else {}),
            **({"event_pathway":"periphery"} if args.foveated_eye else {}),
            **({"split_foveated_pathways":True}
               if args.foveated_eye else {}),
            "fovea_width":max(1,args.fovea_width),
            "fovea_height":max(1,args.fovea_height),
            "peripheral_rings":max(1,args.peripheral_rings),
            "peripheral_spokes":max(1,args.peripheral_spokes),
        },
        # Send the compact realized count sheet across IPC; the receiving
        # world adapter mechanically expands it to the identical packet list.
        "photon_packetize":False,
        "tics":args.tics,"record_path":args.out}
    game=mp.Process(
        target=_doom_process,
        args=(config,actions,eye_commands,frames,result,stop,action_receipts),
                    name="doom-world")
    deaths=0;acts={};last_decision_epoch=-1;last_map_epoch=-1
    processed_cognitive_frames=0;authored_actions=0
    applied_actions=0;expired_stale_actions=0
    expired_world_end_actions=0;expired_actions=0;doom_ticks=0
    max_world_view_cells=0;max_renderable_prior_cells=0
    max_prior_receptors=0;play_started=None;play_elapsed=0.0
    max_foveal_predicted_tiles=0;max_foveal_grounded_tiles=0
    max_foveal_residual=0.0;max_foveal_settled_tiles=0
    max_motion_percepts=0;max_salience_percepts=0
    max_spatial_evidence=0
    prev_cell=None;prev_pose=None;prev_damage_taken=0.0;prev_killcount=0.0
    world_error=None
    system_one_decisions=0;system_two_decisions=0
    background_learning_cycles=0
    try:
        game.start()
        play_started=time.time()
        while game.is_alive() or not frames.empty():
            if stop.is_set():break
            try:packet=frames.get(timeout=0.2)
            except queue.Empty:continue
            processed_cognitive_frames += 1
            prior_pose=prev_pose
            sub,prev_cell,prev_pose=dw.substrate_from_packet(
                packet,prev_cell=prev_cell,prev_pose=prev_pose)
            ctx=packet["ctx"];tic=int(packet["tic"])
            body=next(n for n in sub.graph.nodes() if n.type=="Body")
            agent.observe(sub)
            if args.foveated_eye:
                max_prior_receptors=max(
                    max_prior_receptors,
                    int(agent.s.node(agent.agent)["attrs"].get(
                        "top_down_prior_projected_receptors",0)))
                foveal_exposures=agent.inner.neighbours(
                    agent.agent,"has_foveal_exposure")
                if len(foveal_exposures)==1:
                    foveal_attrs=agent.s.node(foveal_exposures[0])["attrs"]
                    max_foveal_predicted_tiles=max(
                        max_foveal_predicted_tiles,
                        int(foveal_attrs.get("predicted_tile_count",0)))
                    max_foveal_grounded_tiles=max(
                        max_foveal_grounded_tiles,
                        int(foveal_attrs.get("grounded_tile_count",0)))
                    max_foveal_residual=max(
                        max_foveal_residual,
                        float(agent.s.node(agent.agent)["attrs"].get(
                            "foveal_max_predicted_residual",0.0)))
            last_action=tuple(ctx.get("last_action") or ())
            known_before=len(spatial.cells())
            aa=agent.s.node(agent.agent)["attrs"]
            settled=int(aa.get("vision_settled_epoch",-1))
            if settled>=0 and settled>last_map_epoch:
                spatial.record_action(last_action[0] if len(last_action)==1 else "")
                spatial.ingest((body.attrs["x"],body.attrs["y"],body.attrs["angle"]),
                               [])
                max_motion_percepts=max(
                    max_motion_percepts,
                    len(agent.inner.neighbours(
                        agent.agent,"perceives_motion")))
                max_salience_percepts=max(
                    max_salience_percepts,
                    len(agent.inner.neighbours(
                        agent.agent,"perceives_salience")))
                max_spatial_evidence=max(
                    max_spatial_evidence,
                    len(agent.inner.neighbours(
                        agent.agent,"holds_spatial_evidence")))
                ingest_current_optic_evidence(agent)
                if args.foveated_eye:
                    foveal_exposures=agent.inner.neighbours(
                        agent.agent,"has_foveal_exposure")
                    if len(foveal_exposures)==1:
                        max_foveal_settled_tiles=max(
                            max_foveal_settled_tiles,
                            int(agent.s.node(foveal_exposures[0])[
                                "attrs"].get("settled_count",0)))
                view_cells=agent.inner.neighbours(
                    agent.agent,"holds_world_view_cell")
                max_world_view_cells=max(
                    max_world_view_cells,len(view_cells))
                max_renderable_prior_cells=max(
                    max_renderable_prior_cells,
                    sum(agent.s.node(cell)["attrs"].get(
                            "surface_value") is not None
                        for cell in view_cells))
                last_map_epoch=settled
            new_cells=max(0,len(spatial.cells())-known_before)
            damage_taken=float(body.attrs.get("damage_taken",0.0))
            damage_delta=max(0.0,damage_taken-prev_damage_taken)
            prev_damage_taken=damage_taken
            killcount=float(body.attrs.get("killcount",0.0))
            kill_delta=max(0.0,killcount-prev_killcount)
            prev_killcount=killcount
            moved=bool(
                prior_pose is not None and
                ((float(body.attrs["x"])-float(prior_pose[0]))**2+
                 (float(body.attrs["y"])-float(prior_pose[1]))**2)>0.0)
            for token in last_action:
                if token=="noop":continue
                agent.record_action_outcome_observed(
                    token,novelty_delta=float(new_cells),
                    failure_delta=float(bool(ctx.get("respawned"))),
                    boredom_delta=float(new_cells==0),frontier_after=float(new_cells))
                agent.record_self_attr_deltas(token)
            aa=agent.s.node(agent.agent)["attrs"]
            settled=int(aa.get("vision_settled_epoch",-1))
            for receipt in _drain_action_receipts(action_receipts):
                doom_cognition.observe_action_receipt(
                    receipt, observed_epoch=max(0, settled))
            next_action=("noop",)
            intent=None
            if settled>=0 and settled>last_decision_epoch:
                decision_context=doom_cognition.observe_epoch(
                    epoch=settled,
                    health=float(body.attrs.get(
                        "health",body.attrs.get("health_bin",0.0)*25.0)),
                    ammo=float(body.attrs.get(
                        "ammo",body.attrs.get("ammo_bin",0.0)*10.0)),
                    damage_taken=damage_delta,
                    respawned=bool(ctx.get("respawned")),
                    new_cells=float(new_cells),
                    moved=moved,
                    kill_delta=kill_delta,
                    attention_refused=float(aa.get(
                        "attention_refused",1.0)),
                    motion_count=float(len(agent.inner.neighbours(
                        agent.agent,"perceives_motion"))),
                    salience_count=float(len(agent.inner.neighbours(
                        agent.agent,"perceives_salience"))),
                )
                intent,dual_report=doom_cognition.deliberate(
                    decision_context,tic,dw.affordance_footprint)
                # `needs_system_two` is cycle-wide: it may describe the
                # learning-only request for the previous action while this
                # context itself commits through System 1. The graph-authored
                # route on this context is the decision readout.
                decision_route=agent.s.node(
                    decision_context)["attrs"].get("route")
                if decision_route=="system_two":
                    system_two_decisions += 1
                elif decision_route=="system_one":
                    system_one_decisions += 1
                    if dual_report.get("needs_system_two"):
                        background_learning_cycles += 1
                action=controls.enact(intent,tic)
                next_action=action or ("noop",)
                last_decision_epoch=settled
            if next_action != ("noop",):
                if intent is None:
                    raise RuntimeError(
                        "non-noop action was returned without an intent")
                intent_attrs=agent.s.node(intent)["attrs"]
                actions.put(_action_pulse(
                    next_action,
                    action_id=int(
                        intent_attrs.get("created_tick", tic)),
                    authored_world_tick=tic,
                    expires_world_tick=int(
                        intent_attrs.get("expires_tick",tic)),
                ))
                authored_actions += 1
            _replace(eye_commands,_eye_motor_command(agent))
            if args.debug and tic%35==0:
                print(
                    f"tic={tic:5d} decision_epoch={last_decision_epoch} "
                    f"frames={processed_cognitive_frames} "
                    f"authored={authored_actions}",flush=True)
    finally:
        if play_started is not None:
            play_elapsed=max(0.0,time.time()-play_started)
        stop.set()
        if game.is_alive():game.join(timeout=3)
        if game.is_alive():game.terminate();game.join(timeout=1)
        while not result.empty():
            row=result.get()
            if row.get("error"):world_error=row["error"]
            acts=row.get("acts",acts);deaths=row.get("deaths",deaths)
            doom_ticks=row.get("doom_ticks",doom_ticks)
            applied_actions=row.get("applied_actions",applied_actions)
            expired_stale_actions=row.get(
                "expired_stale_actions",expired_stale_actions)
            expired_world_end_actions=row.get(
                "expired_world_end_actions",expired_world_end_actions)
        agent.close()
    if world_error:raise RuntimeError(world_error)
    transport = _reconcile_transport_telemetry(
        authored_actions,applied_actions,
        expired_stale_actions,expired_world_end_actions)
    expired_stale_actions=transport["expired_stale_actions"]
    expired_world_end_actions=transport["expired_world_end_actions"]
    expired_actions=transport["expired_actions"]
    top = sorted(acts.items(), key=lambda kv: -kv[1])[:6]
    print(f"\n{'='*72}")
    print(f"  DOOM {args.map}: {doom_ticks} tics, {deaths} deaths.")
    cognitive_hz=(
        processed_cognitive_frames/play_elapsed if play_elapsed>0 else 0.0)
    print(
        "  cognition/transport: "
        f"{processed_cognitive_frames} frames processed "
        f"({cognitive_hz:.1f} Hz), "
        f"{authored_actions} actions authored, "
        f"{applied_actions} applied, {expired_actions} expired "
        f"({expired_stale_actions} stale, "
        f"{expired_world_end_actions} world-ended).")
    print(
        "  dual process: "
        f"{system_one_decisions} System-1 commits, "
        f"{system_two_decisions} System-2 decisions, "
        f"{background_learning_cycles} background learning cycles.")
    if args.foveated_eye:
        print(
            "  top-down world view: "
            f"{max_world_view_cells} surface supports, "
            f"{max_renderable_prior_cells} photometric priors, "
            f"{max_prior_receptors} predicted scout receptors; "
            f"max motion/salience/range evidence "
            f"{max_motion_percepts}/{max_salience_percepts}/"
            f"{max_spatial_evidence}.")
        print(
            "  predictive fovea: "
            f"{max_foveal_predicted_tiles} decoded prior tiles, "
            f"{max_foveal_grounded_tiles} allocentrically grounded, "
            f"{max_foveal_settled_tiles} residual-selected per exposure, "
            f"max normalized residual {max_foveal_residual:.4f}.")
    print(f"  action mix: {[('+'.join(k), v) for k, v in top]}")
    if args.out:print(f"  recording: {args.out}")
    print("  photon vision -> graph goals/learning/motor terms -> compatible control bundle")
    print(f"  depth/labels disabled. [{time.time()-t0:.1f}s]")
    print(f"{'='*72}")


if __name__ == "__main__":
    main()
