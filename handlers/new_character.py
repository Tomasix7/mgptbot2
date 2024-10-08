import os
import logging
from config import bot
from bot.utils import is_admin
from pymongo import MongoClient
import re
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DBASE = os.getenv('DBASE')

# Подключение к MongoDB
client = MongoClient(MONGO_URI)
db = client[DBASE]
characters_collection = db['characters']

# Переменные для хранения промежуточных данных
character_data = {}

@bot.message_handler(commands=['newchar'])
def new_character(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "Для выполнения этой команды нужны права администратора")
        return
    try:
        chat_id = message.chat.id
        bot.send_message(chat_id, "Пожалуйста, введите имя персонажа (до 12 символов, включая цифры, нижние подчеркивания и дефис):")
        bot.register_next_step_handler(message, get_character_name)
    except Exception as e:
        logging.error(f'Ошибка при обработке команды /new_character: {e}')
        bot.send_message(message.from_user.id, f'{e} 🫤 Процесс завершен.')
        return

def get_character_name(message):
    chat_id = message.chat.id
    character_name = message.text.strip()

    if len(character_name) > 12 or not re.match(r'^[a-zA-Z0-9_-]+$', character_name):
        bot.send_message(chat_id, "Неверный формат имени. Попробуйте еще раз:")
        bot.register_next_step_handler(message, get_character_name)
        return

    character_name = character_name.upper()
    
    # Проверяем, есть ли уже такой персонаж в базе данных
    if characters_collection.find_one({"character": character_name}):
        bot.send_message(chat_id, "Такой персонаж уже существует. Процесс завершен.")
        return

    character_data['character'] = character_name
    bot.send_message(chat_id, "Теперь введите описание персонажа (до 2700 символов):")
    bot.register_next_step_handler(message, get_character_description)

def get_character_description(message):
    chat_id = message.chat.id
    description = message.text.strip()

    if len(description) > 2700:
        bot.send_message(chat_id, "Описание слишком длинное. Попробуйте еще раз:")
        bot.register_next_step_handler(message, get_character_description)
        return

    character_data['description'] = description

    # Сохраняем данные в MongoDB
    result = characters_collection.insert_one(character_data)
    inserted_id = result.inserted_id

    logging.info(f'Новый персонаж сохранен в коллекции: {character_data} с ObjectId: {inserted_id}')
    bot.send_message(chat_id, f"""
    Данные для персонажа {character_data['character']} сохранены! ObjectId нового документа:
    
    {inserted_id}
    """)

    character_data.clear()  # Очистка данных после сохранения