from bot.request_queue import request_queue
from bot.truncation_utils import truncate_message, truncate_messages
import os
import ast
import logging
from telebot import TeleBot
from groq import Groq
# Загрузка переменных окружения (только для локального запуска)
from dotenv import load_dotenv
load_dotenv()

def setup_logging():
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(level=getattr(logging, LOG_LEVEL))

def init_bot_and_groq():
    CLIENT_API_KEY = os.getenv("CLIKEY")
    TELEGRAM_TOKEN = os.getenv("TELKEY")
    
    global client_groq, bot, request_queue
    client_groq = Groq(api_key=CLIENT_API_KEY)
    bot = TeleBot(TELEGRAM_TOKEN)

# Эти переменные пока остаются в congig vars на сервере, но будут использоваться значения из БД
# List of authorized chat IDs
# AUTHORIZED_CHAT_IDS = os.getenv('AUTHORIZED_CHAT_IDS')

# admin IDs 
# Извлекаем и преобразуем строковый список в список чисел
ADMIN_CHAT_IDS = ast.literal_eval(os.getenv('ADMIN_CHAT_IDS', '[]'))

setup_logging()  # Настройка логирования
init_bot_and_groq()  # Инициализация бота и Groq