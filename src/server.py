from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import RealDataOrchestrator

app = FastAPI(title="HER2-ResistAID API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = None

@app.on_event("startup")
async def startup_event():
    global orchestrator
    print("🚀 Starting HER2-ResistAID Orchestrator...")
    orchestrator = RealDataOrchestrator(use_existing_data=True)

class MutationRequest(BaseModel):
    mutation_id: str
    num_candidates: Optional[int] = 3

@app.get("/")
async def root():
    return {"status": "online", "message": "HER2-ResistAID API is running"}

@app.get("/stats")
async def get_stats():
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System initializing")
    return orchestrator.qdrant_manager.get_collection_stats()

@app.post("/analyze")
async def analyze_mutation(request: MutationRequest):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System initializing")
    
    try:
        report = orchestrator.run_for_mutation(
            request.mutation_id, 
            num_candidates=request.num_candidates
        )
        return report
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mutations")
async def list_mutations():
    if not orchestrator:
        return []
    # Return unique mutations from processed data
    return orchestrator.mutations['mutation_id'].unique().tolist()

@app.get("/literature")
async def get_literature(query: Optional[str] = "HER2 resistance"):
    if not orchestrator:
        return []
    return orchestrator.qdrant_manager.search_literature(query=query, limit=20)

@app.get("/experiments")
async def get_experiments(query: Optional[str] = "HER2"):
    if not orchestrator:
        return []
    return orchestrator.qdrant_manager.search_experiments(query=query, limit=20)

@app.get("/protocols")
async def get_protocols():
    if not orchestrator: return []
    return orchestrator.protocols.to_dict('records')

@app.get("/lab-notes")
async def get_lab_notes():
    if not orchestrator: return []
    return orchestrator.lab_notes.to_dict('records')

@app.get("/results")
async def get_results(candidate_id: Optional[str] = None):
    if not orchestrator: return []
    if candidate_id:
        return orchestrator.experimental_results[orchestrator.experimental_results['candidate_id'] == candidate_id].to_dict('records')
    return orchestrator.experimental_results.to_dict('records')

@app.get("/images")
async def get_images(candidate_id: Optional[str] = None):
    if not orchestrator: return []
    if candidate_id:
        return orchestrator.images[orchestrator.images['candidate_id'] == candidate_id].to_dict('records')
    return orchestrator.images.to_dict('records')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
