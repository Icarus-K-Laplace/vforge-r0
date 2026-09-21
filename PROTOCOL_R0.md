# V-Forge R0 Protocol

## Study Design

This document defines the complete protocol for Phase R0-A of the V-Forge research project.

### Phase R0-A Scope
- 5 controlled studies
- 8 mutation families (M01-M08)
- Minimum 3 mutants per family per study
- Target: ≥120 valid mutants, ≥40 benign controls
- Deterministic pipelines where possible
- Minute-scale execution

### Data Split
- TRAIN: 60% of studies (3 studies)
- DEV: 15% of studies (1 study)
- TEST: 25% of studies (1 study, frozen before V0 runs)

### GO/KILL Criteria (Frozen)
1. V1 vs strongest baseline: MKR improvement ≥15pp, bootstrap 95% CI lower bound > 0
2. BAR(V1) ≥ 0.90
3. V1 vs V0: MKR improvement ≥10pp
4. Improvement not from single mutation family
5. Execution errors and timeouts NOT counted as correct detections

### Metrics
- MKR(V) = killed_valid_mutants / all_valid_mutants
- BAR(V) = accepted_benign_controls / all_benign_controls
- VA(V) = MKR(V) + BAR(V) - 1

## Study List

### TRAIN Studies (1-3)
1. study_01: MNIST Logistic Regression Comparison
2. study_02: CIFAR-10 OOD Generalization
3. study_03: Probability Calibration Assessment

### DEV Study (4)
4. study_04: Subgroup Robustness Analysis

### TEST Study (5, FROZEN)
5. study_05: Statistical Significance Testing

## Mutation Implementation

Each mutation operator must:
1. Have clear precondition
2. Modify minimal artifacts
3. Keep pipeline executable
4. Record complete diff with SHA256
5. Document violated claim condition
6. Have independent oracle verification
7. Output mutation manifest
8. Support deterministic replay
9. Classify as valid/trivial/skipped

## Verifier Baselines

- B0: LLM-as-Judge (prompt-based evaluation)
- B1: Static Claim Rubric (rule-based checking)
- B2: Executable Claim Verifier (code generation + execution)
- V0: V-Forge claim-conditioned verifier
- V1: Survivor-Guided V-Forge (improved from V0 using train survivors)

## Execution Steps

1. Generate all studies and claims
2. Apply mutations to create mutants
3. Run verifiers on mutants
4. Evaluate benign controls
5. Extract survivors
6. Generate V1
7. Run V1 on held-out data
8. Compute metrics and report
