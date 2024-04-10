import requests
import time
import json

server = 'http://10.0.10.20:30400'
#server = 'https://www.dmining.ch'
server = 'http://127.0.0.1:8000'

print("----- Get batch ----")
url = f"{server}/jobs/get_batch/"

data = {"token":"3f284c4c087b0ee881642142009da4834a693c12c65a4bb5952d3fde3d5842be",
        "ip":"10.0.0.0",
        "display_name": "zimmi"
        }

response = requests.post(url, data=json.dumps(data))
print(response.json())
id = response.json()['id']

time.sleep(30)

print("----- Send batch ----")
url = f"{server}/jobs/upload_batch/"

data = {"id": id}
files = {'file': open('Archiv.zip', 'rb')}

response = requests.post(url, files=files, data=data)
print(response.json())
