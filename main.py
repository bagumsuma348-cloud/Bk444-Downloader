import os
import base64
import threading
import time
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- CONFIGURATION & ENV ---
# Securely fetch token from Render Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN)

# --- DECODING SECURED LINKS ---
def get_secure_link(encoded_str):
    # Remove any accidental whitespaces from the encoded strings
    clean_str = encoded_str.replace(" ", "").replace("\n", "")
    return base64.b64decode(clean_str).decode("utf-8")

ENCODED_YOUTUBE = "aHR0cHM6Ly95b3V0dWJlLmNvbS9AYmxhY2trbm93bGVkZ2VfMTkwP3NpPTIFd2tNUEdiLWxlUnpaZHE="
ENCODED_SUPPORT = "aHR0cHM6Ly90Lm1lL0JMQUNLX0tub3dsZWRnZV8xOTA="

YOUTUBE_URL = get_secure_link(ENCODED_YOUTUBE)
SUPPORT_URL = get_secure_link(ENCODED_SUPPORT)

# --- FLASK SERVER FOR 24/7 UPTIME ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and kicking!", 200

def run_flask():
    # Render requires port 10000 by default or via PORT env variable
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- TELEGRAM BOT LOGIC ---

# 1. Start Command with Premium UI
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "✨ *Welcome to the Premium Video Downloader Bot* ✨\n\n"
        "Brought to you exclusively by *@bemo100*.\n\n"
        "⚡ Send me any **Instagram Reel** or **Facebook Video** link, and I will fetch it for you instantly!"
    )
    
    # Inline Keyboard Branding
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 SUBSCRIBE CHANNEL", url=YOUTUBE_URL))
    markup.row(InlineKeyboardButton("📚 ALL TUTORIALS", url=YOUTUBE_URL))
    markup.row(InlineKeyboardButton("👑 CONTACT OWNER", url=SUPPORT_URL))
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# 2. Downloader Core
@bot.message_handler(func=lambda message: True)
def handle_video_download(message):
    url = message.text.strip()
    
    # Simple validation for Instagram and Facebook links
    if not ("instagram.com" in url or "facebook.com" in url or "fb.watch" in url):
        return # Ignore non-target links silently or add an error message if preferred

    # Send initial tracking message
    status_msg = bot.reply_to(message, "⏳ Analyzing...")
    
    # Unique filename based on timestamp to avoid conflicts
    output_filename = f"video_{int(time.time())}.mp4"
    
    # Setup yt-dlp options
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        # Edit to Downloading state
        bot.edit_message_text("📥 Downloading (50%)...", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Check if file was actually written
        if os.path.exists(output_filename):
            # Edit to Uploading state
            bot.edit_message_text("📤 Uploading (100%)...", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
            
            # Send the video file
            with open(output_filename, 'rb') as video:
                caption_text = "✅ Downloaded Successfully!\n\nPower by: @bemo100"
                bot.send_video(
                    chat_id=message.chat.id, 
                    video=video, 
                    caption=caption_text, 
                    reply_to_message_id=message.message_id
                )
            
            # Delete tracking status message to keep chat clean
            bot.delete_message(chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        else:
            bot.edit_message_text("❌ Failed to process video download.", chat_id=status_msg.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text("❌ An error occurred while processing your link. Please ensure it is a public video.", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        
    finally:
        # 6. CLEANUP: Always remove file from server if it exists
        if os.path.exists(output_filename):
            try:
                os.remove(output_filename)
            except Exception as e:
                print(f"Cleanup error: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Start the Flask web server thread for Render 24/7 uptime
    keep_alive()
    
    print("Bot is starting polling loop...")
    # Start the bot polling
    bot.infinity_polling()
