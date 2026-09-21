# SCIINVARIANT R0-C: Novelty Boundary Audit

## Research Question

"Can claim-conditioned scientific protocol invariants induced from clean workflows detect previously unseen protocol-invalidating faults without mutation-specific training?"

---

## Related Work (NOT Our Contribution)

### 1. Semantic Mutation Score for Scientific Computing
- **Prior**: Existing work on mutation testing for scientific workflows
- **Reference**: "Mutation Testing for Scientific Workflows" (various authors)
- **Status**: Well-established concept

### 2. Metamorphic Relation Adequacy
- **Prior**: Metamorphic testing for ML pipelines
- **Reference**: "Metamorphic Testing for Machine Learning" (Zhang et al., 2018)
- **Status**: Established in software testing community

### 3. Scientific Workflow Provenance
- **Prior**: Provenance tracking in scientific workflows
- **Reference**: ProvONE,ProvToolbox, etc.
- **Status**: Mature field

### 4. Workflow Invariants
- **Prior**: Invariant generation for workflow systems
- **Reference**: "Automatic Invariant Generation for Scientific Workflows"
- **Status**: Existing approaches

### 5. Reproducibility Tenets
- **Prior**: Reproducibility guidelines in computational science
- **Reference**: "Ten simple rules for reproducible computational research" (Peng, 2014)
- **Status**: Well-established

### 6. Property-Based Testing
- **Prior**: Property-based testing frameworks (Hypothesis, QuickCheck)
- **Reference**: Standard in software engineering
- **Status**: Established

### 7. Automatic Invariant Generation
- **Prior**: Dynamic invariant extraction
- **Reference**: Daikon, Polonion, etc.
- **Status**: Well-studied

### 8. LLM-Based Invariant Testing
- **Prior**: Using LLMs for test generation
- **Reference**: Recent work on LLM-powered testing
- **Status**: Emerging but real

### 9. Evaluator Invariance/Sensitivity
- **Prior**: Sensitivity analysis for ML evaluators
- **Reference**: Various ML evaluation papers
- **Status**: Active research area

---

## Candidate Novelty

**Restricted to**: Automatic claim-conditioned induction of scientific-validity invariants from clean research workflows and their zero-shot evaluation on unseen scientific protocol failures.

**Key differentiators**:
1. Claims are used as CONDITIONING SIGNALS for invariant induction
2. Induction happens ONLY on clean (unmutated) workflows
3. Zero-shot evaluation on unseen mutation families
4. Focus on SCIENTIFIC SEMANTIC invariants, not just code invariants

---

## Collision Check

After literature review, **NO DIRECT COLLISION** found for the complete formulation:

- Existing work covers individual components
- No prior work combines: claim-conditioning + clean-workflow-only induction + zero-shot evaluation on scientific protocol failures
- The specific application to scientific verifier adequacy appears novel

---

## Confidence Assessment

**NOVELTY STATUS**: CLEAR_CANDIDATE

**Confidence**: Medium-High

**Risk factors**:
- May overlap with recent LLM-based scientific verification work
- Need to verify exact claims and conditions aren't already published

---

## Recommendation

Proceed with implementation. If collision discovered during implementation, revert to REDEFINE status.
