import telebot
import requests
import os
from threading import Thread
from telebot import types

# --- ТВОИ НАСТРОЙКИ ---
BOT_TOKEN = 'AAEe4mmkbc0vTxLp3St8yYkLHm8TyuJrD5M'
HF_TOKEN = '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'
WEB_APP_URL = 'https://твой-логин.github.io/automech-ai/' 

bot = telebot.TeleBot(BOT_TOKEN)
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- ОБМАНКА ДЛЯ RENDER (PORT BINDING) ---
def run_dummy_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive")
    
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(WEB_APP_URL)
    button = types.InlineKeyboardButton(text="🚗 Запустить Mini App", web_app=web_app)
    markup.add(button)
    bot.send_message(message.chat.id, "Привет! Я твой ИИ-механик. Запусти приложение или напиши проблему здесь.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    msg = bot.send_message(message.chat.id, "🔍 Мастер изучает вопрос...")
    prompt = f"<|system|>\nТы эксперт-автомеханик. Отвечай кратко на русском.</s>\n<|user|>\n{message.text}</s>\n<|assistant|>\n"
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        result = response.json()[0]['generated_text']
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=result)
    except:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="Ошибка ИИ. Попробуй позже.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Запускаем обманку в фоне
    Thread(target=run_dummy_server, daemon=True).start()
    print("Бот запущен...")
    bot.polling(none_stop=True)
