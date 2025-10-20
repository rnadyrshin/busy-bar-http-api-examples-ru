import requests
import time
import json
import os

# Координаты городов
cities = {
    "Dubai": {"lat": 25.276987, "lon": 55.296249},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "New York": {"lat": 40.7128, "lon": -74.0060}
}

# Путь к папке с иконками
ICON_FOLDER = "icons"
ICON_FILES = ["cloud.png", "fog.png", "partly.png", "rain.png", "snow.png", "sun.png"]

# Загрузка иконки на устройство
def upload_icon(file_name):
    file_path = os.path.join(ICON_FOLDER, file_name)
    url = f"http://10.0.4.20/api/assets/upload?app_id=weather_app&file={file_name}"
    headers = {"Content-Type": "application/octet-stream"}
    with open(file_path, "rb") as f:
        data = f.read()
    requests.post(url, headers=headers, data=data)

# Получение погоды
def get_weather(city):
    url = "https://api.open-meteo.com/v1/forecast"
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
    return response.json()["current_weather"]

# Отправка текста и иконки на экран
def draw_weather(city_name, temp, icon_file):
    url = "http://10.0.4.20/api/display/draw"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {
        "app_id": "weather_app",
        "elements": [
            {
                "id": "0",
                "timeout": 6,
                "type": "image",
                "path": icon_file,
                "x": 0,
                "y": 0
            },
            {
                "id": "1",
                "timeout": 6,
                "type": "text",
                "text": city_name,
                "x": 18,
                "y": 0,
                "font": "small",
                "color": "#FFFFFF",
                "width": 54,
                "scroll_rate": 60
            },
            {
                "id": "2",
                "timeout": 6,
                "type": "text",
                "text": f"{temp}\u00B0C",
                "x": 18,
                "y": 6,
                "font": "big",
                "color": "#FFFF00",
                "width": 54,
                "scroll_rate": 60
            }
        ]
    }
    requests.post(url, headers=headers, data=json.dumps(payload, ensure_ascii=False))

# Загрузка всех иконок один раз
for icon_file in ICON_FILES:
    upload_icon(icon_file)

# Словарь для выбора иконки по weathercode
ICON_MAP = {
    "sun": ["0", "1"],
    "partly": ["2", "3"],
    "cloud": ["45", "48"],
    "fog": ["51", "53", "55"],
    "rain": ["61", "63", "65", "80", "81", "82"],
    "snow": ["71", "73", "75", "77", "85", "86"]
}

def select_icon(weathercode):
    for icon, codes in ICON_MAP.items():
        if str(weathercode) in codes:
            return f"{icon}.png"
    return "sun.png"  # по умолчанию солнце

# Основной цикл
while True:
    for city_name, coords in cities.items():
        weather = get_weather(coords)
        temp = weather["temperature"]
        code = weather.get("weathercode", 0)
        icon_file = select_icon(code)
        draw_weather(city_name, temp, icon_file)
        time.sleep(3)
