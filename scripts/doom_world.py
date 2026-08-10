"""doom_world — a PURE I/O world adapter for ViZDoom (understand-then-act).

The world does exactly two mechanical things and decides NOTHING:

  INGEST: build a fresh typed-graph of the marine's current state — a Body
  (self, x/y/z/angle/health), the objects VizDoom's labels buffer sees, the
  local spatial topology — AND hand the agent its raw optic input as
  side-channels: `vision_screen` (the colour image) and, when requested, the
  measured real-Doom 2-D photon sheet (`vision_photon_packets` and
  `vision_photon_counts`), plus the sensor `vision_calibration`. The world does
  not interpret pixels — no "wall", no occupancy, no map — and depth/labels
  never enter autonomous cognition. The agent's own graph-resident GraphEye
  performs perception on the tick.

  EMIT: apply the composite control the agent CHOSE (its seeded motor /
  exploration / curiosity faculties pick it over legal_actions), stepping the
  live game — which IS the world's state.

This is the CuriousAgent-era Doom adapter (deleted in the burn) rebuilt on the
seed-booted WorldAdapter: no agent logic here, the reasoning is the seeds. The
recorder captures the screen every game tic.
"""
from __future__ import annotations

import math
import time
import numpy as np
import vizdoom as vzd

from domains import doom_photon_world as dpw
from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph

DEFAULT_WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"
DEFAULT_PHOTON_N_AZ = 113
DEFAULT_PHOTON_N_EL = 85
DEFAULT_PHOTON_SEED = 181000

# The FULL affordance set — composite Doom controls (a tuple is read as a
# composition; per-primitive stats accumulate). forward/back/turn/strafe + the
# use/attack primitives, exactly the marine's moveset.
_PRIMS = ("forward", "backward", "turn_left", "turn_right",
          "strafe_left", "strafe_right", "attack", "use")
_ACTIONS = [
    ("noop",), ("forward",), ("backward",), ("turn_left",), ("turn_right",),
    ("strafe_left",), ("strafe_right",), ("attack",), ("use",),
]
# button vector aligned with the order added on the game below.
_BTN_ORDER = ("forward", "backward", "turn_left", "turn_right",
              "attack", "use", "strafe_left", "strafe_right")

def control_basis():
    """Opaque independent actuator axes with mechanical angular calibration."""
    turn_radians = math.radians(5.0)
    return [
        {"axis":"longitudinal","role":"motor","controls":["forward","backward"]},
        {"axis":"lateral","role":"motor","controls":["strafe_left","strafe_right"]},
        {"axis":"angular","role":"motor","controls":[
            {"token":"turn_left","dtheta_ema":-turn_radians},
            {"token":"turn_right","dtheta_ema":turn_radians},
        ]},
        {"axis":"weapon","role":"operate","controls":["attack"]},
        {"axis":"interaction","role":"operate","controls":["use"]},
    ]


def _action_to_buttons(action):
    a = set(action)
    return [int(name in a) for name in _BTN_ORDER]

def affordance_footprint(action):
    names=set(action)
    motion=float(bool(names & {"forward","backward","strafe_left","strafe_right"}))
    return {"deleted_facts":0.0,"overwritten_facts":0.0,
            "recoverability":1.0 if motion==0 else 0.5,"externality":0.0,
            "expected_goal_work":1.0,
            "expected_information_gain":0.5 if motion else 0.1,
            "uncertainty":0.5 if motion else 0.0}


def _retinal_layout_signature(calibration):
    """Cache key for the physical optics, including explicit layouts."""
    cal = calibration or {}
    explicit = cal.get("receptor_layout")
    if explicit is None:
        explicit_signature = None
    else:
        explicit_signature = tuple(
            (
                int(record["cell_index"]),
                float(record["gaze_az"]), float(record["gaze_el"]),
                float(record["angular_width"]),
                float(record["angular_height"]),
                str(record["eye_id"]), str(record["pathway"]),
                tuple(int(i) for i in record["adjacent"]),
            )
            for record in explicit
        )
    return (
        *(cal.get(key) for key in (
            "retinal_layout", "eye_id", "gaze_az_deg", "gaze_el_deg",
            "periphery_gaze_az_deg", "periphery_gaze_el_deg",
            "fovea_width", "fovea_height", "peripheral_rings",
            "peripheral_spokes", "fovea_fov_fraction",
            "fovea_fov_h_deg", "fovea_fov_v_deg",
            "source_width", "source_height", "fov_h_deg", "fov_v_deg",
        )),
        explicit_signature,
    )


