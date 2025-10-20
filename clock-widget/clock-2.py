import requests
from datetime import datetime
import time

screen_width = 72
small_char_width = 4
big_char_width = 7

app_id = "my_app"
url = "http://10.0.4.20/api/display/draw"

while True:
   now = datetime.now()
   date_str = now.strftime("%d.%m.%Y")
   time_str = now.strftime("%H:%M:%S")

   # Вычисляем ширину текста
   date_width_px = len(date_str) * small_char_width
   time_width_px = len(time_str) * big_char_width

   # Центрирование + сдвиг вправо на 3 пикселя
   date_x = (screen_width - date_width_px) // 2 + 3
   time_x = (screen_width - time_width_px) // 2 + 3

   # Позиции по вертикали
   date_y = 0  # сверху
   time_y = 6  # снизу, оставляем место для шрифта big (высота 10)

   data = {
       "app_id": app_id,
       "elements": [
           {
               "id": "date",
               "timeout": 2,
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
               "timeout": 2,
               "type": "text",
               "text": time_str,
               "x": time_x,
               "y": time_y,
               "font": "big",
               "color": "#AAFF00FF",  # светло-зеленый
               "width": screen_width,
               "scroll_rate": 0
           }
       ]
   }

   requests.post(url, json=data)
   time.sleep(1)
