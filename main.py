
import os
import telebot
import requests
import openai
from pydub import AudioSegment

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)

if not os.path.exists("temp"):
    os.makedirs("temp")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
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

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    reply = response['choices'][0]['message']['content']
    bot.send_message(message.chat.id, reply)

bot.polling()