def _publish_photon_sheet(sub, screen, calibration, *, epoch=0, rng=None,
                          counts=None, packets=None, packetize=True,
                          receptor_layout=None):
    """Mechanically attach a real-camera photon sheet to a substrate.

    The conversion is the already measured ``doom_photon_world`` path:
    area-mean luma -> Poisson photon counts -> receptor packets.  Supplying
    ``counts``/``packets`` restores a previously captured sheet byte-for-byte.
    Otherwise a caller-owned RNG is used, or a stateless seed+epoch RNG makes
    each packet independently replayable.
    """
    cal = dict(calibration or {})
    if not bool(cal.get("photon_sheet", False)):
        return
    n_az = int(cal.get("retina_n_az", cal.get("retina_w",
                                              DEFAULT_PHOTON_N_AZ)))
    n_el = int(cal.get("retina_n_el", cal.get("retina_h",
                                              DEFAULT_PHOTON_N_EL)))
    if n_az <= 0 or n_el <= 0:
        raise ValueError("photon-sheet dimensions must be positive")
    sensor_epoch = int(epoch)
    if counts is None:
        if screen is None:
            counts = np.zeros((n_el, n_az), dtype=np.int64)
        else:
            if str(cal.get("retinal_layout", "uniform")).lower() in (
                    "foveated", "fovea_logpolar", "log_polar"):
                # Mechanical optics: the graph selected the gaze and the world
                # applies that command to the canonical receptor apparatus. No
                # salience, target selection, or fallback is performed here.
                from domains.photon_eye import receptor_layout_from_calibration

                layout = receptor_layout
                if layout is None:
                    layout = receptor_layout_from_calibration(cal, n_az, n_el)
                luma = dpw.luma_layout(
                    screen, layout, n_el=n_el, n_az=n_az,
                    fov_h_deg=float(cal.get("fov_h_deg", 90.0)),
                    fov_v_deg=float(cal.get("fov_v_deg", 60.0)))
            else:
                luma = dpw.luma_grid(screen, n_el, n_az)
            photon_rng = rng
            if photon_rng is None and bool(cal.get("photon_poisson", True)):
                seed = int(cal.get("photon_seed", DEFAULT_PHOTON_SEED))
                photon_rng = np.random.default_rng(
                    np.random.SeedSequence([seed, sensor_epoch]))
            counts = dpw.photon_counts(
                luma, photon_rng, gain=float(cal.get("photon_gain", 1.0)))
    counts = np.asarray(counts, dtype=np.int64)
    if counts.shape != (n_el, n_az):
        raise ValueError(
            "photon count grid shape %r does not match configured (%d, %d)"
            % (counts.shape, n_el, n_az))
    if packets is None and packetize:
        packets = dpw.packets_from_counts(counts)
    sub.vision_photon_counts = counts
    sub.vision_photon_packets = (
        None if packets is None else list(packets))
    sub.vision_photon_epoch = sensor_epoch


def observation_packet(sub,ctx,tic):
    body=next(n for n in sub.graph.nodes() if n.type=="Body")
    compact_photons = (
        hasattr(sub, "vision_photon_counts")
        and getattr(sub, "vision_photon_packets", None) is None
    )
    packet={"tic":int(tic),"body":dict(body.attrs),"ctx":dict(ctx),
            # In compact photon mode the child has already performed the
            # mechanical camera->count transduction.  Do not also copy the
            # 640x480 RGB source through IPC; cognition consumes the exact
            # count sheet below and recording remains in the world process.
            "screen":None if compact_photons else sub.vision_screen,
            "vision_calibration":dict(getattr(sub,"vision_calibration",{}))}
    if hasattr(sub,"vision_photon_counts"):
        packet.update({
            "vision_photon_counts":np.array(sub.vision_photon_counts, copy=True),
            "vision_photon_epoch":int(sub.vision_photon_epoch),
        })
        if getattr(sub, "vision_photon_packets", None) is not None:
            packet["vision_photon_packets"] = list(sub.vision_photon_packets)
    return packet

