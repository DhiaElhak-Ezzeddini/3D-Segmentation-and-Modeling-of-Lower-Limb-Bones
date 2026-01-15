from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .entities import SegmentationJob, Implant

class IBoneProcessor(ABC):
    @abstractmethod
    def process_segmentation(self, nifti_path: str, output_dir: str, downsample_factor: int = 2) -> Dict[str, Any]:
        """Process a NIfTI file and extract bones."""
        pass

class IStorageService(ABC):
    @abstractmethod
    def save_file(self, file_content: bytes, filename: str, directory: str) -> str:
        """Save a file to storage and return its path."""
        pass

    @abstractmethod
    def get_job_path(self, job_id: str) -> str:
        """Get the path for a specific job."""
        pass
    
    @abstractmethod
    def list_implants(self) -> List[Implant]:
        """List all available implants."""
        pass
