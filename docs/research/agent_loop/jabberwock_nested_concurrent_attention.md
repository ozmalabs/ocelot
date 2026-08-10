Builder — here's the design. I'll keep it at graph-altitude: reified nodes + edges, rules that fire on them, host calls named as impasses, everything else assembled from holdings. The thread I pull throughout: **per-binding work runs in parallel inside a worker; cross-binding composition happens at the serial fold** — which is exactly what `tick_threads` riding inside `master_tick` already gives me (parallel region-work, serial fold). Nesting and concurrency turn out to be the same shape twice.

---

## Framing: a binding is already a subgraph; nesting just lets a filler BE one

A `WorldBinding` today is a node with six `WorldRole` children, each `{status, confidence, filled_by, found_by, prior_from, reconcile}`. The only structural change nesting needs: **`filled_by` may point at a `WorldBinding` instead of (or alongside) a faculty.** Everything else is edges and rules. I do not need a new substrate for trees — a `WorldBinding` is a node, `parent_binding`/`bound_via_role` are edges, and the tree is just the transitive closure of those edges.

---

## (a) The WorldBinding TREE

### Structure

```
WorldBinding(root="Environment")  activation=active
  ├─ role controllable_locus  filled_by → WorldInstance(body)
  ├─ role affordance_effect   filled_by → WorldInstance(console)
  │     └─ opens → WorldBinding(child="Game")        ← the nesting edge
  │                  ├─ parent_binding → (root)
  │                  ├─ bound_via_role → (console's affordance role)
  │                  ├─ role controllable_locus filled_by → WorldInstance(avatar)
  │                  ├─ role value_signal ...
  │                  │     └─ rolls_up_to → (root.value_signal, transform=T)
  │                  └─ role terminal  escalation = contained | escalates
  ├─ role value_signal  ...
  ├─ role terminal  ...
  └─ role goal  filled_by → (Game.value_signal)      ← parent goal points DOWN
```

A role-filler becomes a child binding by **one rule**:

- **`open_child_binding`** — WHERE an `affordance_effect` role is enacted (its effect observed firing) AND that role carries an `opens_world` marker (seeded by the parent frame, or learned: "enacting this affordance produced a stream whose `stream_shape_signature` differs from the parent's"), THEN mint a child `WorldBinding`, run `categorise_by_shape` on the new stream → `BIND` a frame if one matches (priors seeded), else derive cold; wire `parent_binding`, `bound_via_role`, `opens`; set `activation=active`. This is just BIND fired from inside a parent role instead of from the top — same faculty, deeper in the tree. The console "opening the game" and the agent "first recognising the environment" are the identical motion.

The boundary affordances (`enter` while child dormant, `exit/return` while child active) are themselves reified `affordance_effect` rows on the parent — so "entering a sub-world is an affordance of the parent" is literally true in the data, not a special case.

### Composition up and down — four rules

1. **Value rolls UP.** `rollup_value` — WHERE child `value_signal = v` AND a `rolls_up_to` edge with transform `T` to the parent's `value_signal`, contribute `T(v)` to the parent value. `T` is *seeded by the parent frame* ("winning this minigame is worth a key") and *reconciled by observation* (`reconcile`: does parent score actually move when child value moves? if not, overwrite T). "Winning the child is value in the parent" = this edge. Critically, **rollup is applied at the serial fold**, never inside a worker — it's the one cross-binding write, so it can't race.

2. **Terminal MAY propagate.** `terminal_propagation` — each child terminal role carries an `escalation ∈ {escalates, contained}`, itself a reconcilable bit. WHERE child terminal fires AND `escalates` → fire the parent's terminal/consequence (dying in the environment ends everything). WHERE `contained` → deactivate only the child subtree, hand attention/worker back to the parent (losing a minigame drops you back to the overworld). The bit is *observed, not declared*: after a child terminal, did parent dynamics actually halt? If yes and we'd marked it contained, `reconcile` flips it to escalates. Evidence wins, as everywhere.

3. **Goal composes DOWN.** A parent goal_derive can target a child's `value_signal`/`terminal` as its objective ("my goal here is to win that game"). Achieving the child goal satisfies the parent subgoal that opened it. This is just `goal` pointing at a descendant role — no new machinery.

4. **Affordance composes by boundary.** The `opens`/`return` edges put "enter child" and "exit to parent" into the parent's affordance set automatically, so the action_selector sees them as ordinary moves.

### Suspend / resume a subtree