def substrate_from_packet(packet,prev_cell=None,prev_pose=None,photon_rng=None):
    g=TypedGraph();attrs=dict(packet["body"]);attrs["id"]="agent_self"
    body=g._insert_node("Body",attrs)
    realm=g._insert_node("Realm",{"id":"realm","name":"Doom"})
    g._insert_edge(body,"inhabits",realm)
    cell=(int(attrs["x_bin"]),int(attrs["y_bin"]),int(attrs["z_bin"]))
    cur=g._insert_node("SpatialLocation",{"id":"%d_%d_%d"%cell,
        "x_bin":cell[0],"y_bin":cell[1],"z_bin":cell[2]})
    g._insert_edge(body,"at_location",cur)
    if prev_cell is not None and prev_cell!=cell:
        prev=g._insert_node("SpatialLocation",{"id":"%d_%d_%d"%prev_cell,
            "x_bin":prev_cell[0],"y_bin":prev_cell[1],"z_bin":prev_cell[2]})
        g._insert_edge(prev,"adjacent_to",cur)
    sub=Substrate(graph=g,checker=ConsistencyChecker(Grammar([])))
    sub.vision_screen=packet["screen"];sub.vision_frame=None
    source_epoch=int(packet.get("vision_photon_epoch", packet.get("tic", 0)))
    pose=(float(attrs["x"]),float(attrs["y"]),float(attrs["angle"]),source_epoch)
    translation=0.0 if prev_pose is None else (
        (pose[0]-prev_pose[0])**2+(pose[1]-prev_pose[1])**2)**0.5
    source_epoch_delta=1 if prev_pose is None or len(prev_pose)<4 else max(
        1, source_epoch-int(prev_pose[3]))
    rotation=0.0 if prev_pose is None or len(prev_pose)<3 else (
        (pose[2]-float(prev_pose[2])+180.0)%360.0-180.0)
    cal=dict(packet.get("vision_calibration") or {
        "modality":"camera","oracle_buffers":False,"worker_capacity":4})
    cal["efference_translation"]=translation
    cal["source_epoch_delta"]=source_epoch_delta
    cal["efference_translation_per_source_epoch"]=(
        translation/source_epoch_delta)
    cal["efference_rotation_deg"]=rotation
    cal["efference_rotation_deg_per_source_epoch"]=(
        rotation/source_epoch_delta)
    cal["proprio_x_world"]=pose[0]
    cal["proprio_y_world"]=pose[1]
    cal["proprio_angle_deg"]=pose[2]
    fov_h_deg=float(cal.get("fov_h_deg", cal.get("camera_fov_deg", 90.0)))
    n_az=int(cal.get("retina_n_az", cal.get("retina_w", DEFAULT_PHOTON_N_AZ)))
    cal["retina_focal_cells"]=(0.5*n_az)/math.tan(
        0.5*math.radians(fov_h_deg))
    sub.vision_calibration=cal
    _publish_photon_sheet(
        sub, sub.vision_screen, cal,
        epoch=source_epoch,
        rng=photon_rng, counts=packet.get("vision_photon_counts"),
        packets=packet.get("vision_photon_packets"))
    return sub,cell,pose


