from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.job import job
from src.routers.log import log

description = """
Digitec Scrapy Server😎
"""

app = FastAPI(title="Digitec Scrapy Server", description=description)

app.include_router(job.router)
app.include_router(log.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)