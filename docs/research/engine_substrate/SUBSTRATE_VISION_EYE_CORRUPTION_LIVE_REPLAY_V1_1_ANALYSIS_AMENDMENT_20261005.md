# Post-hoc analysis v1.1 amendment

The v1.1 post-hoc analyzer is preserved as an invalidated analysis attempt. It reconstructed activation sums by iterating the sorted mask list. The reference v1.2 offline scorer iterates a Python set, so addition order can differ and perturb exact ties. The v1.1 report's 583 exact-max mismatches are therefore not valid evidence about native winner parity.

The v1.2 analysis corrects the iteration order and locks its own analyzer, protocol, and all inputs. The v1.1 report remains available to make the correction auditable; do not cite it as a valid parity result. The original v1 live capture and its strict exact-max failure remain unchanged.
