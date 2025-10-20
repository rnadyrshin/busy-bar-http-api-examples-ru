import requests
import time
import json

# Координаты городов
cities = {
    "Dubai": {"lat": 25.276987, "lon": 55.296249},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "New York": {"lat": 40.7128, "lon": -74.0060}
}

# Определяем простые 16x16 иконки как битмапы
ICONS = {
    "sun": [
        "................",
        ".......##.......",
        "......####......",
        ".....######.....",
        ".....######.....",
        "......####......",
        ".......##.......",
        "................",
        ".......##.......",
        "......####......",
        ".....######.....",
        ".....######.....",
        "......####......",
        ".......##.......",
        "................",
        "................",
    ],
    "cloud": [
        "................",
        "................",
        "......####......",
        "....######......",
        "...######.......",
        "..######........",
        "..####..........",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "rain": [
        "................",
        "......####......",
        ".....######.....",
        "....######......",
        "....####........",
        "................",
        "....#..#........",
        ".....##.........",
        "....#..#........",
        ".....##.........",
        "....#..#........",
        "................",
        "................",
        "................",
        "................",
        "................",
    ]
}

# Конвертация битмапа в двоичный формат для загрузки
def bitmap_to_bytes(bitmap):
    from PIL import Image
    import io
    img = Image.new("RGBA", (16, 16), (0,0,0,0))
    for y, row in enumerate(bitmap):
        for x, c in enumerate(row):
            if c == "#":
                img.putpixel((x, y), (255, 255, 0, 255))  # жёлтый для солнца/облака
    b = io.BytesIO()
    img.save(b, format="PNG")
    return b.getvalue()

# Получение погоды
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

# Отправка изображения на экран
def upload_icon(name, bitmap):
    url = f"http://10.0.4.20/api/assets/upload?app_id=weather_app&file={name}.png"
    headers = {"Content-Type": "application/octet-stream"}
    data = bitmap_to_bytes(bitmap)
    requests.post(url, headers=headers, data=data)

# Отправка текста и иконки на экран
def draw_weather(city_name, temp, icon_name):
    url = "http://10.0.4.20/api/display/draw"
    headers = {"Content-Type": "application/json"}
    payload = {
        "app_id": "weather_app",
        "elements": [
            {
                "id": "0",
                "timeout": 6,
                "type": "image",
                "path": f"{icon_name}.png",
                "x": 0,
                "y": 0
            },
            {
                "id": "1",
                "timeout": 6,
                "type": "text",
                "text": city_name,
                "x": 18,  # справа от иконки
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
                "text": f"{temp}°C",
                "x": 18,
                "y": 6,  # ниже названия
                "font": "big",
                "color": "#FFFF00",
                "width": 54,
                "scroll_rate": 60
            }
        ]
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

# Загрузка иконок один раз
for name, bitmap in ICONS.items():
    upload_icon(name, bitmap)

# Основной цикл
while True:
    for city_name, coords in cities.items():
        weather = get_weather(coords)
        temp = weather["temperature"]
        # Определяем тип иконки
        if weather["weathercode"] in [0, 1]:
            icon = "sun"
        elif weather["weathercode"] in [2, 3, 45, 48]:
            icon = "cloud"
        else:
            icon = "rain"
        draw_weather(city_name, temp, icon)
        time.sleep(3)
