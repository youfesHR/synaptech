import random
import hashlib
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict
import numpy as np

class AntibodyDesignerAgent:
    """
    Agent that designs new antibody sequences based on real templates.
    Uses biochemical principles for realistic design.
    """
    
    def __init__(self):
        # Amino acid properties from real biochemistry
        self.aa_properties = {
            'hydrophobic': ['A', 'V', 'L', 'I', 'M', 'F', 'W', 'Y'],
            'hydrophilic': ['S', 'T', 'N', 'Q', 'R', 'H', 'K', 'D', 'E'],
            'small': ['A', 'S', 'G', 'C', 'T'],
            'aromatic': ['F', 'W', 'Y'],
            'charged_positive': ['R', 'H', 'K'],
            'charged_negative': ['D', 'E'],
            'polar': ['S', 'T', 'N', 'Q', 'Y'],
            # Standard Human Codon Table (simplified for discovery)
            'codon_map': {
                'A': 'GCT', 'C': 'TGC', 'D': 'GAC', 'E': 'GAG', 'F': 'TTC',
                'G': 'GGC', 'H': 'CAC', 'I': 'ATC', 'K': 'AAG', 'L': 'CTG',
                'M': 'ATG', 'N': 'AAC', 'P': 'CCC', 'Q': 'CAG', 'R': 'CGC',
                'S': 'TCC', 'T': 'ACC', 'V': 'GTG', 'W': 'TGG', 'Y': 'TAC'
            }
        }
        
        # Known HER2 binding motifs based on literature
        self.her2_binding_motifs = {
            'L755S': ['Y', 'F', 'W', 'R', 'H'],  # Aromatic/charged for Serine mutation
            'T798I': ['D', 'E', 'S', 'T', 'Q'],  # Polar for Isoleucine
            'D769H': ['S', 'T', 'N', 'Q', 'Y'],  # Polar for Histidine
            'V777L': ['Y', 'W', 'F', 'H', 'R']   # Aromatic for Leucine
        }
        
        # Common antibody frameworks from human germlines
        self.frameworks = {
            'VH3-23': "EVQLVESGGGLVQPGGSLRLSCAAS",  # Common in therapeutic antibodies
            'VH1-69': "QVQLVQSGAEVKKPGASVKVSCKAS",   # Good for hydrophobic targets
            'VH4-34': "QVQLQESGPGLVKPSETLSLTCTVS",   # Good stability
            'VH3-07': "EVQLVESGGGLVQPGKSLRLSCAAS"    # Alternative common framework
        }
    
    def design_candidates(self, mutation_id: str, template_cdr3: str = None, 
                         num_candidates: int = 5) -> List[Dict]:
        """
        Design new antibody candidates for a specific mutation.
        Uses biochemical principles for realistic design.
        """
        print(f"[Antibody Designer] 🧬 Designing {num_candidates} candidates for {mutation_id}")
        
        candidates = []
        
        for i in range(num_candidates):
            # Select framework based on mutation type
            framework = self._select_framework_for_mutation(mutation_id)
            
            # Generate CDR regions optimized for the mutation
            cdr1 = self._generate_optimized_cdr(mutation_id, region='cdr1', length=10)
            cdr2 = self._generate_optimized_cdr(mutation_id, region='cdr2', length=16)
            
            # CDR3 is most critical - use template or generate based on mutation
            if template_cdr3:
                cdr3 = self._mutate_for_mutation(template_cdr3, mutation_id, mutation_rate=0.4)
            else:
                cdr3 = self._generate_cdr3_for_mutation(mutation_id)
            
            # Construct full sequence using standard antibody scaffold
            full_sequence = self._construct_full_sequence(framework, cdr1, cdr2, cdr3)
            
            # Calculate design metrics
            design_metrics = self._calculate_design_metrics(full_sequence, cdr3, mutation_id)
            
            # Generate candidate ID
            seq_hash = hashlib.md5(full_sequence.encode()).hexdigest()[:8]
            candidate_id = f"DES_{mutation_id}_{i+1:03d}_{seq_hash}"
            
            candidate = {
                "candidate_id": candidate_id,
                "sequence": full_sequence,
                "cdr1": cdr1,
                "cdr2": cdr2,
                "cdr3": cdr3,
                "framework": self._get_framework_name(framework),
                "length": len(full_sequence),
                "design_confidence": design_metrics['confidence'],
                "binding_optimization": design_metrics['binding_optimization'],
                "stability_score": design_metrics['stability'],
                "specificity_score": design_metrics['specificity'],
                "biochemical_properties": {
                    "aromatic_count": sum(1 for aa in full_sequence if aa in self.aa_properties['aromatic']),
                    "charged_count": sum(1 for aa in full_sequence if aa in self.aa_properties['charged_positive'] + 
                                                                        self.aa_properties['charged_negative']),
                    "cysteine_count": full_sequence.count('C'),
                    "glycosylation_sites": self._count_glycosylation_sites(full_sequence)
                },
                "genetic_code": self._back_translate_to_dna(full_sequence)
            }
            
            candidates.append(candidate)
        
        # Sort by design confidence
        candidates.sort(key=lambda x: x['design_confidence'], reverse=True)
        
        return candidates
    
    def _select_framework_for_mutation(self, mutation_id: str) -> str:
        """Select appropriate antibody framework based on mutation"""
        # Different frameworks have different properties
        if mutation_id in ['L755S', 'T798I']:
            # Kinase domain mutations - use frameworks with good stability
            return random.choice([self.frameworks['VH3-23'], self.frameworks['VH4-34']])
        else:
            # Other mutations
            return random.choice(list(self.frameworks.values()))
    
    def _generate_optimized_cdr(self, mutation_id: str, region: str, length: int) -> str:
        """Generate CDR region optimized for specific mutation"""
        # Get preferred AAs for this mutation
        preferred_aas = self.her2_binding_motifs.get(mutation_id, self.aa_properties['aromatic'])
        
        # Different CDR regions have different requirements
        if region == 'cdr1':
            # CDR1 often has more polar residues
            aa_pool = self.aa_properties['polar'] + self.aa_properties['small']
        elif region == 'cdr2':
            # CDR2 often has mixed properties
            aa_pool = self.aa_properties['hydrophilic'] + self.aa_properties['hydrophobic']
        else:
            aa_pool = list('ACDEFGHIKLMNPQRSTVWY')
        
        # Generate sequence with bias toward preferred AAs
        cdr = []
        for _ in range(length):
            if random.random() < 0.6:  # 60% chance to use preferred AA
                cdr.append(random.choice(preferred_aas))
            else:
                cdr.append(random.choice(aa_pool))
        
        # Ensure no problematic patterns
        sequence = ''.join(cdr)
        sequence = self._fix_problematic_patterns(sequence)
        
        return sequence
    
    def _generate_cdr3_for_mutation(self, mutation_id: str) -> str:
        """Generate CDR3 specifically optimized for mutation"""
        length = random.randint(8, 15)  # Optimal CDR3 length
        preferred_aas = self.her2_binding_motifs.get(mutation_id, ['Y', 'R', 'D', 'W'])
        
        # CDR3 composition rules
        cdr3 = []
        for i in range(length):
            if i < 2 or i > length - 3:
                # Edges - more flexible
                cdr3.append(random.choice(self.aa_properties['small']))
            else:
                # Middle - use preferred binding residues
                if random.random() < 0.8:  # 80% bias for preferred
                    cdr3.append(random.choice(preferred_aas))
                else:
                    # Mix for diversity
                    if random.random() < 0.5:
                        cdr3.append(random.choice(self.aa_properties['charged_positive']))
                    else:
                        cdr3.append(random.choice(self.aa_properties['aromatic']))
        
        sequence = ''.join(cdr3)
        sequence = self._fix_problematic_patterns(sequence)
        
        return sequence
    
    def _mutate_for_mutation(self, template_cdr3: str, mutation_id: str, mutation_rate: float = 0.4) -> str:
        """Mutate template CDR3 to better fit specific mutation"""
        preferred_aas = self.her2_binding_motifs.get(mutation_id, ['Y', 'R', 'D'])
        
        mutated = []
        for aa in template_cdr3:
            if random.random() < mutation_rate:
                # Mutate to preferred AA for this mutation
                mutated.append(random.choice(preferred_aas))
            else:
                mutated.append(aa)
        
        sequence = ''.join(mutated)
        sequence = self._fix_problematic_patterns(sequence)
        
        return sequence
    
    def _construct_full_sequence(self, framework: str, cdr1: str, cdr2: str, cdr3: str) -> str:
        """Construct full antibody heavy chain variable region"""
        # Standard antibody scaffold with proper spacing
        scaffold_parts = [
            framework,                    # Framework region 1
            cdr1,                         # CDR1
            "WVRQAPGKGLEWV",              # Framework region 2
            cdr2,                         # CDR2
            "RFTISADTSKNTAYLQMNSLRAEDTAVYYC",  # Framework region 3
            cdr3,                         # CDR3
            "WGQGTLVTVSS"                 # Framework region 4
        ]
        
        return ''.join(scaffold_parts)
    
    def _calculate_design_metrics(self, sequence: str, cdr3: str, mutation_id: str) -> Dict:
        """Calculate various design metrics"""
        confidence = 0.5  # Base confidence
        
        # 1. CDR3 length check (optimal 8-12)
        cdr3_len = len(cdr3)
        if 8 <= cdr3_len <= 12:
            confidence += 0.2
        elif 6 <= cdr3_len <= 14:
            confidence += 0.1
        
        # 2. Cysteine check (should be even and >=2)
        cys_count = sequence.count('C')
        if cys_count % 2 == 0 and cys_count >= 2:
            confidence += 0.15
        elif cys_count % 2 == 0:
            confidence += 0.1
        else:
            confidence *= 0.7  # Penalize odd cysteines
        
        # 3. Aromatic content in CDR3 (important for HER2 binding)
        aromatic_count = sum(1 for aa in cdr3 if aa in self.aa_properties['aromatic'])
        if aromatic_count >= 2:
            confidence += 0.15
        elif aromatic_count >= 1:
            confidence += 0.05
        
        # 4. Binding optimization for specific mutation
        preferred_aas = self.her2_binding_motifs.get(mutation_id, [])
        binding_aa_count = sum(1 for aa in cdr3 if aa in preferred_aas)
        binding_optimization = min(1.0, binding_aa_count / max(1, len(cdr3)))
        
        # 5. Stability (simplified hydrophobicity check)
        hydrophobic_ratio = sum(1 for aa in sequence if aa in self.aa_properties['hydrophobic']) / len(sequence)
        # Optimal hydrophobic ratio ~0.3 for antibodies
        stability = 0.5 + (0.5 * (0.3 - abs(0.3 - hydrophobic_ratio)))
        
        # 6. Specificity (avoid too many charged residues)
        charged_ratio = sum(1 for aa in sequence if aa in self.aa_properties['charged_positive'] + 
                                                  self.aa_properties['charged_negative']) / len(sequence)
        specificity = 1.0 - min(1.0, abs(0.15 - charged_ratio) / 0.15)  # Target ~15% charged
        
        return {
            'confidence': min(0.95, max(0.3, confidence)),
            'binding_optimization': round(binding_optimization, 3),
            'stability': round(stability, 3),
            'specificity': round(specificity, 3)
        }
    
    def _fix_problematic_patterns(self, sequence: str) -> str:
        """Fix known problematic amino acid patterns"""
        # Convert to list for mutation
        seq_list = list(sequence)
        
        # Fix triple repeats (can cause aggregation)
        for i in range(len(seq_list) - 2):
            if seq_list[i] == seq_list[i+1] == seq_list[i+2]:
                # Mutate middle one
                alternatives = [aa for aa in 'ACDEFGHIKLMNPQRSTVWY' if aa != seq_list[i+1]]
                seq_list[i+1] = random.choice(alternatives)
        
        # Fix glycosylation sites unless desired
        for i in range(len(seq_list) - 2):
            if seq_list[i] == 'N' and seq_list[i+1] in 'GS' and seq_list[i+2] not in 'P':
                # Mutate to break N-glycosylation site
                seq_list[i+1] = random.choice('ACDEFGHIKLMNPQRSTVWY'.replace('N', '').replace('S', '').replace('G', ''))
        
        return ''.join(seq_list)
    
    def _count_glycosylation_sites(self, sequence: str) -> int:
        """Count N-glycosylation sites (N-X-S/T where X != P)"""
        count = 0
        for i in range(len(sequence) - 2):
            if (sequence[i] == 'N' and 
                sequence[i+1] != 'P' and 
                sequence[i+2] in 'ST'):
                count += 1
        return count
    
    def _get_framework_name(self, framework_seq: str) -> str:
        """Get framework name from sequence"""
        for name, seq in self.frameworks.items():
            if seq == framework_seq:
                return name
        return "Custom"

    def _back_translate_to_dna(self, amino_acid_sequence: str) -> str:
        """Convert amino acid sequence to DNA using human codon optimization"""
        dna_sequence = []
        for aa in amino_acid_sequence:
            dna_sequence.append(self.aa_properties['codon_map'].get(aa, 'NNN'))
        return "".join(dna_sequence)
