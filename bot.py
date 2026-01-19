import os
import telebot
import requests
import time
from threading import Thread
from flask import Flask

# Настройки
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
WEB_APP_URL = "https://armiy1706-ctrl.github.io/car-diagnostic-app/"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "OK"

# Функция для ИИ
import sys # Добавь это в самый верх файла к импортам

def ask_ai(text):
    # Самый современный адрес роутера (v1 chat)
    api_url = "https://router.huggingface.co/hf-inference/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Новый формат данных (сообщения ролями)
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [
            {"role": "system", "content": "Ты — профессиональный автомеханик. Отвечай кратко и только на русском языке."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500,
        "stream": False
    }
    
    print(f">>> ИИ: Отправка через Chat API...", flush=True)
    
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=30)
        print(f">>> ИИ: Статус = {res.status_code}", flush=True)

        if res.status_code == 200:
            result = res.json()
            # В новом формате ответ лежит здесь:
            return result['choices'][0]['message']['content'].strip()
            
        elif res.status_code == 503:
            return "⏳ Мастер подготавливает бокс (модель грузится). Подожди 30 секунд и нажми еще раз."
        else:
            print(f">>> Ошибка: {res.text}", flush=True)
            return f"⚠️ Ошибка связи (Код: {res.status_code})"

    except Exception as e:
        print(f">>> Критическая ошибка: {e}", flush=True)
        return "❌ Не удалось связаться с мастером."

# ОТЛАДКА: Бот будет писать в логи любое сообщение
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(f"📩 Получено сообщение: {message.text}") # Это появится в логах Render!
    if message.text == '/start':
        from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("🚗 Открыть диагностику", web_app=WebAppInfo(url=WEB_APP_URL)))
        bot.send_message(message.chat.id, "Бот готов! Нажми на кнопку.", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def get_data(message):
    print(f"📦 Данные из Mini App: {message.web_app_data.data}")
    msg = bot.send_message(message.chat.id, "Думаю...")
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=ask_ai(message.web_app_data.data))

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=run_flask).start()
    print("🚀 ПОПЫТКА ЗАПУСКА ПОЛЛИНГА...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"❌ Ошибка поллинга: {e}")
            time.sleep(5)
