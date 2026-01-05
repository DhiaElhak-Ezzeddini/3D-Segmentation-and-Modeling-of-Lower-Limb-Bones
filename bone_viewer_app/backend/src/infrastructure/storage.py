import shutil
from pathlib import Path
from typing import List
from ..domain.interfaces import IStorageService
from ..domain.entities import Implant

class FileSystemStorage(IStorageService):
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.segmentation_dir = self.base_path / "segmentations"
        self.ply_dir = self.base_path / "ply"
        self.implant_dir = self.base_path / "implants"
        
        # Create directories
        for dir_path in [self.segmentation_dir, self.ply_dir, self.implant_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_object, filename: str, directory_type: str) -> str:
        """
        Save a file object (like UploadFile.file) to disk.
        directory_type: 'segmentation' or 'implant'
        """
        if directory_type == 'segmentation':
            target_dir = self.segmentation_dir
        elif directory_type == 'implant':
            target_dir = self.implant_dir
        else:
            raise ValueError(f"Unknown directory type: {directory_type}")
            
        file_path = target_dir / filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_object, buffer)
            
        return str(file_path)

    def get_job_path(self, job_id: str) -> str:
        return str(self.ply_dir / job_id)
        
    def list_implants(self) -> List[Implant]:
        implants = []
        for implant_file in self.implant_dir.iterdir():
            if implant_file.is_file():
                size_mb = implant_file.stat().st_size / (1024 * 1024)
                implants.append(Implant(
                    filename=implant_file.name,
                    size_mb=round(size_mb, 2),
                    url=f"/implants/{implant_file.name}"
                ))
        return implants
