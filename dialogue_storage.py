from pymongo import MongoClient
from datetime import datetime
import logging
import os
import pytz

# Создаем объект часового пояса UTC+3
tz = pytz.timezone('Europe/Moscow')  # Замените на нужную временную зону

DBASE = os.getenv('DBASE')
DCOLLECTION = os.getenv('DCOLLECTION')

class DialogueStorage:
    def __init__(self):
        MONGO_URI = os.getenv('MONGO_URI')
        client = MongoClient(MONGO_URI)
        db = client[DBASE]
        self.collection = db[DCOLLECTION]
        
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
                'timestamp': datetime.now(tz) 
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

# Создаем глобальный экземпляр DialogueStorage
dialogue_storage = DialogueStorage()