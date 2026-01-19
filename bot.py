import os
import telebot
import requests
import time
from threading import Thread
from flask import Flask, request

# --- 1. НАСТРОЙКИ И ПЕРЕМЕННЫЕ ---
# Токены берем строго из переменных окружения (безопасность)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

# СЮДА ТЫ ВСТАВИШЬ ССЫЛКУ ПОЗЖЕ (например "https://login.github.io/repo/")
WEB_APP_URL = "" 

# --- 2. ПРОВЕРКА ПРИ ЗАПУСКЕ ---
if not BOT_TOKEN or not HF_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Токены не найдены в Environment Variables!")

bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. ИИ (HUGGING FACE) ---
def ask_ai(text):
    api_url = "https://router.huggingface.co/hf-inference/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": f"Ты автомеханик. Клиент жалуется: '{text}'. Напиши кратко 3 возможные причины и что делать.",
        "parameters": {"max_new_tokens": 250, "return_full_text": False}
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        data = response.json()
        
        # Если модель грузится
        if isinstance(data, dict) and 'estimated_time' in data:
            return "⏳ Мастер моет руки (модель грузится). Подожди 20 секунд и попробуй снова."
        
        # Если есть ответ
        if isinstance(data, list) and 'generated_text' in data[0]:
            return data[0]['generated_text'].strip()
            
        return "⚠️ Непонятный ответ от станции. Попробуй позже."
    except Exception as e:
        print(f"Ошибка AI: {e}")
        return "❌ Сбой связи с сервисом."

# --- 4. ОБРАБОТКА СООБЩЕНИЙ ---
@bot.message_handler(commands=['start'])
def start(message):
    from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    # Кнопка, открывающая Mini App
    markup.add(KeyboardButton("🚗 Открыть диагностику", web_app=WebAppInfo(url=WEB_APP_URL)))
    bot.send_message(message.chat.id, "Привет! Нажми кнопку ниже, чтобы описать проблему.", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def get_app_data(message):
    problem = message.web_app_data.data
    msg = bot.send_message(message.chat.id, f"🔍 Принято: {problem}\nДумаю...")
    
    answer = ask_ai(problem)
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=answer)

# --- 5. ЗАПУСК ВЕБ-СЕРВЕРА (ЧТОБЫ RENDER НЕ УБИЛ БОТА) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    # Запускаем на порту 10000 (стандарт Render)
    app.run(host='0.0.0.0', port=10000)

# --- 6. ЗАПУСК БОТА (БЕЗ КОНФЛИКТОВ) ---
if __name__ == '__main__':
    # Сначала запускаем сервер в фоне
    Thread(target=run_flask).start()
    
    print("✅ Бот запускается...")
    
    # Вечный цикл перезапуска при сбоях
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"♻️ Рестарт polling из-за ошибки: {e}")
            time.sleep(5)
