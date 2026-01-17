import telebot
import requests
from telebot import types

# 1. Твои данные
TELEGRAM_TOKEN = '8572493279:AAEe4mmkbc0vTxLp3St8yYkLHm8TyuJrD5M'
HF_TOKEN = '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'
# Ссылка на модель (Llama 3 от Meta, одна из лучших)
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = telebot.TeleBot(TELEGRAM_TOKEN)

SYSTEM_PROMPT = "Ты — эксперт-автомеханик. Дай краткий диагноз, план проверки и список инструментов. Если поломка опасна — напиши ОБАСНО ДЛЯ ЕЗДЫ. Отвечай строго на русском языке."

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo("https://твой-логин.github.io/automech-ai/")
    button = types.InlineKeyboardButton(text="🚗 Запустить Mini App", web_app=web_app)
    markup.add(button)
    bot.send_message(message.chat.id, "Привет! Я твой ИИ-механик. Опиши проблему с машиной здесь или запусти приложение.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    msg = bot.send_message(message.chat.id, "⏳ Мастер изучает проблему...")
    
    # Формируем запрос для Llama 3
    prompt = f"<|system|>\n{SYSTEM_PROMPT}</s>\n<|user|>\n{message.text}</s>\n<|assistant|>\n"
    
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 500, "return_full_text": False}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        output = response.json()
        
        # Hugging Face возвращает список, достаем текст
        result_text = output[0]['generated_text']
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=result_text)
    except Exception as e:
        print(e)
        bot.edit_message_text("Механик сейчас занят, попробуй через минуту.", message.chat.id, msg.message_id)

bot.polling(none_stop=True)
