from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
import shutil
import uuid
from pathlib import Path
from app.config import settings
from app.models import ConversionRequest, ConversionResponse, TaskStatus, VideoFormat
from app.tasks import convert_video, cleanup_task
from app.utils import allowed_file, generate_output_filename

app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_model=ConversionResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: VideoFormat = Form(...),
    quality: str = Form("medium")
):
    
    if not file:
        raise HTTPException(status_code=400, detail="Файл не предоставлен")
    
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Неподдерживаемый формат файла. Поддерживаются: {', '.join(settings.SUPPORTED_INPUT_FORMATS)}"
        )
    
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = settings.UPLOAD_DIR / unique_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла: {str(e)}")
    
    task = convert_video.delay(str(file_path), output_format.value, quality)
    
    background_tasks.add_task(cleanup_task)
    
    return ConversionResponse(
        task_id=task.id,
        status="started",
        message="Конвертация начата",
        original_file=file.filename,
        output_format=output_format.value
    )

@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    from app.tasks import celery_app
    
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        response = TaskStatus(
            task_id=task_id,
            status='PENDING',
            progress=0
        )
    elif task_result.state == 'PROGRESS':
        response = TaskStatus(
            task_id=task_id,
            status='PROGRESS',
            progress=task_result.info.get('current', 0)
        )
    elif task_result.state == 'SUCCESS':
        result = task_result.result
        download_url = f"/download/{Path(result['output_file']).name}"
        response = TaskStatus(
            task_id=task_id,
            status='SUCCESS',
            progress=100,
            download_url=download_url
        )
    else:
        response = TaskStatus(
            task_id=task_id,
            status='FAILURE',
            progress=0,
            error_message=str(task_result.info)
        )
    
    return response

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = settings.CONVERTED_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.get("/api/formats")
async def get_supported_formats():
    return {
        "input_formats": settings.SUPPORTED_INPUT_FORMATS,
        "output_formats": list(settings.SUPPORTED_OUTPUT_FORMATS.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)