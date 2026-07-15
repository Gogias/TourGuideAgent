"""
Юнит-тесты для тула search_places.

Мокаем внутренние функции _query_overpass, _wikipedia_geosearch и
_get_short_extracts, чтобы не было реальных HTTP-запросов.
"""

from unittest.mock import patch, MagicMock
import pytest
import search_places


class TestSearchPlaces:
    """Тесты для search_places: успех, пусто, ошибка Overpass, дедупликация."""

    @patch("search_places._get_short_extracts")
    @patch("search_places._wikipedia_geosearch")
    @patch("search_places._query_overpass")
    def test_search_places_success(
        self, mock_query_overpass, mock_wiki_geosearch, mock_get_extracts
    ):
        """Успешный поиск — возвращает форматированный список объектов."""
        # ═══ Arrange ═══
        mock_query_overpass.return_value = {
            "elements": [
                {
                    "type": "node",
                    "id": 12345,
                    "lat": 55.7558,
                    "lon": 37.6173,
                    "tags": {
                        "name": "Эйфелева башня",
                        "tourism": "attraction",
                        "wikipedia": "ru:Эйфелева башня",
                    },
                }
            ]
        }
        mock_wiki_geosearch.return_value = []
        mock_get_extracts.return_value = {
            "Эйфелева башня": "Знаменитая башня в Париже"
        }

        # ═══ Act ═══
        result = search_places.search_places.invoke(
            {"lat": 55.7558, "lon": 37.6173, "radius": 1000, "limit": 10}
        )

        # ═══ Assert ═══
        assert "🏛️ Найдено 1 объектов" in result
        assert "Эйфелева башня" in result
        assert "Туризм: attraction" in result
        assert "Знаменитая башня в Париже" in result
        assert "wikipedia.org" in result
        assert "openstreetmap.org" in result

    @patch("search_places._wikipedia_geosearch")
    @patch("search_places._query_overpass")
    def test_search_places_empty(
        self, mock_query_overpass, mock_wiki_geosearch
    ):
        """Нет результатов — возвращает сообщение 'Ничего не найдено'."""
        # ═══ Arrange ═══
        mock_query_overpass.return_value = {"elements": []}
        mock_wiki_geosearch.return_value = []

        # ═══ Act ═══
        result = search_places.search_places.invoke(
            {"lat": 55.7558, "lon": 37.6173, "radius": 1000}
        )

        # ═══ Assert ═══
        assert "Ничего не найдено" in result
        assert "1000" in result

    @patch("search_places._wikipedia_geosearch")
    @patch("search_places._query_overpass")
    def test_search_places_overpass_fail(
        self, mock_query_overpass, mock_wiki_geosearch
    ):
        """Overpass вернул ошибку, Wikipedia пустая — сообщение об ошибке."""
        # ═══ Arrange ═══
        mock_query_overpass.return_value = {
            "error": "Все Overpass-серверы недоступны"
        }
        mock_wiki_geosearch.return_value = []

        # ═══ Act ═══
        result = search_places.search_places.invoke(
            {"lat": 55.7558, "lon": 37.6173, "radius": 500}
        )

        # ═══ Assert ═══
        assert "Не удалось найти достопримечательности" in result
        assert "500" in result

    @patch("search_places._get_short_extracts")
    @patch("search_places._wikipedia_geosearch")
    @patch("search_places._query_overpass")
    def test_search_places_dedup(
        self, mock_query_overpass, mock_wiki_geosearch, mock_get_extracts
    ):
        """Один объект найден и в Overpass, и в Wikipedia — без дублирования."""
        # ═══ Arrange ═══
        # Элемент Overpass без wikipedia-тега
        mock_query_overpass.return_value = {
            "elements": [
                {
                    "type": "node",
                    "id": 999,
                    "lat": 48.8584,
                    "lon": 2.2945,
                    "tags": {
                        "name": "Эйфелева башня",
                        "tourism": "attraction",
                    },
                }
            ]
        }
        # Wikipedia geosearch возвращает тот же объект (на тех же координатах)
        mock_wiki_geosearch.return_value = [
            {
                "title": "Эйфелева башня",
                "lat": 48.8584,
                "lon": 2.2945,
                "dist": 5,
            }
        ]
        mock_get_extracts.return_value = {}

        # ═══ Act ═══
        result = search_places.search_places.invoke(
            {"lat": 48.8584, "lon": 2.2945, "radius": 1000, "limit": 10}
        )

        # ═══ Assert ═══
        # Должен быть только 1 объект (дедуплицирован)
        assert "🏛️ Найдено 1 объектов" in result
        assert "Эйфелева башня" in result
        # Wikipedia-ссылка должна быть добавлена к существующему объекту
        assert "ru.wikipedia.org" in result

        # Считаем количество вхождений названия — должно быть ровно 1
        assert result.count("Эйфелева башня") == 1
