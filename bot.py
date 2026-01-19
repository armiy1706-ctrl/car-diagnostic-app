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
WEB_APP_URL = "https://armiy1706-ctrl.github.io/car-diagnostic-app/"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "OK"

def ask_ai(text):
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    payload = {
        "model": "google/gemma-2-2b-it",
        "messages": [
            {"role": "system", "content": "Ты опытный автомеханик с DRIVE2. Отвечай кратко, понятно и только на русском языке."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 400
    }

    # Пытаемся достучаться до ИИ 3 раза
    for attempt in range(3):
        try:
            print(f">>> Попытка {attempt + 1} связаться с ИИ...")
            res = requests.post(api_url, headers=headers, json=payload, timeout=25)
            
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content'].strip()
            
            # Если модель грузится (503), ждем дольше
            if res.status_code == 503:
                print(">>> ИИ прогревается, ждем 10 секунд...")
                time.sleep(10)
                continue
                
            print(f">>> Ошибка сервера {res.status_code}: {res.text}")
        except Exception as e:
            print(f">>> Ошибка при попытке {attempt + 1}: {e}")
            time.sleep(2) # Небольшая пауза перед повтором
            
    return "🛠 Мастер пока занят в боксе. Попробуй нажать кнопку еще раз через полминуты — я точно отвечу!"

@bot.message_handler(content_types=['web_app_data'])
def get_data(message):
    problem = message.web_app_data.data
    msg = bot.send_message(message.chat.id, "🛠 Мастер изучает твой случай...")
    
    answer = ask_ai(problem)
    drive2_url = f"https://www.drive2.ru/search/?text={quote(problem)}"
    
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔍 Поиск на DRIVE2.RU", url=drive2_url))
    
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
    bot.send_message(message.chat.id, "Привет! Опиши проблему с авто, а я подскажу, что делать.", reply_markup=markup)

# Функция запуска Flask
def run():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    # Сначала запускаем Flask, чтобы Render сразу увидел живой порт
    t = Thread(target=run)
    t.daemon = True
    t.start()
    
    print("🚀 Сервер запущен, начинаю опрос Telegram...")
    
    # Запуск бота
    while True:
        try:
            bot.polling(none_stop=True)
        except:
            time.sleep(5)
