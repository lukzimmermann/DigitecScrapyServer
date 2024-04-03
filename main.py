from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.jobs import jobs

description = """
Digitec Scrapy Server😎
"""

app = FastAPI(title="Digitec Scrapy Server", description=description)

app.include_router(jobs.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)