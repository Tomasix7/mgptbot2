import os
import logging
from config import bot
from bot.utils import is_admin
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MONGO_URI = os.getenv("MONGO_URI")

# Подключение к MongoDB
client = MongoClient(MONGO_URI)
DBASE = os.getenv('DBASE')

db = client[DBASE]
collection = db['users_collection']
characters_collection = db['characters']

@bot.message_handler(commands=['editchar'])
def edit_character(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "Для выполнения этой команды нужны права администратора")
        return
    
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите имя персонажа, которого вы хотите отредактировать:")
    bot.register_next_step_handler(message, find_character)

def find_character(message):
    chat_id = message.chat.id
    character_name = message.text.strip().upper()

    # Ищем персонажа по имени
    character = characters_collection.find_one({"character": character_name})

    if not character:
        bot.send_message(chat_id, f"Персонаж с именем {character_name} не найден.")
        return

    # Отправляем текущее описание персонажа
    current_description = character.get("description", "Описание отсутствует")
    bot.send_message(chat_id, f"Текущее описание персонажа {character_name}:\n\n{current_description}")
    
    bot.send_message(chat_id, f"Введите новое описание персонажа (или измените текущее):")
    bot.register_next_step_handler(message, update_character_description, character_name, current_description)

def update_character_description(message, character_name, current_description):
    chat_id = message.chat.id
    new_description = message.text.strip()

    # Если пользователь не ввел новое описание, оставить старое
    if not new_description:
        new_description = current_description

    if len(new_description) > 2700:
        bot.send_message(chat_id, "Описание слишком длинное. Попробуйте еще раз:")
        bot.register_next_step_handler(message, update_character_description, character_name, current_description)
        return

    # Обновляем описание персонажа
    result = characters_collection.update_one(
        {"character": character_name},
        {"$set": {"description": new_description}}
    )

    if result.modified_count > 0:
        bot.send_message(chat_id, f"Описание персонажа {character_name} успешно обновлено.")
    else:
        bot.send_message(chat_id, "Не удалось обновить описание персонажа.")
