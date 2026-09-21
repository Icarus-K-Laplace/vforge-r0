# V-Forge R0: Novelty Boundary Analysis

## What This Study Is NOT Claiming as Novel

The following concepts have existing precedent in the literature:

| Concept | Prior Work |
|---------|-----------|
| Hypothesis → falsification experiment | Popperian philosophy of science; automated hypothesis testing in ML |
| Scientific answer verification | Fact-checking systems, claim verification NLP |
| Claim → executable verification capsule |Executable papers, computational reproducibility |
| Paper → agent + generated tests | AI Scientist frameworks, automated paper testing |
| Metamorphic testing of ML models | Metamorphic testing literature (e.g., Chen et al.) |
| Mutation-guided test generation | Software engineering mutation testing |

## What This Study Specifically Claims to Test

**Core命题:** "Claim-conditioned scientific semantic mutation can serve as an adequacy test for scientific verifiers, and surviving mutants can guide verifier improvement on held-out scientific claims."

This is a **validation study**, not a method-proposal study. The novelty claim is narrow:

1. Systematic mapping of 8 mutation families to verifier blind spots
2. Quantitative adequacy metric (VA = MKR + BAR - 1)
3. Empirical evidence that survivor-guided evolution improves verifier performance on held-out data

## If Collision Found

If literature search reveals this exact命题 is already published:
- Document in NOVELTY_BOUNDARY.md
- Stop the project
- Do not rephrase to avoid detection

## Current Assessment

As of 2026-09-20, no exact collision found. The closest related work:
- Metamorphic testing for ML (2019-2024): focuses on model correctness, not verifier adequacy
- Automated paper testing (2023-2025): focuses on reproducibility, not claim-conditioned mutations
- Verifier evaluation: exists but without mutation-based blind spot analysis

This study's contribution is the **mutation→verifier adequacy pipeline** and **survivor-guided evolution** framework.
