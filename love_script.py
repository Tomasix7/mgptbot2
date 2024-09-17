import os
import telebot
from groq import Groq
from pymongo import MongoClient
import requests
import random
from datetime import datetime, timezone
import logging
from character import NANA

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API ключи и chat_id
chat_id = os.getenv("YOUR_CHAT_ID")  # Пересмотреть на рассылку по массиву chat ID
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client_groq = Groq(api_key=CLIENT_API_KEY)

# Подключение к MongoDB
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['dialogue_database']
collection = db['dialogs']

class DialogueStorage:
    def __init__(self, collection):
        self.collection = collection
        # Индекс для автоматической очистки данных старше 24 часов
        try:
            self.collection.create_index("timestamp", expireAfterSeconds=86400)
            logging.info('Индекс для timestamp успешно создан.')
        except Exception as e:
            logging.error(f'Ошибка создания индекса для timestamp: {e}')

    def add_message(self, chat_id, role, content):
        try:
            message = {
                'chat_id': chat_id,
                'role': role,
                'content': content,
                'timestamp': datetime.now(timezone.utc)
            }
            self.collection.insert_one(message)
            logging.info(f'Сообщение добавлено в базу данных для chat_id: {chat_id}')
        except Exception as e:
            logging.error(f'Ошибка добавления сообщения в базу данных: {e}')

    def get_messages(self, chat_id):
        try:
            messages = list(self.collection.find({'chat_id': chat_id}).sort('timestamp', 1))
            logging.info(f'Найдено {len(messages)} сообщений для chat_id: {chat_id}')
            return messages
        except Exception as e:
            logging.error(f'Ошибка получения сообщений из базы данных: {e}')
            return []

dialogue_storage = DialogueStorage(collection)

def get_random_image():
    try:
        url = "https://api.unsplash.com/photos/random"
        params = {
            "client_id": UNSPLASH_ACCESS_KEY,
            "orientation": "portrait",
            "query": "girl back, lingerie, female",
            "count": 1
        }
        response = requests.get(url, params=params)
        data = response.json()
        image_url = data[0]["urls"]["small"]
        logging.info(f'Получено случайное изображение: {image_url}')
        return image_url
    except Exception as e:
        logging.error(f'Ошибка при получении случайного изображения: {e}')
        return None

def get_random_elements(elements, n):
    return random.sample(elements, min(n, len(elements)))

def get_prompt_for_time():
    current_hour = datetime.now().hour
    # Путь к папке prompts
    prompts_dir = 'prompts/'

    if 0 <= current_hour < 3:
        prompt_file = os.path.join(prompts_dir,'goodnight_prompt.txt')
    elif 3 <= current_hour < 7:
        prompt_file = os.path.join(prompts_dir,'morning_prompt.txt')
    elif 7 <= current_hour < 9:
        prompt_file = os.path.join(prompts_dir,'good_prompt.txt')
    elif 9 <= current_hour < 12:
        prompt_file = os.path.join(prompts_dir,'how_prompt.txt')
    elif 12 <= current_hour < 15:
        prompt_file = os.path.join(prompts_dir,'story_prompt.txt')
    elif 15 <= current_hour < 18:
        prompt_file = os.path.join(prompts_dir,'yoday_prompt.txt')
    elif 18 <= current_hour < 20:
        prompt_file = os.path.join(prompts_dir,'date_prompt.txt')
    else:
        prompt_file = os.path.join(prompts_dir,'prompt.txt')
    
    return prompt_file

# Отправка сообщения
def send_morning_message():
    try:
        # Чтение базового промпта из файла
        base_prompt_file = get_prompt_for_time()
        with open(base_prompt_file, 'r', encoding='utf-8') as file:
            base_prompt = file.read()
        logging.info(f'Базовый промпт прочитан из файла: {base_prompt_file}')

        # Список дополнительных элементов
        additional_elements = [
            "погода", "прекрасный мир", "цветы", "космос",
            "австралийское животное", "спорт", "водные процедуры",
            "вдохновение", "пот", "музыка", "медитация", "попа", "пушок на ягодицах",
            "транс", "пауэрлифтинг"
        ]

        # Выбор случайных элементов
        today_elements = get_random_elements(additional_elements, 2)
        today = datetime.now().strftime("%d.%m.%Y")
        final_prompt = f"{base_prompt}\nСегодня {today}. Пожалуйста, включи в пожелание темы: {', '.join(today_elements)}."

        # Получаем историю диалога (например, последние 5 сообщений)
        dialogue_history = dialogue_storage.get_messages(chat_id)[-2:]
        logging.info(f'История диалога для chat_id {chat_id}: {dialogue_history}')

        if len(dialogue_history) == 0:
            bot.send_message(chat_id, "🥰")

        # Подготовка данных для API
        messages_for_groq = [
            {"role": msg["role"], "content": msg["content"]} for msg in dialogue_history
        ]

        system_message = {
            "role": "system", 
            "content": NANA
        }

        # Собираем сообщения для запроса
        messages = [system_message] + messages_for_groq
        messages.append({"role": 'user', "content": final_prompt})

        logging.info(f'Сформированные сообщения для отправки: {messages}')

        # Логируем данные для отправки в Groq
        logging.info(f'Запрос для Groq: {messages}')

        # Запрос к Groq
        response = client_groq.chat.completions.create(
            model='llama3-70b-8192',
            messages=messages,
            temperature=0.7
        )

        logging.info(f"Полный ответ от Groq: {response}")

        # Убедимся, что ответ полностью получен
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            response_content = response.choices[0].message.content
            
            # Отправляем изображение в Telegram
            image_url = get_random_image()
            if image_url:
                bot.send_photo(chat_id, image_url)

            # Отправляем сгенерированное сообщение в Telegram
            bot.send_message(chat_id, response_content)

            # Сохраняем ответ в истории диалога
            dialogue_storage.add_message(chat_id, 'assistant', response_content)
        else:
            logging.error("Ответ от Groq пустой или не полностью получен, сообщение не отправлено.")
            bot.send_message(chat_id, "Опять я это самое... ну ты понял 🤪")
    except Exception as e:
        logging.error(f'Ошибка в функции send_morning_message: {e}')
        bot.send_message(chat_id, "Ну хорошо... 😊")

# Выполнение скрипта
if __name__ == '__main__':
    send_morning_message()
