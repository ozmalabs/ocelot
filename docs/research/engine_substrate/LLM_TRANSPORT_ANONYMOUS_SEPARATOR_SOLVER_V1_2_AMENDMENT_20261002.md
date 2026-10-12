# LLM transport anonymous-separator solver v1.2 amendment

Date: 2026-10-02

The v1.1 attempt failed before producing scored rows because the hoisted component-factor records did not retain their own vertex set; boundary scoring therefore used a stale component set. The failing capture and source lock are retained. V1.2 stores and uses each component's vertex set alongside its precomputed factors. No v1.1 worker produced a result. The v1 preregistered sample, anonymization, exhaustive proposal, exact solver, gates, and timing scope remain unchanged.
