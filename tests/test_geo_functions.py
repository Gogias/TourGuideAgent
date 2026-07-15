"""
Тесты чистых геопространственных функций:
  - haversine (математика расстояний)
  - _names_match (сравнение названий)
  - _is_likely_landmark (фильтрация не-достопримечательностей)
  - _wiki_tag_to_url (построение URL Wikipedia)
"""
import pytest
from search_places import (
    haversine,
    _names_match,
    _is_likely_landmark,
    _wiki_tag_to_url,
)


# ═══════════════════════════════════════════════════════════════════════
# haversine
# ═══════════════════════════════════════════════════════════════════════

class TestHaversine:
    """Проверка корректности вычисления расстояния по гаверсинусу."""

    def test_haversine_same_point(self):
        """Расстояние от точки до самой себя = 0."""
        lat, lon = 55.7558, 37.6173
        assert haversine(lat, lon, lat, lon) == 0.0

    def test_haversine_moscow_spb(self):
        """
        Москва → Санкт-Петербург: ~635 км.
        Допуск: ±10 км (реальные ~633–640 км по гаверсинусу).
        """
        moscow = (55.7558, 37.6173)
        spb = (59.9343, 30.3351)
        dist = haversine(*moscow, *spb)
        assert 625 <= dist <= 645, f"Москва-СПб: {dist} км, ожидалось ~635 км"

    def test_haversine_equator(self):
        """
        Две точки на экваторе с разницей долготы 1°.
        Расстояние ≈ 111.2 км (длина 1° по экватору = 6371 * π/180).
        """
        dist = haversine(0.0, 0.0, 0.0, 1.0)
        assert 110.0 <= dist <= 112.5, f"Экватор 1°: {dist} км, ожидалось ~111.2 км"

    def test_haversine_poles(self):
        """
        Северный полюс → экватор (по одному меридиану).
        Расстояние = π/2 * R ≈ 10 007.5 км.
        """
        dist = haversine(90.0, 0.0, 0.0, 0.0)
        assert 9980 <= dist <= 10030, f"Полюс→экватор: {dist} км, ожидалось ~10007 км"

    def test_haversine_antipodal(self):
        """Антиподы: точки на противоположных сторонах Земли ≈ 20015 км."""
        dist = haversine(0.0, 0.0, 0.0, 180.0)
        assert 19900 <= dist <= 20100, f"Антиподы: {dist} км, ожидалось ~20015 км"

    def test_haversine_negative_coords(self):
        """Корректная работа с отрицательными координатами (южное полушарие, западная долгота)."""
        # Сидней (-33.86, 151.21) → Токио (35.68, 139.76) ≈ 7820 км
        dist = haversine(-33.86, 151.21, 35.68, 139.76)
        assert 7750 <= dist <= 7900, f"Сидней→Токио: {dist} км, ожидалось ~7820 км"


# ═══════════════════════════════════════════════════════════════════════
# _names_match
# ═══════════════════════════════════════════════════════════════════════

class TestNamesMatch:
    """Проверка сравнения названий объектов."""

    def test_names_match_exact(self):
        """Точное совпадение — True."""
        assert _names_match("Красная площадь", "Красная площадь") is True

    def test_names_match_substring(self):
        """Одно название содержит другое — True."""
        assert _names_match("Красная", "Красная площадь") is True
        assert _names_match("Красная площадь", "Красная") is True

    def test_names_match_case_insensitive(self):
        """Регистронезависимость."""
        assert _names_match("КРАСНАЯ ПЛОЩАДЬ", "красная площадь") is True
        assert _names_match("Красная Площадь", "красная площадь") is True

    def test_names_match_different(self):
        """Разные названия — False."""
        assert _names_match("Красная площадь", "Эйфелева башня") is False

    def test_names_match_whitespace(self):
        """Пробелы в начале/конце не влияют."""
        assert _names_match("  Красная площадь  ", "Красная площадь") is True
        assert _names_match("Красная площадь", "  Красная площадь  ") is True

    def test_names_match_empty(self):
        """Пустая строка — пустое совпадение True, т.к. '' in 'abc'."""
        assert _names_match("", "") is True
        # '' in 'abc' → True, т.к. пустая строка является подстрокой любой строки

    def test_names_match_latin(self):
        """Латиница тоже работает."""
        assert _names_match("Red Square", "Red Square") is True
        assert _names_match("Red", "Red Square") is True
        assert _names_match("Red Square", "red square") is True


