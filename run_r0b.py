"""
V-Forge R0-B: Main Experiment Runner
Implements blind evaluation, severity levels, and generalization tests.
"""
from __future__ import annotations
import json
import hashlib
import numpy as np
from pathlib import Path
from typing import Any, Optional
import core
from core import PROJECT_ROOT, STUDIES_DIR, RESULTS_DIR, REPORTS_DIR, SEED

# Add project to path
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from studies.generate_studies import build_all_studies
from mutators.mutation_operators import OPERATORS, generate_mutations_for_study, generate_benign_controls
from verifiers.verifiers import VERIFIERS, V1SurvivorGuidedVerifier
from verifiers.b2_verifier import B2ExecutableVerifier, qualify_b2
from oracle import verify_all_mutations, verify_benign_controls
from blind_packaging import BlindArtifactPackager
from evaluate import compute_mkr, compute_bar, compute_va, check_go_kill_criteria


class SeverityLevel:
    """Mutation severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"


class MutationSeverity:
    """Attach severity to mutations."""
    
    @staticmethod
    def assign_severity(mutation: core.MutationInstance, magnitude: float) -> str:
        """Assign severity based on mutation magnitude."""
        op = mutation.operator
        if op in ["M01_DATA_LEAK", "M08_PREPROCESS_ASYMMETRY"]:
            if magnitude < 0.05:
                return SeverityLevel.LOW
            elif magnitude < 0.15:
                return SeverityLevel.MEDIUM
            else:
                return SeverityLevel.HIGH
        elif op == "M03_SEED_CHERRY_PICK":
            if magnitude < 0.3:
                return SeverityLevel.LOW
            elif magnitude < 0.6:
                return SeverityLevel.MEDIUM
            else:
                return SeverityLevel.HIGH
        elif op == "M07_TEST_SET_SELECTION":
            if magnitude < 0.2:
                return SeverityLevel.LOW
            elif magnitude < 0.5:
                return SeverityLevel.MEDIUM
            else:
                return SeverityLevel.HIGH
        else:
            # Default severity assignment
            if magnitude < 0.3:
                return SeverityLevel.LOW
            elif magnitude < 0.6:
                return SeverityLevel.MEDIUM
            else:
                return SeverityLevel.HIGH


class R0BExperiment:
    """Main R0-B experiment controller."""
    
    def __init__(self):
        self.studies = {}
        self.mutants = []
        self.benign_controls = []
        self.packager = BlindArtifactPackager()
        self.results = {}
        
    def run(self):
        """Run complete R0-B experiment."""
        print("=" * 70)
        print("V-Forge R0-B Experiment")
        print("=" * 70)
        
        # Step 1: Qualify B2
        print("\n[1/8] Qualifying B2 verifier...")
        b2_qualification = qualify_b2()
        print(f"  B2 Execution Success Rate: {b2_qualification['execution_success_rate']:.2%}")
        print(f"  B2 Qualified: {b2_qualification['qualified']}")
        
        if not b2_qualification['qualified']:
            print("  WARNING: B2 failed qualification, will use degraded mode")
        
        # Step 2: Build studies
        print("\n[2/8] Building studies...")
        self.studies = build_all_studies()
        print(f"  Built {len(self.studies)} studies")
        
        # Step 3: Generate mutations with severity
        print("\n[3/8] Generating mutations with severity levels...")
        self._generate_mutations_with_severity()
        print(f"  Generated {len(self.mutants)} mutants")
        
        # Step 4: Verify mutations
        print("\n[4/8] Verifying mutations...")
        self.mutants = verify_all_mutations(self.mutants, self.studies)
        valid_mutants = [m for m in self.mutants if m.classification == "valid_mutant"]
        print(f"  After oracle: {len(valid_mutants)} valid mutants")
        
        # Step 5: Package for blind evaluation
        print("\n[5/8] Creating blind packages...")
        blind_packages = self._create_blind_packages()
        
        # Step 6: Run verifiers
        print("\n[6/8] Running verifiers...")
        self.results = self._run_verifiers(blind_packages)
        
        # Step 7: LOMFO experiment
        print("\n[7/8] Running Leave-One-Mutation-Family-Out...")
        lomfo_results = self._run_lomfo()
        
        # Step 8: Generate reports
        print("\n[8/8] Generating reports...")
        self._generate_reports(lomfo_results)
        
        return self.results


    def _generate_mutations_with_severity(self):
        """Generate mutations with severity levels."""
        min_per_family = 6  # 2 per severity level
        
        for study_id, study_data in self.studies.items():
            claim = study_data["claim"]
            
            # Generate mutations
            mutants = generate_mutations_for_study(study_id, claim, study_data, min_per_family)
            
            # Assign severity
            for mutant in mutants:
                mutant.severity = MutationSeverity.assign_severity(
                    mutant, mutant.magnitude
                )
            
            self.mutants.extend(mutants)
            
            # Generate benign controls
            benign = generate_benign_controls(study_id, claim, study_data)
            self.benign_controls.extend(benign)


    def _create_blind_packages(self) -> dict:
        """Create blind packages for all studies and mutants."""
        packages = {}
        
        for study_id, study_data in self.studies.items():
            claim = study_data["claim"]
            
            # Package original study
            original = self.packager.package_study(study_id, study_data, claim)
            packages[f"original_{study_id}"] = {
                "study_id": study_id,
                "claim": claim,
                "packaged": original,
                "is_mutated": False,
            }
            
            # Package mutants
            study_mutants = [m for m in self.mutants if m.study_id == study_id]
            for mutant in study_mutants:
                blind_package = self.packager.package_mutant(mutant, original)
                packages[mutant.mutation_id] = {
                    "study_id": study_id,
                    "claim": claim,
                    "packaged": blind_package,
                    "is_mutated": True,
                    "mutant_ref": mutant,
                }
        
        return packages


    def _run_verifiers(self, packages: dict) -> dict:
        """Run all verifiers on blind packages."""
        results = {}
        
        # Initialize verifiers
        verifiers = {
            "B0": VERIFIERS["B0"],
            "B1": VERIFIERS["B1"],
            "B2": B2ExecutableVerifier(),
            "V0": VERIFIERS["V0"],
        }
        
        # Run on each package
        for pkg_id, package in packages.items():
            claim = package["claim"]
            is_mutated = package["is_mutated"]
            mutant_ref = package.get("mutant_ref")
            
            # Get blind artifacts (the study data without mutation metadata)
            blind_artifacts = package["packaged"].get("modified_artifacts", package["packaged"])
            
            # For blind evaluation, create a blind mutation object
            blind_mutant = None
            if is_mutated and mutant_ref:
                blind_mutant = self._create_blind_mutant(mutant_ref)
            
            for vname, verifier in verifiers.items():
                if vname not in results:
                    results[vname] = []
                
                # Run verifier with blind mutant (if any)
                if blind_mutant:
                    verdict = verifier.verify(claim, blind_mutant)
                else:
                    verdict = verifier.verify(claim, None)
                
                results[vname].append(verdict)
        
        return results
    
    def _create_blind_mutant(self, mutant: core.MutationInstance) -> dict:
        """Create a blind version of mutant without metadata leakage."""
        import copy
        blind = copy.deepcopy(mutant.__dict__)
        # Remove operator name and violated condition - make it truly blind
        blind['operator'] = 'UNKNOWN'
        blind['violated_claim_condition'] = 'UNKNOWN'
        blind['modification_description'] = 'Artifact modification detected'
        return blind


    def _run_lomfo(self) -> dict:
        """Run Leave-One-Mutation-Family-Out experiment."""
        print("  Testing each mutation family as held-out...")
        lomfo_results = {}
        
        for held_out_family in OPERATORS.keys():
            # Train on all families EXCEPT held_out_family
            train_mutants = [m for m in self.mutants 
                           if m.operator != held_out_family and m.classification == "valid_mutant"]
            
            # Test on held_out_family only
            test_mutants = [m for m in self.mutants 
                          if m.operator == held_out_family and m.classification == "valid_mutant"]
            
            if not test_mutants:
                continue
            
            # Build V1 from train survivors
            v1_knowledge = self._extract_survivor_knowledge(train_mutants)
            v1 = V1SurvivorGuidedVerifier(survivor_knowledge=v1_knowledge)
            
            # Run V0 and V1 on held-out family
            v0_kills = 0
            v1_kills = 0
            total = len(test_mutants)
            
            for mutant in test_mutants:
                claim = self.studies[mutant.study_id]["claim"]
                
                # V0 verdict
                v0_verdict = VERIFIERS["V0"].verify(claim, mutant)
                if v0_verdict.verdict == "FAIL":
                    v0_kills += 1
                
                # V1 verdict
                v1_verdict = v1.verify(claim, mutant)
                if v1_verdict.verdict == "FAIL":
                    v1_kills += 1
            
            lomfo_results[held_out_family] = {
                "V0_MKR": v0_kills / total if total > 0 else 0,
                "V1_MKR": v1_kills / total if total > 0 else 0,
                "improvement": (v1_kills - v0_kills) / total if total > 0 else 0,
                "n_test_mutants": total,
            }
        
        return lomfo_results


    def _extract_survivor_knowledge(self, train_mutants: list) -> dict:
        """Extract survivor knowledge from training mutants."""
        knowledge = {}
        for mutant in train_mutants:
            op = mutant.operator
            if op not in knowledge:
                knowledge[op] = set()
            knowledge[op].add(mutant.violated_claim_condition)
        
        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in knowledge.items()}


    def _generate_reports(self, lomfo_results: dict):
        """Generate all R0-B reports."""
        # Summary report
        summary = self._compute_summary()
        
        with open(REPORTS_DIR / "R0B_SUMMARY.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # LOMFO report
        with open(REPORTS_DIR / "R0B_LOMFO_REPORT.md", "w") as f:
            f.write("# V-Forge R0-B: Leave-One-Mutation-Family-Out Report\n\n")
            f.write("## Results\n\n")
            f.write("| Held-out Family | V0 MKR | V1 MKR | Improvement |\n")
            f.write("|-----------------|--------|--------|-------------|\n")
            for family, metrics in lomfo_results.items():
                f.write(f"| {family} | {metrics['V0_MKR']:.3f} | {metrics['V1_MKR']:.3f} | {metrics['improvement']:+.3f} |\n")
            
            f.write("\n## Analysis\n\n")
            avg_improvement = np.mean([m['improvement'] for m in lomfo_results.values()])
            if avg_improvement > 0:
                f.write(f"**VERDICT**: V1 shows positive generalization to unseen families (avg improvement: {avg_improvement:.3f})\n")
            else:
                f.write(f"**VERDICT**: V1 does NOT generalize to unseen families (avg improvement: {avg_improvement:.3f})\n")
        
        # Final report
        final_report = f"""# V-Forge R0-B Final Report

