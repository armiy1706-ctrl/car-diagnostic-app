import telebot
import requests
import os
from threading import Thread
from telebot import types

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8572493279:AAEe4mmkbc0vTxLp3St8yYkLHm8TyuJrD5M'
HF_TOKEN = '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'
# Добавь ?v=1 в конце для сброса кэша
WEB_APP_URL = 'https://armiy1706-ctrl.github.io/car-diagnostic-app/'

bot = telebot.TeleBot(BOT_TOKEN)

# --- СЕРВЕР-ЗАГЛУШКА ДЛЯ RENDER ---
def run_dummy_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive")
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚗 Открыть диагностику", web_app=types.WebAppInfo(WEB_APP_URL)))
    bot.send_message(message.chat.id, "Нажми на кнопку внизу для запуска Mini App:", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def web_app(message):
    user_text = message.web_app_data.data
    msg = bot.send_message(message.chat.id, f"🔍 Анализирую: {user_text}...")
    
    api_url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": user_text}, timeout=15)
        response_data = response.json()
        
        # Печатаем ответ в логи Render для проверки
        print(f"Ответ от ИИ: {response_data}")
        
        if isinstance(response_data, list) and 'generated_text' in response_data[0]:
            result = response_data[0]['generated_text']
        elif 'error' in response_data:
            result = f"Ошибка ИИ: {response_data['error']}"
        else:
            result = "ИИ прислал странный ответ. Попробуй еще раз."
            
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=result)
        
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="Сбой связи с ИИ.")

if __name__ == "__main__":
    # Сначала запускаем сервер для Render
    Thread(target=run_dummy_server, daemon=True).start()
    print("Бот запущен и готов к работе...")
    
    # Запускаем бота с удалением старых запросов
    bot.remove_webhook() 
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(f"Получено сообщение: {message.text}")
    bot.reply_to(message, f"Ты написал: {message.text}")

if __name__ == "__main__":
    Thread(target=run_dummy_server, daemon=True).start()
    print("Бот запущен и готов к работе...")
    bot.remove_webhook() 
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
