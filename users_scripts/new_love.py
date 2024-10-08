import os
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import random
import pytz
from pytz import all_timezones_set
import re
from time_zone_manager import TimeZoneManager  # Импортируй свой модуль для управления часовыми поясами
from config import client_groq, bot  # Импортируй клиента и бота из твоего файла конфигурации
from dialogue_storage import dialogue_storage  # Импортируй класс хранения диалогов
from unsplash_functions import get_random_image

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Подключение к MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
DBASE = os.getenv('DBASE')

db = client[DBASE]  # Для каждого бота и сервера своя база данных
users_collection = db["users_collection"]
characters_collection = db["characters"]  # Коллекция персонажей

def convert_numeric_timezone(numeric_timezone):
    """Конвертирует числовой часовой пояс в pytz timezone."""
    try:
        offset_hours = int(numeric_timezone)

        # Поиск временной зоны на основе смещения
        matching_timezones = [tz for tz in all_timezones_set if 'GMT' not in tz and offset_hours == datetime.now(pytz.timezone(tz)).utcoffset().total_seconds() // 3600]
        
        if matching_timezones:
            return pytz.timezone(matching_timezones[0])  # Возвращаем первую найденную временную зону
        else:
            return pytz.UTC  # Если не найдено — по умолчанию UTC

    except ValueError:
        logging.error(f"Неверное значение часового пояса: {numeric_timezone}")
        return pytz.UTC

def get_user_and_character_data(object_id):
    """Получаем данные пользователя и персонажа по ObjectID."""
    try:
        # Поиск данных пользователя по ObjectID
        user_data = users_collection.find_one({"_id": ObjectId(object_id)})
        if not user_data:
            raise ValueError(f"Пользователь с ObjectID {object_id} не найден.")

        # Получаем данные о персонаже из коллекции characters
        character_name = user_data.get("character", "Default Character")
        character_data = characters_collection.find_one({"character": character_name})
        if not character_data:
            raise ValueError(f"Персонаж с именем {character_name} не найден в коллекции characters.")

        character_description = character_data.get("description", "Описание не найдено.")
        users_gender = user_data.get("users_gender", "unknown")
        timezone_offset = user_data.get("timezone", 0)

        return character_description, users_gender, timezone_offset, user_data.get("chat_id")
    except Exception as e:
        logging.error(f"Ошибка при получении данных пользователя или персонажа: {e}")
        return None, None, None, None
    

def get_random_elements(elements, n):
    return random.sample(elements, min(n, len(elements)))

def split_message(message, max_length):
    """Разбивает длинное сообщение на части, не превышающие max_length."""
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

def truncate_repeating_text(text, max_repeats=3):
    """Обрезает повторяющиеся слова и символы."""
    
    # Убираем слишком длинные повторы символов (например, 'срсрсрсрс...')
    def limit_repeated_chars(match):
        char_sequence = match.group(0)
        return char_sequence[:max_repeats]
    
    # Шаблон для поиска повторяющихся символов
    text = re.sub(r'(.)\1{3,}', limit_repeated_chars, text)

    words = text.split()
    result = []
    prev_word = None
    repeat_count = 0
    
    # Обработка повторяющихся слов
    for word in words:
        if word == prev_word:
            repeat_count += 1
        else:
            repeat_count = 0
        
        if repeat_count < max_repeats:
            result.append(word)
        
        prev_word = word
    
    return ' '.join(result)

def process_response(response, chat_id, bot, users_gender):
    """Обрабатывает ответ от Groq, обрезая повторяющиеся символы."""
    if response.choices and response.choices[0].message and response.choices[0].message.content:
        response_content = response.choices[0].message.content
        logging.info(f'Получен ответ: {response_content}')
        logging.info(f'Длина ответа от Groq: {len(response_content)}')

        # Убираем повторяющиеся символы или слова
        cleaned_response = truncate_repeating_text(response_content)
        logging.info(f'Очищенный ответ: {cleaned_response}')

        image_url = get_random_image(users_gender)
        if image_url:
            bot.send_photo(chat_id, image_url)
        else:
            logging.error("url изображения так не получается...")

        send_long_message(chat_id, bot, cleaned_response)
        dialogue_storage.add_message(chat_id, 'assistant', cleaned_response)
    else:
        logging.error("Ответ от Groq пустой или не полностью получен, сообщение не отправлено.")
        bot.send_message(chat_id, "Опять я это самое... 🤪")

def send_long_message(chat_id, bot, message):
    max_message_length = 4096
    # Разбиваем длинное сообщение на части, если оно превышает лимит
    for i in range(0, len(message), max_message_length):
        bot.send_message(chat_id, message[i:i+max_message_length])


def send_scheduled_message(object_id):
    try:
        # Получаем данные пользователя и персонажа из базы по ObjectID
        character_info, users_gender, timezone_offset, chat_id = get_user_and_character_data(object_id)

        if character_info is None:
            logging.error("Не удалось получить данные пользователя или персонажа.")
            return

        # Преобразуем числовой часовой пояс в pytz и передаем строку (через .zone)
        user_timezone = convert_numeric_timezone(timezone_offset).zone
        logging.info(f'Часовой пояс пользователя: {user_timezone}')

        # Передаем строку в TimeZoneManager
        tz_manager = TimeZoneManager(user_timezone)

        # Получаем текущий час
        current_hour = tz_manager.get_current_hour()
        logging.info(f'Текущий час: {current_hour}')

        base_prompt_file = tz_manager.get_prompt_for_time(current_hour)
        logging.info(f'Промпт из файла: {base_prompt_file}')

        time_based_elements = tz_manager.get_elements_for_time(current_hour)
        logging.info(f'Элементы по времени: {time_based_elements}')

        # Добавляем случайные элементы в сообщение
        today_elements = random.sample(time_based_elements, 2)
        today = datetime.now(tz_manager.default_timezone).strftime("%d.%m.%Y")
        final_prompt = f"{base_prompt_file}\nСегодня {today}. Пожалуйста, включи в пожелание темы: {', '.join(today_elements)}."

        logging.info(f'Длина финального промпта: {len(final_prompt)}')

        # Получаем историю диалога из хранения
        dialogue_history = dialogue_storage.get_messages(chat_id)[0:0]
        logging.info(f'История диалога для chat_id {chat_id}: {dialogue_history}')

        if len(dialogue_history) == 0:
            bot.send_message(chat_id, "🎉🥰")

        messages_for_groq = [
            {"role": msg["role"], "content": msg["content"]} for msg in dialogue_history
        ]

        system_message = {
            "role": "system",
            "content": character_info
        }

        messages = [system_message] + messages_for_groq
        messages.append({"role": 'user', "content": final_prompt})

        combined_messages = [msg["content"] for msg in messages]
        full_message = "\n".join(combined_messages)

        logging.info(f'Окончательная длина запроса к Groq: {len(full_message)}')

        # Отправляем сообщение в Groq
        response = client_groq.chat.completions.create(
            model='llama3-70b-8192',
            messages=[{"role": 'user', "content": full_message}],
            temperature=0
        )

        # Обрабатываем ответ и отправляем сообщение пользователю
        process_response(response, chat_id, bot, users_gender)
    except AttributeError as e:
        logging.error(f'Ошибка в функции send_scheduled_message: {e}')
        bot.send_message(chat_id, "Что-то пошло не так с часовым поясом... 😊")
    except Exception as e:
        logging.error(f'Ошибка в функции send_scheduled_message: {e}')
        bot.send_message(chat_id, "Что-то пошло не так... 😊")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        logging.error("Неверное количество аргументов. Ожидался один аргумент - ObjectID.")
    else:
        object_id = sys.argv[1]
        send_scheduled_message(object_id)
