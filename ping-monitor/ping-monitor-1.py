#!/usr/bin/env python3
"""
ping_display.py

Пингует игровой сервер и отображает график пинга на LED-дисплее 72x16 через HTTP API устройства.

Зависимости:
  pip install pillow requests

Запуск:
  python3 ping_display.py --server 1.2.3.4
"""
import sys
import time
import argparse
import collections
import io
import platform
import re
import subprocess

from PIL import Image, ImageDraw
import requests

# === Конфигурация ===
DEVICE_IP = "10.0.4.20"      # IP девайса (взял из твоих данных)
APP_ID = "ping_app"
GRAPH_FILE = "graph.png"     # имя файла в памяти устройства
DISPLAY_WIDTH = 72
DISPLAY_HEIGHT = 16
TEXT_FONT = "small"          # small: высота 5
TEXT_COLOR = "#FFFFFFFF"     # белый (RGBA hex)
GRAPH_X = 0
GRAPH_Y = 5                  # оставляем верхнюю область для текста (высота small=5)
GRAPH_HEIGHT = DISPLAY_HEIGHT - GRAPH_Y  # 11
GRAPH_WIDTH = DISPLAY_WIDTH
BUFFER_LEN = GRAPH_WIDTH     # одно значение на пиксель по X
UPDATE_INTERVAL = 1.0        # сек

# Настройка масштабирования графика (максимальный отображаемый пинг в мс)
MAX_PING_MS = 300.0

# === Вспомогательные функции ===
def ping_once(host, timeout_s=1.0):
    """Пинговая функция: возвращает round(ms) или None при таймауте/ошибке.
       Работает и на Windows, и на Unix-подобных.
    """
    system = platform.system().lower()
    try:
        if system == "windows":
            # -n 1 (1 пакет), -w timeout(ms)
            proc = subprocess.run(["ping", "-n", "1", "-w", str(int(timeout_s * 1000)), host],
                                   capture_output=True, text=True, timeout=timeout_s+1)
            out = proc.stdout
            # Ищем time=12ms
            m = re.search(r"time[=<]\s*([0-9]+)ms", out)
            if m:
                return int(m.group(1))
        else:
            # linux / mac: -c 1 (1 пакет), -W timeout (seconds, linux) or -t on mac? 
            # Use -c 1 and rely on subprocess timeout for portability; many unix ping show "time=X ms"
            proc = subprocess.run(["ping", "-c", "1", host],
                                   capture_output=True, text=True, timeout=timeout_s+1)
            out = proc.stdout
            m = re.search(r"time[=<]?\s*([0-9]+(?:\.[0-9]+)?)\s*ms", out)
            if m:
                return int(round(float(m.group(1))))
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None
    return None

def render_graph_image(values, width=GRAPH_WIDTH, height=GRAPH_HEIGHT, max_ping=MAX_PING_MS):
    """
    Рисует PNG (width x height) с линией графика.
    values: deque/iterable длины <= width, с None или numeric (ms).
    Фон черный, график — яркий цвет.
    Возвращает bytes PNG.
    """
    img = Image.new("RGBA", (width, height), (0,0,0,255))
    draw = ImageDraw.Draw(img)

    # Преобразуем значения в y-координаты (0 сверху).
    ys = []
    for v in values:
        if v is None:
            ys.append(None)
        else:
            # clamp
            vv = max(0.0, min(v, max_ping))
            # перевести: ping 0 -> нижняя линия (height-1), ping=max_ping -> верх 0
            y = int(round((1.0 - (vv / max_ping)) * (height - 1)))
            ys.append(y)

    # Рисуем линию: соединяем последовательные не-None
    prev = None
    for x in range(len(ys)):
        y = ys[x]
        if y is not None:
            # пиксель точки
            draw.point((x, y), fill=(170,255,0,255))  # ярко-зелёный-ish
            if prev is not None:
                # соединяем линией
                x0, y0 = prev
                draw.line((x0, y0, x, y), fill=(170,255,0,255))
            prev = (x, y)
        else:
            prev = None

    # Можно добавить лёгкие горизонтальные метки (например 0ms и max)
    # малый подсказочный текст мы не рисуем — на дисплее текст отдельным элементом

    # Сохранить в bytes
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()

def upload_image_to_device(device_ip, app_id, filename, img_bytes):
    url = f"http://{device_ip}/api/assets/upload"
    params = {"app_id": app_id, "file": filename}
    headers = {"Content-Type": "application/octet-stream"}
    try:
        r = requests.post(url, params=params, data=img_bytes, headers=headers, timeout=5)
        r.raise_for_status()
        return True
    except Exception as e:
        print("Ошибка загрузки изображения на устройство:", e)
        return False

def display_on_device(device_ip, payload):
    url = f"http://{device_ip}/api/display/draw"
    try:
        r = requests.post(url, json=payload, timeout=5)
        r.raise_for_status()
        return True
    except Exception as e:
        print("Ошибка отправки display/draw:", e)
        return False

# === Основная логика ===
def run_loop(server_ip, device_ip=DEVICE_IP):
    buffer = collections.deque([None]*BUFFER_LEN, maxlen=BUFFER_LEN)

    print(f"Пингуем {server_ip} каждую {UPDATE_INTERVAL:.1f}s, обновляем дисплей {device_ip}")
    try:
        while True:
            t0 = time.time()
            ping_ms = ping_once(server_ip, timeout_s=0.9)
            if ping_ms is None:
                display_value = "--"
            else:
                display_value = f"{ping_ms} ms"

            # обновляем буфер
            buffer.append(ping_ms)

            # рендер графика
            img_bytes = render_graph_image(buffer)

            # загружаем в устройство
            ok = upload_image_to_device(device_ip, APP_ID, GRAPH_FILE, img_bytes)
            if not ok:
                # печатаем предупреждение, но продолжаем попытки
                print("WARN: не удалось загрузить изображение на устройство.")

            # формируем payload для вывода: текст (маленький шрифт) + картинка
            payload = {
                "app_id": APP_ID,
                "elements": [
                    {
                        "id": "ping_text",
                        "timeout": 2,
                        "type": "text",
                        "text": display_value,
                        "x": 0,
                        "y": 0,
                        "font": TEXT_FONT,
                        "color": TEXT_COLOR,
                        "width": 72,
                        "scroll_rate": 60
                    },
                    {
                        "id": "graph_img",
                        "timeout": 2,
                        "type": "image",
                        "path": GRAPH_FILE,
                        "x": GRAPH_X,
                        "y": GRAPH_Y
                    }
                ]
            }
            display_on_device(device_ip, payload)

            # печать в консоль для отладки
            print(f"{time.strftime('%H:%M:%S')} | ping={display_value}")

            # wait until next second boundary relative to start of loop
            t_elapsed = time.time() - t0
            to_sleep = UPDATE_INTERVAL - t_elapsed
            if to_sleep > 0:
                time.sleep(to_sleep)
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")

# === CLI ===
def main():
    parser = argparse.ArgumentParser(description="Ping -> LED display 72x16 graph")
    parser.add_argument("--server", "-s", required=True, help="IP или hostname игрового сервера")
    parser.add_argument("--device", "-d", default=DEVICE_IP, help=f"IP LED-устройства (default {DEVICE_IP})")
    args = parser.parse_args()
    run_loop(args.server, args.device)

if __name__ == "__main__":
    main()
