# LLM transport role-separator inference v1.2 amendment

Date: 2026-10-02

The v1.1 capture measured monolithic JT without allocation tracing but timed the role-conditioned solver while `tracemalloc` was active. V1.2 times both solvers without tracing, then repeats the conditioned solve in a separate traced pass solely to record its Python allocation peak. The traced repeat must return the same state and energy as the uninstrumented conditioned pass. V1 and v1.1 captures remain diagnostic pilots; only v1.2 is the final timing result. All other sampling, exactness, sign-parity, and claim-boundary requirements remain unchanged.
