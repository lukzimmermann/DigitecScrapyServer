import os
import time
import uuid
import logging
import asyncio
import zipfile
import threading
from dotenv import load_dotenv

load_dotenv()

CLEAN_JOB_INTERVAL = int(os.getenv("CLEAN_JOB_INTERVAL"))
ZIP_JOB_INTERVAL = int(os.getenv("ZIP_JOB_INTERVAL"))
ZIP_SIZE = int(os.getenv("ZIP_SIZE"))
SCRAP_INTERVAL = float(os.getenv("SCRAP_INTERVAL"))
CONFIG_PATH = str(os.getenv("CONFIG_PATH"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE"))
BASELINE_PATH = str(os.getenv("BASELINE_PATH"))
BASELINE_ZIP_PATH = str(os.getenv("BASELINE_ZIP_PATH"))

logging.basicConfig(filename=f'{CONFIG_PATH}/logs', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class JobState():
    def __init__(self, start: int, end: int) -> None:
        self.id: str = str(uuid.uuid4())
        self.created: float = time.time()
        self.start: int = start
        self.end: int = end
        self.interval = SCRAP_INTERVAL
        self.is_running: bool = False
        self.user: JobUser = None

    def __repr__(self) -> str:
        if self.is_running: state = "IsRunning"
        else: state = "Finished"
        return f'{self.start:>9} -> {self.end:>9}, {state}'

class JobUser():
    def __init__(self, name: str, token: str) -> None:
        self.name = name
        self.token = token
        self.ip = ''
    
    def __repr__(self) -> str:
        return f'{self.name}@{self.ip}: {self.token}'

class JobService():
    def __init__(self) -> None:
        self.jobs: list[JobState] = self.__read_state_file()
        self.run_cleanup = True
        self.users: list[JobUser] = self.__read_users()
        asyncio.create_task(self.__clean_up_joblist())
        asyncio.create_task(self.start_pack_baseline())

    def get_job_by_id(self, id: str) -> JobState:
        for job in self.jobs:
            if job.id == id:
                return job
        return None

    def get_new_job(self, user: str, batch_size: int=BATCH_SIZE) -> JobState:
        self.jobs: list[JobState] = self.__read_state_file()
        for i, _ in enumerate(self.jobs):
            if i > 0:
                if self.jobs[i].start - self.jobs[i-1].end > 1:
                    if self.jobs[i].start-1 - self.jobs[i-1].end+1 > batch_size:
                        new_job = JobState(self.jobs[i-1].end+1, self.jobs[i-1].end+batch_size)
                    else:
                        new_job = JobState(self.jobs[i-1].end+1, self.jobs[i].start-1)
                    new_job.is_running = True
                    new_job.user = user
                    self.jobs.append(new_job)
                    self.jobs = sorted(self.jobs, key=lambda x: x.start)
                    return new_job
                
        new_job = JobState(self.jobs[-1].end+1, self.jobs[-1].end+batch_size)
        new_job.is_running = True
        new_job.user = user
        self.jobs.append(new_job)
        self.jobs = sorted(self.jobs, key=lambda x: x.start)
        return new_job

    def get_user_by_token(self, token: str):
        for user in self.users:
            if str(user.token) == str(token):
                return user
        return None
    
    def is_ip_address_present(self, ip: str):
        for job in self.jobs:
            if job.is_running and job.user.ip == ip:
                return True
        return False

    def is_job_active(self, id: str) -> bool:
        for job in self.jobs:
            if job.id.strip() == id.strip():
                return True
        return False

    def finish_job(self, id: str) -> None:
        for job in self.jobs:
            if job.id.strip() == id.strip():
                job.is_running = False
                self.__save_job_list()
                break

    def stop(self):
        self.run_cleanup = False
    
    async def __clean_up_joblist(self) -> None:
        while self.run_cleanup:
            new_joblist: list[JobState] = []
            for job in self.jobs:
                if not job.is_running:
                    new_joblist.append(job)
            self.jobs = new_joblist
            await asyncio.sleep(CLEAN_JOB_INTERVAL)
        
    def __save_job_list(self) -> None:
        string_list = []
        for job in self.jobs:
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
        
            
    def __read_state_file(self) -> list[JobState]:
        jobs: list[JobState] = []

        with open(f"{CONFIG_PATH}/job_state", "r") as file:
            data = file.readlines()
            for line in data:
                values = line.split('-')
                start = int(values[0].strip())
                end = int(values[1].strip())
                jobs.append(JobState(start, end))
        return jobs
    
    def __read_users(self):
        user_list: list[JobUser] = []
        with open(f'{CONFIG_PATH}/users', 'r') as file:
            lines = file.readlines()

        for line in lines:
            segment = line[0:-1].split(';')
            user_list.append(JobUser(segment[0],  segment[1]))

        return user_list
