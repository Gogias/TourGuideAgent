import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

# Тулзы
from search_places import search_places
from get_place_info import get_place_info
from geocode_place import geocode_place
from route_link import get_route_link
from wikipedia_lookup import wikipedia_lookup

llm = ChatOpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:5001/v1"),
    api_key=os.getenv("LLM_API_KEY", "123"),
    model=os.getenv("LLM_MODEL", "qwen"),
    temperature=0,
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
)

tools = [search_places, get_place_info, geocode_place, get_route_link, wikipedia_lookup]

SYSTEM_PROMPT = """
Ты — русскоязычный ассистент - туристический гид, должен помогать ориентироваться
в месте и рассказать про него интересную информацию. Ты должен точно следовать инструкциям, не придумывать места и факты, а только следовать полученной информации.
## Capabilities
- `get_place_info`: Определяет город и район по координатам.
- `search_places`: Ищет достопримечательности в радиусе от координат.
- `geocode_place`: Находит географические координаты по названию места, адресу или достопримечательности.
- `get_route_link`: Строит ссылку на маршрут между двумя точками в Яндекс.Картах.
- `wikipedia_lookup`: Получает текст статьи Wikipedia про конкретное место,
  чтобы подробно ответить на вопрос пользователя об истории или фактах.
  Используй когда пользователь спрашивает "расскажи про X" или "что за место X",
  а не просто хочет список ближайших достопримечательностей.
Отвечай на основе полученного текста статьи своими словами,
не копируй текст дословно.
Опирайся ТОЛЬКО на полученные данные, ничего не выдумывай.
Отвечай ТОЛЬКО на русском языке.
"""

checkpointer = InMemorySaver()

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

def ask_agent(text: str, thread_id: str) -> str:
    """
    Вызывает агента. thread_id = str(user_id) — даёт каждому
    пользователю свою историю диалога.
    """
    result = agent.invoke(
        {"messages": [{"role": "user", "content": text}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    # Извлекаем текст из content_blocks (как в вашем рабочем коде)
    last = result["messages"][-1]
    try:
        return last.content_blocks[0]["text"]
    except (AttributeError, IndexError, KeyError):
        # fallback если структура ответа другая
        return str(last.content)