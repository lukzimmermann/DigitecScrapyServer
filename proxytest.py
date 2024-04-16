import requests

class Proxy():
    def __init__(self) -> None:
        self.ip: str = ''
        self.port: int = ''
        self.has_ssl: bool = False
        self.alive: bool = False
        self.first_seen: float = 0
        self.alive_since: float = 0
        self.last_seen: float = 0
        self.city: str = ''
        self.country: str = ''
        self.country_code: str = ''
        self.mobile: bool = False
        self.times_dead: int = 0
        self.times_alive: int = 0
        self.protocol: str = ''
        self.average_timeout: float = 0
        self.uptime: float = 0
    
    def __repr__(self) -> str:
        text = f'{self.ip:<10}:{self.port}'
        uptime_ratio = self.times_alive/(self.times_dead+self.times_alive)*100
        return f'{text:<25}{self.alive:>5}{self.average_timeout:>20.0f}{uptime_ratio:>10.1f}%'


proxies: list[Proxy] = []

url = 'https://api.proxyscrape.com/v3/free-proxy-list/get?request=getproxies&skip=0&proxy_format=protocolipport&format=json'

response = requests.get(url)

data = response.json()

for entry in data['proxies']:
    try:
        proxy = Proxy()
        proxy.alive = entry['alive']
        proxy.alive_since = entry['alive_since']
        proxy.first_seen = entry['first_seen']
        proxy.last_seen = entry['last_seen']
        proxy.average_timeout = entry['average_timeout']
        proxy.uptime = entry['uptime']
        proxy.times_alive = entry['times_alive']
        proxy.times_dead = entry['times_dead']
        proxy.ip = entry['ip']
        proxy.port = entry['port']
        proxy.has_ssl = entry['ssl']
        proxy.protocol = entry['protocol']

        proxy.city = entry['ip_data']['city']
        proxy.country = entry['ip_data']['country']
        proxy.country_code = entry['ip_data']['countryCode']
        proxy.mobile = entry['ip_data']['mobile']

        proxies.append(proxy)
    except:
        pass


print(f"Number of proxies:     {len(data['proxies'])}")

for proxy in proxies:
    uptime_ratio = proxy.times_alive/(proxy.times_dead+proxy.times_alive)
    if proxy.average_timeout < 200 and uptime_ratio > 0.90:
        print(proxy)