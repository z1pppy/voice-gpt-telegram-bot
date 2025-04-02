import os
import telebot
import requests
import openai
from pydub import AudioSegment
from collections import defaultdict

# Токены
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Папка для временных файлов
if not os.path.exists("temp"):
    os.makedirs("temp")

# Храним историю общения по user_id
chat_histories = defaultdict(list)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.from_user.id

    file_info = bot.get_file(message.voice.file_id)
    file = requests.get(f'https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}')
    
    ogg_path = f'temp/{message.message_id}.ogg'
    mp3_path = f'temp/{message.message_id}.mp3'
    
    with open(ogg_path, 'wb') as f:
        f.write(file.content)
    
    sound = AudioSegment.from_ogg(ogg_path)
    sound.export(mp3_path, format="mp3")

    with open(mp3_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)

    prompt = transcript["text"]
    bot.send_message(message.chat.id, f"Ты сказал: {prompt}\nДумаю...")

    # Добавляем в историю
    chat_histories[user_id].append({"role": "user", "content": prompt})

    # Ограничим историю последними 10 сообщениями (по желанию)
    chat_histories[user_id] = chat_histories[user_id][-10:]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=chat_histories[user_id],
        temperature=0.7
    )

    reply = response['choices'][0]['message']['content']

    # Добавляем ответ ассистента в историю
    chat_histories[user_id].append({"role": "assistant", "content": reply})

    bot.send_message(message.chat.id, reply)

bot.polling()
