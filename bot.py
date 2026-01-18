import telebot
import requests
import os
import json
from threading import Thread
from telebot import types

# --- ТВОИ ТОКЕНЫ (НЕ ЗАБУДЬ ВСТАВИТЬ СВОИ!) ---
BOT_TOKEN = '8572493279:AAEe4mmkbc0vTxLp3St8yYkLHm8TyuJrD5M'
HF_TOKEN = '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'
WEB_APP_URL = 'https://armiy1706-ctrl.github.io/car-diagnostic-app/?v=1.1'

bot = telebot.TeleBot(BOT_TOKEN)
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- 1. ОБМАНКА ДЛЯ RENDER (чтобы не выключался) ---
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

# --- 2. ФУНКЦИЯ ДЛЯ ЗАПРОСА К НЕЙРОСЕТИ ---
def get_ai_answer(text):
    prompt = f"<|system|>\nТы — эксперт-автомеханик. Отвечай кратко на русском.</s>\n<|user|>\n{text}</s>\n<|assistant|>\n"
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        data = response.json()
        # Извлекаем текст ответа
        if isinstance(data, list):
            return data[0]['generated_text']
        else:
            return "ИИ еще загружается, подождите 30 секунд."
    except Exception as e:
        return "Произошла ошибка при связи с ИИ."

# --- 3. ОБРАБОТКА ДАННЫХ ИЗ MINI APP ---
@bot.message_handler(content_types=['web_app_data'])
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    # ЭТА СТРОЧКА ПОЯВИТСЯ В КОНСОЛИ RENDER, ЕСЛИ ДАННЫЕ ПРИШЛИ
    print("!!! КНОПКА НАЖАТА, ДАННЫЕ ПОЛУЧЕНЫ !!!") 
    
    try:
        data = json.loads(message.web_app_data.data)
        query_text = data.get('text', 'Ошибка данных')
        bot.send_message(message.chat.id, f"Принято: {query_text}")
        
        answer = get_ai_answer(query_text)
        bot.send_message(message.chat.id, answer)
    except Exception as e:
        print(f"ОШИБКА: {e}")
    # Получаем данные, которые мы отправили через tg.sendData в index.html
    raw_data = message.web_app_data.data
    data = json.loads(raw_data)
    
    query_text = data.get('text', 'Нет данных')
    
    msg = bot.send_message(message.chat.id, f"⚙️ *Данные приняты!*\nЗапрос: _{query_text}_\n\nИщу решение...", parse_mode="Markdown")
    
    # Получаем ответ от ИИ
    answer = get_ai_answer(query_text)
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=answer)

# --- 4. ОБЫЧНЫЕ КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚗 Открыть диагностику", web_app=types.WebAppInfo(WEB_APP_URL)))
    bot.send_message(message.chat.id, "Привет! Используй кнопку для выбора симптомов или просто напиши мне вопрос.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def chat_message(message):
    msg = bot.send_message(message.chat.id, "🔍 Думаю...")
    answer = get_ai_answer(message.text)
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=answer)

# --- ЗАПУСК ---
if __name__ == "__main__":
    Thread(target=run_dummy_server, daemon=True).start()
    print("Бот запущен...")
    bot.polling(none_stop=True)
