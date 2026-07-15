import logging
import requests
from langchain.tools import tool
import time
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

load_dotenv()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = os.getenv("USER_AGENT")
if not USER_AGENT:
    logging.getLogger(__name__).warning(
        "USER_AGENT не задан в .env — запросы к Nominatim могут быть заблокированы"
    )


@tool
def geocode_place(query: str) -> dict:
    """
    Находит географические координаты по названию места, адресу или достопримечательности.
    Используй, когда пользователь называет место текстом, а не координатами —
    например: 'Красная площадь', 'Эйфелева башня', 'ул. Пушкина 10, Москва'.
    Возвращает координаты первого наиболее подходящего результата.

    Аргументы:
        query (str): название места или адрес на любом языке

    Возвращает:
        dict: {
            "lat": float,
            "lon": float,
            "display_name": str,   # полный адрес найденного места
            "type": str,           # тип объекта (city, street, amenity и т.д.)
            "importance": float,   # оценка релевантности от 0 до 1
        }
        или {"error": str} если место не найдено
    """
    logger.info("Вызвана geocode_place")

    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,          # берём только лучший результат
        "accept-language": "ru",  # предпочитаем русские названия
    }
    headers = {"User-Agent": USER_AGENT}

    time.sleep(1)  # соблюдаем rate limit Nominatim: не чаще 1 запроса в секунду

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()

        if not results:
            return {"error": f"Место '{query}' не найдено"}

        best = results[0]

        return {
            "lat": float(best["lat"]),
            "lon": float(best["lon"]),
            "display_name": best.get("display_name", ""),
            "type": best.get("type", ""),
            "importance": float(best.get("importance", 0)),
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Ошибка запроса к Nominatim: {e}"}
    except (ValueError, KeyError) as e:
        return {"error": f"Ошибка разбора ответа: {e}"}