import os
import telebot
import requests
import time
from threading import Thread
from flask import Flask
from urllib.parse import quote

# Настройки
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
WEB_APP_URL = "ТВОЯ_ССЫЛКА_GITHUB_PAGES" 

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "OK"

def ask_ai(text):
    # Используем Mistral — она сейчас самая отзывчивая в бесплатном доступе
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [
            {"role": "user", "content": f"Ты автомеханик. Кратко и понятно ответь на русском, что проверить, если: {text}"}
        ],
        "max_tokens": 300
    }
    
    try:
        # Ставим умеренный таймаут, чтобы бот не зависал надолго
        res = requests.post(api_url, headers=headers, json=payload, timeout=25)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
        return "Не удалось получить быстрый совет. Посмотри решение на форуме ниже."
    except:
        return "Связь с сервером ИИ временно прервана. Воспользуйся поиском DRIVE2."

@bot.message_handler(content_types=['web_app_data'])
def get_data(message):
    problem = message.web_app_data.data
    msg = bot.send_message(message.chat.id, "🚗 Мастер думает...")
    
    answer = ask_ai(problem)
    # Ссылка сразу на поиск внутри Drive2
    drive2_url = f"https://www.drive2.ru/search/?text={quote(problem)}"
    
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔍 Поиск этой проблемы на DRIVE2", url=drive2_url))
    
    bot.edit_message_text(
        chat_id=message.chat.id, 
        message_id=msg.message_id, 
        text=f"<b>Совет мастера:</b>\n\n{answer}", 
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.message_handler(commands=['start'])
def start(message):
    from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🚗 Начать диагностику", web_app=WebAppInfo(url=WEB_APP_URL)))
    bot.send_message(message.chat.id, "Привет! Опиши проблему, и я постараюсь помочь.", reply_markup=markup)

def run():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("🚀 Бот запущен!")
    bot.polling(none_stop=True)
