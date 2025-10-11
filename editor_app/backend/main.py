from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys

# Add project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from routers.repository_router import router as repository_router
from routers.concept_router import router as concept_router
from routers.inference_router import router as inference_router
from routers.execution_router import router as execution_router
from routers.global_concept_router import router as global_concept_router
from routers.global_inference_router import router as global_inference_router

app = FastAPI(
    title="Normcode Editor API",
    description="API for the Normcode Editor MVP",
    version="1.0.0"
)

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(repository_router)
app.include_router(concept_router)
app.include_router(inference_router)
app.include_router(execution_router)
app.include_router(global_concept_router)
app.include_router(global_inference_router)

# Mount static files (frontend)
frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def root():
    """Serve the frontend index.html file."""
    from fastapi.responses import FileResponse
    frontend_path = os.path.join(frontend_dir, 'index.html')
    return FileResponse(frontend_path)

# --- How to Run ---
# To run this server, navigate to the `editor_app/backend` directory in your terminal
# and run the following command:
# uvicorn main:app --reload

if __name__ == "__main__":
    # This allows running the app directly for simple testing, though uvicorn is preferred.
    uvicorn.run(app, host="127.0.0.1", port=8000)


# Create data directories if they don't exist
DATA_ROOT = os.path.join(PROJECT_ROOT, 'data')
REPO_STORAGE_DIR = os.path.join(DATA_ROOT, 'repositories')
LOGS_DIR = os.path.join(DATA_ROOT, 'logs')
CONCEPTS_DIR = os.path.join(DATA_ROOT, 'concepts')
INFERENCES_DIR = os.path.join(DATA_ROOT, 'inferences')

os.makedirs(REPO_STORAGE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CONCEPTS_DIR, exist_ok=True)
os.makedirs(INFERENCES_DIR, exist_ok=True)
