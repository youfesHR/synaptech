import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, CollectionInfo
)
from sentence_transformers import SentenceTransformer
import hashlib
import json
from tqdm import tqdm

class QdrantRealDataManager:
    """
    Qdrant manager that handles real biological data.
    """
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(":memory:")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collections for real data
        self.collections = {
            "her2_mutations": {
                "name": "her2_mutations",
                "vector_size": 384,
                "payload_schema": {
                    "mutation_id": "keyword",
                    "gene": "keyword",
                    "amino_acid_change": "keyword",
                    "mutation_type": "keyword",
                    "protein_position": "integer",
                    "clinical_significance": "keyword",
                    "resistance_info": "text",
                    "pubmed_refs": "keyword[]"
                }
            },
            "antibody_db": {
                "name": "antibody_database",
                "vector_size": 384,
                "payload_schema": {
                    "antibody_id": "keyword",
                    "name": "keyword",
                    "target": "keyword",
                    "sequence": "text",
                    "cdr1": "text",
                    "cdr2": "text",
                    "cdr3": "text",
                    "affinity_nM": "float",
                    "source": "keyword",
                    "pdb_id": "keyword",
                    "reference": "text"
                }
            },
            "scientific_literature": {
                "name": "scientific_literature",
                "vector_size": 384,
                "payload_schema": {
                    "pmid": "keyword",
                    "title": "text",
                    "abstract": "text",
                    "full_text": "text",
                    "year": "integer",
                    "author": "keyword",
                    "keywords": "keyword[]",
                    "mutation_mentions": "keyword[]",
                    "antibody_mentions": "keyword[]"
                }
            },
            "lab_experiments": {
                "name": "lab_experiments",
                "vector_size": 384,
                "payload_schema": {
                    "exp_id": "keyword",
                    "mutation": "keyword",
                    "conditions": "text",
                    "measurements": "float",
                    "outcome": "keyword",
                    "notes": "text"
                }
            },
            "synthesis_protocols": {
                "name": "synthesis_protocols",
                "vector_size": 384,
                "payload_schema": {
                    "protocol_id": "keyword",
                    "name": "text",
                    "steps": "text",
                    "reagents": "text",
                    "target": "keyword"
                }
            },
            "lab_notes": {
                "name": "lab_notes",
                "vector_size": 384,
                "payload_schema": {
                    "note_id": "keyword",
                    "experimenter": "keyword",
                    "text": "text",
                    "mutation_context": "keyword",
                    "date": "keyword"
                }
            },
            "experimental_results": {
                "name": "experimental_results",
                "vector_size": 384,
                "payload_schema": {
                    "result_id": "keyword",
                    "candidate_id": "keyword",
                    "type": "keyword",
                    "measurement": "float",
                    "unit": "keyword",
                    "interpretation": "text"
                }
            }
        }
    
    def initialize_collections(self):
        """Initialize all Qdrant collections with proper configuration"""
        print("Initializing Qdrant collections...")
        
        for col_name, config in self.collections.items():
            try:
                # Delete if exists
                self.client.delete_collection(collection_name=config["name"])
            except:
                pass
            
            # Create collection
            self.client.create_collection(
                collection_name=config["name"],
                vectors_config=VectorParams(
                    size=config["vector_size"],
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created collection: {config['name']}")
    
    def load_mutations_to_qdrant(self, mutations_df: pd.DataFrame):
        """Load mutation data to Qdrant"""
        print(f"Loading {len(mutations_df)} mutations to Qdrant...")
        
        points = []
        
        for idx, row in tqdm(mutations_df.iterrows(), total=len(mutations_df)):
            # Create embedding text
            embed_text = f"""
            Mutation: {row.get('amino_acid_change', '')}
            Gene: {row.get('gene', 'ERBB2')}
            Type: {row.get('mutation_type', '')}
            Position: {row.get('protein_position', '')}
            Significance: {row.get('clinical_significance', '')}
            """
            
            # Generate embedding
            vector = self.embedder.encode(embed_text).tolist()
            
            # Generate unique ID
            mutation_id = row.get('mutation_id', f"MUT_{idx}")
            doc_hash = hashlib.md5(mutation_id.encode()).hexdigest()[:8]
            
            # Create payload
            payload = {
                "mutation_id": mutation_id,
                "gene": row.get('gene', 'ERBB2'),
                "amino_acid_change": str(row.get('amino_acid_change', '')),
                "mutation_type": str(row.get('mutation_type', 'Missense_Mutation')),
                "protein_position": int(row.get('protein_position', 0)) if pd.notna(row.get('protein_position')) else 0,
                "clinical_significance": str(row.get('clinical_significance', 'Unknown')),
                "resistance_info": f"Resistance information for {mutation_id}",
                "pubmed_refs": []
            }
            
            # Add PubMed references if available
            if 'pubmed_references' in row and isinstance(row['pubmed_references'], list):
                payload["pubmed_refs"] = row['pubmed_references']
            
            points.append(
                PointStruct(
                    id=int(doc_hash, 16) % 1000000,
                    vector=vector,
                    payload=payload
                )
            )
        
        # Upload to Qdrant
        self.client.upsert(
            collection_name=self.collections["her2_mutations"]["name"],
            points=points
        )
        
        print(f"✅ Loaded {len(points)} mutations to Qdrant")
    
    def load_antibodies_to_qdrant(self, antibodies_df: pd.DataFrame):
        """Load antibody data to Qdrant"""
        print(f"Loading {len(antibodies_df)} antibodies to Qdrant...")
        
        points = []
        
        for idx, row in tqdm(antibodies_df.iterrows(), total=len(antibodies_df)):
            # Create embedding from CDR3 (most important for binding)
            cdr3 = row.get('cdr3', '')
            if not cdr3 and 'sequence' in row:
                # Extract approximate CDR3 region
                seq = row['sequence']
                cdr3 = seq[-30:-15] if len(seq) > 45 else seq
            
            embed_text = f"""
            Antibody: {row.get('name', f'Antibody_{idx}')}
            Target: {row.get('target', 'HER2')}
            CDR3: {cdr3}
            Source: {row.get('source', 'Unknown')}
            Affinity: {row.get('affinity_nM', 'Unknown')} nM
            """
            
            vector = self.embedder.encode(embed_text).tolist()
            
            # Generate unique ID
            antibody_id = row.get('name', f"AB_{idx}")
            doc_hash = hashlib.md5(antibody_id.encode()).hexdigest()[:8]
            
            # Create payload
            payload = {
                "antibody_id": antibody_id,
                "name": row.get('name', f'Antibody_{idx}'),
                "target": row.get('target', 'HER2'),
                "sequence": row.get('sequence', ''),
                "cdr1": row.get('cdr1', ''),
                "cdr2": row.get('cdr2', ''),
                "cdr3": cdr3,
                "affinity_nM": float(row.get('affinity_nM', 0.0)) if pd.notna(row.get('affinity_nM')) else 0.0,
                "source": row.get('source', 'Unknown'),
                "pdb_id": row.get('pdb_id', ''),
                "reference": f"Reference for {antibody_id}"
            }
            
            points.append(
                PointStruct(
                    id=int(doc_hash, 16) % 1000000 + 1000000,  # Different ID range
                    vector=vector,
                    payload=payload
                )
            )
        
        self.client.upsert(
            collection_name=self.collections["antibody_db"]["name"],
            points=points
        )
        
        print(f"✅ Loaded {len(points)} antibodies to Qdrant")
    
    def load_abstracts_to_qdrant(self, abstracts_df: pd.DataFrame):
        """Load scientific abstracts to Qdrant"""
        print(f"Loading {len(abstracts_df)} abstracts to Qdrant...")
        
        points = []
        
        for idx, row in tqdm(abstracts_df.iterrows(), total=len(abstracts_df)):
            # Use full text for embedding
            full_text = row.get('full_text', f"{row.get('title', '')} {row.get('abstract', '')}")
            
            vector = self.embedder.encode(full_text[:1000]).tolist()  # Limit length
            
            # Generate unique ID
            pmid = row.get('pmid', f"ABS_{idx}")
            doc_hash = hashlib.md5(str(pmid).encode()).hexdigest()[:8]
            
            # Extract mutation mentions (simplified)
            mutation_mentions = []
            if 'mutations' in row and isinstance(row['mutations'], list):
                mutation_mentions = row['mutations']
            elif 'abstract' in row:
                # Simple keyword extraction
                text = row['abstract'].lower()
                if 'l755s' in text:
                    mutation_mentions.append('L755S')
                if 't798i' in text:
                    mutation_mentions.append('T798I')
                if 'd769h' in text:
                    mutation_mentions.append('D769H')
            
            # Extract antibody mentions
            antibody_mentions = []
            if 'antibodies' in row and isinstance(row['antibodies'], list):
                antibody_mentions = row['antibodies']
            
            payload = {
                "pmid": str(pmid),
                "title": row.get('title', ''),
                "abstract": row.get('abstract', ''),
                "full_text": full_text[:2000],  # Limit length
                "year": int(row.get('year', 0)) if str(row.get('year', '0')).isdigit() else 0,
                "author": row.get('author', ''),
                "keywords": ['HER2', 'breast cancer', 'resistance'],
                "mutation_mentions": mutation_mentions,
                "antibody_mentions": antibody_mentions
            }
            
            points.append(
                PointStruct(
                    id=int(doc_hash, 16) % 1000000 + 2000000,  # Different ID range
                    vector=vector,
                    payload=payload
                )
            )
        
        self.client.upsert(
            collection_name=self.collections["scientific_literature"]["name"],
            points=points
        )
        
        print(f"✅ Loaded {len(points)} abstracts to Qdrant")

    def load_protocols_to_qdrant(self, protocols_df: pd.DataFrame):
        """Load synthesis protocols to Qdrant"""
        if protocols_df.empty: return
        print(f"Loading {len(protocols_df)} protocols to Qdrant...")
        points = []
        for idx, row in protocols_df.iterrows():
            text = f"Protocol: {row['name']}. Steps: {row['steps']}"
            vector = self.embedder.encode(text[:1000]).tolist()
            doc_hash = hashlib.md5(str(row['protocol_id']).encode()).hexdigest()[:8]
            points.append(PointStruct(id=int(doc_hash, 16) % 1000000 + 4000000, vector=vector, payload=row.to_dict()))
        self.client.upsert(collection_name="synthesis_protocols", points=points)

    def load_lab_notes_to_qdrant(self, notes_df: pd.DataFrame):
        """Load lab notes to Qdrant"""
        if notes_df.empty: return
        print(f"Loading {len(notes_df)} lab notes to Qdrant...")
        points = []
        for idx, row in notes_df.iterrows():
            text = f"Lab Note ({row['mutation_context']}): {row['text']}"
            vector = self.embedder.encode(text[:1000]).tolist()
            doc_hash = hashlib.md5(str(row['note_id']).encode()).hexdigest()[:8]
            points.append(PointStruct(id=int(doc_hash, 16) % 1000000 + 5000000, vector=vector, payload=row.to_dict()))
        self.client.upsert(collection_name="lab_notes", points=points)

    def load_experimental_results_to_qdrant(self, results_df: pd.DataFrame):
        """Load granular experimental results to Qdrant"""
        if results_df.empty: return
        print(f"Loading {len(results_df)} experimental results to Qdrant...")
        points = []
        for idx, row in results_df.iterrows():
            text = f"Result for {row['candidate_id']}: {row['type']} - {row['interpretation']}"
            vector = self.embedder.encode(text[:1000]).tolist()
            doc_hash = hashlib.md5(str(row['result_id']).encode()).hexdigest()[:8]
            points.append(PointStruct(id=int(doc_hash, 16) % 1000000 + 6000000, vector=vector, payload=row.to_dict()))
        self.client.upsert(collection_name="experimental_results", points=points)
    
    def search_mutations(self, query: str, limit: int = 5):
        """Search for mutations similar to query"""
        query_vector = self.embedder.encode(query).tolist()
        
        results = self.client.query_points(
            collection_name=self.collections["her2_mutations"]["name"],
            query=query_vector,
            limit=limit
        ).points
        
        return [
            {
                "score": hit.score,
                "mutation_id": hit.payload.get("mutation_id"),
                "amino_acid_change": hit.payload.get("amino_acid_change"),
                "clinical_significance": hit.payload.get("clinical_significance"),
                "protein_position": hit.payload.get("protein_position"),
                "pubmed_refs": hit.payload.get("pubmed_refs", [])
            }
            for hit in results
        ]
    
    def search_antibodies_by_mutation(self, mutation_id: str, limit: int = 10):
        """Search for antibodies relevant to a specific mutation"""
        # First get mutation details
        mutation_results = self.search_mutations(mutation_id, limit=1)
        
        if not mutation_results:
            return []
        
        mutation = mutation_results[0]
        
        # Search for antibodies with similar context
        query_text = f"Antibodies targeting HER2 with mutation {mutation_id} at position {mutation.get('protein_position', '')}"
        query_vector = self.embedder.encode(query_text).tolist()
        
        results = self.client.query_points(
            collection_name=self.collections["antibody_db"]["name"],
            query=query_vector,
            limit=limit
        ).points
        
        return [
            {
                "score": hit.score,
                "antibody_id": hit.payload.get("antibody_id"),
                "name": hit.payload.get("name"),
                "cdr3": hit.payload.get("cdr3"),
                "affinity_nM": hit.payload.get("affinity_nM"),
                "source": hit.payload.get("source")
            }
            for hit in results
        ]
    
    def search_literature(self, query: str, mutation_filter: str = None, limit: int = 5):
        """Search scientific literature with optional mutation filter"""
        query_vector = self.embedder.encode(query).tolist()
        
        # Apply filter if provided
        search_filter = None
        if mutation_filter:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="mutation_mentions",
                        match=MatchValue(value=mutation_filter)
                    )
                ]
            )
        
        results = self.client.query_points(
            collection_name=self.collections["scientific_literature"]["name"],
            query=query_vector,
            query_filter=search_filter,
            limit=limit
        ).points
        
        return [
            {
                "score": hit.score,
                "pmid": hit.payload.get("pmid"),
                "title": hit.payload.get("title"),
                "abstract": hit.payload.get("abstract")[:200] + "...",
                "year": hit.payload.get("year"),
                "mutation_mentions": hit.payload.get("mutation_mentions", [])
            }
            for hit in results
        ]
    
    def search_experiments(self, query: str, limit: int = 5):
        """Search for similar lab experiments"""
        query_vector = self.embedder.encode(query).tolist()
        
        results = self.client.query_points(
            collection_name=self.collections["lab_experiments"]["name"],
            query=query_vector,
            limit=limit
        ).points
        
        return [
            {
                "score": hit.score,
                "exp_id": hit.payload.get("exp_id"),
                "outcome": hit.payload.get("outcome"),
                "notes": hit.payload.get("notes"),
                "measurements": hit.payload.get("measurements")
            }
            for hit in results
        ]
    
    def get_collection_stats(self):
        """Get statistics for all collections"""
        stats = {}
        
        for col_name, config in self.collections.items():
            try:
                info: CollectionInfo = self.client.get_collection(collection_name=config["name"])
                stats[col_name] = {
                    "vectors_count": info.vectors_count,
                    "points_count": info.points_count,
                    "status": "Active"
                }
            except Exception as e:
                stats[col_name] = {"status": f"Error: {str(e)}"}
        
        return stats

    def seed_experiments(self):
        """Seed default experimental data if collection is empty"""
        stats = self.get_collection_stats()
        if stats.get('lab_experiments', {}).get('vectors_count', 0) == 0:
            print("🌱 Seeding lab experiments collection...")
            exp_data = pd.DataFrame([
                {"exp_id": "EXP-H2-001", "mutation": "L755S", "conditions": "pH 7.4, 37°C, SPR Assay", "measurements": 0.85, "outcome": "Success", "notes": "Strong binding with optimized CDR3 aromatic clusters."},
                {"exp_id": "EXP-H2-002", "mutation": "T798I", "conditions": "pH 6.5, 37°C, Cell-based", "measurements": 0.12, "outcome": "Failure", "notes": "Gatekeeper mutation blocks binding pocket; steric hindrance observed."},
                {"exp_id": "EXP-H2-003", "mutation": "V777L", "conditions": "pH 7.4, 4°C, Flow Cytometry", "measurements": 0.76, "outcome": "Success", "notes": "Hydrophobic patch optimization improved stability by 24%."},
                {"exp_id": "EXP-H3-001", "mutation": "D769H", "conditions": "pH 7.2, 37°C, ELISA", "measurements": 0.45, "outcome": "Success", "notes": "Electrostatic interaction restored via Histidine-targeting motifs."},
                {"exp_id": "EXP-H3-002", "mutation": "L755S", "conditions": "pH 5.5, 37°C, Stability", "measurements": 0.31, "outcome": "Failure", "notes": "Protein aggregation observed in acidic endosomal-mimic conditions."}
            ])
            points = []
            for idx, row in exp_data.iterrows():
                text = f"Experiment {row['exp_id']} for {row['mutation']}: {row['notes']}"
                vector = self.embedder.encode(text).tolist()
                points.append(PointStruct(id=3000000+idx, vector=vector, payload=row.to_dict()))
            self.client.upsert(collection_name="lab_experiments", points=points)
            print(f"✅ Seeded {len(points)} experiments")

