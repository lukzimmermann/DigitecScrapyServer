import zipfile
import io
import os
import logging
import sys
from fastapi import APIRouter, Query, File, UploadFile, Form, HTTPException, Request
from typing import Annotated
from pydantic import BaseModel
from dotenv import load_dotenv
from src.routers.jobs.jobsService import JobService

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

log_format = "%(asctime)s - %(client_ip)s - %(levelname)s: %(message)s"
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=log_format)

class Job(BaseModel):
    id: str

    def __repr__(self) -> str:
        return super().__repr__()

router = APIRouter(prefix="/jobs", tags=["Jobs"])

job_service = JobService()

@router.get("/get_batch/", tags=["Jobs"])
async def get_batch(request: Request, batch_size: Annotated[int | None, Query()] = None):
    if batch_size == None:
        new_job = job_service.get_new_job()
        print(f"{request.client.host} get a new batch from {new_job.start} to {new_job.end}")
        return new_job
    elif batch_size > 0 and batch_size <= 10000:
        return job_service.get_new_job(batch_size)
    else: return {"error": "batch size has to be between 0 and 10000"}


@router.post("/upload_batch/")
async def upload_batch(request: Request, id: Annotated[str, Form()], file: UploadFile = File(...)):
    if job_service.is_job_active(id):
        file_content = await file.read()
        file_content_io = io.BytesIO(file_content)

        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

        with zipfile.ZipFile(file_content_io, "r") as zip_ref:
            zip_ref.extractall(DATA_PATH)

        job_service.finish_job(id)
        print(f"{request.client.host} are finished with job {id}")
        return {"message": "Files uploaded and extracted successfully"}
    else:
        raise HTTPException(status_code=403, detail="Not allowed")


@router.on_event("shutdown")
async def on_shutdown():
    job_service.stop()
