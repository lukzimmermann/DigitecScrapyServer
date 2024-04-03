from fastapi import FastAPI
from src.routers.jobs import jobs

description = """
Digitec Scrapy Server😎
"""

app = FastAPI(title="Digitec Scrapy Server", description=description)

app.include_router(jobs.router)
