# R2V2 Phase -1: Forensic Hash Metadata Correction Audit

**Date**: 2026-09-22
**Scope**: `results/R2_R1C_CASE_FORENSICS.csv` — hash columns for all 8
naturalistic cases (CAND-01 … CAND-08).
**Trigger**: R2V2 brief requires determination of whether CAND-06/07/08
contain manually-entered hashes that do not match recomputed values.

---

## 1. Determination: which CSV columns were wrong

The forensic CSV carries four hash-related columns:

| Column | Intended meaning | Status at R2V2 start |
|---|---|---|
| `manifest_blind_hash` | SHA-256 recorded in `r1c/results/R1C_CASE_FREEZE.json` for the frozen `R1C_BLIND/<id>_BLIND.json` | **Correct for all 8 cases** — byte-for-byte equal to the manifest. |
| `manifest_gold_hash` | SHA-256 recorded in the same manifest for `R1C_DISCOVERY_GOLD/<id>_GOLD.json` | **Correct for all 8 cases** — byte-for-byte equal to the manifest. |
| `recomputed_blind_hash` | Claimed to be an *independent recomputation* of the blind file's hash | **False for all 8 cases**: the column was populated by copying `manifest_blind_hash`, not by recomputing. It therefore carries no independent verification content. |
| `recomputed_gold_hash` | Claimed to be an independent recomputation of the gold file's hash | **False for all 8 cases**: identical copy of `manifest_gold_hash`. |
| `manifest_hash_consistent` | `True` when manifest value equals recomputed value | The value `True` was correct in substance (manifest values are reproducible), but the *basis* was wrong: the "recomputed" side had not actually been recomputed. |

The R2V2 brief's specific suspicion (CAND-06/07/08 wrong) is **not
confirmed**: no case has a wrong `manifest_*` value. The defect is
broader (all 8 rows) and is a *column-semantics* error, not a value
error.

## 2. What each hash is supposed to identify

- `manifest_blind_hash` = identity of the **frozen blind input** for that
  case: the JSON record containing only paper/protocol/case metadata that
  was available *before* gold reveal. It anchors the prediction timestamp.
- `manifest_gold_hash` = identity of the **frozen gold record**: the
  independently-sourced confirmation (author issue / fix PR /
  reproducibility paper metadata). It anchors the gold-reveal timestamp.

Both are content hashes of the two artifact files under
`r1c/R1C_BLIND/` and `r1c/R1C_DISCOVERY_GOLD/`.

## 3. Canonical serialization scheme (verified)

`r1c/isolate_and_freeze.py` computes:

```python
def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
...
blind_json = json.dumps(blind_data, indent=2, ensure_ascii=False)
BLIND_DIR.joinpath(f"{cid}_BLIND.json").write_text(blind_json, encoding="utf-8")
...
"gold_hash": _sha(gold_json), "blind_hash": _sha(blind_json)
```

i.e. SHA-256 over the **UTF-8 encoding of the exact JSON text as written**
(insertion-order keys, `indent=2`, `ensure_ascii=False`). Verified
equivalences:

- `sha256(file_bytes) == sha256(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))`
  for all 8 blind + 8 gold files (files were written verbatim, no
  post-hoc modification).
- Alternative schemes (sorted-key compact, sorted-key indent, raw bytes
  of a pretty-printed re-serialization) do **not** reproduce the
  manifest values — the insertion-order file-bytes scheme is the
  canonical one.

**Recomputed values (canonical scheme)** for each file are, by
construction, equal to the on-disk file hashes; `R1C_SHA256SUMS`
independently records the raw file hashes and all 25 entries verify OK
(re-verified at R2V2 start: 25/25).

## 4. Actual recomputed SHA-256 (all 8, verified this run)

