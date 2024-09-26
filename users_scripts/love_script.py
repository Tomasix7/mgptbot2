import os
import telebot
from groq import Groq
import logging
from time_zone_manager import TimeZoneManager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения (только для локального запуска)
from dotenv import load_dotenv
load_dotenv()

# API ключи и chat_id. !!!!!!!!!!!!!!!!!!! Меняем chat_id на номер нового пользователя !!!!!!!!!!!!!!!!!!
chat_id = str(os.getenv("CHATID")) # NANA to me
CLIENT_API_KEY = os.getenv("CLIKEY")
TELEGRAM_TOKEN = os.getenv("TELKEY")

# Вызываем функцию для оправки сообщений send_scheduled_message после определения констант
from scheduled_message import send_scheduled_message

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client_groq = Groq(api_key=CLIENT_API_KEY)

# !!!!!!!!!!!!!!!!!!!Создаем (выбираем) экземпляр TimeZoneManager для часового пояса !!!!!!!!!!!!!!!!!!!!
# tz_manager = TimeZoneManager('Asia/Yekaterinburg') # Замените на нужную временную зону
tz_manager = TimeZoneManager('Europe/Moscow')  # Замените на нужную временную зону

if __name__ == '__main__':
    send_scheduled_message(chat_id, bot, client_groq, tz_manager)