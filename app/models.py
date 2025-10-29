from pydantic import BaseModel
from typing import Optional
from enum import Enum

class VideoFormat(str, Enum):
    MP4 = "mp4"
    AVI = "avi" 
    MOV = "mov"
    WEBM = "webm"
    MKV = "mkv"

class ConversionRequest(BaseModel):
    output_format: VideoFormat
    quality: str = "medium" 
    
    class Config:
        schema_extra = {
            "example": {
                "output_format": "mp4",
                "quality": "medium"
            }
        }

class ConversionResponse(BaseModel):
    task_id: str
    status: str
    message: str
    original_file: str
    output_format: str

class TaskStatus(BaseModel):
    task_id: str
    status: str 
    progress: int
    download_url: Optional[str] = None
    error_message: Optional[str] = None