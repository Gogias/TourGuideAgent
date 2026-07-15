"""
Юнит-тесты для тула wikipedia_lookup.

Мокаем внутренние функции _find_article_title и _get_article_extract,
чтобы не было реальных HTTP-запросов к Wikipedia API.
"""

from unittest.mock import patch, MagicMock
import pytest
import wikipedia_lookup


class TestWikipediaLookup:
    """Тесты для wikipedia_lookup: успех, не найдено, нет контента."""

    @patch("wikipedia_lookup._get_article_extract")
    @patch("wikipedia_lookup._find_article_title")
    def test_wikipedia_lookup_success(
        self, mock_find_title, mock_get_extract
    ):
        """
        Успешный поиск — возвращает форматированную строку
        с названием статьи и extract.
        """
        # ═══ Arrange ═══
        mock_find_title.return_value = "Москва"
        mock_get_extract.return_value = {
            "title": "Москва",
            "extract": "Москва — столица Российской Федерации.",
            "url": "https://ru.wikipedia.org/wiki/Москва",
        }

        # ═══ Act ═══
        result = wikipedia_lookup.wikipedia_lookup.invoke({"query": "Москва"})

        # ═══ Assert ═══
        assert "Москва" in result
        assert "столица" in result
        assert "ru.wikipedia.org" in result

    @patch("wikipedia_lookup._find_article_title")
    def test_wikipedia_lookup_not_found(self, mock_find_title):
        """Статья не найдена — возвращает сообщение об ошибке."""
        # ═══ Arrange ═══
        mock_find_title.return_value = None

        # ═══ Act ═══
        query = "НесуществующаяСтатья"
        result = wikipedia_lookup.wikipedia_lookup.invoke({"query": query})

        # ═══ Assert ═══
        assert "Не удалось найти статью" in result
        assert query in result

    @patch("wikipedia_lookup._get_article_extract")
    @patch("wikipedia_lookup._find_article_title")
    def test_wikipedia_lookup_no_content(
        self, mock_find_title, mock_get_extract
    ):
        """
        Статья найдена, но extract пустой —
        возвращает сообщение об отсутствии содержимого.
        """
        # ═══ Arrange ═══
        mock_find_title.return_value = "ПустаяСтатья"
        mock_get_extract.return_value = {
            "error": "У статьи нет текстового содержимого"
        }

        # ═══ Act ═══
        query = "ПустаяСтатья"
        result = wikipedia_lookup.wikipedia_lookup.invoke({"query": query})

        # ═══ Assert ═══
        assert "У статьи нет текстового содержимого" in result
        assert query in result
