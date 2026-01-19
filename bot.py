import os
import telebot
import requests
import time
from threading import Thread
from flask import Flask
from urllib.parse import quote

# Настройки
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
WEB_APP_URL = "https://armiy1706-ctrl.github.io/car-diagnostic-app/"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Станция техобслуживания онлайн!"

def ask_ai(text):
    # Используем проверенный роутер и модель Gemma 2
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Новая мощная инструкция для «народного» ответа
    payload = {
        "model": "google/gemma-2-2b-it",
        "messages": [
            {
                "role": "system", 
                "content": "Ты — эксперт с DRIVE2. Ты перечитал тысячи форумов. Твоя задача: дать краткий, дельный совет по ремонту авто простым человеческим языком. Не используй заумных терминов. Пиши как опытный сосед по гаражу: четко, по делу и дружелюбно. Обязательно на русском языке."
            },
            {
                "role": "user", 
                "content": f"Слушай, такая проблема: {text}. Что это может быть и что проверить в первую очередь? Ответь кратко в 3-4 предложениях."
            }
        ],
        "max_tokens": 500,
        "temperature": 0.8 # Немного творчества для «живого» общения
    }
    
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=35)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
        else:
            # Если ошибка сервера, пробуем вернуть хотя бы общие рекомендации
            print(f"Ошибка ИИ: {res.text}")
            return "Похоже, случай непростой. Давай глянем, что люди пишут по этому поводу на форумах."
    except Exception as e:
        print(f"Ошибка связи: {e}")
        return "Связь в гараже барахлит, но я подготовил для тебя подборку с DRIVE2."

@bot.message_handler(content_types=['web_app_data'])
def get_data(message):
    problem = message.web_app_data.data
    msg = bot.send_message(message.chat.id, "🛠 Вспоминаю похожие случаи на форумах...")
    
    # Получаем ответ ИИ
    answer = ask_ai(problem)
    
    # Формируем прямую ссылку на поиск внутри Drive2
    search_query = quote(problem)
    drive2_url = f"https://www.drive2.ru/search/?text={search_query}"
    
    # Красиво оформляем ответ
    final_text = (
        f"<b>Совет мастера:</b>\n\n"
        f"{answer}\n\n"
        f"—————\n"
        f"👉 Подробные отчеты по твоей теме ищи здесь:"
    )
    
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔍 Поиск на DRIVE2.RU", url=drive2_url))
    
    bot.edit_message_text(
        chat_id=message.chat.id, 
        message_id=msg.message_id, 
        text=final_text, 
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.message_handler(commands=['start'])
def start(message):
    from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🚗 Начать диагностику", web_app=WebAppInfo(url=WEB_APP_URL)))
    bot.send_message(message.chat.id, "Привет! Я твой карманный механик. Жми кнопку, описывай проблему — а я подскажу, куда копать.", reply_markup=markup)

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=run_flask).start()
    print("🚀 Поехали! Бот запущен.")
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            time.sleep(5)
