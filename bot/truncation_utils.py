def truncate_message(message, max_length=4000):
    if len(message) <= max_length:
        return message
    return message[:max_length-3] + "..."

def truncate_messages(messages, max_length=4000):
    truncated = []
    for msg in messages:
        truncated.append({
            "role": msg["role"],
            "content": truncate_message(msg["content"], max_length)
        })
    return truncated

# # Example usage in send_request_to_groq:
# async def send_request_to_groq(messages, chat_id):
#     try:
#         truncated_messages = truncate_messages(messages)
#         request_char_count = sum(len(msg['content']) for msg in truncated_messages)
#         logging.info(f"Truncated request character count: {request_char_count}")
        
#         response = client_groq.chat.completions.create(model='llama3-70b-8192', messages=truncated_messages, temperature=0)
        
#         response_content = truncate_message(response.choices[0].message.content)
#         response_char_count = len(response_content)
#         logging.info(f"Truncated response character count: {response_char_count}")
        
#         bot.send_message(chat_id, response_content)
#         dialogue_storage.add_message(chat_id, 'assistant', response_content)
#     except Exception as e:
#         logging.error(f'Error when sending request to Groq: {e}')
#         bot.send_message(chat_id, "Отправь мне смайлик 🙏 🥰")