import asyncio
from collections import deque
import time

class RequestQueue:
    def __init__(self, interval=2):
        self.queue = deque()
        self.interval = interval
        self.last_request_time = 0

    async def add_request(self, func, *args, **kwargs):
        self.queue.append((func, args, kwargs))
        await self.process_queue()

    async def process_queue(self):
        while self.queue:
            current_time = time.time()
            if current_time - self.last_request_time < self.interval:
                await asyncio.sleep(self.interval - (current_time - self.last_request_time))

            func, args, kwargs = self.queue.popleft()
            self.last_request_time = time.time()
            await func(*args, **kwargs)

request_queue = RequestQueue()

# Example usage in get_text_messages:
# async def send_request_to_groq(messages, chat_id):
#     try:
#         response = client_groq.chat.completions.create(model='llama3-70b-8192', messages=messages, temperature=0)
#         bot.send_message(chat_id, response.choices[0].message.content)
#         dialogue_storage.add_message(chat_id, 'assistant', response.choices[0].message.content)
#     except Exception as e:
#         logging.error(f'Error when sending request to Groq: {e}')
#         bot.send_message(chat_id, "Отправь мне смайлик 🙏 🥰")

# @bot.message_handler(content_types=['text'])
# def get_text_messages(message):
#     # ... (previous code remains the same)
    
#     asyncio.run(request_queue.add_request(send_request_to_groq, messages, message.chat.id))