`activation ∈ {active, suspended_self, suspended_by_ancestor, dormant}`. A `propagate_suspension` rule: a binding whose ancestor is suspended becomes `suspended_by_ancestor` (distinct tag so resume restores correctly — only `suspended_self` clears on direct resume; ancestor-suspended children clear when the ancestor reactivates). **Suspension removes worker eligibility only — `filled_by`, `confidence`, learned reconciliations are untouched.** Resume = flip to active, eligible for a worker again, zero relearning. That's the whole point: roles stay BOUND, the subtree is frozen, not forgotten.

---

## (b) Worker-pool attention — NOT a serial head

The "~4" working-memory constant is deleted. It's replaced by a measured integer, `worker_slots`, recomputed every tick from real capacity.

### Introspect capacity as graph-readable signals

A `capacity_probe` adapter (mechanical host I/O — same category as reading audio bytes) writes a `SystemCapacity` node each tick:

```
SystemCapacity { cores_avail, mem_free_mb, budget_remaining, rate_headroom, ts }
```

Then a pure **graph rule** derives slots — no Python decision:

- **`derive_worker_slots`** — `worker_slots = Min( cores_avail, ⌊mem_free_mb / mem_per_worker⌋, ⌊budget_remaining / budget_per_worker⌋, ⌊rate_headroom / rate_per_worker⌋ )`. A `Min` over normalised Terms. The probe is host I/O; the *decision of how many workers* is graph data. As the machine grows, the probe reports more, `worker_slots` rises, attention widens — **no fixed cognitive constant, the agent scales to its body.**

### Allocate — reuse frontier-pick as the allocator

Each `active` binding emits a `WorkerRequest` with:

- **priority = urgency × value**
  - `value` = expected value at stake = the binding's value rolled to root terms (so a child's worth is its parent-discounted contribution — a binding nobody rolls up to is cheap to drop).
  - `urgency` = terminal-imminence + responsiveness-demand (a real-time game role demands fast ticks; async chat tolerates lag — that demand is a frame property).

The **autonomy frontier-pick already ranks axes/goals; I point it at `WorkerRequest`s instead of goals** — same proto-attention machinery, now choosing bindings. It sorts by priority and assigns the top `worker_slots` requests a worker each, fanned out via `tick_threads`/`_concurrency`. 

**Concurrency is the default:** when `active_bindings ≤ worker_slots`, every binding gets its own worker and they run genuinely in parallel — game-worker, chat-worker, environment-worker each running *that binding's subtick* (perceive→reconcile→navigate over its own subgraph) simultaneously. The teacher already spawns off-thread; this is the same fan-out, keyed by binding.

**Concurrency-safety falls out of the subgraph scoping:** a worker is scoped to its binding's subtree (binding node + roles + world instances). Disjoint subtrees → disjoint writes → no contention. The *only* cross-binding writes are the rollup/terminal-propagation edges, and those run **at the serial fold inside `master_tick`, after workers join** — exactly "tick_threads ride inside master_tick." Parallel per-binding, serial cross-binding. That barrier is the whole correctness argument.

### Granularity scales with slack

`slack = worker_slots − active_bindings`. When slack is positive, refine granularity: allocate a worker *per faculty per binding* (perceive ∥ induce ∥ navigate ∥ teacher) on the highest-priority bindings — finer parallelism the holdings already support (teacher-off-thread is this at granularity-1). When slack is zero/negative, coarsen back to one-worker-per-binding, then to time-slice. One knob, derived, no constant.

### Over capacity → degrade, never fail

When `active_bindings > worker_slots`: top `worker_slots` bindings keep **dedicated** workers; the remainder are handled by a single **time-slice worker** that round-robins them weighted by priority — or, for bindings below a `suspend_floor` priority, `suspend` them (roles stay bound, no tick). This is graceful by construction: you always make progress on the most urgent×valuable bindings, and the rest degrade to slower service or frozen-but-preserved. Never an error, just less parallelism.

### Backgrounded terminal INTERRUPTS — the hard part, solved with deduce

A suspended/time-sliced binding isn't ticking, so how does its imminent death pull a worker back? **Don't freeze the terminal clock — extrapolate it cheaply.** At suspend time the terminal role stores its last state (hazard N steps away). A tiny **`terminal_watch` rule runs in the allocator's own tick** (not in a worker) and rolls that state forward using the binding's *own dynamics postulates* — the `deduce` faculty, run cheaply, no perception needed: "M ticks elapsed, hazard now ~N−M away → imminence rising." When extrapolated imminence crosses a threshold:

