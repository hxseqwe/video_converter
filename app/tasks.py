import os
import ffmpeg
from celery import Celery
from pathlib import Path
import time
import subprocess

celery_app = Celery('video_converter')
celery_app.conf.broker_url = 'redis://localhost:6379/0'
celery_app.conf.result_backend = 'redis://localhost:6379/0'

@celery_app.task(bind=True)
def convert_video(self, input_path: str, output_format: str, quality: str = "medium"):
    """Фоновая задача для конвертации видео"""
    
    try:
        input_filename = Path(input_path).name
        output_filename = f"{Path(input_filename).stem}_converted.{output_format}"
        output_path = f"static/converted/{output_filename}"
        
        quality_settings = {
            "low": {"video_bitrate": "500k", "audio_bitrate": "64k"},
            "medium": {"video_bitrate": "1000k", "audio_bitrate": "128k"},
            "high": {"video_bitrate": "2000k", "audio_bitrate": "192k"},
            "original": {"video_bitrate": None, "audio_bitrate": None}
        }
        
        settings = quality_settings.get(quality, quality_settings["medium"])
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-y'
        ]
        
        if settings['video_bitrate']:
            cmd.extend(['-b:v', settings['video_bitrate']])
        if settings['audio_bitrate']:
            cmd.extend(['-b:a', settings['audio_bitrate']])
        
        cmd.append(output_path)
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        for i in range(10):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': (i + 1) * 10,
                    'total': 100,
                    'status': f'Конвертация {(i + 1) * 10}%'
                }
            )
            time.sleep(1)

        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr.decode()}")
        
        return {
            'status': 'SUCCESS',
            'output_file': output_path,
            'output_filename': output_filename
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e)
        }

@celery_app.task
def cleanup_task():
    from app.utils import cleanup_old_files
    cleanup_old_files()