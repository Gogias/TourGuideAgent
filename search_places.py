"""
Модуль поиска достопримечательностей рядом с заданными координатами.
"""

import logging
import requests
import math
import time
from urllib.parse import quote
from langchain.tools import tool
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

# ── Константы ────────────────────────────────────────────────────────────

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

WIKI_API_URL = "https://ru.wikipedia.org/w/api.php"
load_dotenv()
USER_AGENT = os.getenv("USER_AGENT")
if not USER_AGENT:
    logging.getLogger(__name__).warning(
        "USER_AGENT не задан в .env — запросы к Overpass/Wikipedia API могут быть заблокированы"
    )
SHORT_EXTRACT_CHARS = 200
MAX_BATCH_TITLES = 20
DEDUP_DISTANCE_KM = 0.03

NON_LANDMARK_KEYWORDS = [
    "парад", "митинг", "манифестация", "демонстрация",
    "юбилей", "годовщина", "празднование", "торжество",
    "открытие", "закрытие", "драпировка", "церемония",
    "похороны", "похорон", "траур",
    "фестиваль", "выставка (",
    "переговоры", "съезд", "заседание",
    "победа", "победы",
    "улица", "проспект", "переулок", "округ", "библиотека",
    "могила", "похоронен", "захоронение",  # отдельные могилы, не сам объект
]

# ── Вспомогательные функции ─────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def _wiki_tag_to_url(wiki_tag):
    if ":" in wiki_tag:
        lang, title = wiki_tag.split(":", 1)
    else:
        lang, title = "ru", wiki_tag
    title = title.strip().replace(" ", "_")
    return f"https://{lang}.wikipedia.org/wiki/{quote(title)}"


def _names_match(name1, name2):
    n1, n2 = name1.lower().strip(), name2.lower().strip()
    return n1 == n2 or n1 in n2 or n2 in n1


def _is_likely_landmark(title):
    lowered = title.lower()
    return not any(kw in lowered for kw in NON_LANDMARK_KEYWORDS)


# ── Overpass ──────────────────────────────────────────────────────────

