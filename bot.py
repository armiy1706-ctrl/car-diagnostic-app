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
    # НОВЫЙ АДРЕС (ROUTER), КОТОРЫЙ ТРЕБУЕТ HUGGING FACE
    api_url = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Формируем запрос для Mistral
    prompt = f"<s>[INST] Ты — опытный автомеханик. Отвечай только на русском языке. Клиент спрашивает: {text} [/INST]</s>"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    
    print(f">>> ИИ: Запрос отправлен через новый Router...", flush=True)
    
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=30)
        print(f">>> ИИ: Код ответа = {res.status_code}", flush=True)

        if res.status_code == 200:
            result = res.json()
            if isinstance(result, list) and len(result) > 0:
                # Убираем возможные остатки промпта из ответа
                answer = result[0].get('generated_text', '').strip()
                return answer
            return "⚠️ ИИ прислал пустой ответ."
            
        elif res.status_code == 503:
            return "⏳ Станция прогревается (модель грузится). Подождите 30 секунд и нажмите еще раз."
            
        else:
            print(f">>> Подробности ошибки: {res.text}", flush=True)
            return f"⚠️ Ошибка сервера ИИ (Код: {res.status_code})"

    except Exception as e:
        print(f">>> Критическая ошибка: {e}", flush=True)
        return "❌ Не удалось достучаться до мастера."

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
