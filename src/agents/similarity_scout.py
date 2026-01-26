import pandas as pd
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qdrant_setup import QdrantRealDataManager
class SimilarityScoutAgent:
    """
    Agent that finds similar mutations and related information from Qdrant.
    """
    
    def __init__(self, qdrant_manager: QdrantRealDataManager):
        self.qdrant = qdrant_manager
    
    def find_mutation_analogs(self, mutation_id: str) -> Dict:
        """
        Find mutations similar to the query mutation.
        Returns evidence score and supporting literature.
        """
        print(f"[Similarity Scout] 🔍 Searching for analogs of {mutation_id}")
        
        # Search for similar mutations in Qdrant
        similar_mutations = self.qdrant.search_mutations(
            query=f"HER2 mutation {mutation_id} resistance",
            limit=5
        )
        
        # Get literature specifically about this mutation
        literature = self.qdrant.search_literature(
            query=f"HER2 {mutation_id} resistance mechanism",
            mutation_filter=mutation_id,
            limit=3
        )
        
        # Calculate evidence score
        evidence_score = self._calculate_evidence_score(similar_mutations, literature)
        
        # Get clinical context
        clinical_context = self._get_clinical_context(mutation_id)
        
        return {
            "query_mutation": mutation_id,
            "similar_mutations": similar_mutations,
            "supporting_literature": literature,
            "clinical_context": clinical_context,
            "evidence_score": evidence_score,
            "total_analogs_found": len(similar_mutations),
            "total_papers_found": len(literature)
        }
    
    def _calculate_evidence_score(self, mutations: List, literature: List) -> float:
        """Calculate evidence score based on similarity and literature support"""
        if not mutations and not literature:
            return 0.3  # Default low score for novel mutations
        
        # Calculate average similarity scores
        mutation_scores = [m["score"] for m in mutations if m.get("score")]
        literature_scores = [l["score"] for l in literature if l.get("score")]
        
        avg_mutation_score = sum(mutation_scores) / len(mutation_scores) if mutation_scores else 0
        avg_literature_score = sum(literature_scores) / len(literature_scores) if literature_scores else 0
        
        # Weighted average: 60% literature, 40% mutation similarity
        # Literature is more important for evidence
        combined = (0.6 * avg_literature_score) + (0.4 * avg_mutation_score)
        
        # Boost if we have both mutations and literature
        if mutation_scores and literature_scores:
            combined = min(1.0, combined * 1.1)
        
        return round(combined, 3)
    
    def _get_clinical_context(self, mutation_id: str) -> Dict:
        """Get clinical context for mutation"""
        # Known clinical significance from literature
        clinical_data = {
            "L755S": {
                "prevalence": "5-7% of trastuzumab-resistant cases",
                "clinical_impact": "Reduces drug binding affinity by 50-100x",
                "treatment_implications": "Consider T-DM1 or neratinib",
                "prognosis": "Worse progression-free survival"
            },
            "T798I": {
                "prevalence": "2-3% of resistant cases",
                "clinical_impact": "Gatekeeper mutation, affects multiple TKIs",
                "treatment_implications": "Avoid lapatinib/neratinib",
                "prognosis": "Requires novel antibody approaches"
            },
            "D769H": {
                "prevalence": "3-4% of resistant cases",
                "clinical_impact": "Alters activation loop dynamics",
                "treatment_implications": "May respond to higher antibody doses",
                "prognosis": "Variable response to second-line therapies"
            }
        }
        
        return clinical_data.get(mutation_id, {
            "prevalence": "Unknown",
            "clinical_impact": "Novel mutation - limited data",
            "treatment_implications": "Consider experimental approaches",
            "prognosis": "Requires monitoring"
        })