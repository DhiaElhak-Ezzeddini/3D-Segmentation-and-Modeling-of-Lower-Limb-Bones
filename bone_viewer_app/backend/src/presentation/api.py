from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List

from ..application.services import BoneService
from ..infrastructure.nifti_processor import NiftiBoneProcessor
from ..infrastructure.storage import FileSystemStorage

router = APIRouter()

# Dependency Injection
def get_bone_service():
    storage = FileSystemStorage()
    processor = NiftiBoneProcessor()
    return BoneService(processor, storage)

@router.get("/")
async def root():
    return {
        "status": "ok",
        "message": "3D Bone Viewer API (Clean Arch) is running",
        "version": "2.0.0"
    }

@router.post("/upload-segmentation")
async def upload_segmentation(
    file: UploadFile = File(...),
    service: BoneService = Depends(get_bone_service)
):
    if not file.filename.endswith(('.nii', '.nii.gz')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload NIfTI.")
    
    try:
        result = service.process_segmentation(file.file, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bones/{job_id}")
async def get_bones_list(
    job_id: str,
    service: BoneService = Depends(get_bone_service)
):
    metadata = service.get_job_metadata(job_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Job not found")
    return metadata

@router.get("/bones/{job_id}/{bone_name}")
async def get_bone_ply(job_id: str, bone_name: str):
    # This might be better served via StaticFiles for performance, 
    # but keeping it here for API completeness/control if needed.
    # Currently handled by StaticFiles mount in main.py usually, 
    # but let's see how the previous main.py did it. 
    # Previous app had both. Let's keep a direct file server here just in case.
    storage = FileSystemStorage()
    ply_path = Path(storage.get_job_path(job_id)) / f"{bone_name}.ply"
    
    if not ply_path.exists():
        raise HTTPException(status_code=404, detail="Bone not found")
        
    return FileResponse(ply_path, media_type="application/octet-stream", filename=f"{bone_name}.ply")

@router.post("/upload-implant")
async def upload_implant(
    file: UploadFile = File(...),
    service: BoneService = Depends(get_bone_service)
):
    valid_extensions = ('.stl', '.ply', '.obj')
    if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid file format")
        
    try:
        implant = service.upload_implant(file.file, file.filename)
        return implant
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/implants")
async def list_implants(
    service: BoneService = Depends(get_bone_service)
):
    implants = service.list_implants()
    return {"implants": implants, "total": len(implants)}

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    # For now, simplistic implementation direct to storage
    # ideally this goes through service
    import shutil
    storage = FileSystemStorage()
    job_path = Path(storage.get_job_path(job_id))
    if job_path.exists():
        shutil.rmtree(job_path)
        return {"success": True}
    raise HTTPException(status_code=404, detail="Job not found")
