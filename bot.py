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
def ask_ai(text):
    # Прямой адрес модели Llama 3
    api_url = "https://router.huggingface.co/hf-inference/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": f"Ты — профессиональный автомеханик. Клиент говорит: {text}. Дай краткий совет на русском языке.",
        "parameters": {"max_new_tokens": 250, "return_full_text": False}
    }
    
    try:
        print(f"📡 Отправляю запрос к ИИ с токеном: {HF_TOKEN[:5]}...") # Проверка в логах
        res = requests.post(api_url, headers=headers, json=payload, timeout=25)
        
        # Печатаем статус ответа в логи Render
        print(f"Статус ответа ИИ: {res.status_code}")
        
        result = res.json()
        
        # Если модель еще загружается (ошибка 503)
        if res.status_code == 503:
            return "⏳ Мастер еще готовит инструменты (модель загружается). Попробуйте через 20 секунд."
            
        # Если токен неверный (ошибка 401)
        if res.status_code == 401:
            return "❌ Ошибка авторизации. Проверьте HF_TOKEN в настройках Render."

        # Если всё успешно
        if isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text'].strip()
        else:
            print(f"Неожиданный формат ответа: {result}")
            return "⚠️ ИИ прислал странный ответ. Попробуйте еще раз."

    except Exception as e:
        print(f"❌ Полная ошибка в блоке ask_ai: {e}")
        return "❌ Сбой связи с сервером ИИ."

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
