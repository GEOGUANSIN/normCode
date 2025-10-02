from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from routers.repository_router import router as repository_router

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
    uvicorn.run(app, host="127.0.0.1", port=8001)


# Create data directories if they don't exist
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REPO_STORAGE_DIR = os.path.join(PROJECT_ROOT, 'editor_app_data', 'repositories')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'editor_app_data', 'logs')

os.makedirs(REPO_STORAGE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
