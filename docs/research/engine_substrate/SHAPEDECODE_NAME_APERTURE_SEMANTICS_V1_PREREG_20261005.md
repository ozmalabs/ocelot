# ShapeDecode name-aperture semantic controls v1 — preregistration

**Question:** Does the EvalCtx-local name index preserve the scan path's selection and scoring semantics under case-folding, duplicate names, absent scope values, and explicit empty scopes?

## Design

Use a paired fresh-process scan/cache evaluation of one native `MaxOver` Term over ShapeSignature nodes. Nested ShapeDecode calls use a singleton scope derived from each candidate name, matching the v1 name-aperture route. Each control uses identical graph construction, goal, and term; only the process-local cache switch differs. Cases cover baseline unique names, case-varied names, exact duplicate names with a later signature, case-fold-equivalent duplicate names, a declared scope evaluating to `None`, and a declared empty scope. An additional reversed multi-name aperture checks that selection retains original codebook order despite the set's iteration order. For each pair, compare the full Term result; require that an empty scope returns no result and an absent-value scope behaves as unrestricted.

## Gates and boundaries

Lock runner, analyzer, protocol, Rust/Python source manifest, and native binary. Run each arm in a unique process. Require exact paired result parity, no worker errors, and stable source hashes. This is a semantic control panel, not a timing experiment. It does not cover `Surface(Text)` attributes, malformed records, exclusion filters, graph mutation during EvalCtx, or natural-task prevalence; those remain separate gates and must not be inferred from these cases.

## Amendment v1.1 — engine empty-scope result and order control

The initial capture showed the native bridge represents ShapeDecode's no-part wall value as Python `None`; the scan/cache outputs matched, but the analyzer had incorrectly expected a rendered diagnostic string. This amendment records the native value representation and adds a reversed multi-name aperture case to exercise output selection under insertion-order semantics. No implementation or acceptance change is made to parity; a new lock and full paired capture are required because protocol, runner, and analyzer changed.
