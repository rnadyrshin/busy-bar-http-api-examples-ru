import requests
from datetime import datetime

# Текущая дата и время
now = datetime.now()
date_str = now.strftime("%d.%m.%Y")
time_str = now.strftime("%H:%M:%S")

# Параметры экрана
screen_width = 72

# Оценка ширины текста в пикселях
small_char_width = 4
big_char_width = 7

date_width_px = len(date_str) * small_char_width
time_width_px = len(time_str) * big_char_width

# Центрирование по горизонтали
date_x = (screen_width - date_width_px) // 2
time_x = (screen_width - time_width_px) // 2

# Позиции по вертикали
date_y = 0  # сверху
time_y = 6  # снизу, оставляем место для шрифта big (высота 10)

data = {
   "app_id": "my_app",
   "elements": [
       {
           "id": "date",
           "timeout": 6,
           "type": "text",
           "text": date_str,
           "x": date_x,
           "y": date_y,
           "font": "small",
           "color": "#FFFFFFFF",
           "width": screen_width,
           "scroll_rate": 0
       },
       {
           "id": "time",
           "timeout": 6,
           "type": "text",
           "text": time_str,
           "x": time_x,
           "y": time_y,
           "font": "big",
           "color": "#FFFFFFFF",
           "width": screen_width,
           "scroll_rate": 0
       }
   ]
}

response = requests.post("http://10.0.4.20/api/display/draw", json=data)
print(response.text)
