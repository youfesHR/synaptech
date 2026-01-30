# HER2-ResistAID: Real Data Pipeline for Antibody Design

## 🎯 Project Overview
An AI-powered pipeline for designing patient-specific antibodies for HER2-positive breast cancer patients with resistance mutations. Uses **real biological data** from COSMIC, cBioPortal, PubMed, and antibody databases.

## 🧬 Real Data Sources
- **HER2 Mutations**: cBioPortal API (TCGA breast cancer data)
- **Antibody Sequences**: SAbDab database + therapeutic antibodies
- **Scientific Literature**: PubMed abstracts via NCBI EUtils API
- **Clinical Data**: Sample mutation profiles with resistance information

## 🗄️ Core Technology: Qdrant Vector Database
Qdrant serves as the central knowledge base with multiple specialized collections:

| Collection | Data Type | Records | Use Case |
|------------|-----------|---------|----------|
| `her2_mutations` | Mutation profiles | 50+ | Similarity search for mutation analogs |
| `antibody_database` | Antibody sequences | 20+ | Template-based design inspiration |
| `scientific_literature` | PubMed abstracts | 50+ | Evidence linking & validation |

### Key Qdrant Features:
- **Semantic search** using sentence-transformers embeddings
- **Multi-collection architecture** for different data types
- **Filtered search** (e.g., "papers mentioning L755S mutation")
- **Real-time candidate storage** for designed antibodies

## 🏗️ System Architecture: Multi-Agent Framework
The system implements a multi-agent AI framework designed for clinical utility:
1. **Similarity Scout**: Searches for mutation analogs and historical experiments.
2. **Antibody Designer**: Generates sequences using biochemical heuristics.
3. **Evidence Linker**: Connects design choices to PubMed literature.
4. **Feasibility Checker**: Validates chemical stability and manufacturing risks.
5. **RealDataOrchestrator**: Integrates all agents into a unified pipeline.

## 📊 Decision Quadrant
Candidates are prioritized on a 2D axis:
- **X-Axis**: Lab Feasibility (Calculated via BioPython & heuristics)
- **Y-Axis**: Scientific Support (Indexed from PubMed & historical trials)

## 🚀 Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Run the full app: `python run_app.py`
3. Access the Dashboard at `http://localhost:5173`

## 🔮 Multimodal Features
- **Text**: PubMed abstracts & Clinical notes
- **Sequences**: VH/VL CDR regions
- **Experiments**: Historical success/failure labels for similar mutations