def _query_overpass(lat: float, lon: float, radius: int, limit: int) -> dict:
    """
    Отправляет запрос к Overpass API и возвращает список объектов OSM
    рядом с координатами.

    Включает явный catch-all по тегу wikipedia — ловит объекты вроде ГУМа
    или Мавзолея, которые не попадают в "стандартные" категории tourism/historic.
    """
    query = f"""
[out:json][timeout:25];
(
  nwr["historic"]["name"](around:{radius},{lat},{lon});
  nwr["tourism"]["name"](around:{radius},{lat},{lon});
  nwr["leisure"]["name"](around:{radius},{lat},{lon});
  nwr["amenity"="place_of_worship"]["name"](around:{radius},{lat},{lon});
  nwr["building"~"church|cathedral|chapel|religious|castle|ruins|fort|monument|memorial"]["name"](around:{radius},{lat},{lon});
  nwr["amenity"~"fountain|theatre"]["name"](around:{radius},{lat},{lon});
  nwr["shop"~"mall|department_store"]["name"](around:{radius},{lat},{lon});
  // Catch-all: любой объект с вики-ссылкой, независимо от остальных тегов —
  // ловит ГУМ, Мавзолей и подобные объекты без "стандартной" разметки
  nwr["wikipedia"]["name"](around:{radius},{lat},{lon});
);
out body center {limit};
"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    last_error = None

    for server in OVERPASS_SERVERS:
        try:
            logger.info("  → Пробуем Overpass-сервер: %s", server)
            time.sleep(1)
            response = requests.get(
                server, params={"data": query}, headers=headers, timeout=30,
            )
            response.raise_for_status()
            logger.info("  ✓ Ответил: %s", server)
            return response.json()

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "?"
            last_error = f"HTTP {status} от {server}"
            logger.warning("  ✗ %s", last_error)
            if status == 400:
                return {"error": f"Ошибка в Overpass-запросе: {e}"}

        except requests.exceptions.Timeout:
            last_error = f"Таймаут на {server}"
            logger.warning("  ✗ %s", last_error)

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            logger.warning("  ✗ Ошибка соединения: %s", e)

        except Exception as e:
            last_error = str(e)
            logger.warning("  ✗ Неожиданная ошибка на %s: %s", server, e)

    return {"error": f"Все Overpass-серверы недоступны. Последняя ошибка: {last_error}"}


# ── Wikipedia GeoSearch ──────────────────────────────────────────────────

def _wikipedia_geosearch(lat, lon, radius, limit=30):
    """
    Ищет статьи Wikipedia по координатам напрямую — независимо от разметки OSM.
    """
    params = {
        "action": "query",
        "list": "geosearch",          # ИСПРАВЛЕНО: было "geocch"
        "gscoord": f"{lat}|{lon}",
        "gsradius": min(radius, 10000),
        "gslimit": limit,
        "format": "json",
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(WIKI_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("query", {}).get("geosearch", [])  # ИСПРАВЛЕНО: было "geocch"
    except Exception as e:
        logger.warning("  ✗ Ошибка Wikipedia geosearch: %s", e)
        return []


# ── Получение кратких описаний ──────────────────────────────────────────

def _get_short_extracts(titles):
    if not titles:
        return {}
    unique_titles = list(dict.fromkeys(titles))[:MAX_BATCH_TITLES]
    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "exchars": SHORT_EXTRACT_CHARS,
        "titles": "|".join(unique_titles),
        "format": "json",
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(WIKI_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
        result = {}
        for page in pages.values():
            title = page.get("title")
            extract = page.get("extract", "").strip()
            if title and extract:
                result[title] = extract
        return result
    except Exception as e:
        logger.warning("  ✗ Ошибка получения описаний: %s", e)
        return {}


# ── Основной инструмент ──────────────────────────────────────────────────

@tool
def search_places(lat: float, lon: float, radius: int = 1000, limit: int = 10) -> str:
    """
    Ищет достопримечательности через Overpass и Wikipedia, приоритизирует
    значимые объекты (с вики-статьёй, туристические) и сортирует по близости.
    """
    logger.info("Вызвана search_places")

    overpass_limit = 200
    wiki_limit = 30

    results = []
    osm_failed = False

    # ── Overpass ──
    osm_data = _query_overpass(lat, lon, radius, overpass_limit)
    if "error" in osm_data:
        logger.warning("  ⚠ Overpass ошибка: %s", osm_data['error'])
        osm_failed = True
    else:
        elements = osm_data.get("elements", [])
        for elem in elements:
            tags = elem.get("tags", {})
            name = tags.get("name:ru") or tags.get("name")
            if not name:
                continue

            if any(tag in tags for tag in ["abandoned", "disused", "demolished"]):
                continue

            # Отдельные могилы (некрополь) исключаем ВСЕГДА, даже если
            # у конкретного человека есть личная статья в Wikipedia.
            # Оставляем только если это туристический объект целиком
            # (как Мавзолей Ленина — historic=tomb + tourism=attraction).
            is_tomb = (
                tags.get("historic") in ["tomb", "grave"]
                or tags.get("amenity") == "grave_yard"
                or tags.get("landuse") == "cemetery"
            )
            is_tourist_site = bool(tags.get("tourism"))
            if is_tomb and not is_tourist_site:
                continue

            if "center" in elem:
                elat, elon = elem["center"]["lat"], elem["center"]["lon"]
            else:
                elat, elon = elem.get("lat"), elem.get("lon")
                if elat is None or elon is None:
                    continue

            # Тип объекта + приоритет для сортировки
            priority = 2
            if tags.get("tourism"):
                type_str = f"Туризм: {tags['tourism']}"
                priority = 0
            elif tags.get("shop") in ["mall", "department_store"]:
                type_str = f"Торговый объект: {tags['shop']}"
                priority = 1
            elif tags.get("historic"):
                type_str = f"Историческое: {tags['historic']}"
                priority = 0 if tags["historic"] in ["monument", "memorial"] else 1
            elif tags.get("amenity"):
                type_str = f"Услуга: {tags['amenity']}"
                priority = 2
            elif tags.get("building"):
                type_str = f"Здание: {tags['building']}"
                priority = 1
            else:
                type_str = "Объект"

            wiki_tag = tags.get("wikipedia")
            wiki_url, wiki_title = None, None
            if wiki_tag:
                wiki_url = _wiki_tag_to_url(wiki_tag)
                wiki_title = wiki_tag.split(":", 1)[-1] if ":" in wiki_tag else wiki_tag
                priority = 0  # наличие статьи в Wikipedia — сильный сигнал значимости

            dist_km = haversine(lat, lon, elat, elon)

            results.append({
                "name": name,
                "type": type_str,
                "distance_km": round(dist_km, 2),
                "url": f"https://www.openstreetmap.org/{elem.get('type')}/{elem.get('id')}" if elem.get('id') else "",
                "wiki_url": wiki_url,
                "wiki_title": wiki_title,
                "lat": elat,
                "lon": elon,
                "priority": priority,
            })

    # ── Wikipedia GeoSearch (резерв + дополнение) ──
    wiki_places = _wikipedia_geosearch(lat, lon, radius, wiki_limit)
    for wp in wiki_places:
        title = wp["title"]
        if not _is_likely_landmark(title):
            continue

        duplicate = False
        for existing in results:
            if (haversine(wp["lat"], wp["lon"], existing["lat"], existing["lon"]) < DEDUP_DISTANCE_KM
                    or _names_match(existing["name"], title)):
                if not existing.get("wiki_url"):
                    existing["wiki_url"] = f"https://ru.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
                    existing["wiki_title"] = title
                    existing["priority"] = 0
                duplicate = True
                break

        if not duplicate:
            results.append({
                "name": title,
                "type": "Объект (Wikipedia)",
                "distance_km": round(wp["dist"] / 1000, 2),
                "url": "",
                "wiki_url": f"https://ru.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
                "wiki_title": title,
                "lat": wp["lat"],
                "lon": wp["lon"],
                "priority": 0,
            })

    if not results:
        if osm_failed:
            return f"❌ Не удалось найти достопримечательности в радиусе {radius} м."
        return f"😕 Ничего не найдено в радиусе {radius} м."

    # Сортировка: сначала по приоритету (значимость), затем по расстоянию
    results.sort(key=lambda x: (x.get("priority", 2), x["distance_km"]))
    results = results[:limit]

    titles_to_fetch = [r["wiki_title"] for r in results if r["wiki_title"]]
    extracts = _get_short_extracts(titles_to_fetch)

    warning = "⚠️ Overpass временно недоступен, данные только из Wikipedia.\n" if osm_failed else ""
    lines = [f"🏛️ Найдено {len(results)} объектов в радиусе {radius} м:\n{warning}"]
    for i, item in enumerate(results, 1):
        line = f"{i}. **{item['name']}** — {item['distance_km']} км\n   - {item['type']}"
        desc = extracts.get(item["wiki_title"]) if item["wiki_title"] else None
        if desc:
            line += f"\n   - ℹ️ {desc}"
        if item["wiki_url"]:
            line += f"\n   - 📖 {item['wiki_url']}"
        if item["url"]:
            line += f"\n   - 🔗 {item['url']}"
        lines.append(line)

    lines.append("\nИспользуй только эти данные.")
    return "\n".join(lines)