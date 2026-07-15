# TourGuideAgent 🤖🗺️

> **Интеллектуальный Telegram-бот-гид на базе ИИ** — отметьте точку на карте, узнайте о достопримечательностях, получите историческую справку и проложите маршрут.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.3-1C3C3C?logo=langchain)](https://langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-6C5CE7)](https://langchain-ai.github.io/langgraph/)
[![aiogram](https://img.shields.io/badge/aiogram-3.29-2F8F9D)](https://docs.aiogram.dev)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen)](https://docs.pytest.org)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 📖 Обзор

**TourGuideAgent** — это интеллектуальный Telegram-бот, который работает как ваш личный гид. Вместо того чтобы просматривать десятки туристических сайтов, пользователь просто отправляет своё местоположение (или вводит координаты) и задаёт вопросы:

> *«Что здесь интересного рядом?»*  
> *«Расскажи подробнее о Красной площади.»*  
> *«Как мне добраться отсюда до собора?»*

Агент использует **LLM на базе LangChain** с набором геопространственных инструментов для поиска достопримечательностей, получения статей из Wikipedia, обратного геокодирования местоположений и генерации ссылок на маршруты — и всё это в рамках естественного диалога в Telegram.

Проект создан для реальной помощи путешественникам и демонстрирует передовые технологии **разработки ИИ-агентов**: использование инструментов языковой моделью, память диалога, геопространственные API и production-ready асинхронную инфраструктуру.

---

## ✨ Возможности

| Возможность | Описание |
|-------------|----------|
| **📍 Определение местоположения** | Принимает геометки Telegram или ручной ввод координат |
| **🔍 Поиск ближайших достопримечательностей** | Ищет по OpenStreetMap (Overpass API) + Wikipedia GeoSearch для объектов вокруг любой точки |
| **📜 Подробная информация о месте** | Обратное геокодирование координат в город/район через Nominatim |
| **🌐 Интеграция с Wikipedia** | Получение полного текста статей для глубоких описаний мест и исторического контекста |
| **🗺️ Построение маршрутов** | Генерация ссылок на Яндекс.Карты для пеших, автомобильных или общественных маршрутов |
| **💬 Память диалога** | История переписки для каждого пользователя, сохраняемая через SQLite (LangGraph Checkpoint) |
| **⚡ Полностью асинхронный** | Построен на `aiogram` 3.x с асинхронной обработкой событий |
| **🧪 Покрыт тестами** | Комплексный набор pytest, покрывающий все инструменты и граничные случаи |
| **🔁 Автоматический перезапуск** | Корректное восстановление после сбоев с циклом перезапуска (`run_bot.bat`) |
| **📋 Административные команды** | Команда `/restart` для администраторов бота |

---

## 🧠 Как это работает

```
Telegram User → aiogram Bot → LangGraph Agent → Tools
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          ▼                        ▼                        ▼
                   search_places()          get_place_info()         geocode_place()
                   (Overpass + Wiki)        (Nominatim reverse)      (Nominatim search)
                          │                        │                        │
                          ▼                        ▼                        ▼
                   wikipedia_lookup()        get_route_link()
                   (Wiki article)           (Yandex Maps)
```

**LangGraph-агент** получает запрос на естественном языке, принимает решение, какие инструменты вызвать, объединяет результаты и отвечает в разговорном тоне — при этом сохраняя историю диалога для каждого пользователя.

---

## 🏗️ Структура проекта

```
TourGuideAgent/
├── agent.py                # Настройка LangGraph-агента и конфигурация LLM
├── bot.py                  # Точка входа Telegram-бота (aiogram)
├── handlers.py             # Обработчики сообщений и команд Telegram
├── search_places.py        # Инструмент: поиск ближайших достопримечательностей (Overpass + Wikipedia GeoSearch)
├── get_place_info.py       # Инструмент: обратное геокодирование координат → адрес
├── geocode_place.py        # Инструмент: прямое геокодирование названия места → координаты
├── wikipedia_lookup.py     # Инструмент: получение текста статьи Wikipedia
├── route_link.py           # Инструмент: генерация ссылок маршрутов Яндекс.Карт
├── requirements.txt        # Зависимости Python
├── environment.yml         # Спецификация окружения Conda
├── pyproject.toml          # Конфигурация Pytest
├── .env.example            # Шаблон переменных окружения
├── run_bot.bat             # Скрипт автозапуска с восстановлением после сбоев (Windows)
├── tests/                  # Комплексный набор тестов pytest
│   ├── test_search_places.py
│   ├── test_search_places_cases.py
│   ├── test_get_place_info.py
│   ├── test_geocode_place.py
│   ├── test_route_link.py
│   ├── test_wikipedia_lookup.py
│   ├── test_geo_functions.py
│   ├── test_data_quality.py
│   ├── test_admin_ids.py
│   └── conftest.py
├── logs/                   # Ежедневные ротируемые файлы логов
└── .github/workflows/      # CI-пайплайн GitHub Actions
    └── tests.yml
```

---

## 🛠️ Технологический стек

| Уровень | Технология |
|---------|-----------|
| **Язык** | Python 3.13 |
| **Фреймворк бота** | [aiogram](https://docs.aiogram.dev) 3.x — полностью асинхронное Telegram Bot API |
| **ИИ-агент** | [LangChain](https://langchain.com) 1.3 + [LangGraph](https://langchain-ai.github.io/langgraph/) 1.2 |
| **LLM** | OpenAI-совместимая (локально через [Qwen](https://github.com/QwenLM/Qwen) / любое OpenAI API) |
| **Геокодирование** | [Nominatim](https://nominatim.org) (обратное и прямое геокодирование OpenStreetMap) |
| **База мест** | [Overpass API](https://overpass-api.de) (язык запросов OpenStreetMap) |
| **Обогащение данных** | [Wikipedia API](https://en.wikipedia.org/w/api.php) (MediaWiki) |
| **Карты** | Ссылки на маршруты Яндекс.Карт |
| **Разметка** | [telegramify-markdown](https://github.com/FeelNothing/telegramify-markdown) |
| **Память диалога** | SQLite через LangGraph Checkpoint |
| **Тестирование** | [pytest](https://docs.pytest.org) |
| **CI/CD** | GitHub Actions |
| **Конфигурация** | python-dotenv |

---

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.13+ (или Conda)
- Токен Telegram-бота (от [@BotFather](https://t.me/BotFather))
- LLM-эндпоинт (локальный или облачный) — OpenAI-совместимый API

### Установка

#### Вариант 1: pip

```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/TourGuideAgent.git
cd TourGuideAgent

# Создайте и активируйте виртуальное окружение
python -m venv venv
source venv/bin/activate   # Linux/Mac
# .\venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
```

#### Вариант 2: Conda

```bash
git clone https://github.com/yourusername/TourGuideAgent.git
cd TourGuideAgent
conda env create -f environment.yml
conda activate my_project
```

### Конфигурация

Скопируйте шаблон переменных окружения и заполните свои данные:

```bash
cp .env.example .env
```

```ini
# .env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321          # ID пользователей Telegram для административных команд
USER_AGENT=TourGuideAgent/1.0 (your_email@example.com)  # Обязательно для OSM/Wikipedia API
LLM_BASE_URL=http://localhost:5001/v1  # Ваш LLM-эндпоинт
LLM_API_KEY=123                        # API-ключ (если требуется)
LLM_MODEL=qwen                         # Название модели
```

> **Примечание:** Параметр `USER_AGENT` обязателен для API Nominatim и Overpass от OpenStreetMap. Запросы без корректного User-Agent могут быть ограничены или заблокированы.

### Запуск бота

```bash
python bot.py
```

Или на Windows с помощью скрипта автозапуска (перезапускает бота при сбое):

```bash
run_bot.bat
```

Бот начнёт опрос и будет отвечать на сообщения в Telegram. Отправьте `/start`, чтобы начать.

---

## 📱 Использование

### Отправка местоположения

Поделитесь своей геопозицией через меню вложений Telegram или введите координаты:

```
/start
55.772604, 37.682861
```

Агент определит район и предложит ближайшие достопримечательности.

### Вопросы

После того как вы отправили местоположение, можно задавать вопросы:

| Вопрос | Что произойдёт |
|--------|---------------|
| *«Что здесь интересного рядом?»* | Поиск достопримечательностей в радиусе ~1 км |
| *«Расскажи о Кремле»* | Получение статьи Wikipedia о Кремле |
| *«Как добраться отсюда до Красной площади?»* | Генерация ссылки на маршрут в Яндекс.Картах |
| *«В каком я районе?»* | Обратное геокодирование ваших координат |
| *«Где находится Эйфелева башня?»* | Прямое геокодирование названия в координаты |

### Административные команды

- `/restart` — Корректный перезапуск бота (только для администраторов)

---

## 🧪 Запуск тестов

Проект включает комплексный набор тестов, покрывающий все инструменты и граничные случаи:

```bash
# Запуск всех тестов
python -m pytest tests/ -v

# Запуск конкретного файла с тестами
python -m pytest tests/test_search_places.py -v

# Запуск с отчётом о покрытии (если установлен pytest-cov)
python -m pytest tests/ --cov=. --cov-report=term-missing
```

Тесты автоматически выполняются через **GitHub Actions** при каждом пуше и pull request.

---

## 🗺️ Справочник инструментов

### `search_places(lat, lon, radius, limit)`
Выполняет поиск достопримечательностей в OpenStreetMap (Overpass API) вокруг указанных координат, затем дополняет результаты данными Wikipedia GeoSearch. Фильтрует нетуристические объекты (могилы, улицы, события). Удаляет дубликаты и сортирует по значимости и расстоянию.

### `get_place_info(lat, lon)`
Выполняет обратное геокодирование координат через Nominatim. Возвращает город, район, область, страну и полный адрес.

### `geocode_place(query)`
Выполняет прямое геокодирование названия места или адреса в координаты через Nominatim. Возвращает `lat`, `lon`, отображаемое название и тип объекта.

### `wikipedia_lookup(query)`
Ищет статью в Wikipedia по названию места, получает полный текст (до 4000 символов) и возвращает читаемую сводку с URL источника. Использует MediaWiki поиск для нечёткого сопоставления.

### `get_route_link(from_lat, from_lon, to_lat, to_lon, transport)`
Генерирует ссылку на Яндекс.Карты с построенным маршрутом. Поддерживает пеший (`пешком`), автомобильный (`авто`) и общественный (`транспорт`) транспорт.

---


## 🤝 Вклад в проект

Ваш вклад приветствуется! Если у вас есть идеи новых инструментов, улучшенных промптов или дополнительных источников геоданных — смело создавайте issue или отправляйте pull request.

---

## 📄 Лицензия

MIT © 2026 — Создано с заботой о путешественниках и энтузиастах ИИ.

---

<p align="center">
  <sub>Сделано с ❤️ для портфолио по разработке ИИ-агентов</sub>
</p>