# ═══════════════════════════════════════════════════════════════════════
# _is_likely_landmark
# ═══════════════════════════════════════════════════════════════════════

class TestIsLikelyLandmark:
    """Проверка фильтрации не-достопримечательностей."""

    def test_is_likely_landmark_true(self):
        """Известные достопримечательности — True."""
        assert _is_likely_landmark("Красная площадь") is True
        assert _is_likely_landmark("Эйфелева башня") is True
        assert _is_likely_landmark("Собор Василия Блаженного") is True
        assert _is_likely_landmark("Московский Кремль") is True

    def test_is_likely_landmark_false(self):
        """Объекты, не являющиеся достопримечательностями — False."""
        assert _is_likely_landmark("улица Ленина") is False
        assert _is_likely_landmark("похороны Петрова") is False
        assert _is_likely_landmark("библиотека N1") is False
        assert _is_likely_landmark("проспект Мира") is False

    def test_is_likely_landmark_edge_more(self):
        """Дополнительные граничные случаи."""
        # Содержат ключевые слова из NON_LANDMARK_KEYWORDS
        assert _is_likely_landmark("траурная церемония") is False
        assert _is_likely_landmark("митинг оппозиции") is False
        assert _is_likely_landmark("переулок Столярный") is False
        assert _is_likely_landmark("фестиваль красок") is False

    def test_is_likely_landmark_pobeda(self):
        """'победа' в списке исключений — победа как событие блокируется."""
        assert _is_likely_landmark("победа сборной") is False
        # Но "Парк Победы" — это достопримечательность!
        # Обратите внимание: 'победа' есть в NON_LANDMARK_KEYWORDS,
        # поэтому "Парк Победы" будет ложно исключён!
        assert _is_likely_landmark("Парк Победы") is False  # ложное срабатывание

    def test_is_likely_landmark_okrug(self):
        """'округ' — не достопримечательность."""
        assert _is_likely_landmark("Центральный округ") is False

    def test_is_likely_landmark_empty(self):
        """Пустая строка — достопримечательность (нет ключевых слов)."""
        assert _is_likely_landmark("") is True


# ═══════════════════════════════════════════════════════════════════════
# _wiki_tag_to_url
# ═══════════════════════════════════════════════════════════════════════

class TestWikiTagToUrl:
    """Проверка построения URL Wikipedia из wiki-тега OSM."""

    def test_wiki_tag_russian(self):
        """Тег 'ru:Москва' → русская Wikipedia."""
        url = _wiki_tag_to_url("ru:Москва")
        assert url == "https://ru.wikipedia.org/wiki/%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0"
        assert "ru.wikipedia.org" in url

    def test_wiki_tag_english(self):
        """Тег 'en:London' → английская Wikipedia."""
        url = _wiki_tag_to_url("en:London")
        assert url == "https://en.wikipedia.org/wiki/London"
        assert "en.wikipedia.org" in url

    def test_wiki_tag_no_lang(self):
        """Тег без языка → по умолчанию 'ru'."""
        url = _wiki_tag_to_url("Москва")
        assert url == "https://ru.wikipedia.org/wiki/%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0"
        assert "ru.wikipedia.org" in url

    def test_wiki_tag_multilang(self):
        """Тег 'de:Berlin' → немецкая Wikipedia."""
        url = _wiki_tag_to_url("de:Berlin")
        assert url == "https://de.wikipedia.org/wiki/Berlin"

    def test_wiki_tag_spaces(self):
        """Пробелы в названии заменяются на подчёркивания."""
        url = _wiki_tag_to_url("ru:Красная площадь")
        assert "_" in url
        assert " " not in url

    def test_wiki_tag_special_chars(self):
        """Спецсимволы кодируются через quote()."""
        url = _wiki_tag_to_url("en:St. Peter's Basilica")
        assert "%27" in url  # апостроф кодируется
        assert "St." in url
