"""seeds/grid_navigation.json — the jabberwock's GRAPH-NATIVE nav + exploration faculty. The host keeps ONLY
mechanical perception (measure the avatar body, fire slide_flood, stamp `fresh`, read chosen_action); every
DECISION is a rule here, matched over the `reached` set (~100 cells), so it stays microseconds.

EXPLORATION POLICY (progress -> abandon -> quarantine -> reopen), adapted from the older feature_navigation
pattern to the cell/`committed_goal` mechanism. ls20 is a DYNAMIC sliding puzzle: the value-9 movers shift the
reachable frontier every tick, so the old "release the goal whenever it falls out of this frame's flood" thrashed
(commit-near -> stale -> release -> re-commit -> oscillate forever, 0 coverage). The fix is COMMITMENT with
progress-based abandon: hold the goal across frames; release only when REACHED (visited) or STUCK (no new
coverage for K frames); on stuck, QUARANTINE that frontier (abandoned, with a frame stamp) so select picks a
different one; reopen abandoned cells after Q frames so a later world-state can retry them."""
import json
def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def ADD(a, b): return {"type": "Plus", "items": [a, b]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NEQ(a, b): return {"type": "Not", "arg": EQ(a, b)}
def NOT(x): return {"type": "Not", "arg": x}
def LT(a, b): return {"type": "Lt", "a": a, "b": b}
def GT(a, b): return {"type": "Gt", "a": a, "b": b}
def GTE(a, b): return {"type": "Gte", "a": a, "b": b}
def AND(*xs): return {"type": "And", "items": list(xs)}
def OR(*xs): return {"type": "Or", "items": list(xs)}
def MINUS(a, b): return {"type": "Minus", "a": a, "b": b}
def ITE(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def NEIGH(var, et): return {"type": "Neighbours", "node": V(var), "edge_type": et, "any_type": False}
def FILTER(s, v, p): return {"type": "Filter", "source": s, "var_name": v, "predicate": p}
def MINOVER(s, v, val, d): return {"type": "MinOver", "source": s, "var_name": v, "value": val, "default": d}
def MAXOVER(s, v, val, d): return {"type": "MaxOver", "source": s, "var_name": v, "value": val, "default": d}
def ARGMIN(s, v, val, d): return {"type": "Argmin", "source": s, "var_name": v, "value": val, "default": d}
def ARGMAX(s, v, val, d): return {"type": "Argmax", "source": s, "var_name": v, "value": val, "default": d}
def EXISTS(s, v): return {"type": "Exists", "source": s, "var_name": v, "predicate": L(True)}
def T(x): return {"__term__": x}
BIG = 1000000.0
K_STUCK = 3.0        # abandon a goal after this many frames with no NEW cell covered (frontier_seek)
K_PATIENT = 8.0      # ... but in mover_avoid mode, hold the goal longer (let the churn settle)
Q_QUARANTINE = 12.0  # reopen an abandoned frontier cell after this many frames (dynamics may have changed)
K_ESC = 4.0          # confinement: no new coverage for this many frames -> pocket_escape mode activates
K_FLUX = 10.0        # frontier flux: this many reached-cells churning move-to-move -> mover_avoid activates
is_av = lambda v: EQ(P0(V(v), "is_avatar_cell"), L(1.0))
mode_is = lambda m: EQ(A(V("game"), "nav_mode"), L(m))   # nav_mode is a STRING -> plain Attr (P0 would coerce to 0)
# explorable = reached, not yet covered, not currently quarantined.
explorable = FILTER(NEIGH("game", "reached"), "C",
    AND(NEQ(P0(V("C"), "visited"), L(1.0)), NEQ(P0(V("C"), "abandoned"), L(1.0))))

# 1. mark_visited_self: the avatar's cell -> visited.
mark_visited_self = {
    "name": "mark_visited_self", "match": [["game", "reached", "A"]],
    "where": is_av("A"), "effects": [["set_attr", "A", "visited", 1.0]]}
# 2. mark_visited_footprint: the avatar cell's 1-neighbours (its blob footprint) -> visited. Rides the ~100
#    `reached` set to bind A (the unique avatar cell), THEN expands A's ~4 neighbours.
mark_visited_footprint = {
    "name": "mark_visited_footprint", "match": [["game", "reached", "A"], ["A", "neighbour", "n"]],
    "where": is_av("A"), "effects": [["set_attr", "n", "visited", 1.0]]}
# 3. cover_tick: ONCE PER FRAME (guarded by cover_stamp == flood_epoch, so it can't race-increment across the
#    many fixpoint passes), advance the no-progress counter: reset to 0 if the avatar landed on a FRESH cell
#    this frame (`game.fresh`, stamped by the host from the pre-mark visited state), else +1. This is the
#    coverage-progress signal the abandon rule reads.
cover_tick = {
    "name": "cover_tick", "match": [["game", "reached", "A"]],
    "where": AND(is_av("A"), NEQ(P0(V("game"), "cover_stamp"), P0(V("game"), "flood_epoch"))),
    "effects": [
        ["set_attr", "game", "cover_stuck",
            T(ITE(EQ(P0(V("game"), "fresh"), L(1.0)), L(0.0), ADD(P0(V("game"), "cover_stuck"), L(1.0))))],
        ["set_attr", "game", "cover_stamp", T(P0(V("game"), "flood_epoch"))]]}
# 4. goal_abandon: the committed goal has gone K frames without yielding new coverage -> quarantine it
#    (abandoned + frame stamp) and drop the commitment. Reset cover_stuck to 0 so the NEXT goal gets a fresh
#    K-frame chance (and so this rule can't cascade-abandon every frontier in one fixpoint).
goal_abandon = {
    "name": "goal_abandon", "match": [["game", "committed_goal", "G"]],
    "where": GTE(P0(V("game"), "cover_stuck"),
                 ITE(mode_is("mover_avoid"), L(K_PATIENT), L(K_STUCK))),   # mover_avoid holds the goal longer
    "effects": [
        ["set_attr", "G", "abandoned", 1.0],
        ["set_attr", "G", "abandon_frame", T(P0(V("game"), "flood_epoch"))],
        ["del_edge", "game", "committed_goal", "G"],
        ["set_attr", "G", "committed", 0.0],
        ["set_attr", "game", "cover_stuck", 0.0]]}
# 5. release_goal: drop the commitment when its cell is REACHED (visited) or has been ABANDONED. NOTE: NO
#    transient-staleness clause anymore — in a dynamic world the goal falling out of one frame's flood is not
#    a reason to abandon; that caused the per-frame thrash. Loss-of-progress is handled by goal_abandon.
release_goal = {
    "name": "release_goal", "match": [["game", "committed_goal", "G"]],
    "where": OR(EQ(P0(V("G"), "visited"), L(1.0)), EQ(P0(V("G"), "abandoned"), L(1.0))),
    "effects": [["del_edge", "game", "committed_goal", "G"], ["set_attr", "G", "committed", 0.0]]}
# --- THE JABBERWOCK'S OWN SHAPE: navigation-mode selection is WINNER-TAKE-ALL (categorise_by_shape ->
#     competitive_inhibition). Each NavMode competitor holds an `activation` the SITUATION drives; the Argmax
#     winner becomes game.nav_mode; the winning mode GATES which behaviour runs. ---
# 6a-c. activate_<mode>: drive each competitor's activation from a situation signal (bind game + the mode via
#       the host-wired has_mode edge). Magnitudes encode the priority the agent regulates by: a confining
#       situation (pocket_escape, 2.0) outranks churn (mover_avoid, 1.0) outranks the baseline explorer (0.5).
activate_pocket = {
    "name": "activate_pocket_escape", "match": [["game", "has_mode", "m"]],
    "where": EQ(A(V("m"), "name"), L("pocket_escape")),
    "effects": [["set_attr", "m", "activation",
                 T(ITE(GTE(P0(V("game"), "cover_stuck"), L(K_ESC)), L(2.0), L(0.0)))]]}
activate_mover = {
    "name": "activate_mover_avoid", "match": [["game", "has_mode", "m"]],
    "where": EQ(A(V("m"), "name"), L("mover_avoid")),
    "effects": [["set_attr", "m", "activation",
                 T(ITE(GTE(P0(V("game"), "frontier_flux"), L(K_FLUX)), L(1.0), L(0.0)))]]}
activate_seek = {
    "name": "activate_frontier_seek", "match": [["game", "has_mode", "m"]],
    "where": EQ(A(V("m"), "name"), L("frontier_seek")),
    "effects": [["set_attr", "m", "activation", 0.5]]}
# 7. select_mode: WINNER-TAKE-ALL. game.nav_mode = the name of the Argmax-activation NavMode. Binds game via
#    the avatar; Argmax over the has_mode competitors by activation.
winner = ARGMAX(NEIGH("game", "has_mode"), "m", P0(V("m"), "activation"), V("A"))
select_mode = {
    "name": "select_mode", "match": [["game", "reached", "A"]],
    "where": is_av("A"), "effects": [["set_attr", "game", "nav_mode", T(A(winner, "name"))]]}
# 8a. select_seek: frontier_seek / mover_avoid -> commit the NEAREST explorable cell (always genuinely
#     reachable in the dynamic floods). Gated OFF in pocket_escape.
select_seek = {
    "name": "select_seek", "match": [["game", "reached", "c"]],
    "where": AND(NOT(EXISTS(NEIGH("game", "committed_goal"), "_g")),
                 NOT(mode_is("pocket_escape")),
                 NEQ(P0(V("c"), "visited"), L(1.0)),
                 NEQ(P0(V("c"), "abandoned"), L(1.0)),
                 EQ(P0(V("c"), "_adist"), MINOVER(explorable, "C", P0(V("C"), "_adist"), L(BIG)))),
    "effects": [["add_edge", "game", "committed_goal", "c"], ["set_attr", "c", "committed", 1.0]]}
# 8b. select_escape: pocket_escape -> commit the FARTHEST explorable cell, driving the avatar toward the
#     region EDGE to break out of the pocket (the host also clears stale blocks in this mode).
select_escape = {
    "name": "select_escape", "match": [["game", "reached", "c"]],
    "where": AND(NOT(EXISTS(NEIGH("game", "committed_goal"), "_g")),
                 mode_is("pocket_escape"),
                 NEQ(P0(V("c"), "visited"), L(1.0)),
                 NEQ(P0(V("c"), "abandoned"), L(1.0)),
                 EQ(P0(V("c"), "_adist"), MAXOVER(explorable, "C", P0(V("C"), "_adist"), L(0.0)))),
    "effects": [["add_edge", "game", "committed_goal", "c"], ["set_attr", "c", "committed", 1.0]]}
# 7. reopen_abandoned: lift the quarantine on a frontier cell after Q frames (the dynamic world may have opened
#    a path since). Matched over the bounded `reached` set, not all cells.
reopen_abandoned = {
    "name": "reopen_abandoned", "match": [["game", "reached", "C"]],
    "where": AND(EQ(P0(V("C"), "abandoned"), L(1.0)),
                 GTE(MINUS(P0(V("game"), "flood_epoch"), P0(V("C"), "abandon_frame")), L(Q_QUARANTINE))),
    "effects": [["set_attr", "C", "abandoned", 0.0]]}
# 8. hop_descend_gradient: after the goal flood (`_dist` = distance-to-goal), press toward the avatar's true
#    direct slide-neighbour (avatar-flood `_adist`==1, current epoch) with the lowest goal `_dist`. Restricting
#    to `_adist`==1 keeps only REAL one-slide moves -> never a blocked press. cardinal = sign(neighbour - avatar).
direct_neighbours = FILTER(NEIGH("game", "reached"), "n",
    AND(EQ(P0(V("n"), "_adist"), L(1.0)), EQ(P0(V("n"), "_epoch"), P0(V("game"), "flood_epoch"))))
B = ARGMIN(direct_neighbours, "n", P0(V("n"), "_dist"), V("A"))
dr = MINUS(A(B, "row"), P0(V("A"), "row")); dc = MINUS(A(B, "col"), P0(V("A"), "col"))
cardinal = ITE(LT(dr, L(0)), L("Up"), ITE(GT(dr, L(0)), L("Down"),
              ITE(LT(dc, L(0)), L("Left"), ITE(GT(dc, L(0)), L("Right"), L("")))))
hop_descend_gradient = {
    "name": "hop_descend_gradient", "match": [["game", "reached", "A"]],
    "where": is_av("A"), "effects": [["set_attr", "game", "chosen_action", T(cardinal)]]}

rules = [mark_visited_self, mark_visited_footprint, cover_tick,
         activate_pocket, activate_mover, activate_seek, select_mode,   # WTA mode selection (the agent's shape)
         goal_abandon, release_goal, select_seek, select_escape, reopen_abandoned, hop_descend_gradient]
seed = {"id": "grid_navigation", "version": "1.0.0", "depends_on": ["navigation_modes"],
        "description": ("Graph-native grid nav + exploration + MODE SELECTION. The agent UNDERSTANDS navigation "
            "modes (navigation_modes concepts) and ACTIVELY CHOOSES between them by its own shape "
            "(winner-take-all): activate_<mode> drive each NavMode's activation from a situation signal "
            "(cover_stuck->pocket_escape, frontier_flux->mover_avoid, baseline->frontier_seek); select_mode is "
            "the Argmax winner -> game.nav_mode; the mode gates behaviour (select_seek=nearest when seeking, "
            "select_escape=farthest when escaping, goal_abandon patient in mover_avoid). Plus the exploration "
            "core: mark_visited, cover_tick, goal_abandon+reopen_abandoned (quarantine), release_goal (on "
            "reached/abandoned), hop_descend_gradient. Host: measure body, fire slide_flood, wire has_mode, "
            "stamp fresh+frontier_flux, clear blocks in pocket_escape, read chosen_action. Every decision is a rule."),
        "nodes": [], "edges": [], "productions": [], "concepts": [], "rules": rules}
json.dump(seed, open("seeds/grid_navigation.json", "w"), indent=1); json.load(open("seeds/grid_navigation.json"))
print("wrote seeds/grid_navigation.json:", [r["name"] for r in rules])
