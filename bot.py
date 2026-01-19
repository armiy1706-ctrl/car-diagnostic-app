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
    # Используем более новую версию 3.1 - она сейчас основная и стабильная
    api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Максимально простой и понятный формат для модели
    payload = {
        "inputs": f"Ты — автомеханик. Дай краткий совет на русском языке по этой проблеме: {text}",
        "parameters": {
            "max_new_tokens": 300,
            "return_full_text": False
        }
    }
    
    print(f">>> ИИ: Запрос отправлен на Llama 3.1...", flush=True)
    
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=30)
        print(f">>> ИИ: Код ответа = {res.status_code}", flush=True)

        if res.status_code == 200:
            result = res.json()
            # Проверяем формат ответа
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'Пустой ответ от мастера.').strip()
            return "⚠️ Не удалось прочитать ответ ИИ."
            
        elif res.status_code == 503:
            return "⏳ Станция перегружена (модель грузится). Подожди 20-30 секунд и нажми кнопку еще раз."
            
        elif res.status_code == 410:
            return "❌ Модель устарела. Требуется обновление ссылки в коде."
            
        else:
            print(f">>> Ошибка сервера ИИ: {res.text}", flush=True)
            return f"⚠️ Сервер ИИ ответил ошибкой {res.status_code}"

    except Exception as e:
        print(f">>> ИИ: Критическая ошибка: {e}", flush=True)
        return "❌ Не удалось связаться с мастером-ИИ."

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
