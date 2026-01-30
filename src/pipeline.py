import argparse
import json
from datetime import datetime
from typing import Dict, List
import pandas as pd
import os

from qdrant_setup import QdrantRealDataManager
from data_loader import HER2DataLoader
from agents.similarity_scout import SimilarityScoutAgent
from agents.antibody_designer import AntibodyDesignerAgent
from agents.feasibility_checker import FeasibilityCheckerAgent
from agents.evidence_linker import EvidenceLinkerAgent

class RealDataOrchestrator:
    """
    Main orchestrator using real biological data.
    """
    
    def __init__(self, use_existing_data: bool = True):
        print("=" * 70)
        print("🧬 HER2-ResistAID: Real Data Pipeline")
        print("=" * 70)
        
        # Initialize data loader
        self.data_loader = HER2DataLoader()
        
        # Initialize Qdrant with real data
        self.qdrant_manager = QdrantRealDataManager()
        
        # Initialize agents
        self.scout_agent = SimilarityScoutAgent(self.qdrant_manager)
        self.designer_agent = AntibodyDesignerAgent()
        self.checker_agent = FeasibilityCheckerAgent()
        self.linker_agent = EvidenceLinkerAgent(self.qdrant_manager)
        
        # Load or create data
        if use_existing_data:
            print("\n📂 Loading existing data...")
            try:
                self.mutations = pd.read_csv("data/processed/mutations_processed.csv")
                self.antibodies = pd.read_csv("data/processed/antibodies_processed.csv")
                self.abstracts = pd.read_csv("data/processed/abstracts_processed.csv")
                
                # Advanced Data
                self.protocols = pd.read_csv("data/raw/synthesis_protocols.csv") if os.path.exists("data/raw/synthesis_protocols.csv") else pd.DataFrame()
                self.lab_notes = pd.read_csv("data/raw/lab_notes.csv") if os.path.exists("data/raw/lab_notes.csv") else pd.DataFrame()
                self.experimental_results = pd.read_csv("data/raw/experimental_results.csv") if os.path.exists("data/raw/experimental_results.csv") else pd.DataFrame()
                self.images = pd.read_csv("data/raw/images_metadata.csv") if os.path.exists("data/raw/images_metadata.csv") else pd.DataFrame()
                
                # Load data to Qdrant
                print("   Loading data to Qdrant...")
                self.qdrant_manager.load_mutations_to_qdrant(self.mutations)
                self.qdrant_manager.load_antibodies_to_qdrant(self.antibodies)
                self.qdrant_manager.load_abstracts_to_qdrant(self.abstracts)
                self.qdrant_manager.load_protocols_to_qdrant(self.protocols)
                self.qdrant_manager.load_lab_notes_to_qdrant(self.lab_notes)
                self.qdrant_manager.load_experimental_results_to_qdrant(self.experimental_results)
                self.qdrant_manager.seed_experiments()
                
            except FileNotFoundError:
                print("   No existing data found, creating new...")
                self._load_and_setup_data()
        else:
            self._load_and_setup_data()
        
        # Show system status
        self._show_system_status()
    
    def _load_and_setup_data(self):
        """Load and setup all data"""
        print("\n📥 Loading real biological datasets...")
        (self.mutations, self.antibodies, self.abstracts, 
         self.protocols, self.lab_notes, self.experimental_results, 
         self.images) = self.data_loader.process_all_data()
        
        print("\n🗄️ Initializing Qdrant collections...")
        self.qdrant_manager.initialize_collections()
        
        print("\n📤 Loading data to Qdrant...")
        self.qdrant_manager.load_mutations_to_qdrant(self.mutations)
        self.qdrant_manager.load_antibodies_to_qdrant(self.antibodies)
        self.qdrant_manager.load_abstracts_to_qdrant(self.abstracts)
        self.qdrant_manager.load_protocols_to_qdrant(self.protocols)
        self.qdrant_manager.load_lab_notes_to_qdrant(self.lab_notes)
        self.qdrant_manager.load_experimental_results_to_qdrant(self.experimental_results)
        self.qdrant_manager.seed_experiments()
    
    def _show_system_status(self):
        """Display system status"""
        stats = self.qdrant_manager.get_collection_stats()
        
        print("\n📊 SYSTEM STATUS")
        print("-" * 40)
        print(f"   Mutations in database: {len(self.mutations)}")
        print(f"   Antibodies in database: {len(self.antibodies)}")
        print(f"   Scientific abstracts: {len(self.abstracts)}")
        print("\n   Qdrant Collections:")
        for col_name, stat in stats.items():
            count = stat.get('vectors_count', 'N/A')
            print(f"     • {col_name}: {count} vectors")
    
    def run_for_mutation(self, mutation_id: str, num_candidates: int = 3) -> Dict:
        """
        Run complete pipeline for a specific mutation.
        """
        print(f"\n🎯 PROCESSING MUTATION: {mutation_id}")
        print("=" * 60)
        
        # Step 1: Similarity Scout - Find mutation analogs and evidence
        print("\n[1/4] 🔍 SIMILARITY SCOUT")
        scout_results = self.scout_agent.find_mutation_analogs(mutation_id)
        
        if scout_results['similar_mutations']:
            print(f"   Found {scout_results['total_analogs_found']} similar mutations:")
            for mut in scout_results['similar_mutations'][:3]:
                print(f"     • {mut['mutation_id']} (similarity: {mut['score']:.3f})")
        
        if scout_results['supporting_literature']:
            print(f"   Found {scout_results['total_papers_found']} relevant papers:")
            for paper in scout_results['supporting_literature'][:2]:
                print(f"     • {paper['title'][:60]}... (score: {paper['score']:.3f})")
        
        evidence_score = scout_results['evidence_score']
        print(f"   Evidence Score: {evidence_score:.3f}")
        
        # Step 2: Find relevant antibodies for inspiration
        print("\n[2/4] 💉 FINDING RELEVANT ANTIBODIES")
        relevant_antibodies = self.qdrant_manager.search_antibodies_by_mutation(
            mutation_id, limit=3
        )
        
        if relevant_antibodies:
            print(f"   Found {len(relevant_antibodies)} relevant antibodies:")
            for ab in relevant_antibodies:
                print(f"     • {ab['name']} - CDR3: {ab['cdr3'][:15]}... (score: {ab['score']:.3f})")
            
            # Use best antibody's CDR3 as template
            template_cdr3 = relevant_antibodies[0]['cdr3']
        else:
            print("   No directly relevant antibodies found, using general design")
            template_cdr3 = None
        
        # Step 3: Antibody Designer - Generate new candidates
        print(f"\n[3/4] 🧬 DESIGNING NEW ANTIBODIES")
        candidates = self.designer_agent.design_candidates(
            mutation_id=mutation_id,
            template_cdr3=template_cdr3,
            num_candidates=num_candidates
        )
        
        print(f"   Designed {len(candidates)} candidate antibodies")
        
        # Step 4: Feasibility Check - Evaluate each candidate
        print(f"\n[4/4] ⚙️ FEASIBILITY ASSESSMENT")
        ranked_candidates = []
        
        for candidate in candidates:
            print(f"   Evaluating {candidate['candidate_id']}...", end=" ")
            
            # Evaluate feasibility
            feasibility = self.checker_agent.evaluate_candidate(candidate)
            
            # Link evidence and get scientific support score
            evidence_link = self.linker_agent.link_evidence(mutation_id, candidate)
            support_score = evidence_link['scientific_support_score']
            
            # Combine scores: 40% evidence, 30% design, 30% feasibility
            combined_score = (
                0.3 * support_score +
                0.1 * evidence_score +
                0.3 * candidate['design_confidence'] +
                0.3 * feasibility['feasibility_score']
            )
            
            candidate_result = {
                **candidate,
                **feasibility,
                **evidence_link,
                "combined_score": combined_score,
                "evidence_score": evidence_score
            }
            
            ranked_candidates.append(candidate_result)
            print(f"Score: {combined_score:.3f}")
        
        # Rank candidates by combined score
        ranked_candidates.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Step 5: Generate final report
        final_report = self._generate_report(mutation_id, ranked_candidates, scout_results)
        
        return final_report
    
    def _generate_report(self, mutation_id: str, candidates: List[Dict], scout_results: Dict) -> Dict:
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            "report_id": f"HER2_Report_{mutation_id}_{timestamp}",
            "mutation": mutation_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "candidates_generated": len(candidates),
                "top_score": candidates[0]['combined_score'] if candidates else 0,
                "average_feasibility": sum(c['feasibility_score'] for c in candidates) / len(candidates) if candidates else 0
            },
            "evidence_found": {
                "similar_mutations": len(scout_results['similar_mutations']),
                "relevant_papers": len(scout_results['supporting_literature']),
                "evidence_score": scout_results['evidence_score']
            },
            "top_candidates": candidates[:3],  # Top 3 candidates
            "recommendations": self._generate_recommendations(candidates[:3])
        }
        
        # Save report to file
        filename = f"reports/report_{mutation_id}_{timestamp}.json"
        os.makedirs("reports", exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {filename}")
        
        return report
    
    def _generate_recommendations(self, top_candidates: List[Dict]) -> List[str]:
        """Generate practical recommendations"""
        recommendations = []
        
        if not top_candidates:
            return ["No viable candidates generated - consider different approach"]
        
        # Check if any candidates have high feasibility
        high_feasibility = [c for c in top_candidates if c['feasibility_score'] >= 0.8]
        
        if high_feasibility:
            best_candidate = high_feasibility[0]
            recommendations.append(
                f"Prioritize {best_candidate['candidate_id']} for synthesis "
                f"(Feasibility: {best_candidate['feasibility_score']:.2f}, "
                f"Combined Score: {best_candidate['combined_score']:.2f})"
            )
        
        # Check for common issues
        all_issues = []
        for candidate in top_candidates[:2]:
            all_issues.extend(candidate.get('issues', []))
        
        if all_issues:
            unique_issues = list(set(all_issues))
            if len(unique_issues) > 0:
                recommendations.append(
                    f"Common issues to address: {', '.join(unique_issues[:2])}"
                )
        
        # General recommendations
        recommendations.append(
            "Consider in vitro testing for top 2-3 candidates"
        )
        recommendations.append(
            "Validate binding with computational docking before synthesis"
        )
        
        return recommendations
    
    def display_results(self, report: Dict):
        """Display results in a readable format"""
        print("\n" + "=" * 70)
        print("✅ PIPELINE COMPLETE - FINAL RESULTS")
        print("=" * 70)
        
        mutation = report['mutation']
        print(f"\nMutation: {mutation}")
        print(f"Evidence Score: {report['evidence_found']['evidence_score']:.3f}")
        print(f"Candidates Generated: {report['summary']['candidates_generated']}")
        print(f"Top Score: {report['summary']['top_score']:.3f}")
        
        print(f"\n📚 Evidence Found:")
        print(f"   • Similar mutations: {report['evidence_found']['similar_mutations']}")
        print(f"   • Relevant papers: {report['evidence_found']['relevant_papers']}")
        
        print(f"\n🏆 TOP CANDIDATES:")
        for i, candidate in enumerate(report['top_candidates'], 1):
            print(f"\n  #{i}: {candidate['candidate_id']}")
            print(f"     Combined Score: {candidate['combined_score']:.3f}")
            print(f"     Evidence: {candidate['evidence_score']:.3f}")
            print(f"     Design Confidence: {candidate['design_confidence']:.3f}")
            print(f"     Feasibility: {candidate['feasibility_score']:.3f} ({candidate['feasibility_category']})")
            print(f"     CDR3: {candidate['cdr3'][:20]}...")
            
            if candidate.get('passes'):
                print(f"     ✓ {candidate['passes'][0]}")
            
            if candidate.get('issues'):
                print(f"     ⚠️  {candidate['issues'][0]}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
        
        print(f"\n📊 Next steps saved to: {report.get('report_id', 'report')}")

def main():
    parser = argparse.ArgumentParser(
        description="HER2-ResistAID: Real Data Pipeline for Antibody Design"
    )
    
    parser.add_argument(
        "--mutation",
        type=str,
        required=True,
        help="HER2 mutation ID (e.g., L755S, T798I, D769H)"
    )
    
    parser.add_argument(
        "--candidates",
        type=int,
        default=3,
        help="Number of candidates to generate (default: 3)"
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demonstration with multiple mutations"
    )
    
    parser.add_argument(
        "--skip-data-load",
        action="store_true",
        help="Skip loading data (use existing)"
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    orchestrator = RealDataOrchestrator(use_existing_data=args.skip_data_load)
    
    if args.demo:
        print("\n🎪 DEMONSTRATION MODE")
        demo_mutations = ["L755S", "T798I", "D769H", "V777L"]
        
        for mutation in demo_mutations:
            report = orchestrator.run_for_mutation(mutation, num_candidates=2)
            orchestrator.display_results(report)
            print("\n" + "=" * 70 + "\n")
    else:
        report = orchestrator.run_for_mutation(args.mutation, num_candidates=args.candidates)
        orchestrator.display_results(report)

if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    main()