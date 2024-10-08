import os
import logging
from config import init_bot_and_groq
import telebot
from flask import Flask, render_template, request
from handlers import db_handler, edit_char, edit_user, new_character
from bot.handlers import bot

WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Initialize Flask app
app = Flask(__name__)

# Initialize bot and Groq client
init_bot_and_groq()

@app.route('/' + bot.token, methods=['POST'])
def get_message():
    json_str = request.get_data().decode('UTF-8')
    logging.info(f'Received update: {json_str}')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'ok', 200

@app.route('/')
def index():
    return render_template('index.html')

# PRODUCTION
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url= WEBHOOK_URL + bot.token)
    logging.info(f'Webhook set to: {WEBHOOK_URL}{bot.token}')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# 'https://mgptbot2.onrender.com/'