- **`preempt_for_terminal`** — spike that binding's `urgency` to max → priority recompute → frontier-pick re-sorts → it preempts the lowest-priority *running* worker (or is promoted out of the time-slice pool into a dedicated slot). The displaced binding drops to time-slice/suspend in turn.

So a backgrounded game about to kill the avatar yanks a worker back *before* it dies, using the postulates it already induced — the watch is O(1) per suspended binding, runs every tick, costs no worker. This is the same deduce-a-death-never-suffered faculty from the postulate work, repurposed as the interrupt source.

---

## (c) Generic, no donkey, graceful — what's assembled vs. what I must ask for

**Assembled from holdings (no new primitive):**
- Tree structure, all four composition rules, suspension propagation — pure node/edge/rule data on the existing `WorldBinding`/`WorldRole` substrate.
- BIND/reconcile/categorise_by_shape per child binding — held, just fired deeper.
- Allocator = frontier-pick re-pointed at `WorkerRequest`s — held.
- Parallel execution + serial fold = `tick_threads`/`_concurrency` inside `master_tick` — held.
- Off-thread granularity = teacher-spawn pattern generalised — held.
- terminal_watch interrupt = `deduce` over held postulates — held.

**HumanImpasse — primitives I genuinely cannot synthesise:**

1. **`probe_system_capacity() → {cores_avail, mem_free_mb, budget_remaining, rate_headroom}`** — a thin host stat read (cores, RSS/free mem, token-budget counter, API-rate headroom). Mechanical adapter I/O, but it needs a real syscall/host hook I don't have a Term for. This is the one true new primitive. Everything downstream (`derive_worker_slots`) is graph rules over its output.

2. **`spawn_worker(binding_id)` / binding-keyed dispatch** — *possibly* not a full impasse. The holdings already fan out parallel workers and spawn the teacher off-thread; I believe this is a **small extension of `tick_threads`** (key the existing fan-out by `binding_id` + subgraph scope) rather than a new primitive. I'll attempt it as an assembly first and only escalate to impasse if `tick_threads` can't be scoped to a node-set. (If it can't, the ask is: `tick_region(seed_nodes, rule_ids) → joins at fold` — and note this is the *same* scoped-rollout primitive the postulate/deduce arena wanted, so it'd pay for two faculties.)

**Graceful-at-capacity** is structural, not bolted on: if the probe ever fails or returns 1, `worker_slots=1` → the whole system degrades to a single time-slice worker servicing bindings by priority — i.e. it collapses *back into the old serial-head model as a limiting case*, never an error. The serial head isn't wrong, it's just `worker_slots=1`. As capacity rises the same code fans out. One mechanism across the whole range.

---

## Build order (each step bench-provable, donkey=0)

1. **Tree as data** — add `parent_binding`/`bound_via_role`/`opens`/`rolls_up_to` edges + `open_child_binding` rule. Prove: a console affordance opens a child Game binding; verify a *flat* binding still behaves identically (regression: nesting-of-depth-0 ≡ today).
2. **Composition rules** — `rollup_value`, `terminal_propagation` (contained vs escalates, both reconcilable), `goal`-down. Prove on a minigame-in-overworld: winning child raises parent value; `contained` child death returns to parent without ending it; reconcile flips a mis-seeded escalation bit from observation.
3. **Capacity → slots** — impasse #1 (`probe_system_capacity`), then `derive_worker_slots` as a graph `Min`. Prove slots track a throttled budget.
4. **Allocator** — frontier-pick over `WorkerRequest`s; parallel workers on disjoint subgraphs, rollup at fold. Prove game+chat+environment tick simultaneously and a shared-graph race is impossible (assert no cross-binding write outside the fold).
5. **Degrade + interrupt** — time-slice/suspend below capacity; `terminal_watch` deduce-extrapolation; `preempt_for_terminal`. Prove a backgrounded binding's imminent death pulls a worker back *before* the terminal fires — the headline result.

The arc is one claim: **a binding is a subgraph, attention is a worker per subgraph up to the measured body, and both nesting and concurrency are "parallel within, serial at the fold."** The old single serial 4-slot head was just this with `worker_slots` pinned to 1 — I'm unpinning it and letting the machine set the number.

One thing I'd want your call on before step 4: when slack lets me go to **faculty-granularity** parallelism inside one binding, faculties on the *same* subgraph DO contend (perceive writes what navigate reads). I'd fold those at a per-binding sub-barrier rather than the global one — but confirm you want me to spend slots on intra-binding parallelism at all, versus always preferring breadth (one worker per binding, more bindings live) over depth (more faculties per binding). My instinct is **breadth-first** — more worlds attended beats more threads per world — but that's a values call, and it's yours.