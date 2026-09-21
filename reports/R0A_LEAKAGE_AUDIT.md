# V-Forge R0-A Leakage Audit Report

## Executive Summary

**STATUS: MAJOR_LEAKAGE**

R0-A has critical information leakage from mutation metadata to verifiers. This means R0-A results are not trustworthy for generalization claims.

## Detailed Findings

### 1. Verifier Direct Access to Mutation Metadata

**Location**: `verifiers/verifiers.py`, lines 68-69, 383-384, 495-496

```python
# B0 sees operator directly
op = mutation.operator  # e.g., "M01_DATA_LEAK"
violated = mutation.violated_claim_condition

# V0 sees operator and violated condition
op = mutation.operator
violated = mutation.violated_claim_condition

# V1 sees operator and uses hardcoded mappings
matched_conditions = self.known_conditions.get(op, [])
```

**Impact**: Verifiers receive exact operator names and violated conditions. V1 has hard-coded M01-M08 → condition mappings, essentially memorizing the test.

### 2. Verifier Access to Mutation ID

**Location**: All verifiers, lines 89, 391, 459

```python
verdict_id=f"{self.name}_{mutation.mutation_id}"
```

**Impact**: While verdict_id is output-only, the mutation_id contains the operator name (e.g., "M01_DATA_LEAK_study_01_000").

### 3. Verifier Access to Modification Description

**Location**: `verifiers/verifiers.py`, line 82

```python
reasoning = f"Claim appears valid. No obvious inconsistency detected in {op}."
```

**Impact**: The mutation's human-readable description contains the operator type.

### 4. V1 Survivor Knowledge Contains Hard-coded Rules

**Location**: `verifiers/verifiers.py`, lines 441-450

```python
self.known_conditions = {
    "M01_DATA_LEAK": [...],
    "M02_BASELINE_HANDICAP": [...],
    # ... etc
}
```

**Impact**: V1 doesn't learn from survivors; it has pre-programmed operator-to-condition mappings. This is not "survivor-guided" evolution—it's hard-coded rules.

### 5. Artifact Metadata Leaks Mutant Type

**Location**: `mutators/mutation_operators.py`, lines 31-35, 62-64

```python
mutated["leak_info"] = {
    "n_leaked": int(n_leak),
    "leak_source": "test_set",
    "leak_percentage": round(n_leak / len(mutated["X_test"]) * 100, 1),
}
```

**Impact**: Modified study data contains keys like "leak_info", "corrupted_labels", "original_seed", "dropped_subgroup" which explicitly reveal the mutation type.

### 6. Oracle Information May Leak

**Location**: `oracle.py`, lines 42-64

The oracle uses operator-specific checks but doesn't pass results to verifiers. However, if any artifact contains oracle-derived metadata, this could leak.

**Current Status**: No direct leak found, but the oracle's classification logic mirrors the verifier logic.

## Severity Assessment

| Issue | Severity | Impact on Results |
|-------|----------|-------------------|
| Operator name passed to verifier | MAJOR | V1 knows exactly what to check |
| Violated condition passed to verifier | MAJOR | Verifier can directly check condition |
| Hard-coded M01-M08 mappings in V1 | MAJOR | No actual learning occurred |
| Artifact metadata reveals mutation type | MAJOR | Study data itself is contaminated |
| Modification descriptions | MINOR | Could be sanitized |

## Conclusion

**R0-A has MAJOR_LEAKAGE**. The V1 improvement from MKR=0.5 to MKR=1.0 is achieved through hard-coded operator mappings, not genuine learning. The apparent "survivor-guided evolution" is actually just pre-programmed knowledge injection.

**Required Action**: R0-A results must be considered invalid for generalization claims. A clean-room reimplementation is required for R0-B.
