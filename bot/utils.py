import os
import logging
from config import ADMIN_CHAT_IDS
from pymongo import MongoClient
import hashlib
# Загрузка переменных окружения (только для локального запуска)
from dotenv import load_dotenv
load_dotenv()

# Подключение к MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
DBASE = os.getenv('DBASE')

db = client[DBASE]  # Название базы данных
collection = db['users_collection']  # Название коллекции

## Новая версия is_authorized проверяет наличие chat_id в коллекции users_collection
def is_authorized(chat_id):
    # Поиск документа с данным chat_id
    result = collection.find_one({"chat_id": chat_id})
    
    # Если результат найден, возвращаем True, иначе False
    return result is not None

def is_admin(chat_id):
    return chat_id in ADMIN_CHAT_IDS

# Функция для уведомления администратора о новом пользователе
def notify_admin(bot, message, admin_chat_id):
    user = message.from_user
    logging.info(f'Обращение от пользователя {user.id} {user.first_name} {user.last_name or "(фамилия не указана)"}')
    if not collection.find_one({"chat_id": user.id}):
        # Собираем информацию о пользователе
        user_info = f"""
        Новый пользователь:
        - ID: {user.id}
        - Имя: {user.first_name}
        - Фамилия: {user.last_name or 'Не указана'}
        - Username: @{user.username or 'Не установлен'}
        """

        # Отправляем сообщение админу
        bot.send_message(admin_chat_id, user_info)


# Класс фильтра дублирующих сообшений. Используется в обработчиках в handlers.py
class DuplicateMessageFilter:
    def __init__(self):
        self.last_hash = None  # Локальная переменная для хранения хеша последнего сообщения

    def is_duplicate(self, message_text):
        # Генерация хеша входящего сообщения
        current_hash = hashlib.md5(message_text.encode()).hexdigest()
        
        # Проверка, дубликат ли это сообщение
        if current_hash == self.last_hash:
            return True
        
        # Обновляем хеш последнего сообщения
        self.last_hash = current_hash
        return False


## Эта версия is_authorized работала со списком из переменных окружения
# def is_authorized(chat_id):
#     return str(chat_id) in AUTHORIZED_CHAT_IDS