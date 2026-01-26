import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List, Tuple
from Bio.SeqUtils.ProtParam import ProteinAnalysis

class FeasibilityCheckerAgent:
    """
    Agent that evaluates antibody candidates for lab feasibility.
    Based on real biochemical and manufacturing constraints.
    """
    
    def __init__(self):
        # Real constraints from antibody manufacturing
        self.constraints = {
            'max_length': 250,      # Max residues for scFv format
            'min_length': 100,      # Min residues
            'max_cysteines': 6,     # Too many can cause misfolding
            'min_cysteines': 2,     # Need at least 2 for disulfide
            'problematic_motifs': [
                'CCC',              # Can form incorrect disulfides
                'WWW',              # Tryptophan clusters cause aggregation
                'KKKK',             # Poly-lysine can be immunogenic
                'DDDD',             # Poly-aspartate affects stability
                'EEEE',             # Poly-glutamate affects stability
                'RRRR',             # Poly-arginine can be toxic
                'GPGG',             # Too flexible
                'GPGP',             # Unstable turns
                'NGS', 'NGT', 'NGA' # N-glycosylation (unless desired)
            ],
            'ideal_pi_range': (5.0, 9.0),      # Isoelectric point
            'ideal_gravy_range': (-1.0, 0.5),  # Grand average of hydropathy
            'max_instability_index': 40.0,     # Instability index threshold
            'ideal_molecular_weight': (12000, 28000)  # For scFv
        }
        
        # Manufacturing-specific issues
        self.manufacturing_constraints = {
            'aggregation_risk_residues': ['W', 'F', 'Y', 'I', 'L', 'V'],  # Hydrophobic/aromatic
            'protease_sites': ['DP', 'TP', 'GP', 'AP', 'KP', 'RP'],       # Common protease sites
            'oxidation_risk': ['M', 'W'],                                 # Oxidizable
            'deamidation_risk': ['NG', 'NS', 'NT', 'DG', 'DS', 'DT'],     # Deamidation sites
            'isomerization_risk': ['DG', 'DS', 'DT'],                     # Asp isomerization
            'max_aromatic_density': 0.15,  # Max % aromatic residues
            'max_charged_density': 0.25,   # Max % charged residues
            'min_complexity': 0.65         # Min sequence complexity
        }
    
    def evaluate_candidate(self, candidate: Dict) -> Dict:
        """
        Comprehensive evaluation of antibody candidate feasibility.
        Returns detailed report with scores and recommendations.
        """
        candidate_id = candidate.get('candidate_id', 'Unknown')
        print(f"[Feasibility Checker] ⚙️ Evaluating {candidate_id}")
        
        sequence = candidate['sequence']
        evaluation = {
            "feasibility_score": 0.0,
            "feasibility_category": "Unknown",
            "passes": [],
            "warnings": [],
            "issues": [],
            "critical_issues": [],
            "biochemical_properties": {},
            "manufacturing_risks": [],
            "recommendations": []
        }
        
        # Calculate all metrics
        properties = self._calculate_biochemical_properties(sequence)
        evaluation['biochemical_properties'] = properties
        
        # Run all checks
        self._check_sequence_length(sequence, evaluation)
        self._check_cysteine_patterns(sequence, evaluation)
        self._check_problematic_motifs(sequence, evaluation)
        self._check_biochemical_properties(properties, evaluation)
        self._check_manufacturing_issues(sequence, evaluation)
        self._check_structural_features(sequence, evaluation)
        
        # Calculate final score
        evaluation['feasibility_score'] = self._calculate_final_score(evaluation)
        evaluation['feasibility_category'] = self._categorize_feasibility(evaluation['feasibility_score'])
        
        # Generate recommendations
        evaluation['recommendations'] = self._generate_recommendations(evaluation)
        
        return evaluation
    
    def _calculate_biochemical_properties(self, sequence: str) -> Dict:
        """Calculate all biochemical properties"""
        try:
            analysis = ProteinAnalysis(sequence)
            
            return {
                "length": len(sequence),
                "molecular_weight": analysis.molecular_weight(),
                "isoelectric_point": analysis.isoelectric_point(),
                "gravy": analysis.gravy(),  # Hydrophobicity
                "instability_index": analysis.instability_index(),
                "aromaticity": analysis.aromaticity(),
                "secondary_structure_fraction": analysis.secondary_structure_fraction(),
                "molar_extinction_coefficient": analysis.molar_extinction_coefficient(),
                "amino_acid_composition": analysis.get_amino_acids_percent(),
                "charge_at_ph7": self._calculate_charge_at_ph7(sequence)
            }
        except Exception as e:
            # Fallback if BioPython analysis fails
            return {
                "length": len(sequence),
                "molecular_weight": self._estimate_mw(sequence),
                "isoelectric_point": 7.0,
                "gravy": self._estimate_gravy(sequence),
                "instability_index": 30.0,
                "aromaticity": sum(1 for aa in sequence if aa in 'FWY') / len(sequence),
                "amino_acid_composition": {}
            }
    
    def _check_sequence_length(self, sequence: str, evaluation: Dict):
        """Check sequence length constraints"""
        length = len(sequence)
        min_len = self.constraints['min_length']
        max_len = self.constraints['max_length']
        
        if min_len <= length <= max_len:
            evaluation['passes'].append(f"Length OK ({length} residues)")
        else:
            evaluation['issues'].append(
                f"Length {length} outside ideal range ({min_len}-{max_len})"
            )
    
    def _check_cysteine_patterns(self, sequence: str, evaluation: Dict):
        """Check cysteine patterns for disulfide bonding"""
        cys_count = sequence.count('C')
        min_cys = self.constraints['min_cysteines']
        max_cys = self.constraints['max_cysteines']
        
        if cys_count % 2 == 0:
            if min_cys <= cys_count <= max_cys:
                evaluation['passes'].append(
                    f"Cysteine count OK ({cys_count}, all can form disulfides)"
                )
            elif cys_count > max_cys:
                evaluation['warnings'].append(
                    f"High cysteine count ({cys_count}) - may cause misfolding"
                )
            else:
                evaluation['warnings'].append(
                    f"Low cysteine count ({cys_count}) - may lack structural disulfides"
                )
        else:
            evaluation['critical_issues'].append(
                f"Odd number of cysteines ({cys_count}) - cannot form proper disulfide bonds"
            )
    
    def _check_problematic_motifs(self, sequence: str, evaluation: Dict):
        """Check for problematic amino acid motifs"""
        found_motifs = []
        
        for motif in self.constraints['problematic_motifs']:
            if motif in sequence:
                found_motifs.append(motif)
        
        if found_motifs:
            evaluation['issues'].append(
                f"Problematic motifs found: {', '.join(found_motifs)}"
            )
        else:
            evaluation['passes'].append("No problematic motifs detected")
    
    def _check_biochemical_properties(self, properties: Dict, evaluation: Dict):
        """Check biochemical properties against constraints"""
        # Isoelectric point check
        pi = properties.get('isoelectric_point', 7.0)
        pi_min, pi_max = self.constraints['ideal_pi_range']
        
        if pi_min <= pi <= pi_max:
            evaluation['passes'].append(f"Isoelectric point OK (pI = {pi:.2f})")
        else:
            evaluation['warnings'].append(
                f"Extreme isoelectric point (pI = {pi:.2f}) - may affect solubility"
            )
        
        # Hydrophobicity (GRAVY) check
        gravy = properties.get('gravy', 0)
        gravy_min, gravy_max = self.constraints['ideal_gravy_range']
        
        if gravy_min <= gravy <= gravy_max:
            evaluation['passes'].append(f"Hydrophobicity OK (GRAVY = {gravy:.2f})")
        else:
            evaluation['issues'].append(
                f"Extreme hydrophobicity (GRAVY = {gravy:.2f}) - aggregation risk"
            )
        
        # Instability index check
        instability = properties.get('instability_index', 30)
        max_instability = self.constraints['max_instability_index']
        
        if instability < max_instability:
            evaluation['passes'].append(f"Stable protein (instability index = {instability:.1f})")
        else:
            evaluation['warnings'].append(
                f"Potentially unstable (instability index = {instability:.1f})"
            )
    
    def _check_manufacturing_issues(self, sequence: str, evaluation: Dict):
        """Check for manufacturing-specific issues"""
        issues = []
        
        # Aggregation risk (clusters of hydrophobic/aromatic)
        aggregation_risk = self._check_aggregation_risk(sequence)
        if aggregation_risk:
            issues.append(aggregation_risk)
        
        # Protease sites
        protease_sites = self._check_protease_sites(sequence)
        if protease_sites:
            issues.append(protease_sites)
        
        # Oxidation risk
        oxidation_risk = self._check_oxidation_risk(sequence)
        if oxidation_risk:
            issues.append(oxidation_risk)
        
        # Deamidation/isomerization risk
        degradation_risk = self._check_degradation_risk(sequence)
        if degradation_risk:
            issues.append(degradation_risk)
        
        # Charge density
        charge_density = self._check_charge_density(sequence)
        if charge_density:
            issues.append(charge_density)
        
        if issues:
            evaluation['manufacturing_risks'].extend(issues)
        else:
            evaluation['passes'].append("No major manufacturing risks detected")
    
    def _check_structural_features(self, sequence: str, evaluation: Dict):
        """Check structural features"""
        # Sequence complexity
        complexity = self._calculate_sequence_complexity(sequence)
        min_complexity = self.manufacturing_constraints['min_complexity']
        
        if complexity >= min_complexity:
            evaluation['passes'].append(f"Good sequence complexity ({complexity:.2f})")
        else:
            evaluation['warnings'].append(
                f"Low sequence complexity ({complexity:.2f}) - may express poorly"
            )
        
        # Check for signal peptide-like sequences (N-terminal)
        if sequence[:20].count('L') > 5 and sequence[:20].count('A') > 3:
            evaluation['warnings'].append(
                "N-terminal region resembles signal peptide - may affect secretion"
            )
    
    def _calculate_final_score(self, evaluation: Dict) -> float:
        """Calculate final feasibility score (0-1)"""
        score = 1.0
        
        # Apply penalties
        penalty_factors = {
            'critical_issues': 0.5,   # 50% penalty per critical issue
            'issues': 0.8,            # 20% penalty per issue
            'warnings': 0.9,          # 10% penalty per warning
            'manufacturing_risks': 0.95  # 5% penalty per manufacturing risk
        }
        
        for issue_type, penalty in penalty_factors.items():
            count = len(evaluation.get(issue_type, []))
            score *= (penalty ** count)  # Exponential penalty
        
        # Bonus for passes
        pass_bonus = 1.0 + (0.02 * len(evaluation.get('passes', [])))
        score = min(1.0, score * pass_bonus)
        
        return round(score, 3)
    
    def _categorize_feasibility(self, score: float) -> str:
        """Categorize feasibility based on score"""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Good"
        elif score >= 0.7:
            return "Moderate"
        elif score >= 0.6:
            return "Marginal"
        else:
            return "Poor"
    
    def _generate_recommendations(self, evaluation: Dict) -> List[str]:
        """Generate practical recommendations"""
        recommendations = []
        score = evaluation['feasibility_score']
        
        # General recommendation based on score
        if score >= 0.8:
            recommendations.append("Good candidate for immediate synthesis and testing")
        elif score >= 0.6:
            recommendations.append("Moderate candidate - consider optimization before synthesis")
        else:
            recommendations.append("Not recommended for synthesis without major redesign")
        
        # Specific recommendations based on issues
        if evaluation.get('critical_issues'):
            recommendations.append(f"Fix critical issues first: {evaluation['critical_issues'][0]}")
        
        if evaluation.get('issues'):
            recommendations.append(f"Address: {evaluation['issues'][0]}")
        
        # Manufacturing recommendations
        if evaluation.get('manufacturing_risks'):
            risk = evaluation['manufacturing_risks'][0]
            if 'aggregation' in risk.lower():
                recommendations.append("Consider adding solubility tags or optimizing hydrophobic patches")
            elif 'protease' in risk.lower():
                recommendations.append("Consider mutation to remove protease sites")
            elif 'oxidation' in risk.lower():
                recommendations.append("Consider formulation with antioxidants")
        
        # Always include these
        recommendations.append("Validate binding with computational docking")
        recommendations.append("Test expression in mammalian system (HEK293 or CHO)")
        
        return recommendations
    
    # Helper methods for specific checks
    def _check_aggregation_risk(self, sequence: str) -> str:
        """Check for aggregation-prone sequences"""
        # Check for hydrophobic clusters
        hydrophobic = self.manufacturing_constraints['aggregation_risk_residues']
        max_cluster = 0
        current_cluster = 0
        
        for aa in sequence:
            if aa in hydrophobic:
                current_cluster += 1
                max_cluster = max(max_cluster, current_cluster)
            else:
                current_cluster = 0
        
        if max_cluster >= 5:
            return f"Aggregation risk: {max_cluster} consecutive hydrophobic residues"
        return ""
    
    def _check_protease_sites(self, sequence: str) -> str:
        """Check for common protease cleavage sites"""
        for site in self.manufacturing_constraints['protease_sites']:
            if site in sequence:
                return f"Protease cleavage site: {site}"
        return ""
    
    def _check_oxidation_risk(self, sequence: str) -> str:
        """Check for oxidation-prone residues"""
        met_count = sequence.count('M')
        trp_count = sequence.count('W')
        
        if met_count > 3:
            return f"Oxidation risk: High methionine count ({met_count})"
        elif trp_count > 2:
            return f"Oxidation risk: High tryptophan count ({trp_count})"
        return ""
    
    def _check_degradation_risk(self, sequence: str) -> str:
        """Check for deamidation/isomerization sites"""
        for i in range(len(sequence) - 1):
            if sequence[i:i+2] in ['NG', 'NS', 'NT']:
                return f"Deamidation risk at position {i}"
            elif sequence[i:i+2] in ['DG', 'DS', 'DT']:
                return f"Isomerization risk at position {i}"
        return ""
    
    def _check_charge_density(self, sequence: str) -> str:
        """Check charge density"""
        charged = sum(1 for aa in sequence if aa in 'DEKRH')
        density = charged / len(sequence)
        max_density = self.manufacturing_constraints['max_charged_density']
        
        if density > max_density:
            return f"High charge density ({density:.1%}) - may affect solubility"
        return ""
    
    def _calculate_sequence_complexity(self, sequence: str) -> float:
        """Calculate sequence complexity (0-1)"""
        # Count unique k-mers
        k = 2
        kmers = [sequence[i:i+k] for i in range(len(sequence) - k + 1)]
        unique_kmers = len(set(kmers))
        total_kmers = len(kmers)
        
        return unique_kmers / total_kmers if total_kmers > 0 else 0
    
    def _calculate_charge_at_ph7(self, sequence: str) -> float:
        """Calculate net charge at pH 7"""
        # Simplified calculation
        positive = sum(1 for aa in sequence if aa in 'KRH')
        negative = sum(1 for aa in sequence if aa in 'DE')
        return positive - negative
    
    def _estimate_mw(self, sequence: str) -> float:
        """Estimate molecular weight"""
        aa_weights = {
            'A': 89.09, 'R': 174.20, 'N': 132.12, 'D': 133.10,
            'C': 121.15, 'Q': 146.15, 'E': 147.13, 'G': 75.07,
            'H': 155.16, 'I': 131.17, 'L': 131.17, 'K': 146.19,
            'M': 149.21, 'F': 165.19, 'P': 115.13, 'S': 105.09,
            'T': 119.12, 'W': 204.23, 'Y': 181.19, 'V': 117.15
        }
        return sum(aa_weights.get(aa, 110) for aa in sequence)
    
    def _estimate_gravy(self, sequence: str) -> float:
        """Estimate GRAVY (Grand Average of Hydropathicity)"""
        # Kyte-Doolittle hydropathy values
        hydropathy = {
            'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5,
            'C': 2.5, 'Q': -3.5, 'E': -3.5, 'G': -0.4,
            'H': -3.2, 'I': 4.5, 'L': 3.8, 'K': -3.9,
            'M': 1.9, 'F': 2.8, 'P': -1.6, 'S': -0.8,
            'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
        }
        return sum(hydropathy.get(aa, 0) for aa in sequence) / len(sequence)