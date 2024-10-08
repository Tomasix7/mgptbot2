import os
import logging
from config import bot
from bot.utils import is_admin
from pymongo import MongoClient
from bson import ObjectId
import re
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MONGO_URI = os.getenv("MONGO_URI")
DBASE = os.getenv('DBASE')

# Подключение к MongoDB
client = MongoClient(MONGO_URI)
db = client[DBASE]
collection = db['users_collection']
characters_collection = db['characters']

# Словарь для хранения состояния редактирования для каждого пользователя
edit_states = {}

@bot.message_handler(commands=['edituser'])
def start_edit_user(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "Для выполнения этой команды нужны права администратора")
        return
    
    chat_id = message.chat.id
    bot.send_message(chat_id, "Пожалуйста, введите ObjectId документа для редактирования:")
    bot.register_next_step_handler(message, get_object_id)

def get_object_id(message):
    chat_id = message.chat.id
    object_id = message.text.strip()
    
    try:
        document = collection.find_one({"_id": ObjectId(object_id)})
        if not document:
            bot.send_message(chat_id, "Документ не найден.")
            return
        
        edit_states[chat_id] = {"document": document, "current_field": "chat_id"}
        bot.send_message(chat_id, f"Текущий chat_id: {document['chat_id']}\nВведите новый chat_id или отправьте '-' чтобы оставить текущее значение:")
        bot.register_next_step_handler(message, process_edit)
    except:
        bot.send_message(chat_id, "Неверный формат ObjectId.")

def process_edit(message):
    chat_id = message.chat.id
    new_value = message.text.strip()
    
    if new_value == '-':
        move_to_next_field(chat_id)
        return
    
    current_field = edit_states[chat_id]["current_field"]
    document = edit_states[chat_id]["document"]
    
    if current_field == "chat_id":
        if not new_value.isdigit():
            bot.send_message(chat_id, "chat_id должен быть целым числом. Попробуйте снова.")
            bot.register_next_step_handler(message, process_edit)
            return
        document['chat_id'] = int(new_value)
    elif current_field == "character":
        if not characters_collection.find_one({"character": new_value}):
            bot.send_message(chat_id, f"Персонаж {new_value} не найден в базе. Попробуйте снова.")
            bot.register_next_step_handler(message, process_edit)
            return
        document['character'] = new_value
    elif current_field == "users_name":
        names = [name.strip() for name in new_value.split(',')]
        if len(new_value) > 150 or any(len(name) > 50 or not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9\s\-']+$", name) for name in names):
            bot.send_message(chat_id, "Неверный формат имен пользователей. Попробуйте снова.")
            bot.register_next_step_handler(message, process_edit)
            return
        document['users_name'] = names
    elif current_field == "gender":
        if new_value.lower() not in ['male', 'female']:
            bot.send_message(chat_id, "Пол должен быть 'male' или 'female'. Попробуйте снова.")
            bot.register_next_step_handler(message, process_edit)
            return
        document['users_gender'] = new_value.lower()
    elif current_field == "timezone":
        try:
            tz = int(new_value)
            if tz < -12 or tz > 14:
                raise ValueError
            document['timezone'] = tz
        except ValueError:
            bot.send_message(chat_id, "Часовой пояс должен быть целым числом от -12 до 14. Попробуйте снова.")
            bot.register_next_step_handler(message, process_edit)
            return
    
    move_to_next_field(chat_id)

def move_to_next_field(chat_id):
    fields = ["chat_id", "character", "users_name", "gender", "timezone"]
    current_field = edit_states[chat_id]["current_field"]
    current_index = fields.index(current_field)
    
    if current_index + 1 < len(fields):
        next_field = fields[current_index + 1]
        edit_states[chat_id]["current_field"] = next_field
        document = edit_states[chat_id]["document"]
        bot.send_message(chat_id, f"Текущее значение {next_field}: {document.get(next_field, 'Не задано')}\nВведите новое значение или отправьте '-' чтобы оставить текущее:")
        bot.register_next_step_handler_by_chat_id(chat_id, process_edit)
    else:
        save_changes(chat_id)

def save_changes(chat_id):
    document = edit_states[chat_id]["document"]
    result = collection.replace_one({"_id": document["_id"]}, document)
    
    if result.modified_count > 0:
        logging.info(f'Документ успешно обновлен: {document}')
        bot.send_message(chat_id, "Документ успешно обновлен.")
    else:
        logging.warning(f'Документ не был изменен: {document}')
        bot.send_message(chat_id, "Документ не был изменен.")
    
    del edit_states[chat_id]

# Остальной код бота...