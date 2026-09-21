# R0-D Mutation Residue Audit

**Date**: 2026-09-20
**Scope**: R0-D production verifier source files

---

## Files Audited

R0-D production files:
- `run_r0d1.py`
- `sciinvariant_r0d.py`

R0-C and earlier files (retained for reference only, NOT part of R0-D production):
- `sciinvariant.py`
- `verifiers/verifiers.py`
- `verifiers/b2_verifier.py`
- `mutators/mutation_operators.py`
- `oracle.py`
- `run_experiment.py`
- `run_r0b.py`
- `evaluate.py`
- `blind_packaging.py`
- `core.py`
- `tests/test_vforge.py`

---

## Findings

### Production R0-D Verifier (`sciinvariant_r0d.py`)

Found the following mutation-era residue:

1. **`mutation_hint` parameter** — present in `SCIInvariantVerifier.verify()`:
   ```python
   def verify(self, paper_id: str, mutation_hint=None, benign_control=None):
   ```
   The shortcut `if mutation_hint is None: return PASS` made the entire real-world
   evaluation a no-op. **This is the root cause of the INVALID_RUN.**

2. **`benign_control` parameter** — mutation-era concept:
   ```python
   if benign_control:
       return "PASS", "Benign control verified.", 0.95
   ```
   No legitimate role in real-world paper-code verification.

3. **`self.contracts` typed as `Dict[str, NormativeContract]`** — but loaded
   contracts are JSON dicts, not `NormativeContract` dataclass instances. This
   type mismatch silently broke invariant checking.

4. **`mutation_hint is None` → PASS** — the exact forbidden fallback:
   "if no mutation: PASS".

### `run_r0d1.py`

5. **`verify_paper_repo(paper_id, contract, graph)`** calls:
   ```python
   verdict, reason, confidence = verifier.verify(
       paper_id=paper_id,
       mutation_hint=None,  # "No mutation - this is real-world evaluation"
   )
   ```
   Passes `None` mutation hint, triggering the DEFAULT_PASS_SHORTCUT.

6. Does not pass `graph` to the verifier at all — the contract-graph comparison
   is never actually performed.

---

## Required Production-Verifier Invariants

The production R0-D verifier logic must depend ONLY on:

- paper-derived normative contract
- repository-derived observed graph

It must NOT depend on:

- `mutation_hint`
- `mutation_id`
- `mutant`
- `is_original`
- `original_study`
- `known_fault`
- `fault_family`
- `expected_verdict`
- `gold_label`
- `benign_control`

---

## Audit Verdict

```
MUTATION_RESIDUE_FOUND = YES
FILES_AFFECTED = sciinvariant_r0d.py, run_r0d1.py
SEVERITY = CRITICAL (caused INVALID_RUN)
REMEDIAL_ACTION = Remove all listed parameters and shortcuts before R0-D1-v2
```
