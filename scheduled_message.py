import logging
from datetime import datetime
from characters import get_character
from dialogue_storage import dialogue_storage
from unsplash_functions import get_random_image
import random
import re

def get_random_elements(elements, n):
    return random.sample(elements, min(n, len(elements)))

def split_message(message, max_length):
    """Разбивает длинное сообщение на части, не превышающие max_length."""
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

def truncate_repeating_text(text, max_repeats=3):
    """Обрезает повторяющиеся слова и символы."""
    
    # Убираем слишком длинные повторы символов (например, 'срсрсрсрс...')
    def limit_repeated_chars(match):
        char_sequence = match.group(0)
        return char_sequence[:max_repeats]
    
    # Шаблон для поиска повторяющихся символов
    text = re.sub(r'(.)\1{3,}', limit_repeated_chars, text)

    words = text.split()
    result = []
    prev_word = None
    repeat_count = 0
    
    # Обработка повторяющихся слов
    for word in words:
        if word == prev_word:
            repeat_count += 1
        else:
            repeat_count = 0
        
        if repeat_count < max_repeats:
            result.append(word)
        
        prev_word = word
    
    return ' '.join(result)

def process_response(response, chat_id, bot, users_gender):
    """Обрабатывает ответ от Groq, обрезая повторяющиеся символы."""
    if response.choices and response.choices[0].message and response.choices[0].message.content:
        response_content = response.choices[0].message.content
        logging.info(f'Получен ответ: {response_content}')
        logging.info(f'Длина ответа от Groq: {len(response_content)}')

        # Убираем повторяющиеся символы или слова
        cleaned_response = truncate_repeating_text(response_content)
        logging.info(f'Очищенный ответ: {cleaned_response}')

        image_url = get_random_image(users_gender)
        if image_url:
            bot.send_photo(chat_id, image_url)
        else:
            logging.error("url изображения так не получается...")

        send_long_message(chat_id, bot, cleaned_response)
        dialogue_storage.add_message(chat_id, 'assistant', cleaned_response)
    else:
        logging.error("Ответ от Groq пустой или не полностью получен, сообщение не отправлено.")
        bot.send_message(chat_id, "Опять я это самое... 🤪")

def send_long_message(chat_id, bot, message):
    max_message_length = 4096
    # Разбиваем длинное сообщение на части, если оно превышает лимит
    for i in range(0, len(message), max_message_length):
        bot.send_message(chat_id, message[i:i+max_message_length])

def send_scheduled_message(chat_id, bot, client_groq, tz_manager):
    try:
        max_groq_length = 4000  # Установим лимит длины для Groq

        current_hour = tz_manager.get_current_hour()
        base_prompt_file = tz_manager.get_prompt_for_time(current_hour)
        time_based_elements = tz_manager.get_elements_for_time(current_hour)

        with open(base_prompt_file, 'r', encoding='utf-8') as file:
            base_prompt = file.read()
        logging.info(f'Базовый промпт прочитан из файла: {base_prompt_file}')

        today_elements = get_random_elements(time_based_elements, 2)
        today = datetime.now(tz_manager.default_timezone).strftime("%d.%m.%Y")
        final_prompt = f"{base_prompt}\nСегодня {today}. Пожалуйста, включи в пожелание темы: {', '.join(today_elements)}."

        logging.info(f'Длина финального промпта: {len(final_prompt)}')

        dialogue_history = dialogue_storage.get_messages(chat_id)[0:0]
        logging.info(f'История диалога для chat_id {chat_id}: {dialogue_history}')

        if len(dialogue_history) == 0:
            bot.send_message(chat_id, "🎉🥰")

        messages_for_groq = [
            {"role": msg["role"], "content": msg["content"]} for msg in dialogue_history
        ]

        character, users_gender = get_character(chat_id)
        system_message = {
            "role": "system", 
            "content": character
        }

        messages = [system_message] + messages_for_groq
        messages.append({"role": 'user', "content": final_prompt})

        combined_messages = [msg["content"] for msg in messages]
        full_message = "\n".join(combined_messages)

        logging.info(f'Окончательная длина запроса к Groq: {len(full_message)}')

        # Обрезка полного сообщения, если оно превышает лимит
        if len(full_message) > max_groq_length:
            full_message = full_message[:max_groq_length]
            logging.warning(f'Сообщение обрезано до {max_groq_length} символов.')

        # Отправляем сообщение в Groq
        response = client_groq.chat.completions.create(
            model='llama3-70b-8192',
            messages=[{"role": 'user', "content": full_message}],
            temperature=0
        )
        process_response(response, chat_id, bot, users_gender)

    except Exception as e:
        logging.error(f'Ошибка в функции send_scheduled_message: {e}')
        bot.send_message(chat_id, "Ну хорошо... 😊")

