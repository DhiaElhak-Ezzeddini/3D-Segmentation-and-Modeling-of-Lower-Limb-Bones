from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Bone:
    name: str
    label_id: int
    filename: str
    num_voxels: int
    num_points: int
    color: List[int]
    bounding_box: Dict[str, Any]

@dataclass
class SegmentationJob:
    job_id: str
    filename: str
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    bones: List[Bone] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Implant:
    filename: str
    size_mb: float
    url: str