class DoomWorld:
    def __init__(self, wad=DEFAULT_WAD, doom_map="E1M1", ticks_per_action=4,
                 depth_scale=6.5, wall_clearance=8.0, observation_radius=1024.0,
                 res=vzd.ScreenResolution.RES_640X480, recorder=None,
                 visible=True, realtime=True, ticrate=35,
                 auto_restart=True, oracle_buffers=False,
                 ingest_oracle_objects=False, worker_capacity=4,
                 retina_tick_hz=120.0, photon_sheet=False,
                 photon_n_az=DEFAULT_PHOTON_N_AZ,
                 photon_n_el=DEFAULT_PHOTON_N_EL, photon_gain=1.0,
                 photon_seed=DEFAULT_PHOTON_SEED, photon_rng=None,
                 photon_poisson=True, photon_eye_context=None,
                 photon_packetize=True):
        self.map_name = doom_map
        self.ticks_per_action = ticks_per_action
        self.depth_scale = depth_scale
        self.wall_clearance = wall_clearance
        self.observation_radius = observation_radius
        self.recorder = recorder
        self.visible = bool(visible)
        self.realtime = bool(realtime)
        self.ticrate = int(ticrate)
        self.auto_restart = bool(auto_restart)
        self.oracle_buffers = bool(oracle_buffers)
        self.ingest_oracle_objects = bool(ingest_oracle_objects)
        self.worker_capacity = int(worker_capacity)
        self.retina_tick_hz = float(retina_tick_hz)
        self.photon_sheet = bool(photon_sheet)
        self.photon_n_az = int(photon_n_az)
        self.photon_n_el = int(photon_n_el)
        if self.photon_n_az <= 0 or self.photon_n_el <= 0:
            raise ValueError("photon-sheet dimensions must be positive")
        self.photon_gain = float(photon_gain)
        self.photon_seed = int(photon_seed)
        self.photon_rng = photon_rng
        self.photon_poisson = bool(photon_poisson)
        self.photon_eye_context = dict(photon_eye_context or {})
        # Physical eye-actuator state. The graph emits the command; this world
        # boundary merely retains the enacted gaze between one-tic pulses, just
        # as ViZDoom retains the body pose produced by a motor command.
        self._eye_gaze_az_deg = float(
            self.photon_eye_context.get("gaze_az_deg", 0.0))
        self._eye_gaze_el_deg = float(
            self.photon_eye_context.get("gaze_el_deg", 0.0))
        self._eye_motor_command = {
            "eye_motor_active": 0.0,
            "eye_motor_source_epoch": -1,
            "eye_motor_target_column": -1,
            "eye_motor_target_row": -1,
            "eye_motor_target_az_deg": self._eye_gaze_az_deg,
            "eye_motor_target_el_deg": self._eye_gaze_el_deg,
            "eye_motor_fixation_epoch": -1,
            "eye_motor_duration_tics": 0,
            "eye_motor_status": "refused",
        }
        self._photon_layout_signature = None
        self._photon_receptor_layout = None
        self.photon_packetize = bool(photon_packetize)
        # Epoch zero is the graph's "not yet observed" sentinel.
        self._photon_epoch = 1
        self._next_tic_deadline = None
        self._closed = False
        g = vzd.DoomGame()
        g.set_doom_game_path(wad)
        g.set_doom_scenario_path(wad)
        g.set_doom_map(doom_map)
        g.set_screen_resolution(res)
        g.set_screen_format(vzd.ScreenFormat.RGB24)
        g.set_render_hud(True)
        g.set_render_weapon(True)
        g.set_depth_buffer_enabled(self.oracle_buffers)
        g.set_labels_buffer_enabled(self.oracle_buffers)
        gv = vzd.GameVariable
        for v in (gv.POSITION_X, gv.POSITION_Y, gv.POSITION_Z, gv.ANGLE, gv.HEALTH,
                  gv.ARMOR, gv.SELECTED_WEAPON_AMMO, gv.KILLCOUNT, gv.DAMAGE_TAKEN):
            g.add_available_game_variable(v)
        for name in _BTN_ORDER:
            g.add_available_button(getattr(vzd.Button, {
                "forward": "MOVE_FORWARD", "backward": "MOVE_BACKWARD",
                "turn_left": "TURN_LEFT", "turn_right": "TURN_RIGHT",
                "attack": "ATTACK", "use": "USE",
                "strafe_left": "MOVE_LEFT", "strafe_right": "MOVE_RIGHT"}[name]))
        g.set_window_visible(self.visible)
        g.set_mode(vzd.Mode.PLAYER)
        g.set_ticrate(self.ticrate)
        g.set_living_reward(0.0)
        g.set_death_penalty(0.0)
        g.init()
        self._game = g
        self._gv = gv
        self._prev_loc_cell = None
        self._prev_pose = None
        self._prev_angle = None

    # -- INGEST: current game state -> typed graph + optic side-channels ----
    def _build_substrate(self):
        gv, G = self._gv, self._game
        g = TypedGraph()
        px = G.get_game_variable(gv.POSITION_X); py = G.get_game_variable(gv.POSITION_Y)
        pz = G.get_game_variable(gv.POSITION_Z); angle = G.get_game_variable(gv.ANGLE)
        health = G.get_game_variable(gv.HEALTH); armor = G.get_game_variable(gv.ARMOR)
        translation = 0.0 if self._prev_pose is None else (
            (px - self._prev_pose[0]) ** 2 + (py - self._prev_pose[1]) ** 2
        ) ** 0.5
        self._prev_pose = (px, py)
        rotation = 0.0 if self._prev_angle is None else (
            (angle - self._prev_angle + 180.0) % 360.0 - 180.0)
        self._prev_angle = angle
        ammo = G.get_game_variable(gv.SELECTED_WEAPON_AMMO)
        body = g._insert_node("Body", {
            "id": "agent_self", "x": round(px, 1), "y": round(py, 1), "z": round(pz, 1),
            "x_bin": int(px // 64), "y_bin": int(py // 64), "z_bin": int(pz // 64),
            "angle": round(angle % 360, 1),
            "health": float(health), "armor": float(armor),
            "ammo": float(ammo),
            "damage_taken": float(G.get_game_variable(gv.DAMAGE_TAKEN)),
            "killcount": float(G.get_game_variable(gv.KILLCOUNT)),
            "health_bin": int(health // 25), "armor_bin": int(armor // 25),
            "ammo_bin": min(int(ammo // 10), 10), "alive": health > 0})
        realm = g._insert_node("Realm", {"id": "realm", "name": "Doom", "map": self.map_name})
        g._insert_edge(body, "inhabits", realm)
        # local spatial topology (the transition the agent's map accumulates)
        cell = (int(px // 64), int(py // 64), int(pz // 64))
        cur = g._insert_node("SpatialLocation", {"id": "%d_%d_%d" % cell,
                                                 "x_bin": cell[0], "y_bin": cell[1], "z_bin": cell[2]})
        g._insert_edge(body, "at_location", cur)
        if self._prev_loc_cell is not None and self._prev_loc_cell != cell:
            pv = g._insert_node("SpatialLocation", {"id": "%d_%d_%d" % self._prev_loc_cell,
                                                    "x_bin": self._prev_loc_cell[0],
                                                    "y_bin": self._prev_loc_cell[1],
                                                    "z_bin": self._prev_loc_cell[2]})
            g._insert_edge(pv, "adjacent_to", cur)
        self._prev_loc_cell = cell
        # Labels are an optional scoring oracle, never part of autonomous play.
        st = G.get_state()
        if self.oracle_buffers and self.ingest_oracle_objects and st is not None and st.labels:
            for lab in st.labels:
                name = lab.object_name or "UnknownObject"
                if name == "DoomPlayer":
                    continue          # that's the marine itself, already the Body
                ox, oy = lab.object_position_x, lab.object_position_y
                if ((ox - px) ** 2 + (oy - py) ** 2) ** 0.5 > self.observation_radius:
                    continue
                oid = g._insert_node(name, {"id": "obj_%d" % lab.object_id,
                                            "x": round(ox, 1), "y": round(oy, 1),
                                            "x_bin": int(ox // 64), "y_bin": int(oy // 64)})
                g._insert_edge(body, "sees", oid)
        sub = Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))
        # OPTIC SIDE-CHANNEL — RGB radiance only. Pose/body state above is
        # proprioception, not vision. Depth/labels never enter this substrate.
        sub.vision_screen = st.screen_buffer if st is not None else None
        sub.vision_frame = None
        sub.vision_calibration = {
            "modality": "camera", "oracle_buffers": False,
            "worker_capacity": self.worker_capacity,
            "retina_tick_hz": self.retina_tick_hz,
            "efference_translation": float(translation),
            "source_epoch_delta": 1,
            "efference_translation_per_source_epoch": float(translation),
            "efference_rotation_deg": float(rotation),
            "efference_rotation_deg_per_source_epoch": float(rotation),
            "proprio_x_world": float(px),
            "proprio_y_world": float(py),
            "proprio_angle_deg": float(angle % 360),
            "fov_h_deg": 90.0,
            "photon_sheet": self.photon_sheet,
            "retina_2d": self.photon_sheet,
            "retina_n_az": self.photon_n_az,
            "retina_n_el": self.photon_n_el,
            "retina_w": self.photon_n_az,
            "retina_h": self.photon_n_el,
            "photon_gain": self.photon_gain,
            "photon_seed": self.photon_seed,
            "photon_poisson": self.photon_poisson,
            "photon_packet_format": "col_row_wavelength_nm_count",
        }
        if st is not None and st.screen_buffer is not None:
            screen_shape = st.screen_buffer.shape
            sub.vision_calibration["source_width"] = int(screen_shape[1])
            sub.vision_calibration["source_height"] = int(screen_shape[0])
        if self.photon_sheet:
            # Apparatus configuration supplied by the caller. Sensor identity,
            # geometry, and oracle refusal above remain authoritative.
            reserved = {
                "photon_sheet", "retina_2d", "retina_n_az", "retina_n_el",
                "retina_w", "retina_h", "oracle_buffers",
            }
            sub.vision_calibration.update({
                key: value for key, value in self.photon_eye_context.items()
                if key not in reserved
            })
            # The current physical pointing direction is a property of the
            # enacted optical apparatus. Cognitive selection happened before
            # this command crossed the boundary.
            sub.vision_calibration.update(self._eye_motor_command)
            sub.vision_calibration["gaze_az_deg"] = self._eye_gaze_az_deg
            sub.vision_calibration["gaze_el_deg"] = self._eye_gaze_el_deg
        # Pinhole calibration in receptor-cell units. This happens after the
        # caller's apparatus context is applied, so a non-90-degree eye never
        # inherits the 90-degree n_az/2 coincidence.
        fov_h_deg = float(sub.vision_calibration.get("fov_h_deg", 90.0))
        sub.vision_calibration["retina_focal_cells"] = (
            0.5 * self.photon_n_az
            / math.tan(0.5 * math.radians(fov_h_deg)))
        receptor_layout = None
        if str(sub.vision_calibration.get(
                "retinal_layout", "uniform")).lower() in (
                    "foveated", "fovea_logpolar", "log_polar"):
            layout_signature = _retinal_layout_signature(
                sub.vision_calibration)
            if layout_signature != self._photon_layout_signature:
                from domains.photon_eye import receptor_layout_from_calibration

                self._photon_receptor_layout = (
                    receptor_layout_from_calibration(
                        sub.vision_calibration,
                        self.photon_n_az, self.photon_n_el))
                self._photon_layout_signature = layout_signature
            receptor_layout = self._photon_receptor_layout
        _publish_photon_sheet(
            sub, sub.vision_screen, sub.vision_calibration,
            epoch=self._photon_epoch, rng=self.photon_rng,
            packetize=self.photon_packetize,
            receptor_layout=receptor_layout)
        if self.photon_sheet:
            self._photon_epoch += 1
        return sub

    def apply_eye_motor_command(self, command):
        """Mechanically enact one graph-issued eye command.

        An inactive command means "no new pulse", not "teleport to centre".
        The physical gaze therefore persists until the graph emits a new
        command, exactly like a body or camera actuator.
        """
        if command is None:
            return
        copied = {
            "eye_motor_active": float(command.get("eye_motor_active", 0.0)),
            "eye_motor_source_epoch":
                int(command.get("eye_motor_source_epoch", -1)),
            "eye_motor_target_column":
                int(command.get("eye_motor_target_column", -1)),
            "eye_motor_target_row":
                int(command.get("eye_motor_target_row", -1)),
            "eye_motor_target_az_deg":
                float(command.get(
                    "eye_motor_target_az_deg", self._eye_gaze_az_deg)),
            "eye_motor_target_el_deg":
                float(command.get(
                    "eye_motor_target_el_deg", self._eye_gaze_el_deg)),
            "eye_motor_fixation_epoch":
                int(command.get("eye_motor_fixation_epoch", -1)),
            "eye_motor_duration_tics":
                int(command.get("eye_motor_duration_tics", 0)),
            "eye_motor_status":
                str(command.get("eye_motor_status", "refused")),
        }
        self._eye_motor_command = copied
        if copied["eye_motor_active"] == 1.0:
            self._eye_gaze_az_deg = copied["eye_motor_target_az_deg"]
            self._eye_gaze_el_deg = copied["eye_motor_target_el_deg"]

    def screen(self):
        st = self._game.get_state()
        return None if st is None else st.screen_buffer

    def _capture(self):
        if self.recorder is not None:
            fr = self.screen()
            if fr is not None:
                self.recorder(fr)

    # -- world-dict interface (the WorldAdapter live loop consumes this) ----
    def reset(self):
        self._game.new_episode()
        self._prev_loc_cell = None
        self._prev_pose = None
        self._prev_angle = None
        self._photon_epoch = 1
        self._next_tic_deadline = time.monotonic()
        self._capture()
        return self._build_substrate(), {"model_tick": 0, "deaths": 0}

    def legal_actions(self, sub, ctx):
        return list(_ACTIONS)

    def interpret_acts_on(self, sub, ctx, action):
        return ["Body"]

    def apply_action(self, sub, ctx, action):
        for _ in range(self.ticks_per_action):
            if not self.step_tic(action):
                break
        respawned = False
        if self._game.is_player_dead() or self._game.is_episode_finished():
            if self.auto_restart and self.is_running():
                self._game.new_episode()
                self._prev_loc_cell = None
                self._prev_pose = None
                self._prev_angle = None
                respawned = True
            else:
                return sub, {**ctx, "terminal": True, "respawned": False}
        return self._build_substrate(), {"model_tick": ctx.get("model_tick", 0) + 1,
                                         "deaths": ctx.get("deaths", 0) + (1 if respawned else 0),
                                         "last_action": action, "respawned": respawned}

    def step_tic(self, action=("noop",)):
        """Apply exactly one expiring control pulse and optionally pace to ticrate."""
        if not self.is_running() or self._game.is_player_dead() or self._game.is_episode_finished():
            return False
        buttons = _action_to_buttons(action or ("noop",))
        self._game.make_action(buttons, 1)
        self._capture()
        if self.realtime:
            period = 1.0 / max(1, self.ticrate)
            now = time.monotonic()
            deadline = self._next_tic_deadline
            if deadline is None or now - deadline > period:
                deadline = now
            deadline += period
            self._next_tic_deadline = deadline
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
        return True

    def pause(self):
        """Synchronous PLAYER pause: intentionally advance zero game tics."""
        self._next_tic_deadline = time.monotonic()

    def is_running(self):
        return not self._closed and bool(self._game.is_running())

    def effect_footprint(self, sub, ctx, action):
        return affordance_footprint(action)

    def release_action(self):
        if self.is_running():
            self._game.set_action(_action_to_buttons(("noop",)))

    def close(self):
        if self._closed:
            return
        if not self._game.is_player_dead() and not self._game.is_episode_finished():
            self.release_action()
        self._closed = True
        try:
            self._game.close()
        except Exception:
            pass


def make_world(recorder=None, **kw):
    w = DoomWorld(recorder=recorder, **kw)
    return w, {"name": "doom_e1m1", "preview_safe": False,
               "reset": w.reset, "legal_actions": w.legal_actions,
               "apply_action": w.apply_action,
               "interpret_acts_on": w.interpret_acts_on,
               "effect_footprint": w.effect_footprint,
               "is_running": w.is_running}
