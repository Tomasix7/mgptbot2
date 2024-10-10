from datetime import datetime
import pytz
import os
import logging
from dictionary import NIGHT_ELEMENTS, DAY_ELEMENTS, EVENING_ELEMENTS

class TimeZoneManager:
    def __init__(self, default_timezone='Europe/Moscow'):
        self.default_timezone = pytz.timezone(default_timezone)

    def get_current_hour(self, timezone=None):
        
        tz = pytz.timezone(timezone) if timezone else self.default_timezone
        return datetime.now(tz).hour

    def get_prompt_for_time(self, current_hour=None):
        if current_hour is None:
            current_hour = self.get_current_hour()
        
        prompts_dir = 'prompts/'
        
        if 0 <= current_hour < 2:
            prompt_file = 'goodnight_prompt.txt'
        elif 2 <= current_hour < 4:
            prompt_file = 'sleepwell_prompt.txt'
        elif 4 <= current_hour < 6:
            prompt_file = 'sleepwell_prompt.txt'
        elif 6 <= current_hour < 7:
            prompt_file = 'morning_prompt.txt'
        elif 7 <= current_hour < 8:
            prompt_file = '7_prompt.txt'
        elif 8 <= current_hour < 9:
            prompt_file = '8_prompt.txt'
        elif 9 <= current_hour < 10:
            prompt_file = 'main_prompt.txt'
        elif 10 <= current_hour < 11:
            prompt_file = '10_prompt.txt'
        elif 11 <= current_hour < 12:
            prompt_file = 'meditation_prompt.txt'
        elif 12 <= current_hour < 13:
            prompt_file = 'lunch_prompt.txt'
        elif 13 <= current_hour < 14:
            prompt_file = '134_prompt.txt'
        elif 14 <= current_hour < 15:
            prompt_file = '14_prompt.txt'
        elif 15 <= current_hour < 16:
            prompt_file = 'coffee_prompt.txt'
        elif 16 <= current_hour < 17:
            prompt_file = 'afternoon_prompt.txt'
        elif 17 <= current_hour < 18:
            prompt_file = '17_prompt.txt'
        elif 18 <= current_hour < 19:
            prompt_file = 'prompt.txt'
        elif 19 <= current_hour < 20:
            prompt_file = 'meditation_prompt.txt'
        elif 20 <= current_hour < 21:
            prompt_file = 'date_prompt.txt'
        elif 21 <= current_hour < 22:
            prompt_file = '21_prompt.txt'
        elif 22 <= current_hour < 23:
            prompt_file = 'goodnight_prompt.txt'
        else:
            prompt_file = 'meditation_prompt.txt'
        
        # return os.path.join(prompts_dir, prompt_file)

        prompt_path = os.path.join(prompts_dir, prompt_file)
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except FileNotFoundError:
            logging.error(f"Файл промпта не найден: {prompt_path}")
            return "Базовый промпт недоступен."
        except IOError as e:
            logging.error(f"Ошибка при чтении файла промпта: {e}")
            return "Ошибка при чтении базового промпта."

    def get_elements_for_time(self, current_hour=None):
        if current_hour is None:
            current_hour = self.get_current_hour()
        
        if 0 <= current_hour < 6:
            return NIGHT_ELEMENTS
        elif 6 <= current_hour < 18:
            return DAY_ELEMENTS
        else:
            return EVENING_ELEMENTS

# Пример использования
# tz_manager = TimeZoneManager() # если ничего не передаем в скобках, то используется дефолтный часовой пояс
# current_hour_moscow = tz_manager.get_current_hour()
# current_hour_yekaterinburg = tz_manager.get_current_hour('Asia/Yekaterinburg')
# prompt_file = tz_manager.get_prompt_for_time()
# elements = tz_manager.get_elements_for_time()