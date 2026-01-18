import os
import telebot
import requests
from threading import Thread
from flask import Flask

# Теперь бот берет токены из настроек Render, а не из текста кода
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
# Ссылку на Mini App можно оставить текстом, это не секрет
WEB_APP_URL = "https://armiy1706-ctrl.github.io/car-diagnostic-app/"

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
    msg = bot.send_message(message.chat.id, "🚗 Мастер изучает проблему...")
    
    # Прямая ссылка на модель через новый роутер
    api_url = "https://router.huggingface.co/hf-inference/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Короткий и понятный запрос для ИИ
    payload = {
        "inputs": f"Ты — опытный автомеханик. Кратко ответь на русском, в чем может быть причина: {user_text}",
        "parameters": {"max_new_tokens": 200, "return_full_text": False}
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=25)
        
        # Если в логах Render увидишь это число, поймем статус (200 - ок, 401 - плохой токен, 503 - ИИ спит)
        print(f"Статус ответа ИИ: {response.status_code}") 
        
        response_data = response.json()

        if response.status_code == 200 and isinstance(response_data, list):
            result = response_data[0].get('generated_text', 'Не удалось разобрать ответ.')
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=result)
        elif "estimated_time" in str(response_data):
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="⚠️ ИИ просыпается, подожди 30 секунд и нажми еще раз.")
        else:
            print(f"Ошибка от ИИ: {response_data}")
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="ИИ временно занят. Попробуй через минуту.")
            
    except Exception as e:
        print(f"Ошибка в блоке запроса: {e}")
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="Сбой связи. Проверь настройки токена.")

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
