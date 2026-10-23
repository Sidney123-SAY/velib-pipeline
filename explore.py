import requests

url = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
data = requests.get(url, timeout=20).json()

print(len(data["data"]["stations"]))
print(data["data"]["stations"][0])
