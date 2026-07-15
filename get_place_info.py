import logging
import requests
from langchain.tools import tool
from typing import Dict, Optional
import time
from dotenv import load_dotenv
import os


# Константы для Nominatim (соблюдаем правила использования)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

load_dotenv()
USER_AGENT = os.getenv("USER_AGENT")
if not USER_AGENT:
    logging.getLogger(__name__).warning(
        "USER_AGENT не задан в .env — запросы к Nominatim могут быть заблокированы"
    )

@tool
def get_place_info(lat: float, lon: float) -> Dict[str, Optional[str]]:
    """
    Определяет город и район по географическим координатам с помощью Nominatim.
    Используй, когда пользователь присылает координаты, и нужно их обработать

    Аргументы:
        lat (float): широта (например, 55.7558)
        lon (float): долгота (например, 37.6173)

    Возвращает:
        dict: {
            "city": str или None,
            "district": str или None,   # район/округ
            "state": str или None,      # область/регион
            "country": str или None,
            "full_address": str
        }
    """
    print('ВЫЗВАНА get_place_info')

    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "zoom": 18,
    }
    headers = {"User-Agent": USER_AGENT}

    time.sleep(1)

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return {"error": data["error"]}

        address = data.get("address", {})
        # Извлекаем нужные компоненты
        city = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("hamlet") or
            None
        )
        district = (
            address.get("suburb") or
            address.get("city_district") or
            address.get("district") or
            address.get("borough") or
            None
        )
        state = address.get("state") or None
        country = address.get("country") or None
        full_address = data.get("display_name", "")

        return {
            "city": city,
            "district": district,
            "state": state,
            "country": country,
            "full_address": full_address,
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Ошибка запроса к Nominatim: {e}"}
    except ValueError as e:
        return {"error": f"Ошибка разбора JSON: {e}"}