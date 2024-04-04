import os
import time
import uuid
import asyncio
from dotenv import load_dotenv

load_dotenv()

CLEAN_JOB_INTERVAL = int(os.getenv("CLEAN_JOB_INTERVAL"))
SCRAP_INTERVAL = float(os.getenv("SCRAP_INTERVAL"))
CONFIG_PATH = str(os.getenv("CONFIG_PATH"))

class JobState():
    def __init__(self, start: int, end: int) -> None:
        self.id: str = str(uuid.uuid4())
        self.created: float = time.time()
        self.start: int = start
        self.end: int = end
        self.interval = SCRAP_INTERVAL
        self.is_running: bool = False
        self.user: str = None

    def __repr__(self) -> str:
        if self.is_running: state = "IsRunning"
        else: state = "Finished"
        return f'{self.start:>9} -> {self.end:>9}, {state}'


class JobService():
    def __init__(self) -> None:
        self.jobs: list[JobState] = self.__read_state_file()
        self.run_cleanup = True
        self.users = self.__read_users()
        asyncio.create_task(self.__clean_up_joblist())

    def get_job_by_id(self, id: str) -> JobState:
        for job in self.jobs:
            if job.id == id:
                return job
        return None

    def get_new_job(self, user: str, batch_size: int=1000) -> JobState:
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
        users: dict[str, str] = {}
        with open(f'{CONFIG_PATH}/users', 'r') as file:
            lines = file.readlines()

        for line in lines:
            segment = line[0:-1].split(';')
            users[segment[1]] = segment[0]

        return users
