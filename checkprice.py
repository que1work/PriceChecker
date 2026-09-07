import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 120
TARGET_SIZE = "42,5"


# =========================================================
# ТОВАРЫ, ГДЕ ОТСЛЕЖИВАЕМ НАЛИЧИЕ EU 42.5
# =========================================================

SIZE_PRODUCTS = [
    {
        "name": "New Balance 2002R M2002RDA",
        "url": "https://newbalance.ua/store/kros-vki-un-s-2002r-s-r-m2002rda",
    },
    {
        "name": "New Balance 2002R M2002RPJ",
        "url": "https://newbalance.ua/store/krosivki-col-2002r-corni-newbalance-m2002rpj-cornij",
    },
    {
        "name": "New Balance ABZORB 2010 U201011N",
        "url": "https://newbalance.ua/store/krosivky-unis-2010-siri-u201011n",
    },
]


# =========================================================
# ТОВАРЫ, ГДЕ ОТСЛЕЖИВАЕМ ТОЛЬКО ЦЕНУ
# =========================================================

PRICE_PRODUCTS = [
    {
        "name": "New Balance 2002 Gore-Tex U200227R",
        "url": "https://newbalance.ua/store/krosivky-uni-2002-gore-tex-siri-u200227r",
    },
    {
        "name": "New Balance 2002R M2002RBK",
        "url": "https://newbalance.ua/store/new-balance-2002r-newbalance-m2002rbk-cornij",
    },
    {
        "name": "New Balance 2002R M2002RSF",
        "url": "https://newbalance.ua/store/kros-vki-un-s-2002r-sin-m2002rsf",
    },
    {
        "name": "New Balance 2002R M2002RST",
        "url": "https://newbalance.ua/store/new-balance-2002r-newbalance-m2002rst-sirij",
    },
    {
        "name": "New Balance 2010 U20103EJ",
        "url": "https://newbalance.ua/store/krosivky-unis-2010-t-siri-u20103ej",
    },
    {
        "name": "New Balance 2010 U20107B1",
        "url": "https://newbalance.ua/store/krosivky-unis-2010-chorni-chorni-u20107b1",
    },
    {
        "name": "New Balance 2010 U20107Z3",
        "url": "https://newbalance.ua/store/krosivky-uni-2010-siri-u20107z3",
    },
    {
        "name": "New Balance 2010 U20106KC",
        "url": "https://newbalance.ua/store/krosivky-uni-2010-fioletovi-siri-u20106kc",
    },
    {
        "name": "New Balance 2010 U2010892",
        "url": "https://newbalance.ua/store/krosivky-uni-2010-chorni-u2010892",
    },
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    )
}


session = requests.Session()
session.headers.update(HEADERS)


def send_telegram(message):
    telegram_url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    response = requests.post(
        telegram_url,
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )

    response.raise_for_status()

    print("Telegram: сообщение отправлено")


def get_page(url):
    response = session.get(
        url,
        timeout=20,
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser",
    )


def get_price(soup):
    price_element = soup.select_one(
        ".product-page-prices__price_new"
    )

    if price_element is None:
        raise Exception("Цена не найдена")

    price = price_element.get("data-price")

    if price is None:
        raise Exception("data-price не найден")

    return float(price)


def get_size_available(soup):
    size_element = soup.select_one(
        f'button[data-eu="{TARGET_SIZE}"]'
    )

    if size_element is None:
        raise Exception(
            f"EU {TARGET_SIZE} не найден"
        )

    return (
        size_element.get("data-available") == "1"
    )


# =========================================================
# СОСТОЯНИЕ
# =========================================================

previous_prices = {}
previous_sizes = {}


def check_size_products():
    for product in SIZE_PRODUCTS:

        name = product["name"]
        url = product["url"]

        try:
            soup = get_page(url)

            available = get_size_available(soup)

            status = (
                "ЕСТЬ"
                if available
                else "нет"
            )

            print(
                f"  {name}: "
                f"EU {TARGET_SIZE} — {status}"
            )

            # Первый запуск — просто запоминаем
            if url not in previous_sizes:
                previous_sizes[url] = available
                continue

            old_available = previous_sizes[url]

            # Состояние изменилось
            if available != old_available:

                if available:
                    message = (
                        f"🔥 РАЗМЕР ПОЯВИЛСЯ!\n\n"
                        f"{name}\n"
                        f"EU {TARGET_SIZE}: ЕСТЬ ✅\n\n"
                        f"{url}"
                    )

                else:
                    message = (
                        f"❌ РАЗМЕР ПРОПАЛ\n\n"
                        f"{name}\n"
                        f"EU {TARGET_SIZE}: нет\n\n"
                        f"{url}"
                    )

                send_telegram(message)

            previous_sizes[url] = available

        except Exception as e:
            print(
                f"  ОШИБКА {name}: {e}"
            )


def check_price_products():
    for product in PRICE_PRODUCTS:

        name = product["name"]
        url = product["url"]

        try:
            soup = get_page(url)

            price = get_price(soup)

            print(
                f"  {name}: "
                f"{price:.0f} грн"
            )

            # Первый запуск — просто запоминаем
            if url not in previous_prices:
                previous_prices[url] = price
                continue

            old_price = previous_prices[url]

            # Цена изменилась
            if price != old_price:

                difference = price - old_price

                if difference > 0:
                    change = (
                        f"📈 +{difference:.0f} грн"
                    )
                else:
                    change = (
                        f"📉 {difference:.0f} грн"
                    )

                message = (
                    f"💰 ИЗМЕНИЛАСЬ ЦЕНА\n\n"
                    f"{name}\n\n"
                    f"Было: {old_price:.0f} грн\n"
                    f"Стало: {price:.0f} грн\n"
                    f"{change}\n\n"
                    f"{url}"
                )

                send_telegram(message)

            previous_prices[url] = price

        except Exception as e:
            print(
                f"  ОШИБКА {name}: {e}"
            )


print("Мониторинг New Balance запущен")
print(
    f"Проверка каждые "
    f"{CHECK_INTERVAL // 60} минуты"
)
print(
    f"Наличие: {len(SIZE_PRODUCTS)} товаров"
)
print(
    f"Цена: {len(PRICE_PRODUCTS)} товаров"
)
print()


while True:

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print("=" * 60)
    print(f"[{now}] Новая проверка")

    print("\nНАЛИЧИЕ:")
    check_size_products()

    print("\nЦЕНЫ:")
    check_price_products()

    print(
        f"\nСледующая проверка "
        f"через {CHECK_INTERVAL} секунд"
    )

    time.sleep(CHECK_INTERVAL)
