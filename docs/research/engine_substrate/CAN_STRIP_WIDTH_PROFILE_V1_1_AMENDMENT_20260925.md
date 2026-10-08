# Amendment 1.1: bounded-width strip profile gate

The v1 pilot stopped at height 5, length 32 because its harness required the generic min-fill upper bound to equal the strip height. The valid column-order elimination certificate gave width 5, while min-fill returned width 6. Exact junction-tree/oracle scoring had passed for the failing worker. The partial stdout record is preserved separately.

The v1.1 gate now treats the column-order bag size h+1 as the strip-width certificate, requires min-fill to return a valid width upper bound no smaller than h, and records any min-fill overestimate as a measured outcome. It still requires each order's bag size to match its measured width and both exact MAP energies to match the independent transfer-matrix oracle. No topology, weights, sizes, or replicates change.
