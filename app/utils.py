import os
from pathlib import Path
from app.config import settings

def allowed_file(filename: str) -> bool:
    extension = Path(filename).suffix.lower()
    return extension in settings.SUPPORTED_INPUT_FORMATS

def generate_output_filename(input_filename: str, output_format: str) -> str:
    stem = Path(input_filename).stem
    return f"{stem}_converted.{output_format}"

def get_quality_settings(quality: str) -> dict:
    quality_presets = {
        "low": {"video_bitrate": "500k", "audio_bitrate": "64k"},
        "medium": {"video_bitrate": "1000k", "audio_bitrate": "128k"},
        "high": {"video_bitrate": "2000k", "audio_bitrate": "192k"},
        "original": {"video_bitrate": None, "audio_bitrate": None}
    }
    return quality_presets.get(quality, quality_presets["medium"])

def cleanup_old_files(max_age_hours: int = 24):
    import time
    current_time = time.time()
    
    for directory in [settings.UPLOAD_DIR, settings.CONVERTED_DIR]:
        for file_path in directory.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file_path.unlink()