import requests

r = requests.get("https://historical-forecast-api.open-meteo.com/v1/forecast?latitude=49.2497&longitude=-123.1193&start_date=2020-01-01&end_date=2025-01-01&daily=rain_sum,snowfall_sum&timezone=auto")
f = open("public/weather.json", "w")
f.write(r.text)
f.close()