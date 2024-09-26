from config import AUTHORIZED_CHAT_IDS
# Загрузка переменных окружения (только для локального запуска)
from dotenv import load_dotenv
load_dotenv()

def is_authorized(chat_id):
    return str(chat_id) in AUTHORIZED_CHAT_IDS