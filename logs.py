import os
from dotenv import load_dotenv


load_dotenv()

CONFIG_PATH = str(os.getenv("CONFIG_PATH"))
LOG_LENGTH = 5

def get_logs() -> list[str]:
    logs: list[str] = []

    with open(CONFIG_PATH+"/logs", "r") as file:
        data = file.readlines()
        if len(data) > LOG_LENGTH:
            data = data[-LOG_LENGTH:]

    for element in data:
        if "@" in element:
            segments = element.split('@')
            log = segments[0] + " " + " ".join(segments[1].split(' ')[1:])
            logs.append(log)
        else:
            logs.append(element)
    return logs[::-1]

def create_log_html():
    with open('./src/html/logs.html', 'r') as file:
        html = file.read()

    logs = get_logs()

    log_text = ''
    for log in logs:
        log_text += f'<p>{log}</p>'

    html = html.replace('XXX', log_text)

    with open('./src/html/logs_final.html', 'w') as file:
        file.write(html)

create_log_html()

