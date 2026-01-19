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

from urllib.parse import quote # Добавь этот импорт в самый верх!

def ask_ai(text):
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # МЕНЯЕМ ИНСТРУКЦИЮ: теперь он эксперт с Drive2
    payload = {
        "model": "google/gemma-2-2b-it",
        "messages": [
            {
                "role": "user", 
                "content": f"Ты — легендарный мастер с форума DRIVE2. К тебе пришел новичок. У него проблема: '{text}'. Ответь ему по-простому, по-пацански, дай 2-3 практических совета, что проверить в первую очередь. Используй человеческий язык, а не техническую документацию. Отвечай кратко."
            }
        ],
        "max_tokens": 400
    }
    
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
        return "🛠 Мастер на перекуре. Попробуй позже."
    except:
        return "❌ Не удалось связаться с гаражом."

@bot.message_handler(content_types=['web_app_data'])
def get_data(message):
    problem = message.web_app_data.data
    msg = bot.send_message(message.chat.id, "🚗 Мастер изучает твой случай...")
    
    # Получаем ответ от ИИ
    answer = ask_ai(problem)
    
    # Создаем ссылку для поиска на Drive2
    # Она будет искать именно на сайте drive2.ru через Google
    search_query = quote(f"site:drive2.ru {problem}")
    drive2_url = f"https://www.google.com/search?q={search_query}"
    
    # Добавляем кнопку со ссылкой под ответом
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📖 Читать похожие случаи на DRIVE2", url=drive2_url))
    
    bot.edit_message_text(
        chat_id=message.chat.id, 
        message_id=msg.message_id, 
        text=f"{answer}\n\n---", 
        reply_markup=markup
    )

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
