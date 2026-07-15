"""
Тесты качества данных: структура ответов, User-Agent валидация, edge cases.

ВНИМАНИЕ: @tool-декорированные функции вызываются через .invoke(dict),
а не напрямую. Пример:
    import search_places
    search_places.search_places.invoke({"lat": ..., "lon": ...})
"""
import pytest
from unittest.mock import patch, MagicMock
import logging


# ═══════════════════════════════════════════════════════════════════════
# Структура ответов
# ═══════════════════════════════════════════════════════════════════════

class TestGeocodePlaceResultStructure:
    """Проверка, что geocode_place возвращает все ожидаемые ключи."""

    def test_geocode_place_result_structure(self):
        """
        Успешный ответ geocode_place должен содержать:
        lat (float), lon (float), display_name (str), type (str), importance (float).
        """
        import geocode_place

        mock_response_data = [
            {
                "lat": "55.7558",
                "lon": "37.6173",
                "display_name": "Красная площадь, Москва, Россия",
                "type": "square",
                "importance": 0.8,
                "address": {},
            }
        ]

        with patch("geocode_place.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = geocode_place.geocode_place.invoke({"query": "Красная площадь"})

            assert "error" not in result, f"Неожиданная ошибка: {result}"

            # Проверяем наличие всех обязательных ключей
            assert "lat" in result, "Отсутствует ключ 'lat'"
            assert "lon" in result, "Отсутствует ключ 'lon'"
            assert "display_name" in result, "Отсутствует ключ 'display_name'"
            assert "type" in result, "Отсутствует ключ 'type'"
            assert "importance" in result, "Отсутствует ключ 'importance'"

            # Проверяем типы
            assert isinstance(result["lat"], float), f"lat должен быть float, получен {type(result['lat'])}"
            assert isinstance(result["lon"], float), f"lon должен быть float, получен {type(result['lon'])}"
            assert isinstance(result["display_name"], str), f"display_name должен быть str"
            assert isinstance(result["type"], str), f"type должен быть str"
            assert isinstance(result["importance"], float), f"importance должен быть float"

    def test_geocode_place_not_found(self):
        """Пустой ответ от Nominatim → сообщение об ошибке."""
        import geocode_place

        with patch("geocode_place.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            result = geocode_place.geocode_place.invoke({"query": "asdfghjkzxcvbnm_nonexistent"})
            assert "error" in result, "Должна быть ошибка для ненайденного места"
            assert "не найдено" in result["error"].lower()

    def test_geocode_place_missing_fields(self):
        """Ответ с пропущенными полями → не падает, а возвращает значения по умолчанию."""
        import geocode_place

        mock_response_data = [
            {
                "lat": "55.7558",
                "lon": "37.6173",
                # display_name, type, importance отсутствуют
            }
        ]

        with patch("geocode_place.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = geocode_place.geocode_place.invoke({"query": "тест"})
            assert "error" not in result
            assert result["display_name"] == ""
            assert result["type"] == ""
            assert result["importance"] == 0.0


class TestGetPlaceInfoResultStructure:
    """Проверка структуры ответа get_place_info."""

    def test_get_place_info_result_structure(self):
        """
        Успешный ответ get_place_info должен содержать:
        city, district, state, country, full_address.
        """
        import get_place_info

        mock_response_data = {
            "display_name": "Москва, Россия",
            "address": {
                "city": "Москва",
                "state": "Москва",
                "country": "Россия",
            },
        }

        with patch("get_place_info.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = get_place_info.get_place_info.invoke(
                {"lat": 55.7558, "lon": 37.6173}
            )

            assert "error" not in result, f"Неожиданная ошибка: {result}"
            assert "city" in result, "Отсутствует ключ 'city'"
            assert "district" in result, "Отсутствует ключ 'district'"
            assert "state" in result, "Отсутствует ключ 'state'"
            assert "country" in result, "Отсутствует ключ 'country'"
            assert "full_address" in result, "Отсутствует ключ 'full_address'"

            assert result["city"] == "Москва"
            assert result["state"] == "Москва"
            assert result["country"] == "Россия"

    def test_get_place_info_all_address_fields(self):
        """Проверка извлечения всех типов адресных полей."""
        import get_place_info

        mock_response_data = {
            "display_name": "ул. Тверская, Тверской район, Москва, Россия",
            "address": {
                "road": "Тверская",
                "suburb": "Тверской район",
                "city": "Москва",
                "state": "Москва",
                "country": "Россия",
            },
        }

        with patch("get_place_info.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = get_place_info.get_place_info.invoke(
                {"lat": 55.76, "lon": 37.61}
            )
            assert result["district"] == "Тверской район"
            assert result["city"] == "Москва"
            assert result["full_address"] == "ул. Тверская, Тверской район, Москва, Россия"

    def test_get_place_info_town_fallback(self):
        """
        Если нет 'city', но есть 'town' → city берётся из 'town'.
        """
        import get_place_info

        mock_response_data = {
            "display_name": "Пушкинские Горы, Псковская обл., Россия",
            "address": {
                "town": "Пушкинские Горы",
                "state": "Псковская область",
                "country": "Россия",
            },
        }

        with patch("get_place_info.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = get_place_info.get_place_info.invoke(
                {"lat": 57.0, "lon": 28.9}
            )
            assert result["city"] == "Пушкинские Горы"

    def test_get_place_info_error_response(self):
        """Ответ с 'error' от Nominatim → передаётся в результат."""
        import get_place_info

        with patch("get_place_info.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"error": "Unable to geocode"}
            mock_get.return_value = mock_response

            result = get_place_info.get_place_info.invoke(
                {"lat": 999.0, "lon": 999.0}
            )
            assert "error" in result


# ═══════════════════════════════════════════════════════════════════════
# User-Agent валидация
# ═══════════════════════════════════════════════════════════════════════

class TestUserAgentWarning:
    """
    Проверка, что при отсутствии USER_AGENT логируется предупреждение.
    Тестируем geocode_place, get_place_info, search_places, wikipedia_lookup.
    """

    def _check_warning(self, caplog, module_name):
        """Проверяет, что есть запись WARNING c USER_AGENT в указанном логгере."""
        assert any(
            record.levelno == logging.WARNING
            and record.name == module_name
            and "USER_AGENT" in record.message
            for record in caplog.records
        ), f"Нет предупреждения о USER_AGENT в {module_name}"

    def test_user_agent_warning_geocode_place(self, caplog):
        """geocode_place: отсутствие USER_AGENT → warning."""
        with patch("geocode_place.os.getenv", return_value=None):
            caplog.clear()
            with caplog.at_level(logging.WARNING):
                import importlib
                import geocode_place
                importlib.reload(geocode_place)

            self._check_warning(caplog, "geocode_place")

    def test_user_agent_warning_get_place_info(self, caplog):
        """get_place_info: отсутствие USER_AGENT → warning."""
        with patch("get_place_info.os.getenv", return_value=None):
            caplog.clear()
            with caplog.at_level(logging.WARNING):
                import importlib
                import get_place_info
                importlib.reload(get_place_info)

            self._check_warning(caplog, "get_place_info")

    def test_user_agent_warning_search_places(self, caplog):
        """search_places: отсутствие USER_AGENT → warning."""
        with patch("search_places.os.getenv", return_value=None):
            caplog.clear()
            with caplog.at_level(logging.WARNING):
                import importlib
                import search_places
                importlib.reload(search_places)

            self._check_warning(caplog, "search_places")

    def test_user_agent_warning_wikipedia_lookup(self, caplog):
        """wikipedia_lookup: отсутствие USER_AGENT → warning."""
        with patch("wikipedia_lookup.os.getenv", return_value=None):
            caplog.clear()
            with caplog.at_level(logging.WARNING):
                import importlib
                import wikipedia_lookup
                importlib.reload(wikipedia_lookup)

            self._check_warning(caplog, "wikipedia_lookup")


# ═══════════════════════════════════════════════════════════════════════
# Edge cases Nominatim
# ═══════════════════════════════════════════════════════════════════════

class TestNominatimEdgeCases:
    """Проверка обработки спецсимволов и граничных координат."""

    def test_geocode_place_special_chars(self):
        """
        Запрос со спецсимволами: "Москва, ул. Пушкина & 10".
        Должен корректно передать query в Nominatim.
        """
        import geocode_place

        with patch("geocode_place.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {
                    "lat": "55.7558",
                    "lon": "37.6173",
                    "display_name": "Москва, ул. Пушкина & 10",
                    "type": "address",
                    "importance": 0.5,
                }
            ]
            mock_get.return_value = mock_response

            result = geocode_place.geocode_place.invoke(
                {"query": "Москва, ул. Пушкина & 10"}
            )
            assert "error" not in result
            assert result["lat"] == 55.7558

            # Проверяем, что query был передан в params правильно
            called_params = mock_get.call_args[1]["params"]
            assert called_params["q"] == "Москва, ул. Пушкина & 10"

    def test_geocode_place_html_entities(self):
        """Запрос с HTML-опасными символами: <script>, кавычки."""
        import geocode_place

        with patch("geocode_place.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {
                    "lat": "0.0",
                    "lon": "0.0",
                    "display_name": "Test",
                    "type": "test",
                    "importance": 0.1,
                }
            ]
            mock_get.return_value = mock_response

            result = geocode_place.geocode_place.invoke(
                {"query": '<script>alert("xss")</script>'}
            )
            assert "error" not in result

            called_params = mock_get.call_args[1]["params"]
            assert called_params["q"] == '<script>alert("xss")</script>'

    def test_get_place_info_boundary_coords(self):
        """Координаты на границе: lat=0, lon=0 (нулевая точка)."""
        import get_place_info

        mock_response_data = {
            "display_name": "Null Island",
            "address": {
                "country": "International waters",
            },
        }

        with patch("get_place_info.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = get_place_info.get_place_info.invoke(
                {"lat": 0.0, "lon": 0.0}
            )
            assert "error" not in result
            assert result["full_address"] == "Null Island"

            # Проверяем, что параметры переданы верно
            called_params = mock_get.call_args[1]["params"]
            assert called_params["lat"] == 0.0
            assert called_params["lon"] == 0.0

    def test_get_place_info_missing_address(self):
        """Ответ без поля 'address' — не падает."""
        import get_place_info

        with patch("get_place_info.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "display_name": "Где-то в океане",
                # 'address' отсутствует
            }
            mock_get.return_value = mock_response

            result = get_place_info.get_place_info.invoke(
                {"lat": 0.0, "lon": 0.0}
            )
            assert "error" not in result
            assert result["city"] is None
            assert result["district"] is None
            assert result["state"] is None
            assert result["country"] is None
            assert result["full_address"] == "Где-то в океане"

    def test_geocode_place_request_exception(self):
        """Ошибка соединения с Nominatim → корректный error response."""
        import geocode_place

        with patch("geocode_place.requests.get") as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

            result = geocode_place.geocode_place.invoke({"query": "Москва"})
            assert "error" in result
            assert "Ошибка запроса" in result["error"]

    def test_get_place_info_json_exception(self):
        """Некорректный JSON от Nominatim → ValueError → error response."""
        import get_place_info

        with patch("get_place_info.requests.get") as mock_get:
            # Нельзя вызвать json() — будет ValueError
            mock_response = MagicMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response

            result = get_place_info.get_place_info.invoke(
                {"lat": 55.0, "lon": 37.0}
            )
            assert "error" in result
