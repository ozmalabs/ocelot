# Nonholonomic control v1 results

The preregistered Racecar claim **failed**.

The executed protocol SHA-256 was
`1bc9fb88e20adb99546f1346e01889f9e2822c3084599458d8256ebeb1165045`.
All 54 runs completed. Enhanced and legacy calibration trajectories matched
exactly, both damage arms adapted, and the ablation disabled heading escape.

At the preregistered heading weight of `1.0`, Racecar had zero enhanced wins.
Median enhanced progress was `0.1362`, legacy progress was `0.1365`, and
median paired advantage was `0.0`. One pair was materially worse
(`-0.3089`); the others were identical or nearly identical. The trigger fired,
but its orientation term was generally too weak to change the selected action.

V1 then became development data. A declared sweep over weights `2`, `5`, and
`10` selected `5`: it produced 6/6 Racecar wins, median paired advantage
`0.2013`, and median progress `0.4395` on the v1 cases. R2-D2's median paired
advantage was `+0.0212`; Husky's was `0.0`. Version 1.5.1 fixes that weight
before any v2 case is executed.

The v1 result's per-run regime counter included a stale regime label during
some recalibration actions. The primary progress comparisons are unaffected.
The reporter now requires `decision_kind == "forward_model"` when counting a
heading-escape action.
