"""Main Telegram bot application with async support."""

import os
import logging
import asyncio
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import re

from .todoist_client import TodoistClient
from .models import TodoistTask, BotResponse
from .database import user_storage

# Load environment variables
load_dotenv()

token_regex = re.compile('^[a-z\\d]{40}$')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=['start'])
async def start_command(message):
    """Handle /start command."""
    welcome_text = """
🤖 Добро пожаловать в Todoist Бот!

Я помогу вам создавать задачи в Todoist прямо из Telegram.

<b>Быстрый старт</b>:
1. Получите ваш API токен Todoist здесь: https://todoist.com/prefs/integrations
2. Отправьте `ВАШ_ТОКЕН_ЗДЕСЬ`
3. Отправьте любое сообщение, чтобы создать задачу!

<b>Команды</b>:
• /start - Показать инструкцию
• /help - Получить помощь

Пример: "Купить молоко" → Создаст задачу "Купить молоко" в ваших Входящих
    """
    await bot.reply_to(message, welcome_text, parse_mode='HTML')


@bot.message_handler(commands=['help'])
async def help_command(message):
    """Handle /help command."""
    help_text = """
🤖 <b>Справка по Todoist Боту</b>

<b>Настройка</b>:
1. Получите ваш API токен Todoist здесь: https://todoist.com/prefs/integrations
2. Отправьте: `ВАШ_ТОКЕН_ЗДЕСЬ`

<b>Использование</b>:
• Отправьте любое текстовое сообщение чтобы создать задачу
• Задачи создаются в ваших Входящих с приоритетом 3
• Каждое сообщение становится одной задачей

<b>Примеры</b>:
• "Купить продукты" → Задача: "Купить продукты"
• "Позвонить стоматологу завтра" → Задача: "Позвонить стоматологу завтра"
• "Просмотреть презентацию" → Задача: "Просмотреть презентацию"

<b>Команды</b>:
• /start - Показать инструкцию
• /help - Это справочное сообщение

<b>Возможности</b>:
• ✅ Защита от дублирования
• ✅ Поддержка нескольких пользователей
• ✅ Обработка ошибок
• ✅ Асинхронная обработка
    """
    await bot.reply_to(message, help_text, parse_mode='HTML')


@bot.message_handler(func=lambda message: True)
async def handle_message(message):
    """Handle all text messages and create Todoist tasks."""
    user_id = message.from_user.id
    message_text = message.text

    if token_regex.search(message_text):
        # Validate token by testing API connection
        try:
            todoist_client = TodoistClient(message_text)
            await todoist_client.get_projects()  # Test API connection

            # Store token
            await user_storage.store_token(user_id, message_text)
            await bot.reply_to(
                message, "✅ Токен успешно сохранен!\n\n"
                "Теперь вы можете отправлять мне сообщения для создания задач в Todoist."
            )
            return

        except Exception as e:
            await bot.reply_to(
                message, f"❌ Неверный токен или ошибка API: {str(e)}\n\n"
                "Пожалуйста, проверьте ваш токен и попробуйте снова.")
            return

    # Check if user has token
    if not await user_storage.has_token(user_id):
        await bot.reply_to(
            message, "❌ Сначала установите ваш токен Todoist!\n\n"
            "Отправьте: `ВАШ_ТОКЕН_ЗДЕСЬ`\n\n"
            "Получите токен здесь: https://todoist.com/prefs/integrations",
            parse_mode='Markdown')
        return

    # Get user's token
    todoist_token = await user_storage.get_token(user_id)
    if not todoist_token:
        await bot.reply_to(
            message,
            "❌ Ошибка получения вашего токена. Пожалуйста, установите его заново"
        )
        return

    # Send "creating task" notification
    creating_msg = await bot.reply_to(message, "⏳ Создаю задачу...")

    try:
        # Create Todoist client
        todoist_client = TodoistClient(todoist_token)

        # Create task with idempotency using Telegram message_id
        task = TodoistTask(content=message_text,
                           priority=3,
                           request_id=f"tg_{user_id}_{message.message_id}")

        # Create task in Todoist
        task_response = await todoist_client.create_task(task)

        # Send success confirmation
        success_text = (
            f"✅ **Задача успешно создана!**\n\n"
            f"📝 **Задача:** {task_response.content}\n"
            f"📁 **Место:** Входящие\n"
            f"⭐ **Приоритет:** P{task_response.priority}\n"
            f"🔗 **Ссылка:** [Посмотреть в Todoist]({task_response.url})")

        await bot.edit_message_text(success_text,
                                    creating_msg.chat.id,
                                    creating_msg.message_id,
                                    parse_mode='Markdown')

        logger.info(f"Task created for user {user_id}: {message_text}")

    except ValueError as e:
        # Handle known API errors
        await bot.edit_message_text(f"❌ **Ошибка создания задачи:**\n{str(e)}",
                                    creating_msg.chat.id,
                                    creating_msg.message_id,
                                    parse_mode='Markdown')
        logger.error(f"Error creating task for user {user_id}: {e}")

    except Exception as e:
        # Handle unexpected errors
        await bot.edit_message_text(
            "❌ **Произошла неожиданная ошибка.**\nПожалуйста, попробуйте позже.",
            creating_msg.chat.id,
            creating_msg.message_id,
            parse_mode='Markdown')
        logger.error(f"Unexpected error for user {user_id}: {e}")


async def main():
    """Main async function to run the bot."""
    logger.info("Starting Todoist Telegram Bot...")

    try:
        await bot.polling(non_stop=True)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
