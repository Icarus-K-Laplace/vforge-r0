
Epsilon (eps) definition per experiment:
- R1-A (controlled identifiability): no explicit epsilon threshold;
  pairs are defined by construction (clean vs. single-predicate-violation
  execution of the same code). The "value-preserving" characterization
  is post-hoc: we report whether the reported scalar difference |y+ - y-|
  is within 1% of the clean scalar (VPS < 0.01) or not.
- R1-B1 (real-trace, constructed deviations): VPS = |y+ - y-| / |y+|
  where y+ is the clean-trace scalar. A pair is "value-preserving" if
  VPS <= 0.25 (all 48 pairs in the frozen set satisfy this; observed
  range 0.052 to 0.246).
- R1-C (naturalistic): 2 of 8 cases are flagged value-preserving
  (value_preserving_naturalistic_cases=2). The remaining 6 are "process-
  violating" but not value-preserving (the reported values do differ
  between pre-fix and post-fix, or the violation is structural rather
  than numeric).
