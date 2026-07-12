import asyncio
from aiogram import Router
from aiogram.types import Message, MessageEntity
from aiogram.filters import CommandStart, Command
from telegramify_markdown import convert, split_entities
from aiogram.utils.chat_action import ChatActionSender
import os
import sys
from aiogram.types import ReplyKeyboardRemove

from agent import ask_agent
from dotenv import load_dotenv

load_dotenv()

router = Router()

MAX_MESSAGE_LENGTH = 4096

ADMIN_IDS = os.getenv("ADMIN_IDS")

@router.message(Command("restart"))
async def cmd_restart(message: Message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        # Не показываем обычным пользователям, что такая команда вообще есть
        return

    await message.answer("♻️ Перезапускаю бота...")

    # Даём aiogram время отправить сообщение перед завершением процесса
    await asyncio.sleep(1)

    # Полностью завершает процесс — bat-файл с циклом поднимет его заново
    raise SystemExit(1)

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Отправь мне геолокацию 📍 или координаты в формате:\n"
        "`55.772604, 37.682861`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )


def to_aiogram_entities(tg_entities) -> list[MessageEntity]:
    """
    Конвертирует MessageEntity из telegramify-markdown
    в MessageEntity из aiogram через промежуточный dict.
    """
    return [MessageEntity(**e.to_dict()) for e in tg_entities]


async def send_converted(message: Message, raw_text: str):
    text, entities = convert(raw_text)

    chunks = split_entities(text, entities, max_utf16_len=MAX_MESSAGE_LENGTH)

    for chunk_text, chunk_entities in chunks:
        await message.answer(
            chunk_text,
            entities=to_aiogram_entities(chunk_entities),
        )


# @router.message()
# async def handle_message(message: Message):
#     user_id = str(message.from_user.id)

#     if message.location:
#         lat = message.location.latitude
#         lon = message.location.longitude
#         user_text = f"Что интересного есть на координатах {lat}, {lon}?"
#     else:
#         user_text = message.text

#     await message.bot.send_chat_action(message.chat.id, "typing")

#     response = await asyncio.get_event_loop().run_in_executor(
#         None, ask_agent, user_text, user_id
#     )

#     await send_converted(message, response)



@router.message()
async def handle_message(message: Message):
    user_id = str(message.from_user.id)

    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        user_text = f"Что интересного есть на координатах {lat}, {lon}?"
    else:
        user_text = message.text

    async with ChatActionSender.typing(
        bot=message.bot,
        chat_id=message.chat.id,
    ):
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            ask_agent,
            user_text,
            user_id,
        )

    await send_converted(message, response)