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
    # Используем классический адрес (он иногда стабильнее для бесплатных аккаунтов)
    api_url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nТы автомеханик. Ответь кратко на русском: {text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        "parameters": {"max_new_tokens": 300}
    }
    
    # Принудительно выводим в логи начало процесса
    print(">>> ИИ: Начинаю запрос к Hugging Face...", flush=True)
    
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        # Печатаем всё, что узнали
        print(f">>> ИИ: Статус код = {res.status_code}", flush=True)
        print(f">>> ИИ: Ответ сервера = {res.text[:100]}", flush=True) 

        if res.status_code == 200:
            result = res.json()
            # У Llama 3 ответ приходит списком
            if isinstance(result, list):
                return result[0]['generated_text'].split("assistant<|end_header_id|>\n\n")[-1].strip()
            return result.get('generated_text', 'Ошибка формата')
            
        elif res.status_code == 503:
            return "⏳ Модель загружается на сервере ИИ. Повтори через 30 секунд."
        else:
            return f"❌ Сервер ИИ ответил ошибкой {res.status_code}"

    except Exception as e:
        print(f">>> ИИ: Ошибка внутри try: {e}", flush=True)
        return "❌ Не удалось достучаться до ИИ."

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
