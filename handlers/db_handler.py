import os
import logging
from config import bot
from bot.utils import is_admin
from pymongo import MongoClient
import re
from dotenv import load_dotenv
load_dotenv()

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>     DBASE HANDLER     >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

MONGO_URI = os.getenv("MONGO_URI")
DBASE = os.getenv('DBASE')

# Подключение к MongoDB
client = MongoClient(MONGO_URI)
db = client[DBASE]
collection = db['users_collection']
characters_collection = db['characters']

# Переменные для хранения промежуточных данных
user_data = {}

# Старт команды /newuser
@bot.message_handler(commands=['newuser'])
def new_user(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "Для выполнения этой команды нужны права администратора")
        return
    try:
        chat_id = message.chat.id
        bot.send_message(chat_id, "Пожалуйста, введите chat_id:")
        bot.register_next_step_handler(message, get_chat_id)
    except Exception as e:
        logging.error(f'Ошибка при обработке команды /newuser: {e}')
        bot.send_message(message.from_user.id, f'{e} 🫤 Процесс завершен.')
        return

# Получение chat_id и проверка на уникальность
def get_chat_id(message):
    chat_id = message.chat.id
    try:
        entered_chat_id = int(message.text)
        # Проверяем, есть ли уже такой chat_id в базе данных
        if collection.find_one({"chat_id": entered_chat_id}):
            bot.send_message(chat_id, "Такой chat_id уже существует. Процесс завершен.")
            return  # Прерываем выполнение, если chat_id не уникален
        user_data['chat_id'] = entered_chat_id

        # Получаем список доступных персонажей из коллекции characters
        characters = characters_collection.find({}, {"character": 1, "_id": 0})
        character_list = [char['character'] for char in characters]
        # Формируем строку с именами персонажей
        characters_str = ', '.join(character_list)
        # Отправляем пользователю список персонажей
        bot.send_message(chat_id, f"Выберите имя персонажа: {characters_str}")

        # bot.send_message(chat_id, "Теперь введите имя персонажа:")
        bot.register_next_step_handler(message, save_character)
    except ValueError:
        bot.send_message(chat_id, "chat_id должно быть целым числом. Попробуйте снова.")
        bot.register_next_step_handler(message, get_chat_id)  # Повторная попытка
    except Exception as e:
        logging.error(f'Ошибка при обработке команды /newuser: {e}')
        bot.send_message(message.chat.id, f"Процесс завершен. {e}")
        return

# Сохранение персонажа с проверкой
def save_character(message):
    chat_id = message.chat.id
    character_name = message.text
    # Проверяем, есть ли персонаж в коллекции characters
    if not characters_collection.find_one({"character": character_name}):
        bot.send_message(chat_id, f"Персонаж {character_name} не найден в базе. Попробуйте снова.")
        bot.register_next_step_handler(message, save_character) # Повторная попытка
        return  # Прерываем выполнение, если персонажа нет
    user_data['character'] = character_name
    bot.send_message(chat_id, "Введите имя пользователя (можно несколько через запятую):")
    bot.register_next_step_handler(message, get_user_name)

# Получение имен пользователей с проверкой длины строки и символов
def get_user_name(message):
    chat_id = message.chat.id
    users_name_string = message.text.strip()
    
    # Проверка общей длины строки (макс. 150 символов)
    if len(users_name_string) > 150:
        bot.send_message(chat_id, "Слишком длинный ввод. Общая длина всех имен не должна превышать 150 символов.")
        bot.register_next_step_handler(message, get_user_name)  # Повторная попытка
        return

    # Разбиваем строку на отдельные имена
    users_name = [name.strip() for name in users_name_string.split(',')]
    
    # Проверка каждого имени пользователя
    for name in users_name:
        # Ограничение длины имени (макс. 50 символов)
        if len(name) > 50:
            bot.send_message(chat_id, f"Имя '{name}' слишком длинное. Максимальная длина — 50 символов.")
            bot.register_next_step_handler(message, get_user_name)  # Повторная попытка
            return
        
        # Проверка на допустимые символы (буквы латиницы, кириллицы, цифры, пробелы, дефисы и апострофы)
        if not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9\s\-']+$", name):
            bot.send_message(chat_id, f"Имя '{name}' содержит недопустимые символы. Разрешены только буквы, цифры, пробелы, дефисы и апострофы.")
            bot.register_next_step_handler(message, get_user_name)  # Повторная попытка
            return
    
    # Если все имена прошли проверку, сохраняем их
    user_data['users_name'] = users_name
    bot.send_message(chat_id, "Теперь введите пол пользователя (male/female):")
    bot.register_next_step_handler(message, get_user_gender)

# Получение пола пользователя с валидацией и отправкой ObjectId
def get_user_gender(message):
    chat_id = message.chat.id
    user_gender = message.text.lower()  # Приводим к нижнему регистру для проверки
    
    # Проверяем, что введенный пол равен либо 'male', либо 'female'
    if user_gender not in ['male', 'female']:
        bot.send_message(chat_id, "Неверный ввод. Пожалуйста, введите 'male' или 'female'.")
        bot.register_next_step_handler(message, get_user_gender)  # Повторная попытка
        return
    
    # Если ввод корректный, сохраняем данные
    user_data['gender'] = user_gender
    bot.send_message(chat_id, "Теперь введите ваш часовой пояс (целое число от -12 до 14):")
    bot.register_next_step_handler(message, get_user_timezone)


# Получение часового пояса с проверкой
def get_user_timezone(message):
    chat_id = message.chat.id
    try:
        timezone = int(message.text)  # Пробуем преобразовать введенное значение в целое число
        
        # Проверяем, что значение находится в диапазоне от -12 до 14, включая 0
        if timezone < -12 or timezone > 14:
            raise ValueError  # Исключение, если значение вне диапазона

        user_data['timezone'] = timezone
        # Сохраняем все данные в MongoDB
        new_chat = {
            "chat_id": user_data['chat_id'],
            "character": user_data['character'],
            "users_name": user_data['users_name'],  # Массив имен
            "users_gender": user_data['gender'],
            "timezone": timezone  # Новое поле timezone
        }
        result = collection.insert_one(new_chat)  # Сохраняем документ
        inserted_id = result.inserted_id  # Получаем ObjectId нового документа

        logging.info(f'Новый документ сохранен в коллекции: {new_chat} с ObjectId: {inserted_id}') 
        bot.send_message(chat_id, f"""
        Данные для чата {user_data['chat_id']} сохранены! Вызов скрипта по ObjectId:
        
        python -m users_scripts.new_love "{inserted_id}"
        """)

        user_data.clear()  # Очистка данных после сохранения

    except ValueError:
        bot.send_message(chat_id, "Неверный ввод. Пожалуйста, введите целое число от -12 до 14.")
        bot.register_next_step_handler(message, get_user_timezone)  # Повторная попытка