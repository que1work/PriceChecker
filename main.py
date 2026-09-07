import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://newbalance.ua/store/krosivky-unis-2010-siri-u201011n"
TARGET_SIZE = "42,5"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 120

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    )
}


def send_telegram(message):
    telegram_url = (
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    )

    response = requests.post(
        telegram_url,
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=15
    )

    response.raise_for_status()
    print("Telegram: сообщение отправлено")


def check_product():
    response = requests.get(
        URL,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    price_element = soup.select_one(
        ".product-page-prices__price_new"
    )

    if not price_element:
        raise Exception("Цена не найдена")

    price = float(
        price_element.get("data-price")
    )

    size_element = soup.select_one(
        f'button[data-eu="{TARGET_SIZE}"]'
    )

    if not size_element:
        raise Exception(
            f"Размер EU {TARGET_SIZE} не найден"
        )

    available = (
        size_element.get("data-available") == "1"
    )

    return price, available


previous_price = None
previous_available = None

print("Мониторинг запущен")

send_telegram("✅ Мониторинг New Balance запущен")

while True:
    try:
        price, available = check_product()

        now = datetime.now().strftime("%H:%M:%S")

        print(
            f"[{now}] "
            f"Цена: {price:.0f} грн | "
            f"EU {TARGET_SIZE}: "
            f"{'ЕСТЬ' if available else 'нет'}"
        )

        # Цена изменилась
        if (
            previous_price is not None
            and price != previous_price
        ):

            message = (
                f"💰 ИЗМЕНИЛАСЬ ЦЕНА\n\n"
                f"New Balance U201011N\n\n"
                f"Было: {previous_price:.0f} грн\n"
                f"Стало: {price:.0f} грн\n\n"
                f"{URL}"
            )

            send_telegram(message)

        # Наличие размера изменилось
        if (
            previous_available is not None
            and available != previous_available
        ):

            if available:
                status = "🔥 РАЗМЕР ПОЯВИЛСЯ"
            else:
                status = "❌ РАЗМЕР ПРОПАЛ"

            message = (
                f"{status}\n\n"
                f"New Balance U201011N\n"
                f"EU: {TARGET_SIZE}\n"
                f"Цена: {price:.0f} грн\n\n"
                f"{URL}"
            )

            send_telegram(message)

        previous_price = price
        previous_available = available

    except Exception as e:
        print("Ошибка:", e)

    time.sleep(CHECK_INTERVAL)
