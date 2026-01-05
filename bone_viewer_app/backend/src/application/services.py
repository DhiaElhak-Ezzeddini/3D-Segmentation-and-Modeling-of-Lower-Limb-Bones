from typing import List, Dict, Any, BinaryIO
import uuid
from ..domain.interfaces import IBoneProcessor, IStorageService
from ..domain.entities import Implant

class BoneService:
    def __init__(self, bone_processor: IBoneProcessor, storage_service: IStorageService):
        self.bone_processor = bone_processor
        self.storage_service = storage_service

    def process_segmentation(self, file_object: BinaryIO, filename: str) -> Dict[str, Any]:
        # Generate job ID
        job_id = str(uuid.uuid4())[:8]
        saved_filename = f"{job_id}_{filename}"
        
        # Save file
        file_path = self.storage_service.save_file(file_object, saved_filename, 'segmentation')
        
        # Prepare output directory
        output_dir = self.storage_service.get_job_path(job_id)
        
        # Process
        metadata = self.bone_processor.process_segmentation(file_path, output_dir)
        
        return {
            "success": True,
            "job_id": job_id,
            "filename": filename,
            "metadata": metadata
        }

    def get_job_metadata(self, job_id: str) -> Dict[str, Any]:
        output_dir = self.storage_service.get_job_path(job_id)
        # In a real database, we'd query the DB. Here we read the JSON we saved.
        import json
        from pathlib import Path
        
        metadata_file = Path(output_dir) / "metadata.json"
        if not metadata_file.exists():
            return None
            
        with open(metadata_file, 'r') as f:
            return json.load(f)

    def upload_implant(self, file_object: BinaryIO, filename: str) -> Implant:
        self.storage_service.save_file(file_object, filename, 'implant')
        # We need to return the Implant object, but save_file doesn't return size.
        # We can fetch the list and find it, or update save_file.
        # For simplicity, we'll re-list or check the file stats.
        # Let's simple re-list and filter for now as it's low traffic.
        implants = self.storage_service.list_implants()
        for implant in implants:
            if implant.filename == filename:
                return implant
        raise RuntimeError("Implant saved but not found")

    def list_implants(self) -> List[Implant]:
        return self.storage_service.list_implants()
