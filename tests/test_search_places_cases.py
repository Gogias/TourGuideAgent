"""
Тесты граничных случаев search_places с моками Overpass и Wikipedia API.

ВНИМАНИЕ: @tool-декорированные функции вызываются через .invoke(dict):
    import search_places
    search_places.search_places.invoke({"lat": 55.0, "lon": 37.0, ...})
"""
import pytest
from unittest.mock import patch, MagicMock


# ═══════════════════════════════════════════════════════════════════════
# Search Places — граничные случаи
# ═══════════════════════════════════════════════════════════════════════

class TestSearchPlacesEdgeCases:
    """Проверка обработки экстремальных и граничных входных данных."""

    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_invalid_coords(
        self, mock_wiki_geo, mock_overpass
    ):
        """
        Экстремальные значения координат (lat=999, lon=999).
        Функция не валидирует диапазон координат, передаёт запрос в Overpass.
        """
        import search_places

        mock_overpass.return_value = {"elements": []}
        mock_wiki_geo.return_value = []

        result = search_places.search_places.invoke(
            {"lat": 999.0, "lon": 999.0, "radius": 1000, "limit": 10}
        )
        assert "Ничего не найдено" in result or "Не удалось найти" in result

    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_negative_coords(
        self, mock_wiki_geo, mock_overpass
    ):
        """Отрицательные координаты (южное полушарие, западная долгота)."""
        import search_places

        mock_overpass.return_value = {"elements": []}
        mock_wiki_geo.return_value = []

        result = search_places.search_places.invoke(
            {"lat": -33.86, "lon": 151.21, "radius": 1000, "limit": 10}
        )
        assert isinstance(result, str)

    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_zero_radius(
        self, mock_wiki_geo, mock_overpass
    ):
        """Radius=0 — не находит ничего, т.к. around:0 ищет на нулевом расстоянии."""
        import search_places

        mock_overpass.return_value = {"elements": []}
        mock_wiki_geo.return_value = []

        result = search_places.search_places.invoke(
            {"lat": 55.7558, "lon": 37.6173, "radius": 0, "limit": 10}
        )
        assert "Ничего не найдено" in result or "Не удалось найти" in result

    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_negative_radius(
        self, mock_wiki_geo, mock_overpass
    ):
        """Radius < 0 — передаётся в Overpass как есть."""
        import search_places

        mock_overpass.return_value = {"elements": []}
        mock_wiki_geo.return_value = []

        result = search_places.search_places.invoke(
            {"lat": 55.7558, "lon": 37.6173, "radius": -100, "limit": 10}
        )
        assert isinstance(result, str)

    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_large_radius(
        self, mock_wiki_geo, mock_overpass
    ):
        """Radius=50000 (больше max 10000 для Wikipedia)."""
        import search_places

        mock_overpass.return_value = {"elements": []}
        mock_wiki_geo.return_value = []

        result = search_places.search_places.invoke(
            {"lat": 55.7558, "lon": 37.6173, "radius": 50000, "limit": 10}
        )
        assert isinstance(result, str)

    @patch("search_places._get_short_extracts")
    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_dedup_same_object(
        self, mock_wiki_geo, mock_overpass, mock_extracts
    ):
        """
        Один и тот же объект найден и Overpass, и Wikipedia.
        Результат: один объект с обогащённым wiki_url, не дублируется.
        """
        import search_places

        mock_overpass.return_value = {
            "elements": [
                {
                    "type": "node",
                    "id": 12345,
                    "lat": 55.7558,
                    "lon": 37.6173,
                    "tags": {
                        "name": "Красная площадь",
                        "tourism": "attraction",
                        "wikipedia": "ru:Красная площадь",
                    },
                }
            ]
        }
        mock_wiki_geo.return_value = [
            {
                "title": "Красная площадь",
                "lat": 55.7558,
                "lon": 37.6173,
                "dist": 50,
                "pageid": 123,
            }
        ]
        mock_extracts.return_value = {}

        result = search_places.search_places.invoke(
            {"lat": 55.76, "lon": 37.62, "radius": 1000, "limit": 10}
        )
        # Должен быть только 1 объект
        assert "Найдено 1 объектов" in result
        assert "ru.wikipedia.org" in result

    @patch("search_places._get_short_extracts")
    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_wikipedia_enriches_existing(
        self, mock_wiki_geo, mock_overpass, mock_extracts
    ):
        """
        Wikipedia возвращает объект, уже найденный Overpass (без wiki-тега),
        — существующая запись обогащается wiki_url.
        """
        import search_places

        mock_overpass.return_value = {
            "elements": [
                {
                    "type": "node",
                    "id": 12345,
                    "lat": 55.7558,
                    "lon": 37.6173,
                    "tags": {
                        "name": "Красная площадь",
                        "tourism": "attraction",
                    },
                }
            ]
        }
        mock_wiki_geo.return_value = [
            {
                "title": "Красная площадь",
                "lat": 55.7558,
                "lon": 37.6173,
                "dist": 10,
                "pageid": 123,
            }
        ]
        mock_extracts.return_value = {}

        result = search_places.search_places.invoke(
            {"lat": 55.76, "lon": 37.62, "radius": 1000, "limit": 10}
        )
        # Только 1 объект, с wiki_url
        assert "Найдено 1 объектов" in result
        assert "wikipedia.org" in result

    @patch("search_places._get_short_extracts")
    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_priority_sorting(
        self, mock_wiki_geo, mock_overpass, mock_extracts
    ):
        """
        Объекты с Wikipedia (priority=0) должны идти ПЕРВЫМИ,
        затем с priority=1, затем priority=2.
        """
        import search_places

        mock_wiki_geo.return_value = []
        mock_extracts.return_value = {}

        mock_overpass.return_value = {
            "elements": [
                {
                    "type": "node",
                    "id": 1,
                    "lat": 55.75,
                    "lon": 37.61,
                    "tags": {"name": "Обычное место", "amenity": "cafe"},
                },
                {
                    "type": "node",
                    "id": 2,
                    "lat": 55.76,
                    "lon": 37.62,
                    "tags": {
                        "name": "Музей",
                        "tourism": "museum",
                        "wikipedia": "ru:Музей",
                    },
                },
                {
                    "type": "node",
                    "id": 3,
                    "lat": 55.77,
                    "lon": 37.63,
                    "tags": {"name": "ТЦ", "shop": "mall"},
                },
            ]
        }

        result = search_places.search_places.invoke(
            {"lat": 55.76, "lon": 37.62, "radius": 1000, "limit": 10}
        )
        lines = [line.strip() for line in result.split("\n") if line.strip()]
        idx_museum = next(i for i, l in enumerate(lines) if "Музей" in l)
        idx_mall = next(i for i, l in enumerate(lines) if "ТЦ" in l)
        idx_cafe = next(i for i, l in enumerate(lines) if "Обычное место" in l)
        assert idx_museum < idx_mall < idx_cafe, (
            f"Порядок сортировки нарушен: Музей={idx_museum}, ТЦ={idx_mall}, "
            f"Кафе={idx_cafe}"
        )

    @patch("search_places._get_short_extracts")
    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_limit_respected(
        self, mock_wiki_geo, mock_overpass, mock_extracts
    ):
        """Параметр limit ограничивает количество результатов."""
        import search_places

        elements = []
        for i in range(20):
            elements.append({
                "type": "node",
                "id": i,
                "lat": 55.75 + i * 0.001,
                "lon": 37.61 + i * 0.001,
                "tags": {"name": f"Объект {i}", "tourism": "attraction"},
            })
        mock_overpass.return_value = {"elements": elements}
        mock_wiki_geo.return_value = []
        mock_extracts.return_value = {}

        result = search_places.search_places.invoke(
            {"lat": 55.76, "lon": 37.62, "radius": 1000, "limit": 5}
        )
        lines = [l for l in result.split("\n") if l.strip()]
        object_count = sum(1 for l in lines if l.strip() and l.strip()[0].isdigit())
        assert object_count <= 5, f"Ожидалось ≤5 объектов, получено {object_count}"

    @patch("search_places._query_overpass")
    @patch("search_places._wikipedia_geosearch")
    def test_search_places_overpass_error(
        self, mock_wiki_geo, mock_overpass
    ):
        """Overpass недоступен — используется только Wikipedia."""
        import search_places

        mock_overpass.return_value = {"error": "Все серверы недоступны"}
        mock_wiki_geo.return_value = []

        result = search_places.search_places.invoke(
            {"lat": 55.7558, "lon": 37.6173, "radius": 1000, "limit": 10}
        )
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════════════════
# verify_coordinate_ranges — проверка инструментов, принимающих lat/lon
# ═══════════════════════════════════════════════════════════════════════

