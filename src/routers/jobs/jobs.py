import zipfile
import io
import os
from fastapi import APIRouter, Query, File, UploadFile, Form, HTTPException
from typing import Annotated
from pydantic import BaseModel
from src.routers.jobs.jobsService import JobService

class Job(BaseModel):
    id: str

    def __repr__(self) -> str:
        return super().__repr__()

router = APIRouter(prefix="/jobs", tags=["Jobs"])

job_service = JobService()

@router.get("/get_batch/", tags=["Jobs"])
async def get_batch(batch_size: Annotated[int | None, Query()] = None):
    if batch_size == None:
        return job_service.get_new_job()
    elif batch_size > 0 and batch_size <= 10000:
        return job_service.get_new_job(batch_size)
    else: return {"error": "batch size has to be between 0 and 10000"}


@router.post("/upload_batch/")
async def upload_batch(id: Annotated[str, Form()], file: UploadFile = File(...)):
    data_path = '/Users/lukas/Documents/LocalProjects/DigitecScrapyServer/data'

    if job_service.is_job_active(id):
        file_content = await file.read()
        file_content_io = io.BytesIO(file_content)

        if not os.path.exists(data_path):
            os.makedirs(data_path)

        with zipfile.ZipFile(file_content_io, "r") as zip_ref:
            zip_ref.extractall(data_path)

        job_service.finish_job(id)
        return {"message": "Files uploaded and extracted successfully"}
    else:
        raise HTTPException(status_code=403, detail="Not allowed")


@router.on_event("shutdown")
async def on_shutdown():
    job_service.stop()
