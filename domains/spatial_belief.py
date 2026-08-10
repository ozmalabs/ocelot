"""Mechanical vision/proprioception -> generic graph occupancy observations."""
from __future__ import annotations
import math
from substrate.seed_loader import manifest_for

class SpatialBeliefAdapter:
    def __init__(self,agent,*,cell_size=64.0,fov_deg=90.0,max_range_cells=16):
        self.agent=agent;self.s=agent.s;self.inner=agent.inner
        names={r.get("name") for r in self.inner.export_rules()}
        if "spatial_belief_free_new" not in names:
            self.inner.load_seed_manifest(manifest_for("spatial_belief_core"),agent.agent)
        self.cell_size=float(cell_size);self.fov=math.radians(float(fov_deg))
        self.max_range=int(max_range_cells)
        self.space=self.s.add_node("WorldInstance",{
            "world_type":"Game","spatial_belief":1.0,
            "body_w":1.0,"flood_epoch":0,"last_action":""})
        self.self_region=self.s.add_node("Region",{
            "is_self":1.0,"is_ground":0.0,"cy":0.0,"cx":0.0,
            "drow":0.0,"dcol":0.0,"respond_votes":2.0})
        self.inner.add_edge_unchecked(self.space,"has_region",self.self_region)
        self._prev_cell=None

    def record_action(self,name):
        self.inner.set_attr(self.space,"last_action",str(name))

    def ingest(self,pose,motion_depths):
        px,py,angle_deg=map(float,pose)
        cell=self.cell_size
        own=(int(math.floor(px/cell)),int(math.floor(py/cell)))
        observations=[(own,"walk")]
        prev=self._prev_cell or own
        self.inner.set_attr(self.self_region,"cy",float(own[0]))
        self.inner.set_attr(self.self_region,"cx",float(own[1]))
        self.inner.set_attr(self.self_region,"drow",float(own[0]-prev[0]))
        self.inner.set_attr(self.self_region,"dcol",float(own[1]-prev[1]))
        self._prev_cell=own
        facing=math.radians(angle_deg)
        for az_norm,depth in motion_depths:
            if depth is None or float(depth)<=0:continue
            distance=float(depth); steps=min(int(distance/cell),self.max_range)
            world_angle=facing+float(az_norm)*self.fov
            for step in range(1,steps+1):
                x=px+math.cos(world_angle)*step*cell
                y=py+math.sin(world_angle)*step*cell
                observations.append(((int(math.floor(x/cell)),int(math.floor(y/cell))),"seen_free"))
            if distance/cell<self.max_range:
                x=px+math.cos(world_angle)*distance
                y=py+math.sin(world_angle)*distance
                observations.append(((int(math.floor(x/cell)),int(math.floor(y/cell))),"seen_wall"))
        rank={"seen_free":0,"seen_wall":1,"walk":2};best={}
        for pos,src in observations:
            if pos not in best or rank[src]>rank[best[pos]]:best[pos]=src
        for pos,src in best.items():
            obs=self.s.add_node("ObsCell",{"pose":list(pos),"src":src})
            self.inner.add_edge_unchecked(self.space,"observed",obs)
        self.inner.run_rules()
        for obs in list(self.inner.neighbours(self.space,"observed")):
            self.inner.remove_node(obs)

    def cells(self):
        return {
            tuple(self.s.node(c)["attrs"]["pose"]):self.s.node(c)["attrs"]["value"]
            for c in self.inner.neighbours(self.space,"has_cell")}
