# SciCoQA Dataset Field Audit (Actual)

## Dataset Version
- Name: UKPLab/scicoqa
- Version: v1.1
- Download Date: 2026-09-20

## Actual Fields Discovered

### SAFE_INPUT Fields (Can be used by SI-D)
| Field | Type | Description |
|-------|------|-------------|
| discrepancy_id | string | Unique identifier |
| paper_url | string | Base paper URL |
| paper_url_versioned | string | Versioned paper URL (PDF) |
| code_url | string | Base code URL |
| code_url_versioned | string | Versioned code URL (specific commit) |
| arxiv_subject | string | ArXiv subject category |
| arxiv_categories | list | Full ArXiv categories |
| arxiv_year | integer | Publication year |

### GOLD_SEALED Fields (MUST NOT be accessed during inference)
| Field | Type | Description |
|-------|------|-------------|
| discrepancy_date | string | Date of discrepancy report |
| origin_type | string | Source type (real/synthetic) |
| origin_url | string | Origin URL |
| origin_discrepancy_text | string | Original discrepancy description |
| discrepancy_description_pooled_gpt_5 | string | GPT-5 description |
| discrepancy_description_pooled_gemini_2_5_pro | string | Gemini description |
| discrepancy_description_pooled_gpt_oss_20b | string | GPT OSS description |
| is_valid_discrepancy_gemini | boolean | Gemini validation |
| is_valid_discrepancy_gpt | boolean | GPT validation |
| is_valid_discrepancy_reason_gemini | string | Validation reason (Gemini) |
| is_valid_discrepancy_reason_gpt | string | Validation reason (GPT) |
| discrepancy_description_gemini | string | Final Gemini description |
| discrepancy_description_gpt | string | Final GPT description |
| relevant_paper_sections_gemini | list | Gemini-annotated sections |
| relevant_paper_sections_gpt | list | GPT-annotated sections |
| relevant_code_files_gemini | list | Gemini-annotated files |
| relevant_code_files_gpt | list | GPT-annotated files |
| changed_code_files | list | Files with changes |
| changed_code_snippets | list | Changed code snippets |
| discrepancy_type | string | Type of discrepancy |
| discrepancy_category | string | Category of discrepancy |
| synthetic_origin | string | Synthetic source (if applicable) |
| synthetic_source_paper | string | Source paper (if synthetic) |

### Field Audit Result
- Total fields: 28
- Safe for SI-D: 7
- Gold sealed: 21
- Leakage check: **PASSED**

## Blind Projection
- Source: `external/scicoqa/raw_gold/scicoqa_real_v1.1.jsonl`
- Output: `external/scicoqa/blind/scicoqa_real_blind.jsonl`
- Records: 92
- SHA256: `5fabe2bd68b44894ea89635978721e69c8618cf9d45c0cc588f0bfc0a5b64395`

## Raw Gold
- Path: `external/scicoqa/raw_gold/scicoqa_real_v1.1.jsonl`
- SHA256: `4de50ad228859ee108a99efab0c28bfd0c2c8cbd561fdb180302795bb94124cc`
- **ACCESS RESTRICTED**: Only evaluation code after prediction freeze
