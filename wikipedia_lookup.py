import logging
import requests
from langchain.tools import tool
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

load_dotenv()


WIKI_API_URL = "https://ru.wikipedia.org/w/api.php"
USER_AGENT = os.getenv("USER_AGENT")
if not USER_AGENT:
    logging.getLogger(__name__).warning(
        "USER_AGENT не задан в .env — запросы к Wikipedia API могут быть заблокированы"
    )

MAX_EXTRACT_CHARS = 4000  # ограничиваем объём текста, чтобы не перегружать контекст LLM


def _find_article_title(query: str) -> str | None:
    """
    Ищет наиболее подходящее название статьи по неточному запросу пользователя.
    Использует полнотекстовый поиск MediaWiki, а не точное совпадение названия.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 1,
        "format": "json",
    }
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(WIKI_API_URL, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = data.get("query", {}).get("search", [])
    if not results:
        return None
    return results[0]["title"]


def _get_article_extract(title: str) -> dict:
    """
    Получает чистый текст статьи (без вики-разметки, инфобоксов и ссылок)
    по её точному названию.
    """
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,       # чистый текст без HTML/wiki-разметки
        "exsectionformat": "plain",
        "titles": title,
        "format": "json",
    }
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(WIKI_API_URL, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return {"error": "Статья не найдена"}

    page = next(iter(pages.values()))
    if "missing" in page:
        return {"error": "Статья не найдена"}

    extract = page.get("extract", "")
    if not extract:
        return {"error": "У статьи нет текстового содержимого"}

    return {
        "title": page.get("title", title),
        "extract": extract,
        "url": f"https://ru.wikipedia.org/wiki/{title.replace(' ', '_')}",
    }


@tool
def wikipedia_lookup(query: str) -> str:
    """
    Находит статью в Wikipedia по названию места и возвращает её содержание,
    чтобы ответить на вопрос пользователя об этом месте — истории, фактах,
    интересных деталях. Используй, когда пользователь спрашивает
    "расскажи подробнее про X" или "что это за место" про конкретный объект.

    Аргументы:
        query (str): название места или объекта, например "ГУМ" или "Собор Василия Блаженного"

    Возвращает:
        str: текст статьи (сокращённый) вместе со ссылкой на источник,
             или сообщение что статья не найдена
    """
    logger.info("Вызвана wikipedia_lookup")

    title = _find_article_title(query)
    if not title:
        return f"😕 Не удалось найти статью в Wikipedia по запросу '{query}'."

    result = _get_article_extract(title)
    if "error" in result:
        return f"😕 {result['error']} (запрос: '{query}')"

    extract = result["extract"]
    truncated = len(extract) > MAX_EXTRACT_CHARS
    if truncated:
        extract = extract[:MAX_EXTRACT_CHARS].rsplit(".", 1)[0] + "."

    footer = f"\n\n📖 Источник: {result['url']}"
    if truncated:
        footer = f"\n\n(текст сокращён, полная статья по ссылке){footer}"

    return f"**{result['title']}**\n\n{extract}{footer}"