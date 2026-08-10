"""A Tetris world for the world-understanding interface. Tetris is a deliberate STRESS TEST: unlike forage/snake
(navigate a locus to a goal location), it is placement/packing — the controllable locus is a FALLING piece;
ROTATE is a non-translation affordance (it transforms the piece's shape, not a point's position); the value
signal is LINES CLEARED (a configuration objective), not a location to reach; and gravity moves the piece
autonomously every tick. The world only provides observations (the grid) + affordances (the buttons); whether
the agent can do anything with it is the question.

Action map (ArcWorld names -> ARC actions -> Tetris effect; the agent learns the effects, not the names):
  Up=ACTION1 -> ROTATE   Down=ACTION2 -> soft drop   Left=ACTION3 -> move left   Right=ACTION4 -> move right
"""
from __future__ import annotations
import os, sys, random
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4

EMPTY, SETTLED, PIECE = 0, 5, 9
SHAPES=[[(0,0),(0,1),(1,0),(1,1)],            # O
        [(0,0),(1,0),(2,0),(3,0)],            # I
        [(0,0),(1,0),(2,0),(2,1)],            # L
        [(0,0),(0,1),(0,2),(1,1)]]            # T

class TetrisEnv(Arc3Env):
    game_id="tetris"; grid_h=16; grid_w=8
    def __init__(self, seed=3): self._rng=random.Random(seed); super().__init__()
    def _init_world(self):
        self._board=[[EMPTY]*self.grid_w for _ in range(self.grid_h)]
        self._score=0; self._grav=0; self._spawn()
    def _spawn(self):
        self._shape=list(self._rng.choice(SHAPES))
        self._pr,self._pc=0,self.grid_w//2-1
        if self._collides(self._shape,self._pr,self._pc): self._state=GameState.GAME_OVER
    def _cells(self,sh,pr,pc): return [(pr+dr,pc+dc) for (dr,dc) in sh]
    def _collides(self,sh,pr,pc):
        for (r,c) in self._cells(sh,pr,pc):
            if c<0 or c>=self.grid_w or r>=self.grid_h: return True
            if r>=0 and self._board[r][c]!=EMPTY: return True
        return False
    def _rotate(self,sh):
        rot=[(c,-r) for (r,c) in sh]; mr=min(r for r,c in rot); mc=min(c for r,c in rot)
        return [(r-mr,c-mc) for (r,c) in rot]
    def _settle(self):
        for (r,c) in self._cells(self._shape,self._pr,self._pc):
            if 0<=r<self.grid_h and 0<=c<self.grid_w: self._board[r][c]=SETTLED
        kept=[row for row in self._board if any(v==EMPTY for v in row)]
        cleared=self.grid_h-len(kept); self._score+=cleared
        self._board=[[EMPTY]*self.grid_w for _ in range(cleared)]+kept
        self._spawn()
    def _render(self):
        g=[row[:] for row in self._board]
        for (r,c) in self._cells(self._shape,self._pr,self._pc):
            if 0<=r<self.grid_h and 0<=c<self.grid_w: g[r][c]=PIECE
        return g
    def _apply(self, action, coord):
        if self._state==GameState.GAME_OVER: return
        if action==ACTION3 and not self._collides(self._shape,self._pr,self._pc-1): self._pc-=1
        elif action==ACTION4 and not self._collides(self._shape,self._pr,self._pc+1): self._pc+=1
        elif action==ACTION1:
            rs=self._rotate(self._shape)
            if not self._collides(rs,self._pr,self._pc): self._shape=rs
        elif action==ACTION2 and not self._collides(self._shape,self._pr+1,self._pc): self._pr+=1
        # gravity every 2 frames (gives the agent control frames in between)
        self._grav+=1
        if self._grav%2==0:
            if not self._collides(self._shape,self._pr+1,self._pc): self._pr+=1
            else: self._settle()
        if self._state!=GameState.GAME_OVER: self._state=GameState.NOT_FINISHED
