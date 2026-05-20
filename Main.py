import os
import telebot
from flask import Flask, request
from openai import OpenAI

# ========================
# ENV VARIABLES
# ========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("Missing BOT_TOKEN or HF_TOKEN")

# ========================
# AI CLIENT (HuggingFace Router)
# ========================
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# ========================
# TELEGRAM BOT + FLASK
# ========================
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========================
# BOT COMMANDS
# ========================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Hello! I am your AI bot.\nSend me any message!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')

        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "user", "content": message.text}
            ],
        )

        reply = response.choices[0].message.content
        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

# ========================
# WEBHOOK ROUTES
# ========================
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Bot is running!", 200

# ========================
# SET WEBHOOK (IMPORTANT)
# ========================
bot.remove_webhook()

if RENDER_EXTERNAL_URL:
    webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    print("Webhook set:", webhook_url)
else:
    print("Running locally")
