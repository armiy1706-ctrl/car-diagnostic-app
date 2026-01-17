import telebot
import requests
import os
from threading import Thread
from telebot import types

# --- ТВОИ ТОКЕНЫ (Проверь их!) ---
BOT_TOKEN = '8572493279:AAEe4mmkbc0vTxLp3St8yYkLHm8TyuJrD5M'
HF_TOKEN = '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'
WEB_APP_URL = 'https://твой-логин.github.io/automech-ai/' 

bot = telebot.TeleBot(BOT_TOKEN)

# Настройки нейросети
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- ФУНКЦИЯ-ОБМАНКА ДЛЯ RENDER ---
def run_dummy_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is active")
    
    # Render сам передает номер порта через переменную окружения PORT
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"Сервер-заглушка запущен на порту {port}")
    server.serve_forever()

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(WEB_APP_URL)
    button = types.InlineKeyboardButton(text="🚗 Запустить диагностику", web_app=web_app)
    markup.add(button)
    
    bot.send_message(
        message.chat.id, 
        f"Привет! Я твой ИИ-механик. Нажми кнопку ниже, чтобы открыть приложение, или опиши проблему здесь.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    msg = bot.send_message(message.chat.id, "🔍 Мастер изучает ваш вопрос...")
    
    # Формируем запрос для Llama 3
    prompt = f"<|system|>\nТы — профессиональный автомеханик. Отвечай кратко и только на русском языке.</s>\n<|user|>\n{message.text}</s>\n<|assistant|>\n"
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 500}}

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        data = response.json()
        result = data[0]['generated_text']
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=result)
    except:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="ИИ еще загружается, подождите 30 секунд и повторите вопрос.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Запускаем сервер-заглушку в отдельном потоке
    Thread(target=run_dummy_server, daemon=True).start()
    
    print("Бот запускается...")
    bot.polling(none_stop=True)
