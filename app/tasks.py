import os
import ffmpeg
from celery import Celery
from pathlib import Path
from app.config import settings
from app.utils import generate_output_filename, get_quality_settings

celery_app = Celery(
    'video_converter',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task(bind=True)
def convert_video(self, input_path: str, output_format: str, quality: str = "medium"):
    
    try:
        input_filename = Path(input_path).name
        output_filename = generate_output_filename(input_filename, output_format)
        output_path = settings.CONVERTED_DIR / output_filename
        
        quality_settings = get_quality_settings(quality)
        
        probe = ffmpeg.probe(input_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        if not video_stream:
            raise Exception("Не удалось найти видео поток в файле")
        
        output_args = {
            'format': output_format,
        }
        
        if quality_settings['video_bitrate']:
            output_args['video_bitrate'] = quality_settings['video_bitrate']
        if quality_settings['audio_bitrate']:
            output_args['audio_bitrate'] = quality_settings['audio_bitrate']
        
        (
            ffmpeg
            .input(input_path)
            .output(str(output_path), **output_args)
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        
        for i in range(100):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': 100,
                    'status': f'Конвертация {i+1}%'
                }
            )
            import time
            time.sleep(0.1)
        
        return {
            'status': 'SUCCESS',
            'output_file': str(output_path),
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