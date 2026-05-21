import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Load Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
# Render automatically sets this environment variable for your web service
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL") 

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("Missing BOT_TOKEN or HF_TOKEN environment variables.")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI Client (pointing to Hugging Face router)
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 4. Define Bot Message Handler
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # Show "typing..." status in Telegram
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call the Hugging Face model via OpenAI SDK
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Flash:fireworks-ai",
            messages=[
                {"role": "system", "content": "You are a helpful and conversational assistant."},
                {"role": "user", "content": message.text},
            ],
        )
        
        # Get the response text and send it back to the user
        reply_text = response.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I encountered an error while processing your request.")

# 5. Define Flask Routes for Webhook
@app.route('/', methods=['GET'])
def index():
    return "Telegram Bot is running!", 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    # Receive updates from Telegram and pass them to the bot
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

# 6. Set Webhook on Startup
if RENDER_EXTERNAL_URL:
    bot.remove_webhook()
    # Set the webhook URL to your Render app URL + the bot token path
    bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    # Render assigns a dynamic PORT via environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
