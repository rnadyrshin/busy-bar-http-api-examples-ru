import requests
import time
import json

# Функция получения погоды
def get_weather(city):
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "current_weather": "true",
        "temperature_unit": "celsius",
        "windspeed_unit": "kmh",
        "precipitation_unit": "mm",
        "timezone": "Europe/London"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["current_weather"]

# Функция отправки данных на экран
def send_to_display(text):
    url = "http://10.0.4.20/api/display/draw"
    headers = {"Content-Type": "application/json"}
    payload = {
        "app_id": "weather_app",
        "elements": [
            {
                "id": "0",
                "timeout": 6,
                "type": "text",
                "text": text,
                "x": 1,
                "y": 3,
                "font": "medium",
                "color": "#FFFFFF",
                "width": 72,
                "scroll_rate": 60
            }
        ]
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

# Список городов с координатами
cities = {
    "Dubai": {"lat": 25.276987, "lon": 55.296249},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "New York": {"lat": 40.7128, "lon": -74.0060}
}

# Основной цикл
while True:
    for city_name, coords in cities.items():
        weather = get_weather(coords)
        temp = weather["temperature"]
        wind_speed = weather["windspeed"]
        text = f"{city_name}: {temp}°C, Wind: {wind_speed} km/h"
        send_to_display(text)
        time.sleep(3)
