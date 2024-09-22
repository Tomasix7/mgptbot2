import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

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
