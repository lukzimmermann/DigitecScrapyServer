import zipfile
import io
import os
import logging
import time
import datetime
import numpy as np
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from typing import Annotated
from dotenv import load_dotenv
from src.routers.job.jobService import JobService, User
from src.model.jobDto import BatchRequestDto, BatchDto, JobStatusDto

load_dotenv()

DATA_PATH = os.getenv("BASELINE_PATH")
CONFIG_PATH = os.getenv("CONFIG_PATH")
BATCH_SIZE = int(os.getenv("BATCH_SIZE"))

logging.basicConfig(filename=f'{CONFIG_PATH}/logs', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/job", tags=["Job"])

job_service = JobService()

@router.post("/get_batch/")
async def get_batch(batch_request_data: BatchRequestDto) -> BatchDto:
    return job_service.get_new_baseline_job(batch_request_data)
    
@router.get("/status/")
async def get_status() -> list[JobStatusDto]:
    status: list[JobStatusDto] = []
    for job in job_service.baseline_jobs:
        user: User = job.user
        if job.is_running:
            formatted_time = datetime.datetime.fromtimestamp(job.created).strftime('%Y-%m-%d %H:%M:%S')
            status.append(JobStatusDto(user_name=user.display_name, created=formatted_time, min_number=np.min(job.number_list), max_number=np.max(job.number_list), number_count=len(job.number_list)))
    return status
    
@router.post("/upload_batch/")
async def upload_batch(request: Request, id: Annotated[str, Form()], file: UploadFile = File(...)):
    #if job_service.is_job_active(id):
    job_service.finish_job(id)
    file_content = await file.read()
    file_content_io = io.BytesIO(file_content)
    job = job_service.get_job_by_id(id)
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
    with zipfile.ZipFile(file_content_io, "r") as zip_ref:
        file_names = zip_ref.namelist()
        number_files = len(file_names)
        zip_ref.extractall(DATA_PATH)
    logging.info(f'{job.user.display_name}@{job.user.ip} send {number_files} datasets from {job.start} to {job.end} ({((number_files)/(job.end-job.start+1)*100):.1f}%) in {(time.time() - job.created):.1f}s ({(float(BATCH_SIZE)/(time.time() - job.created)):.1f}A/s)')
    return {"message": "Files uploaded and extracted successfully"}
    #else:
    #    raise HTTPException(status_code=404, detail="No corresponding job found")


@router.on_event("shutdown")
async def on_shutdown():
    job_service.stop()
