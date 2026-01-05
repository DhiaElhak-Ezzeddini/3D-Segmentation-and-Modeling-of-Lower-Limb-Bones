from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
import logging

from .presentation.api import router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="3D Bone Viewer API",
    description="Clean Architecture API for Medical Visualization",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
# We need to know where 'uploads' is relative to where we run.
# Assuming we run from 'backend/' directory root.
UPLOAD_DIR = Path("uploads")
PLY_DIR = UPLOAD_DIR / "ply"
IMPLANT_DIR = UPLOAD_DIR / "implants"

# Ensure directories exist
for dir_path in [PLY_DIR, IMPLANT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

app.mount("/ply", StaticFiles(directory=str(PLY_DIR)), name="ply")
app.mount("/implants", StaticFiles(directory=str(IMPLANT_DIR)), name="implants")

# Router
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8001, reload=True)
