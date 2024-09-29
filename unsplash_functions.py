import requests
import logging
import os
# from dotenv import load_dotenv

# load_dotenv()
UNSPLASH_ACCESS_KEY = os.getenv('UNSKEY')

# Функция получения случайного изображения из UNSPLASH
def get_random_image(gender):
    try:
        url = "https://api.unsplash.com/photos/random"
        query = """
        man back, man body, bodybuilding, abs, gym, underwear, male, love images, kiss images,
        roses, laboratory, coffee, tea
        """ if gender == "female" else """
        girl back, lingerie, female, roses, laboratory, coffee, tea
        """
        params = {
            "client_id": UNSPLASH_ACCESS_KEY,
            "orientation": "portrait",
            "query": query,
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
