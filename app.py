import os
import logging
import telebot
from pymongo import MongoClient
from datetime import datetime
from flask import Flask, request
from groq import Groq

# Настройки логирования
logging.basicConfig(level=logging.INFO)

# Подключение к MongoDB
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['dialogue_database']
collection = db['dialogs']

class DialogueStorage:
    def __init__(self, collection):
        self.collection = collection
        # Создание TTL индекса для удаления сообщений старше 24 часов
        self.collection.create_index("timestamp", expireAfterSeconds=86400)

    def add_message(self, chat_id, role, content):
        # Сохранение сообщения с меткой времени
        message = {
            'chat_id': chat_id,
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow()
        }
        self.collection.insert_one(message)

    def get_messages(self, chat_id):
        # Получение всех сообщений для данного чата
        return list(self.collection.find({'chat_id': chat_id}).sort('timestamp', 1))

    def clean_old_messages(self):
        # MongoDB сам очистит старые сообщения по TTL индексу
        pass

# Инициализация Groq и Telegram Bot
YOUR_CHAT_ID = os.getenv("YOUR_CHAT_ID")
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

client_groq = Groq(api_key=CLIENT_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Инициализация Flask приложения и DialogueStorage
app = Flask(__name__)
dialogue_storage = DialogueStorage(collection)

@app.route('/' + bot.token, methods=['POST'])
def get_message():
    json_str = request.get_data().decode('UTF-8')
    logging.info(f'Received update: {json_str}')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'ok', 200

@bot.message_handler(commands=['restart'])
def restart_model(message):
    chat_id = str(message.chat.id)
    try:
        result = dialogue_storage.collection.delete_many({'chat_id': chat_id})  # Очистить все сообщения для данного чата
        
        if result.deleted_count > 0:
            logging.info(f'Удалено {result.deleted_count} сообщений для чата {chat_id}')
            bot.send_message(message.from_user.id, f'Ок, давай начнем с чистого листа! 😊📝 Очищено {result.deleted_count} сообщений для чата № {chat_id}.')
        else:
            logging.info(f'Коллекция пуста для чата {chat_id}')
            bot.send_message(message.from_user.id, f'Коллекция уже пуста. Нечего удалять для чата № {chat_id}. 😄 Давай всё равно начнём заново.')
    except Exception as e:
        logging.error(f'Ошибка при обработке команды /restart: {e}')
        bot.send_message(message.from_user.id, 'Произошла ошибка при выполнении команды. Попробуй ещё раз. 😓')

@bot.message_handler(commands=['len'])
def get_dialogue_length(message):
    chat_id = str(message.chat.id)
    
    all_messages = dialogue_storage.get_messages(chat_id)
    total_chars = sum(len(msg['content']) for msg in all_messages)
    message_count = len(all_messages)
    
    response = f"Статистика диалога:\n"
    response += f"Количество сообщений: {message_count}\n"
    response += f"Общее количество символов: {total_chars}\n"
    response += f"Первое сообщение: {all_messages[0]['timestamp'] if all_messages else 'Нет сообщений'}\n"
    response += f"Последнее сообщение: {all_messages[-1]['timestamp'] if all_messages else 'Нет сообщений'}"
    
    bot.send_message(message.from_user.id, response)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    logging.info(f'Received message: {message.text}')
    
    chat_id = str(message.chat.id)
    dialogue_storage.add_message(chat_id, 'user', message.text)
   
    # Получаем историю диалога
    dialogue_history = dialogue_storage.get_messages(chat_id)

    # Устанавливаем лимит на количество сообщений (например, 10 последних сообщений)
    max_messages = 10
    if len(dialogue_history) > max_messages:
        dialogue_history = dialogue_history[-max_messages:]

    logging.info(f"Dialogue history for chat {chat_id}: {dialogue_history}")

    if len(dialogue_history) == 0:
        bot.send_message(message.from_user.id, "Поехали 🚀🏁 )")

    # Убираем поле 'timestamp' из сообщений перед отправкой в API
    messages_for_groq = [
        {"role": msg["role"], "content": msg["content"]} for msg in dialogue_history
    ]

    # Формируем сообщение для системы
    system_message = {
        "role": "system", 
        "content": "You are a character named Nana"
    }

    # Добавляем системное сообщение и историю диалога
    messages = [system_message] + messages_for_groq

    # Логируем отправляемые данные
    logging.info(f'Sending messages to Groq: {messages}')

    try:
        response = client_groq.chat.completions.create(model='llama3-70b-8192', messages=messages, temperature=0)
        bot.send_message(message.from_user.id, response.choices[0].message.content)
        dialogue_storage.add_message(chat_id, 'assistant', response.choices[0].message.content)
    except Exception as e:
        logging.error(f'Error when sending request to Groq: {e}')
        bot.send_message(message.from_user.id, "Отправь мне смайлик 🙏 🥰")

@app.route('/')
def index():
    return 'Hello, this is your botfriend on Render!'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://mgptbot2.onrender.com/' + bot.token)
    logging.info(f'Webhook set to: https://mgptbot2.onrender.com/{bot.token}')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
