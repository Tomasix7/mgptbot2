import requests
import os

UNSPLASH_ACCESS_KEY = os.getenv('UNSKEY')

def get_random_image():
    url = "https://api.unsplash.com/photos/random"
    params = {
        "client_id": UNSPLASH_ACCESS_KEY,
        "orientation": "landscape",
        "query": "nature",
        "count": 1
    }
    response = requests.get(url, params=params)
    data = response.json()
    image_url = data[0]["urls"]["small"]
    return image_url