if __name__ == "__main__":
    # Test the Qdrant setup
    qdrant_manager = QdrantRealDataManager()
    qdrant_manager.initialize_collections()
    
    # Load sample data
    from data_loader import HER2DataLoader
    loader = HER2DataLoader()
    mutations, antibodies, abstracts = loader.process_all_data()
    
    # Load data to Qdrant
    qdrant_manager.load_mutations_to_qdrant(mutations)
    qdrant_manager.load_antibodies_to_qdrant(antibodies)
    qdrant_manager.load_abstracts_to_qdrant(abstracts)
    
    # Load sample experiments
    exp_data = pd.DataFrame([
        {"exp_id": "EXP001", "mutation": "L755S", "conditions": "pH 7.4, 37C", "measurements": 0.85, "outcome": "Success", "notes": "High binding affinity observed"},
        {"exp_id": "EXP002", "mutation": "T798I", "conditions": "pH 6.8, 37C", "measurements": 0.12, "outcome": "Failure", "notes": "Poor stability in acidic conditions"}
    ])
    
    points = []
    for idx, row in exp_data.iterrows():
        text = f"Experiment {row['exp_id']} for {row['mutation']}: {row['notes']}"
        vector = qdrant_manager.embedder.encode(text).tolist()
        points.append(PointStruct(id=3000000+idx, vector=vector, payload=row.to_dict()))
    
    qdrant_manager.client.upsert(collection_name="lab_experiments", points=points)
    print(f"✅ Loaded {len(points)} sample experiments")

    # Get stats
    stats = qdrant_manager.get_collection_stats()
    print("\n📊 Qdrant Collection Stats:")
    for col, stat in stats.items():
        print(f"   {col}: {stat.get('vectors_count', 'N/A')} vectors")