import json
P = "seeds/vision_dorsal.json"
d = json.load(open(P))
r = [x for x in d["rules"] if x["name"] == "dv_oja_learn"][0]

old_start = "WHY NOT THE ANTI-HEBBIAN LATERAL FIRST"
i = r["comment"].index(old_start)
r["comment"] = r["comment"][:i] + (
 "WHY BISTABILITY AND NOT THE ANTI-HEBBIAN LATERAL (the other named candidate;"
 " rung 4's vm_burst_lateral is a precedent for lateral interactions in this"
 " tree). THE REASON IS MATHEMATICAL, AND IT IS THE ONLY REASON: any rule LINEAR"
 " in x has an AVERAGING attractor. Lateral decorrelation changes WHICH average a"
 " unit converges to (which principal component); it does not make an average"
 " directional. The local Foldiak form w <- w(1 - eta*y_v^2) - eta*y_v*x has fixed"
 " point w = -xbar/ybar -- MINUS the mean, still the mean. Bistability is NONLINEAR"
 " IN w, which is the property the measured diagnosis actually demands: it makes"
 " the mean a REPELLER rather than converging to a different one.\n\n"
 " WHAT IS *NOT* A REASON, AND WAS WRONGLY GIVEN AS ONE (retracted 2026-07-17): an"
 " earlier version of this comment also rejected Sanger's deflation as 'not local'"
 " (a synapse must read the WINNER's weight vector) and Rubner-Tavan's as racing"
 " dv_burst_winner's Argmax over the same dact inside the fixpoint. Both are true"
 " statements about TODAY'S ENGINE and NEITHER is grounds to discard a mechanism."
 " The standing directive is that any biologically plausible mechanism is allowed"
 " and the ENGINE IS EXTENDED TO FIT THE BIOLOGY -- this tree's own rule is"
 " 'primitive in Rust, composition in graph': when the DSL genuinely cannot express"
 " something, you add a Rust Term or change the evaluation semantics (CLAUDE.md,"
 " 'When a new primitive is needed -> Rust'). A missing primitive is a BUILD TASK,"
 " never a veto on the science. Letting the engine's current shape decide which"
 " biology is admissible is exactly backwards, and it is how a model quietly"
 " becomes a model of its own implementation.\n\n"
 " THE HONEST STATUS OF THE ALTERNATIVES, THEREFORE: the anti-Hebbian lateral"
 " family is UNBUILT AND UNREFUTED. It is set aside on the linearity argument"
 " above -- which bites the local Foldiak form squarely, and which a genuine"
 " deflation (Sanger/Rubner-Tavan onto a LOWER principal component) may well"
 " escape, because eviction from the DC mode lands a unit in what is plausibly a"
 " DEGENERATE direction-carrying multiplet under isotropy, where the tie is broken"
 " by the unit's own random delays rather than by the average. That is a real"
 " candidate mechanism and it is recorded as such, not dismissed. What it would"
 " cost the engine is nameable and is a first-class deliverable in its own right:"
 " a Rust Term for a non-local read (a synapse reaching the winner's corresponding"
 " weight), or two-phase evaluation so a lateral term can modify an output BEFORE"
 " the competition Argmax reads it, or an outer-product primitive.")

d["version"] = "1.1.1"
json.dump(d, open(P, "w"), indent=1)
print("seed comment corrected ->", d["version"])
