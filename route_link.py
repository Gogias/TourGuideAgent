import logging
from langchain.tools import tool
from typing import Literal

logger = logging.getLogger(__name__)


# Соответствие способов передвижения параметрам Яндекс.Карт
TRANSPORT_TYPES = {
    "пешком": "pd",
    "авто": "auto",
    "транспорт": "mt",   # общественный транспорт (mt = mass transit)
}


@tool
def get_route_link(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    transport: Literal["пешком", "авто", "транспорт"] = "пешком",
) -> str:
    """
    Строит ссылку на маршрут между двумя точками в Яндекс.Картах.
    Используй, когда пользователь спрашивает как добраться до места,
    или просит проложить маршрут от своего местоположения до точки.

    Аргументы:
        from_lat (float): широта начальной точки (откуда едет пользователь)
        from_lon (float): долгота начальной точки
        to_lat (float): широта конечной точки (куда нужно добраться)
        to_lon (float): долгота конечной точки
        transport (str): способ передвижения — "пешком", "авто" или "транспорт"

    Возвращает:
        str: ссылка на Яндекс.Карты с построенным маршрутом
    """
    logger.info("Вызвана get_route_link")

    rtt = TRANSPORT_TYPES.get(transport, "pd")

    # В Яндекс.Картах координаты в rtext указываются как "широта,долгота"
    from_point = f"{from_lat},{from_lon}"
    to_point = f"{to_lat},{to_lon}"

    url = (
        "https://yandex.ru/maps/?"
        f"rtext={from_point}~{to_point}"
        f"&rtt={rtt}"
        "&mode=routes"
    )

    transport_names = {
        "пешком": "пешком",
        "авто": "на автомобиле",
        "транспорт": "на общественном транспорте",
    }
    transport_label = transport_names.get(transport, transport)

    return f"🗺️ Маршрут {transport_label}: {url}"