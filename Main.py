import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
# Render automatically provides this variable, so we know our App's URL!
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("BOT_TOKEN or HF_TOKEN is missing in environment variables.")

# 2. Initialize OpenAI Client pointing to Hugging Face Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 3. Initialize Telegram Bot & Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- TELEGRAM BOT LOGIC ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am an AI chatbot. Send me a message and I will reply!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Show "typing..." status in Telegram
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call Hugging Face Router API via OpenAI library
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                },
            ],
        )
        
        # Extract the AI's reply and send it back to the user
        reply = chat_completion.choices[0].message.content
        bot.reply_to(message, reply)
        
    except Exception as e:
        bot.reply_to(message, f"Sorry, an error occurred: {str(e)}")


# --- FLASK WEBHOOK LOGIC ---

# Telegram will send new messages to this route securely
@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# Simple health check route so Render knows the app is alive
@app.route("/")
def index():
    return "Bot is running and waiting for messages!", 200


if __name__ == "__main__":
    # Remove any existing webhooks
    bot.remove_webhook()
    
    # Automatically set the webhook if running on Render
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        print(f"Webhook securely set to: {webhook_url}")
    else:
        print("Running locally. Please use polling or set up ngrok.")
        
    # Render assigns a dynamic port, defaulting to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Start the Flask server
    app.run(host="0.0.0.0", port=port)
