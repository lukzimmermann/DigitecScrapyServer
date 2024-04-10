import os
import time
import datetime
import logging
import asyncio
import zipfile
import threading
from dotenv import load_dotenv
from fastapi import HTTPException
from src.model.jobModel import JobUser, Job, BaseLineJob
from src.model.jobDto import BatchRequestDto, BatchDto
from src.utils.logger import logger

load_dotenv()

CLEAN_JOB_INTERVAL = int(os.getenv("CLEAN_JOB_INTERVAL"))
ZIP_JOB_INTERVAL = int(os.getenv("ZIP_JOB_INTERVAL"))
ZIP_SIZE = int(os.getenv("ZIP_SIZE"))
SCRAP_INTERVAL = float(os.getenv("SCRAP_INTERVAL"))
CONFIG_PATH = str(os.getenv("CONFIG_PATH"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE"))
BASELINE_PATH = str(os.getenv("BASELINE_PATH"))
BASELINE_ZIP_PATH = str(os.getenv("BASELINE_ZIP_PATH"))



class JobService():
    def __init__(self) -> None:
        self.baseline_jobs: list[BaseLineJob] = self.__read_state_file()
        self.run_cleanup = True
        self.users: list[JobUser] = self.__read_users()
        asyncio.create_task(self.__clean_up_joblist())
        #asyncio.create_task(self.start_pack_baseline())

    def get_job_by_id(self, id: str) -> Job:
        for job in self.baseline_jobs:
            if job.id == id:
                return job
        return None

    def get_new_baseline_job(self, batch_request_data: BatchRequestDto) -> Job:
        self.__validate_batch_request(batch_request_data)
        user: JobUser = self.get_user_by_token(batch_request_data.token)
        user.ip = batch_request_data.ip
        user.display_name = batch_request_data.display_name

        self.baseline_jobs: list[BaseLineJob] = self.__read_state_file()
        self.baseline_jobs[0]
        start = self.baseline_jobs[-1].end+1
        end = self.baseline_jobs[-1].end+BATCH_SIZE
        job: BaseLineJob = None

        for i, _ in enumerate(self.baseline_jobs):
            if i > 0 and self.baseline_jobs[i].start - self.baseline_jobs[i-1].end > 1:
                start = self.baseline_jobs[i-1].end+1
                end = self.baseline_jobs[i].start-1
                if self.baseline_jobs[i].start-1 - self.baseline_jobs[i-1].end+1 > BATCH_SIZE:
                    end = self.baseline_jobs[i-1].end+BATCH_SIZE
                job = self.__create_new_baseline_job(user, start, end)
        
        job = self.__create_new_baseline_job(user, start, end)
        
        formatted_time = datetime.datetime.fromtimestamp(job.created).strftime('%Y-%m-%d %H:%M:%S')
        logging.debug(f'{user.display_name}@{user.ip} get a new batch from {job.start} to {job.end}')

        batch = BatchDto(id = job.id, 
                         number_list = job.number_list,
                         interval = SCRAP_INTERVAL,
                         created = formatted_time,
                         user_name = user.display_name)
        
        return batch


    def get_user_by_token(self, token: str):
        for user in self.users:
            if str(user.token) == str(token):
                return user
        return None
    
    def is_ip_address_present(self, ip: str):
        for job in self.baseline_jobs:
            if job.is_running and job.user.ip == ip:
                return True
        return False

    def is_job_active(self, id: str) -> bool:
        for job in self.baseline_jobs:
            if job.id.strip() == id.strip():
                return True
        return False

    def finish_job(self, id: str) -> None:
        for job in self.baseline_jobs:
            if job.id.strip() == id.strip():
                job.is_running = False
                self.__save_job_list()
                break

    def stop(self):
        self.run_cleanup = False

    def __create_new_baseline_job(self, user: JobUser, start: int, end: int) -> BaseLineJob:
        new_job = BaseLineJob(user, start, end)
        self.baseline_jobs.append(new_job)
        self.baseline_jobs = sorted(self.baseline_jobs, key=lambda x: x.start)
        return new_job
    
    def __validate_batch_request(self, batch_request_data: BatchRequestDto):
        if self.get_user_by_token(batch_request_data.token) is None:
            logging.error(f'Unauthorized batch request from {batch_request_data.display_name}')
            raise HTTPException(status_code=401, detail="No valid token")
        if self.is_ip_address_present(batch_request_data.ip):
            logging.error(f'Request from user {batch_request_data.display_name} although there is still an open job under this ip')
            raise HTTPException(status_code=403, detail="IP address registered for another job, please wait...")
    
    async def __clean_up_joblist(self) -> None:
        while self.run_cleanup:
            new_joblist: list[Job] = []
            for job in self.baseline_jobs:
                if not job.is_running:
                    new_joblist.append(job)
            self.baseline_jobs = new_joblist
            await asyncio.sleep(CLEAN_JOB_INTERVAL)
        
    def __save_job_list(self) -> None:
        string_list = []
        for job in self.baseline_jobs:
            if not job.is_running:
                string_list.append(f'{job.start} - {job.end}\n')

        with open(f"{CONFIG_PATH}/job_state", 'w') as file:
            file.writelines(string_list)

    async def start_pack_baseline(self):
        while self.run_cleanup:
            thread = threading.Thread(target=self.pack_baseline, args=(BASELINE_PATH, BASELINE_ZIP_PATH, ZIP_SIZE))
            thread.start()
            await asyncio.sleep(ZIP_JOB_INTERVAL)

    def pack_baseline(self, baseline_path: str, baseline_zip_path: str, zip_size: int = 100000):
        logging.info("---- Start pack-baseline service ----")
        start_time = time.time()
        if not os.path.exists(baseline_path):
            os.mkdir(baseline_path)
        if len(os.listdir(baseline_path)) > zip_size:
            zip_files = []
            files = []
            file_list = os.listdir(baseline_path)
            file_list =  sorted(file_list, key=lambda x: int(x.split('_')[0]))
            for i, file in enumerate(file_list):
                full_path = os.path.join(baseline_path, file)
                if i != 0:
                    files.append([file, full_path])
                    if i%zip_size == 0:
                        zip_files.append(files)
                        files = []
            for zip_file in zip_files:
                start = zip_file[0][0].split('_')[0]
                end = zip_file[-1][0].split('_')[0]
                zip_filename = f"{start}_{end}.zip"
                if not os.path.exists(baseline_zip_path):
                    os.mkdir(baseline_zip_path)
                logging.info(f"pack-baseline service: start creating {zip_filename}")
                with zipfile.ZipFile(os.path.join(baseline_zip_path, zip_filename), 'w') as zipf:
                    for file in zip_file:
                        zipf.write(file[1], os.path.basename(file[1]))
                        os.remove(file[1])
                logging.info(f"pack-baseline service: end creating {zip_filename}")
            logging.info(f"pack-baseline service: successful after {(time.time()-start_time):.1f}s")
        else:
            logging.info(f"pack-baseline service: nothing to pack after {(time.time()-start_time):.1f}s")
        
            
    def __read_state_file(self) -> list[BaseLineJob]:
        jobs: list[BaseLineJob] = []

        with open(f"{CONFIG_PATH}/job_state", "r") as file:
            data = file.readlines()
            for line in data:
                values = line.split('-')
                start = int(values[0].strip())
                end = int(values[1].strip())
                job = BaseLineJob(None, start, end)
                job.is_running = False
                jobs.append(job)
        return jobs
    
    def __read_users(self):
        user_list: list[JobUser] = []
        with open(f'{CONFIG_PATH}/users', 'r') as file:
            lines = file.readlines()

        for line in lines:
            segment = line[0:-1].split(';')
            user_list.append(JobUser(segment[0],  segment[1]))

        return user_list