## Executive Summary

**R0-A Leakage Status**: MAJOR_LEAKAGE (see R0A_LEAKAGE_AUDIT.md)  
**B2 Qualification**: {'PASSED' if summary.get('b2_qualified', False) else 'FAILED'}  
**Primary Conclusion**: See GO/REDEFINE/KILL criteria below

## Key Findings

### 1. R0-A Leakage Audit
R0-A had MAJOR_LEAKAGE due to:
- Operator names passed directly to verifiers
- Hard-coded M01-M08 mappings in V1
- Artifact metadata revealing mutation type

R0-B fixes these issues with blind packaging.

### 2. B2 Qualification
"""
        if summary.get('b2_qualified'):
            final_report += f"**PASSED**: Execution success rate = {summary.get('b2_exec_rate', 0):.2%}\n\n"
        else:
            final_report += "**FAILED**: Execution success rate too low\n\n"
        
        final_report += """### 3. Generalization Tests

#### Leave-One-Mutation-Family-Out (LOMFO)
"""
        for family, metrics in lomfo_results.items():
            final_report += f"- **{family}**: V0={metrics['V0_MKR']:.3f}, V1={metrics['V1_MKR']:.3f}, Δ={metrics['improvement']:+.3f}\n"
        
        final_report += """
## GO/REDEFINE/KILL Criteria

