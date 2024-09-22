import os
import telebot
from groq import Groq
from pymongo import MongoClient
import requests
import random
from datetime import datetime, timezone
import logging
import pytz
from character import NANA
from dictionary import NIGHT_ELEMENTS, DAY_ELEMENTS, EVENING_ELEMENTS
# from dotenv import load_dotenv # только для локального запуска
# load_dotenv()

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

# Функция получения случайного изображения из UNSPLASH
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

# Функция выбора количества дополнительных элементов для промпта
def get_random_elements(elements, n):
    return random.sample(elements, min(n, len(elements)))

# Получаем часовой пояс, но в Монго почему то всё равно UTC+0
def get_current_hour_utc3(): 
    tz = pytz.timezone('Europe/Moscow')  # Замените на нужную временную зону
    return datetime.now(tz).hour

# Функция выбора промпта в зависимости от времени суток
def get_prompt_for_time():
    current_hour = get_current_hour_utc3()
    # current_hour = datetime.now().hour
    # Путь к папке prompts
    prompts_dir = 'prompts/'

    if 0 <= current_hour < 2:
        prompt_file = os.path.join(prompts_dir,'goodnight_prompt.txt')
    elif 2 <= current_hour < 4:
        prompt_file = os.path.join(prompts_dir,'sleepwell_prompt.txt')
    elif 4 <= current_hour < 6:
        prompt_file = os.path.join(prompts_dir,'sleepwell_prompt.txt')
    elif 6 <= current_hour < 8:
        prompt_file = os.path.join(prompts_dir,'morning_prompt.txt')
    elif 8 <= current_hour < 10:
        prompt_file = os.path.join(prompts_dir,'good_prompt.txt')
    elif 10 <= current_hour < 12:
        prompt_file = os.path.join(prompts_dir,'how_prompt.txt')
    elif 12 <= current_hour < 14:
        prompt_file = os.path.join(prompts_dir,'lunch_prompt.txt')
    elif 14 <= current_hour < 16:
        prompt_file = os.path.join(prompts_dir,'story_prompt.txt')
    elif 16 <= current_hour < 18:
        prompt_file = os.path.join(prompts_dir,'yoday_prompt.txt')
    elif 18 <= current_hour < 20:
        prompt_file = os.path.join(prompts_dir,'prompt.txt')
    elif 20 <= current_hour < 22:
        prompt_file = os.path.join(prompts_dir,'date_prompt.txt')
    elif 22 <= current_hour < 23:
        prompt_file = os.path.join(prompts_dir,'goodnight_prompt.txt')
    else:
        prompt_file = os.path.join(prompts_dir,'goodnight_prompt.txt')
    
    return prompt_file

# Функция выбора массива дополнительных тем в зависимости от времени суток
def get_elements_for_time():
    current_hour = datetime.now().hour
    if 0 <= current_hour < 6:
        return NIGHT_ELEMENTS
    elif 6 <= current_hour < 18:
        return DAY_ELEMENTS
    else:
        return EVENING_ELEMENTS

# Отправка сообщения
def send_morning_message():
    try:
        # Чтение базового промпта из файла
        base_prompt_file = get_prompt_for_time()
        with open(base_prompt_file, 'r', encoding='utf-8') as file:
            base_prompt = file.read()
        logging.info(f'Базовый промпт прочитан из файла: {base_prompt_file}')

        # Выбор случайных элементов
        time_based_elements = get_elements_for_time()
        today_elements = get_random_elements(time_based_elements, 2)
        today = datetime.now().strftime("%d.%m.%Y")
        final_prompt = f"{base_prompt}\nСегодня {today}. Пожалуйста, включи в пожелание темы: {', '.join(today_elements)}."

        # Получаем историю диалога (например, последние 5 сообщений или 0, как сейчас)
        dialogue_history = dialogue_storage.get_messages(chat_id)[0:0]
        logging.info(f'История диалога для chat_id {chat_id}: {dialogue_history}')

        if len(dialogue_history) == 0:
            bot.send_message(chat_id, "🎉🥰")

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
            temperature=0
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
