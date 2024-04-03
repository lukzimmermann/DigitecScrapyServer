import requests
import time

print("----- Get batch ----")
url = "http://localhost:8000/jobs/get_batch/"
response = requests.get(url)
id = response.json()['id']
print(id)


time.sleep(1)

print("----- Send batch ----")
url = "http://localhost:8000/jobs/upload_batch/"

files = {'file': open('Archiv.zip', 'rb')}
data = {"id": id}

response = requests.post(url, files=files, data=data)
print(response.json())