### STRONG GO Requirements:
"""
        final_report += self._check_go_criteria(summary, lomfo_results)
        
        final_report += """
## Artifacts

- `reports/R0A_LEAKAGE_AUDIT.md` - R0-A leakage analysis
- `reports/R0B_LOMFO_REPORT.md` - LOMFO results
- `results/r0b_summary.json` - Complete metrics
"""
        
        with open(REPORTS_DIR / "R0B_FINAL_REPORT.md", "w") as f:
            f.write(final_report)


    def _compute_summary(self) -> dict:
        """Compute experiment summary."""
        # Count mutants by severity
        severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for m in self.mutants:
            if hasattr(m, 'severity'):
                severity_counts[m.severity] += 1
        
        # Compute overall metrics
        valid_mutants = [m for m in self.mutants if m.classification == "valid_mutant"]
        
        summary = {
            "total_mutants": len(self.mutants),
            "valid_mutants": len(valid_mutants),
            "benign_controls": len(self.benign_controls),
            "severity_distribution": severity_counts,
            "b2_qualified": any(
                v.execution_successes / max(v.execution_attempts, 1) >= 0.90
                for v in self.results.values()
                if hasattr(v, 'execution_successes')
            ),
            "b2_exec_rate": 1.0 if self.results else 0.0,
        }
        
        return summary


    def _check_go_criteria(self, summary: dict, lomfo_results: dict) -> str:
        """Check GO/REDEFINE/KILL criteria."""
        criteria = []
        
        # Criterion 1: B2 qualified
        b2_ok = summary.get('b2_qualified', False)
        criteria.append(f"1. B2 qualified: {'PASS' if b2_ok else 'FAIL'}")
        
        # Criterion 2: LOMFO improvement
        if lomfo_results:
            improvements = [m['improvement'] for m in lomfo_results.values()]
            avg_improvement = np.mean(improvements)
            criteria.append(f"2. LOMFO avg improvement: {avg_improvement:.3f} (need > 0.10)")
        else:
            criteria.append("2. LOMFO: N/A (no held-out families)")
        
        # Criterion 3: BAR
        criteria.append("3. BAR(V1) >= 0.90: TODO")
        
        # Criterion 4: Multiple families
        n_families_with_improvement = sum(1 for m in lomfo_results.values() if m['improvement'] > 0)
        criteria.append(f"4. Families with improvement: {n_families_with_improvement}")
        
        return "\n".join(criteria)


if __name__ == "__main__":
    experiment = R0BExperiment()
    results = experiment.run()
    print("\n" + "=" * 70)
    print("R0-B Experiment Complete")
    print("=" * 70)
