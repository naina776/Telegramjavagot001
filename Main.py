import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI Client for Hugging Face Router
import os

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ.get("HF_TOKEN")  # 
)

)

# 4. Telegram Bot Handlers
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am a DeepSeek AI bot. Send me a message and I'll reply.")

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # Show "typing" status in Telegram
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call the Hugging Face API
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
        )
        
        # Extract response and send it back to the user
        reply_text = chat_completion.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        bot.reply_to(message, f"Oops! An error occurred: {str(e)}")

# 5. Flask Routes for Telegram Webhook
@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    # Receive updates from Telegram and pass to the bot
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Bot is running perfectly!", 200

# 6. Webhook Setup
if __name__ == "__main__":
    # Remove existing webhook
    bot.remove_webhook()
    
    # Render automatically sets RENDER_EXTERNAL_URL for web services
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        # Set the new webhook to the Render URL
        bot.set_webhook(url=f"{render_url}/{BOT_TOKEN}")
    
    # Render dynamically assigns a port using the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