class TestCoordinateRanges:
    """
    Проверка, что инструменты корректно принимают широту [-90, 90]
    и долготу [-180, 180]. Тестируем get_place_info и get_route_link,
    так как они принимают lat/lon напрямую.
    """

    @patch("get_place_info.requests.get")
    def test_get_place_info_valid_range_negative(self, mock_get):
        """Отрицательные lat/lon в пределах допустимого диапазона."""
        import get_place_info

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "display_name": "Test",
            "address": {
                "country": "Test Country",
            },
        }
        mock_get.return_value = mock_response

        result = get_place_info.get_place_info.invoke(
            {"lat": -33.86, "lon": -60.0}
        )
        assert "error" not in result, f"Ошибка для (-33.86, -60.0): {result}"

    @patch("get_place_info.requests.get")
    def test_get_place_info_valid_range_boundary(self, mock_get):
        """Граничные значения: lat=90, lon=180."""
        import get_place_info

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "display_name": "Boundary",
            "address": {"country": "Nowhere"},
        }
        mock_get.return_value = mock_response

        result = get_place_info.get_place_info.invoke(
            {"lat": 90.0, "lon": 180.0}
        )
        assert "error" not in result

    def test_route_link_valid_ranges(self):
        """Проверка get_route_link с разными комбинациями lat/lon."""
        import route_link

        # Северное полушарие → южное полушарие
        url1 = route_link.get_route_link.invoke({
            "from_lat": 55.7558, "from_lon": 37.6173,
            "to_lat": -33.86, "to_lon": 151.21,
        })
        assert "yandex.ru/maps" in url1

        # Граничные значения
        url2 = route_link.get_route_link.invoke({
            "from_lat": 90.0, "from_lon": 180.0,
            "to_lat": -90.0, "to_lon": -180.0,
        })
        assert "yandex.ru/maps" in url2

        # Нулевые координаты
        url3 = route_link.get_route_link.invoke({
            "from_lat": 0.0, "from_lon": 0.0,
            "to_lat": 0.0, "to_lon": 0.0,
        })
        assert "yandex.ru/maps" in url3

    def test_route_link_param_types(self):
        """Проверка, что get_route_link принимает разные числовые типы (int, float)."""
        import route_link

        # int → в URL преобразуется в float (55.0)
        url = route_link.get_route_link.invoke({
            "from_lat": 55, "from_lon": 37,
            "to_lat": 60, "to_lon": 30,
            "transport": "пешком",
        })
        assert "yandex.ru/maps" in url
        assert "rtext=55.0,37.0~60.0,30.0" in url

        # float
        url2 = route_link.get_route_link.invoke({
            "from_lat": 55.5, "from_lon": 37.5,
            "to_lat": 60.0, "to_lon": 30.0,
            "transport": "пешком",
        })
        assert "yandex.ru/maps" in url2
        assert "55.5,37.5" in url2
