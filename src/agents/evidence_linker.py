import sys
import os
from typing import List, Dict
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qdrant_setup import QdrantRealDataManager

class EvidenceLinkerAgent:
    """
    Agent that validates candidate antibodies against scientific literature and experimental data.
    Provides the 'Scientific Support' dimension of the decision quadrant.
    """
    
    def __init__(self, qdrant_manager: QdrantRealDataManager):
        self.qdrant = qdrant_manager
        
    def link_evidence(self, mutation_id: str, candidate: Dict) -> Dict:
        """
        Find specific scientific evidence supporting the design choices of a candidate.
        """
        print(f"[Evidence Linker] 🔗 Linking evidence for {candidate['candidate_id']}")
        
        # 1. Search for papers mentioning both the mutation and binding motifs
        motifs = self._extract_key_motifs(candidate)
        query = f"HER2 {mutation_id} antibody binding {', '.join(motifs)}"
        
        relevant_papers = self.qdrant.search_literature(query=query, mutation_filter=mutation_id, limit=5)
        
        # 2. Extract 'Actionable Evidence' sentences
        evidence_statements = self._extract_evidence_statements(relevant_papers, mutation_id)
        
        # 3. Calculate Scientific Support Score
        support_score = self._calculate_support_score(candidate, relevant_papers, evidence_statements)
        
        return {
            "scientific_support_score": support_score,
            "supporting_papers": [p['pmid'] for p in relevant_papers],
            "evidence_statements": evidence_statements,
            "confidence_level": "High" if len(relevant_papers) > 2 else "Medium" if len(relevant_papers) > 0 else "Low"
        }
    
    def _extract_key_motifs(self, candidate: Dict) -> List[str]:
        """Extract important sequence motifs from the candidate"""
        cdr3 = candidate.get('cdr3', '')
        # Simple heuristic: find aromatic clusters
        aromatics = [aa for aa in cdr3 if aa in 'FWY']
        return list(set(aromatics))
    
    def _extract_evidence_statements(self, papers: List[Dict], mutation_id: str) -> List[str]:
        """Extract specific sentences that provide evidence for the design"""
        statements = []
        for paper in papers:
            abstract = paper.get('abstract', '')
            # Simple keyword-based extraction (in a real system, this would be LLM-based)
            sentences = abstract.split('. ')
            for sentence in sentences:
                if mutation_id.lower() in sentence.lower() and ('binding' in sentence.lower() or 'affinity' in sentence.lower()):
                    statements.append(sentence[:200] + "...")
        
        return list(set(statements))[:3]
    
    def _calculate_support_score(self, candidate: Dict, papers: List[Dict], statements: List[str]) -> float:
        """Score based on paper relevance and content match"""
        if not papers:
            return 0.4 # Base score for biologically plausible design
            
        base_score = min(0.95, 0.4 + (len(papers) * 0.1) + (len(statements) * 0.05))
        
        # Adjust based on candidate design confidence
        design_conf = candidate.get('design_confidence', 0.5)
        final_score = (base_score * 0.7) + (design_conf * 0.3)
        
        return round(final_score, 3)
