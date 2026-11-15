# Project poster (March 2026): outdated

> **Warning: this poster reports results that were later shown to be incorrect.**

The poster was produced at the start of March 2026 from the early implementation of the SCHC
variants. That implementation used a termination rule that made run length depend on each variant's
counting rule rather than on convergence, disadvantaging SCHC-imp in particular, and tested SCHC-imp over an unsuitable Lc range (see
[`../README.md`](../README.md)). After these problems were corrected, all experiments were
rerun on the Falcon HPC cluster with statistical testing.

Claims on the poster that the final results do not support:

| Poster (March 2026) | Final result (May 2026) |
|---|---|
| SCHC-imp improves on HC by 11.5% at Sprint scale | 14.2% (p < 0.001) |
| SCHC-acp is insensitive to Lc at Sprint scale | Strongly Lc-sensitive: mean penalty 73.9 at Lc = 100, 55.2 at Lc = 1500 |
| Variant behaviour is explained by acceptance rate | Explained by the improving move rate (about 1% of iterations) |
| Practical optimum at Lc of about 1.0 × problem size | Optimal Lc is variant-specific: 1500 to 2500 for SCHC-all and SCHC-acp, 15 to 25 for SCHC-imp |

The final, correct results are in the [main README](../../README.md) and the
[dissertation](../../dissertation/SCHC_NRP_Dissertation.pdf). The poster is kept only as a
record of the project's development.
