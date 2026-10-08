# V1.3 amendment: mint-time support semantics

The V1.2 sweep reached N=4 recurrent-residual. Statuses, mint count, codebook epoch, fixed point, and index invariants passed; one added acceptance check failed because it compared the minted shape's `support` to the final population size. The baseline rule computes support at mint time from all observations with the key. Mint first becomes eligible at support 2, and the minted node's support is a snapshot; later observations do not update it.

This amendment changes the expected minted support to 2 for recurrent-residual workloads and 0 minted shapes for recognition workloads. Final per-key index support remains required to equal the final observation-grouping oracle, independently of the immutable mint-time support snapshot. No treatment or workload behavior changed. The full six-cell sweep will be rerun under this corrected check.