| Case | blind (manifest = recomputed) | gold (manifest = recomputed) |
|---|---|---|
| CAND-01 | `ea3990786c…` ✅ | `31779ca3be…` ✅ |
| CAND-02 | `c8337a2a45…` ✅ | `bacafe1858…` ✅ |
| CAND-03 | `602206edb7…` ✅ | `856126acd9…` ✅ |
| CAND-04 | `ecba8f77c6…` ✅ | `8b3f97c715…` ✅ |
| CAND-05 | `f7605bfc48…` ✅ | `170b4ed4ff…` ✅ |
| CAND-06 | `847cae043e…` ✅ | `539aed3498…` ✅ |
| CAND-07 | `f06f4eb573…` ✅ | `2476a1e4b3…` ✅ |
| CAND-08 | `1bbc6205e6…` ✅ | `f05ef9d720…` ✅ |

Full 64-hex values: see `reports/R2_R1C_FORENSIC_AUDIT.md` (R2 §3) and
the corrected CSV. All 16 equal the manifest and equal the
`R1C_SHA256SUMS` entries for the corresponding files.

## 5. Root-cause classification

For each affected record:

| CASE_ID | FIELD | OLD_VALUE | RECOMPUTED_VALUE | CANONICAL_HASH_METHOD | ROOT_CAUSE | SCIENTIFIC_RESULT_AFFECTED | FORENSIC_GRADE_AFFECTED |
|---|---|---|---|---|---|---|---|
| CAND-01 | `recomputed_blind_hash` | copy of manifest | `ea399078…` (identical) | sha256(utf8(json.dumps(indent=2))) | **Clerical metadata error** (column populated by copy, not recomputation) | NO | NO |
| CAND-01 | `recomputed_gold_hash` | copy of manifest | `31779ca3…` (identical) | same | clerical | NO | NO |
| CAND-02 | both recomputed cols | copies | identical | same | clerical | NO | NO |
| CAND-03 | both | copies | identical | same | clerical | NO | NO |
| CAND-04 | both | copies | identical | same | clerical | NO | NO |
| CAND-05 | both | copies | identical | same | clerical | NO | NO |
| CAND-06 | both | copies | identical | same | clerical | NO | NO |
| CAND-07 | both | copies | identical | same | clerical | NO | NO |
| CAND-08 | both | copies | identical | same | clerical | NO | NO |

Classification: **clerical metadata error** (all 16 entries).
- Not a serialization mismatch: manifest values reproduce exactly under
  the canonical scheme.
- Not a wrong artifact reference: manifest hashes map to the correct
  blind/gold files.
- **Not** a forensic-chain failure: no artifact identity or chronology
  is implicated. The blind files contain no gold fields; the prediction
  files contain no post-verdict fields; the freeze manifest carries a
  single timestamp; and `gold_leakage=NO` in `R1C_NATURALISTIC_METRICS.json`.

## 6. Correction applied

- `recomputed_blind_hash` / `recomputed_gold_hash` are now populated from
  an actual recomputation (canonical scheme, run `r2v2/verify_forensic_hashes.py`),
  no longer from a copy.
- Old values preserved in this audit report (§5) — they are identical
  to the corrected values, so no scientific or chronological content
  changed.
- `manifest_hash_consistent` remains `True` for all 8, now on an
  honest basis.

## 7. Gate: 8/8 internal consistency

Re-ran the full 8-case forensic consistency check after correction:

```
CAND-01 … CAND-08: manifest_blind == recomputed_blind == file hash  -> CONSISTENT
CAND-01 … CAND-08: manifest_gold  == recomputed_gold  == file hash  -> CONSISTENT
R1C_SHA256SUMS: 25/25 OK
```

**GATE PASSED: 8/8 forensic records internally consistent.**
No mismatch changes artifact identity or chronology → do **not** set
`FAIL_PENDING_REVIEW`. Proceed to Phase 1.

```
HASH_METADATA_STATUS = PASS (after correction)
FORENSIC_STATUS      = PASS
```

## 8. Note on the R1-C trace `self_hash` fields (separate, pre-existing)

Distinct from the above: the 16 files under `r1c/traces_pre|post/` carry
their own `self_hash` fields that do **not** recompute under standard
schemes (flagged in R2 §9 Limitation 9 / Appendix I of the V1
readiness report). This is a *trace-level* opacity already recorded as a
limitation. It is **not** part of the blind/gold freeze chain audited
here, does not touch `R1C_CASE_FREEZE.json`, and does not affect the
8/8 gate. It remains a disclosed limitation, unchanged.
