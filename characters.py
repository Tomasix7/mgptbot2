import os
import logging
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
load_dotenv()

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MONGO_URI = os.getenv("MONGO_URI")
logging.info(f"MONGO_URI: {MONGO_URI}")
DBASE = os.getenv('DBASE')

# Подключение к MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client[DBASE]
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Error connecting to MongoDB: {e}")
    raise

# Коллекция с пользователями (chat_id, character, gender)
user_collection = db['users_collection']

# Коллекция с персонажами (NANA, MARKO, MARGO и т.п.)
character_collection = db['characters']

def get_character(chat_id):
    logging.info(f"Attempting to get character for chat_id: {chat_id}")
    logging.info(f"Using collection: {user_collection.name}")  # Логируем коллекцию
    # Ищем пользователя по chat_id
    user_data = user_collection.find_one({"chat_id": chat_id})
    
    if user_data:
        logging.info(f"User data found: {user_data}")
        character_name = user_data.get("character")
        users_name = user_data.get("users_name", [])
        users_gender = user_data.get("users_gender")
        timezone = user_data.get("timezone")
        
        # Ищем описание персонажа в коллекции персонажей
        character_data = character_collection.find_one({"character": character_name})
        if character_data:
            # logging.info(f"Character data found: {character_data}")
            character_description = character_data.get("description")
        else:
            logging.warning(f"No character description found for {character_name}")
            character_description = "No description available."
        
        # Формируем строку для промпта - описание персонажа и имена пользователя одной строкой
        character_info = (
            f"Prompt: {character_description} "
            f"User's names: {', '.join(users_name)}. "
        )
        
        logging.info(f"Returning character info for {character_name}")
        # Выводим три переменные: 1. строку для промпта, 2. имя персонада, 3. пол пользователя
        return character_info, character_name, users_gender, timezone
    else:
        logging.warning(f"No user data found for chat_id: {chat_id}")
        return "Character not found.", None, None
