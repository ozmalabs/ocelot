# Vision settling single-sweep scale v1.1 amendment

Before the source lock or complete worker matrix, a diagnostic worker attempted the preregistered `n_side=12` case. `settle_lib.lattice_centres` rejected it because the current 16×16 retina with RF 7 supports at most 10 uniformly spaced centers per side. No complete matrix or capture was produced. The supported size set is amended to `{3,4,6,8,10}`; seeds, paired variants, measurements, gates, and interpretation are unchanged. This avoids claiming evidence for an unsupported anatomy.
