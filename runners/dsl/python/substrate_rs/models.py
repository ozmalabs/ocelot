"""Graph-resident model authoring.

The proposition: given (a) graph-resident parameters everywhere
(kernels, concepts, rules, productions), (b) a composable DSL, and
(c) a rewrite engine — the agent can **author** arbitrary models
the same way it authors a concept: as a typed subgraph it
understands.

A `Model` here is a single graph node carrying:

* ``name`` — the agent's handle for it
* ``kind`` — one of five canonical shapes (see below)
* ``version`` — monotonically increasing via ``revises`` edges
* ``inputs`` / ``outputs`` — declared types, attrs on the node
* ``body_spec`` — a kind-specific schema (stored as a Dict attr)
* ``origin`` — who/what authored it (for the agent's archaeology)

Five canonical kinds (each with a dedicated runner that
``apply_model`` dispatches to):

* **``vision_pipeline``** — sequence of Kernel-node convolutions over
  an Image. Body carries the kernel NodeIDs (in their substrate;
  cross-substrate refs explicitly carry the substrate handle in the
  apply call).
* **``concept``** — a DSL Term-tree the agent evaluates against an
  input env. Same shape as the concepts ``Holds`` resolves; this
  surface unifies the model and concept worlds.
* **``rewrite_set``** — a list of rule indices that ``run_rules``
  applies to a fixed point. The model IS its rule set.
* **``policy``** — a Term that scores a candidate action under an
  env binding; ``apply_model`` returns argmax + per-option scores.
* **``causal_dag``** — explicit cause→effect edges between node
  types with strengths. ``apply_model`` propagates a perturbation
  through the DAG.

Composition (``compose_models``) lets the agent build bigger models
out of smaller ones: serial (output of A feeds B) or parallel
(both run on the same input, combiner Term reduces the outputs).

Versioning (``revise_model``) mints a new Model node with
``revises`` pointing at the original — the agent's edit history
is graph data it can walk later.

Persistence is automatic: Models live on the agent's mind substrate
so the existing ``graph_to_dict`` path round-trips them. The
external-substrate references (e.g. a ``vision_pipeline`` whose
kernels live in a separate vision substrate) are stored as opaque
ints in ``body_spec`` — the caller's responsibility to also
persist the referenced substrate.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from . import Substrate as _PySubstrate
from . import Term

# --- Constants ---------------------------------------------------------

MODEL = "Model"

# Edge types
REVISES = "revises"           # M_new -revises-> M_old (versioning)
HAS_PART = "has_part"         # M -has_part-> M (composition)
HAS_BODY = "has_body_root"    # M -has_body_root-> any (kind-specific anchor)

# Kind names
KIND_VISION_PIPELINE = "vision_pipeline"
KIND_CONCEPT = "concept"
KIND_REWRITE_SET = "rewrite_set"
KIND_POLICY = "policy"
KIND_CAUSAL_DAG = "causal_dag"

_KNOWN_KINDS = {
    KIND_VISION_PIPELINE,
    KIND_CONCEPT,
    KIND_REWRITE_SET,
    KIND_POLICY,
    KIND_CAUSAL_DAG,
}


def _native(s):
    return s._inner if isinstance(s, _PySubstrate) else s


# --- Grammar seeding ---------------------------------------------------

def seed_models_grammar(s) -> int:
    """Add productions for Model + the relationship edges. Lets the
    agent's Π gate Model-shaped writes through Γ. Returns count
    added."""
    from . import NodePattern, Production
    inner = _native(s)
    prods = [
        Production(
            src=NodePattern(type=MODEL, var="src"),
            edge_type=REVISES,
            tgt=NodePattern(type=MODEL, var="tgt"),
            where=None, weight=None,
            provenance="models:revises",
        ),
        Production(
            src=NodePattern(type=MODEL, var="src"),
            edge_type=HAS_PART,
            tgt=NodePattern(type=MODEL, var="tgt"),
            where=None, weight=None,
            provenance="models:has_part",
        ),
    ]
    for p in prods:
        inner.add_production(p.to_dict())
    return len(prods)


# --- Model node creation ---------------------------------------------

def _validate_kind(kind: str) -> None:
    if kind not in _KNOWN_KINDS:
        raise ValueError(
            f"unknown model kind: {kind!r} (known: {sorted(_KNOWN_KINDS)})")


def author_model(
    s,
    name: str,
    kind: str,
    body_spec: dict[str, Any],
    inputs: Iterable[str] = (),
    outputs: Iterable[str] = (),
    origin: str = "user_authored",
) -> Any:
    """Create a new Model node on `s`. The model is its body_spec —
    a kind-specific schema (see module docstring for each kind's
    expected shape). Returns the new NodeID.

    ``body_spec`` is stored as a Dict attr on the Model node; for
    kinds that reference graph nodes (e.g. vision_pipeline's kernel
    list) the NodeIDs appear as integers inside the dict — opaque
    to the engine, meaningful to the kind's runner.
    """
    _validate_kind(kind)
    inner = _native(s)
    return inner.add_node(MODEL, {
        "name": name,
        "kind": kind,
        "version": 1,
        "inputs": tuple(inputs),
        "outputs": tuple(outputs),
        "body_spec": body_spec,
        "origin": origin,
    })


# --- Introspection ----------------------------------------------------

def list_models(s, kind: str | None = None) -> list:
    """All Model NodeIDs, optionally filtered by kind. The agent's
    own catalog of authored models."""
    inner = _native(s)
    models = inner.nodes(MODEL)
    if kind is None:
        return models
    out = []
    for m in models:
        if inner.node(m)["attrs"].get("kind") == kind:
            out.append(m)
    return out


def describe_model(s, model_nid) -> dict:
    """Human/agent-readable snapshot. Includes version chain
    information so the agent can see its edit history."""
    inner = _native(s)
    a = inner.node(model_nid)["attrs"]
    version_chain = _version_chain(s, model_nid)
    composed_of = [n for n in inner.neighbours(model_nid, HAS_PART)]
    return {
        "id": model_nid,
        "name": a.get("name"),
        "kind": a.get("kind"),
        "version": a.get("version", 1),
        "inputs": list(a.get("inputs", ())),
        "outputs": list(a.get("outputs", ())),
        "origin": a.get("origin", ""),
        "version_chain_length": len(version_chain),
        "composed_of_count": len(composed_of),
        "body_keys": sorted(a.get("body_spec", {}).keys()),
    }


def _version_chain(s, model_nid) -> list:
    """Walk ``revises`` edges backward to build the version history.
    Returns the list of NodeIDs newest-first; the supplied model is
    [0]."""
    inner = _native(s)
    chain = [model_nid]
    cur = model_nid
    seen = {model_nid}
    while True:
        prev = inner.neighbours(cur, REVISES)
        if not prev:
            break
        nxt = prev[0]
        if nxt in seen:  # cycle guard
            break
        seen.add(nxt)
        chain.append(nxt)
        cur = nxt
    return chain


# --- Versioning -------------------------------------------------------

def revise_model(
    s,
    original_nid,
    new_body_spec: dict[str, Any],
    origin: str = "revision",
) -> Any:
    """Mint a new Model node that revises ``original_nid``. The new
    node inherits name / kind / inputs / outputs; ``body_spec``
    replaces the original's. Version is original.version + 1. A
    ``revises`` edge from new → old preserves the history.

    The original Model is NOT modified — version chains are
    additive, the agent can always walk back to any prior version.
    """
    inner = _native(s)
    a = inner.node(original_nid)["attrs"]
    kind = a["kind"]
    new_nid = inner.add_node(MODEL, {
        "name": a["name"],
        "kind": kind,
        "version": int(a.get("version", 1)) + 1,
        "inputs": a.get("inputs", ()),
        "outputs": a.get("outputs", ()),
        "body_spec": new_body_spec,
        "origin": origin,
    })
    inner.add_edge(new_nid, REVISES, original_nid)
    return new_nid


# --- Composition ------------------------------------------------------

def compose_models(
    s,
    name: str,
    parts: list,
    combiner: str = "serial",
    combiner_term: Term | None = None,
    origin: str = "composed",
) -> Any:
    """Create a composite Model from `parts` (list of Model NodeIDs).

    ``combiner``:
      * ``"serial"`` — apply parts in order; each part's output is
        fed to the next part's input. Requires output/input type
        compatibility (we declare on the new model's outputs the
        LAST part's outputs; inputs the FIRST part's inputs).
      * ``"parallel"`` — apply every part to the same input; the
        ``combiner_term`` (a Term taking ``Var("results")`` →
        scalar/structure) reduces the list of part outputs. If no
        combiner_term is given, ``apply_model`` returns the raw
        list of part outputs.

    The composite is itself a Model (kind "composite_serial" /
    "composite_parallel"). Parts are wired via ``has_part`` edges
    in input order so ``apply_model`` knows which order to run.

    NB: composite kinds aren't in the canonical 5 since they're
    intentionally a meta-shape — the runner inspects ``parts``
    and dispatches each by its own kind.
    """
    if not parts:
        raise ValueError("compose_models: need at least one part")
    if combiner not in ("serial", "parallel"):
        raise ValueError(
            f"compose_models: combiner must be 'serial' or 'parallel'")
    inner = _native(s)
    first = inner.node(parts[0])["attrs"]
    last = inner.node(parts[-1])["attrs"]
    body_spec = {
        "combiner": combiner,
        "part_ids": [_nid_to_int(p) for p in parts],
        "combiner_term": combiner_term.to_dict() if combiner_term else None,
    }
    composite = inner.add_node(MODEL, {
        "name": name,
        "kind": f"composite_{combiner}",
        "version": 1,
        "inputs": first.get("inputs", ()),
        "outputs": last.get("outputs", ()) if combiner == "serial" else first.get("outputs", ()),
        "body_spec": body_spec,
        "origin": origin,
    })
    # Wire `has_part` edges in order so the agent's introspection
    # can walk them.
    for p in parts:
        inner.add_edge(composite, HAS_PART, p)
    return composite


def _nid_to_int(nid) -> int:
    """NodeID → its underlying int. Composite body_spec stores
    parts as ints (the substrate's persistence preserves them as
    NodeIDs via the __nid__ tag; we use ints here so the spec is a
    plain dict)."""
    return nid.value if hasattr(nid, "value") else int(nid)


# --- Application: dispatch by kind -------------------------------------

def apply_model(s, model_nid, *args, **kwargs):
    """Run the model. Dispatches by kind to the right runner.

    Per-kind signatures:

    * ``vision_pipeline``:
        ``apply_model(s, model, vision_substrate, image_nid) -> [Image NodeIDs]``
        Returns the list of intermediate images (one per kernel).

    * ``concept``:
        ``apply_model(s, model, env: dict) -> Value``
        Evaluates the body Term against the env via the standard DSL.

    * ``rewrite_set``:
        ``apply_model(s, model, max_steps=100_000) -> int``
        Runs the registered rules to a fixed point on `s`; returns
        step count. (The rules live on `s` and are referenced by
        index; the model carries their indices.)

    * ``policy``:
        ``apply_model(s, model, actions: list[dict]) -> {best_action, scores}``
        Evaluates the body Term once per candidate action with the
        action attrs bound into env; returns argmax + per-action scores.

    * ``causal_dag``:
        ``apply_model(s, model, perturb: dict[str, float]) -> dict[str, float]``
        Given an initial perturbation per node type, propagates one
        hop through the DAG and returns accumulated effects.

    * ``composite_serial`` / ``composite_parallel``:
        Recurses on `parts`; passes outputs / inputs through.
    """
    inner = _native(s)
    a = inner.node(model_nid)["attrs"]
    kind = a["kind"]
    spec = dict(a.get("body_spec", {}))
    if kind == KIND_VISION_PIPELINE:
        return _apply_vision_pipeline(s, spec, args, kwargs)
    if kind == KIND_CONCEPT:
        return _apply_concept(s, spec, args, kwargs)
    if kind == KIND_REWRITE_SET:
        return _apply_rewrite_set(s, spec, args, kwargs)
    if kind == KIND_POLICY:
        return _apply_policy(s, spec, args, kwargs)
    if kind == KIND_CAUSAL_DAG:
        return _apply_causal_dag(s, spec, args, kwargs)
    if kind == "composite_serial":
        return _apply_composite_serial(s, spec, args, kwargs)
    if kind == "composite_parallel":
        return _apply_composite_parallel(s, spec, args, kwargs)
    raise ValueError(f"unknown model kind: {kind!r}")


def _apply_vision_pipeline(s, spec, args, kwargs):
    """Walk the kernel NodeIDs and apply convolve in sequence.
    Vision pipeline kernels typically live in a SEPARATE vision
    substrate (per Phase 10c); the caller passes that substrate +
    the input image NodeID."""
    from . import vision as v
    vision_substrate, image_nid = args[:2]
    kernel_ids = spec.get("kernel_ids", [])
    if not kernel_ids:
        return [image_nid]
    # kernel_ids are ints; rehydrate via the vision substrate.
    from . import NodeID
    kernels = [NodeID(int(k)) for k in kernel_ids]
    return v.apply_pipeline(vision_substrate, image_nid, kernels)


def _apply_concept(s, spec, args, kwargs):
    """Evaluate the body Term against the supplied env."""
    inner = _native(s)
    env = args[0] if args else (kwargs.get("env", {}) or {})
    term_json = spec.get("definition_term")
    if term_json is None:
        return None
    return inner.evaluate(term_json, env)


def _apply_rewrite_set(s, spec, args, kwargs):
    """Run the model's rules to a fixed point. The rule indices
    must be valid for `s` — typically the rules were registered on
    `s` at author time, the model just lists which ones it owns."""
    inner = _native(s)
    max_steps = kwargs.get("max_steps", 100_000)
    if args:
        max_steps = args[0]
    # For simplicity, the model's rule set IS all rules registered
    # on the substrate. Future revisions could filter to specific
    # rule_ids in spec.
    return inner.run_rules(max_steps)


def _apply_policy(s, spec, args, kwargs):
    """Evaluate the body Term once per candidate action; return
    argmax + per-action scores."""
    inner = _native(s)
    actions = args[0] if args else (kwargs.get("actions", []) or [])
    if not actions:
        return {"best_action": None, "scores": []}
    term_json = spec.get("score_term")
    if term_json is None:
        return {"best_action": actions[0], "scores": [0.0] * len(actions)}
    base_env = dict(spec.get("env", {}) or {})
    scores = []
    for action in actions:
        env = {**base_env, **action}
        scores.append(float(inner.evaluate(term_json, env)))
    best_idx = max(range(len(actions)), key=lambda i: scores[i])
    return {"best_action": actions[best_idx], "scores": scores}


def _apply_causal_dag(s, spec, args, kwargs):
    """One-hop propagation through the declared cause→effect edges.
    `perturb` is {node_type → magnitude}; returns the accumulated
    effect per downstream type."""
    perturb = args[0] if args else (kwargs.get("perturb", {}) or {})
    edges = spec.get("edges", [])
    out: dict[str, float] = {k: float(v) for k, v in perturb.items()}
    for e in edges:
        src_t = e.get("src_type")
        tgt_t = e.get("tgt_type")
        strength = float(e.get("strength", 1.0))
        if src_t in perturb:
            out[tgt_t] = out.get(tgt_t, 0.0) + perturb[src_t] * strength
    return out


def _apply_composite_serial(s, spec, args, kwargs):
    """Run each part in order; thread output → input. For maximum
    polymorphism we just hand the previous part's output forward as
    the first positional arg to the next."""
    inner = _native(s)
    from . import NodeID
    part_ids = [NodeID(int(p)) for p in spec.get("part_ids", [])]
    cur_args = list(args)
    cur_kwargs = dict(kwargs)
    result = None
    for pid in part_ids:
        result = apply_model(s, pid, *cur_args, **cur_kwargs)
        # The output of part N becomes the SECOND positional arg
        # for part N+1 (after the substrate / first arg if any).
        # We keep the first arg fixed and replace subsequent ones.
        cur_args = list(args[:1]) + [result] if args else [result]
        cur_kwargs = {}
    return result


def _apply_composite_parallel(s, spec, args, kwargs):
    """Run every part on the same args; reduce via combiner_term
    (if given) or return the raw list."""
    inner = _native(s)
    from . import NodeID
    part_ids = [NodeID(int(p)) for p in spec.get("part_ids", [])]
    results = [apply_model(s, pid, *args, **kwargs) for pid in part_ids]
    combiner_json = spec.get("combiner_term")
    if combiner_json is None:
        return results
    # Combiner sees the results list under `results` var.
    return inner.evaluate(combiner_json, {"results": results})


# --- Builder helpers — author canonical model shapes -----------------

def author_vision_pipeline(
    s,
    name: str,
    kernel_ids: list,
    *,
    inputs: tuple = ("Image",),
    outputs: tuple = ("Image",),
    origin: str = "user_authored",
) -> Any:
    """Convenience: build a vision_pipeline Model from a list of
    kernel NodeIDs. The kernels typically live in a separate
    vision substrate; the model just stores their integer ids."""
    return author_model(
        s, name, KIND_VISION_PIPELINE,
        body_spec={"kernel_ids": [_nid_to_int(k) for k in kernel_ids]},
        inputs=inputs, outputs=outputs, origin=origin,
    )


def author_concept_model(
    s,
    name: str,
    definition: Term,
    *,
    inputs: tuple = (),
    outputs: tuple = ("Value",),
    origin: str = "user_authored",
) -> Any:
    """A concept Model wraps a DSL Term. ``apply_model`` evaluates
    it under the env the caller supplies."""
    return author_model(
        s, name, KIND_CONCEPT,
        body_spec={"definition_term": definition.to_dict()},
        inputs=inputs, outputs=outputs, origin=origin,
    )


def author_policy(
    s,
    name: str,
    score_term: Term,
    env: dict | None = None,
    *,
    inputs: tuple = ("Action",),
    outputs: tuple = ("Action", "Score"),
    origin: str = "user_authored",
) -> Any:
    """A policy Model maps perception attrs to a per-action score
    via a DSL Term. ``apply_model`` returns ``{best_action, scores}``."""
    return author_model(
        s, name, KIND_POLICY,
        body_spec={
            "score_term": score_term.to_dict(),
            "env": env or {},
        },
        inputs=inputs, outputs=outputs, origin=origin,
    )


def author_causal_dag(
    s,
    name: str,
    edges: list[dict],
    *,
    inputs: tuple = (),
    outputs: tuple = (),
    origin: str = "user_authored",
) -> Any:
    """A causal DAG Model carries an explicit list of cause→effect
    edges. Each edge: ``{"src_type", "tgt_type", "strength"}``.
    ``apply_model`` propagates a perturbation one hop through.
    """
    return author_model(
        s, name, KIND_CAUSAL_DAG,
        body_spec={"edges": list(edges)},
        inputs=inputs, outputs=outputs, origin=origin,
    )


def author_rewrite_set(
    s,
    name: str,
    *,
    inputs: tuple = (),
    outputs: tuple = (),
    origin: str = "user_authored",
) -> Any:
    """A rewrite-set Model wraps "run all rules registered on the
    substrate". Future revisions can filter by index."""
    return author_model(
        s, name, KIND_REWRITE_SET,
        body_spec={"all_substrate_rules": True},
        inputs=inputs, outputs=outputs, origin=origin,
    )


__all__ = [
    "MODEL", "REVISES", "HAS_PART", "HAS_BODY",
    "KIND_VISION_PIPELINE", "KIND_CONCEPT", "KIND_REWRITE_SET",
    "KIND_POLICY", "KIND_CAUSAL_DAG",
    "seed_models_grammar",
    "author_model", "list_models", "describe_model",
    "revise_model", "compose_models", "apply_model",
    "author_vision_pipeline", "author_concept_model",
    "author_policy", "author_causal_dag", "author_rewrite_set",
]
