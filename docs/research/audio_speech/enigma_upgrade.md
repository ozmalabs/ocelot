# Enigma upgrade — current model and solver boundary

The earlier Enigma work was a useful recovery experiment, but its forward
model was narrower than its claims: three rotors only, ring AAA in the search,
reflector B only, and an implicit `encrypt == decrypt` API.

## Landed upgrade

The compatibility implementation in `domains/toy_enigma.py` now provides:

- historical rotors I–V plus naval Beta/Gamma;
- reflectors A/B/C and thin B/C;
- explicit `decrypt()` methods and one-shot `decrypt()`;
- ring-aware turnover (the old AAA-only turnover behavior was a real defect);
- M4-style four-rotor operation with a stationary Greek rotor;
- exact fast scrambler support for the existing blind/hill-climb path;
- choose-three-of-five rotor search via `rotor_count`.

The new public import is `domains.enigma`; `domains.toy_enigma` remains a
backward-compatible import for the old scripts.

## Solver machinery

`domains/enigma_solver.py` applies the current solver boundary to this domain:
an `EnigmaProblem` has an explicit shape, hard failures return `status="wall"`
with a reason, and successful results carry an answer plus diagnostics.

`solve()` selects among three existing recovery modes:

- known-plug crib: graph-resident candidates are filtered by the native
  `EnigmaCrib` term in `run_rules`, then language-model ranking sees only the
  admissible frontier;
- unknown-plug crib: the native `EnigmaBombe` term performs the same
  plugboard-independent cut and returns a graph-composed partial steckering
  witness before Python completes the survivors;
- no crib: the existing IoC/quadgram plus multi-start plugboard search.

The Γ seed is `seeds/enigma_recovery.json`. Candidates and their machine
settings are graph nodes linked by `has_candidate`; a scan node causes a Rust
`Filter`/`MapList` to evaluate the hard predicate and write the admissible
frontier back onto the problem node. Language scoring is deliberately outside
that hard cut. The blind language-model winner remains a hypothesis, not a
proof.

## Verified result

`tests/test_enigma_upgrade.py` passes 8/8. It verifies reciprocal decryption,
ring turnover, M4 stepping, exact equivalence of the precomputed scrambler to
the full machine, the historical five-rotor pool, solver-shaped crib recovery,
the native graph cut, and the Bombe witness path.

On the release engine, a representative three-rotor run over all 105,456
rotor-order/start hypotheses took 2.2 s for a known-plug crib (10 hard
survivors) and 3.3 s for a full-crib Bombe recovery (1 hard survivor). Those
figures include graph candidate construction and the Γ fixpoint; they are
measurements for this machine and crib length, not universal guarantees.

The old full blind result remains the honest capability boundary: the existing
3-rotor/10-plugboard attack recovered reliably from sufficiently long
ciphertext, with the documented frontier around 800–1600 letters. The new
M4 and non-AAA configurations are now decryptable and representable, but their
blind key recovery is not being claimed as solved: adding ring search and the
extra rotor dimension expands the hypothesis space substantially.
