import telebot
from telebot import types
import yt_dlp
import os
import time
import base64
import logging
from flask import Flask, request
import threading

# ========================= CONFIGURATION =========================
BOT_TOKEN = "8916971089:AAGdbevtF44LK5WYgDZWo_yms00aPHX_b2w"   # ←←← YE ZARUR CHANGE KARO

# Branded links (base64 hidden)
YOUTUBE_CHANNEL = base64.b64decode("aHR0cHM6Ly93d3cueW91dHViZS5jb20vQEJrTWlhNDQ0=").decode('utf-8')
SUPPORT_CHANNEL = base64.b64decode("aHR0cHM6Ly90Lm1lL0JLNDQ0X09mZmljaWFs=").decode('utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========================= FLASK WEBHOOK =========================
@app.route('/')
def index():
    return "✅ @Bk_Mia444_BOT Video Downloader Bot is LIVE 24/7!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

# ========================= BOT COMMANDS =========================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 <b>Welcome to BK444_Official Video Downloader Bot!</b>\n\n"
        "🚀 Send me any Instagram Reel, Facebook Video, YouTube, TikTok ya koi bhi supported link.\n"
        "Main turant download kar ke bhej dunga.\n\n"
        "💡 High Quality • yt-dlp Powered\n"
        "Made with ❤️ for @Bk_Mia444_BOT"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 SUBSCRIBE CHANNEL", url=YOUTUBE_CHANNEL))
    markup.add(types.InlineKeyboardButton("📂 ALL TUTORIALS", url=SUPPORT_CHANNEL))
    markup.add(types.InlineKeyboardButton("👨‍💻 CONTACT OWNER", url=SUPPORT_CHANNEL))

    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_video_link(message):
    url = message.text.strip()
    if not url.startswith(('http://', 'https://')):
        bot.reply_to(message, "❌ Please send a valid video URL")
        return

    status_msg = bot.reply_to(message, "🔍 Analyzing link...")

    try:
        # Enhanced yt-dlp options for better YouTube + Instagram support
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',  # Better quality selector
            'outtmpl': 'video_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'prefer_free_formats': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            # Additional options for Instagram & YouTube
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            },
            'extractor_args': {
                'youtube': {'player_client': ['ios', 'web']},  # Helps with YouTube
                'instagram': {'player_client': ['ios']},
            },
            'retries': 3,
            'fragment_retries': 3,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)

            # Show progress
            bot.edit_message_text(
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id,
                text="⚡ Downloading... (0%)"
            )

            ydl.download([url])

        bot.edit_message_text(
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            text="📤 Uploading to Telegram (100%)..."
        )

        with open(filename, 'rb') as f:
            bot.send_video(
                message.chat.id,
                f,
                caption="✅ Downloaded Successfully! \n\n🔥 Powered by: @Bk666767786",
                supports_streaming=True
            )

        if os.path.exists(filename):
            os.remove(filename)

        bot.edit_message_text(
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            text="✅ Video sent successfully!"
        )

    except Exception as e:
        logger.error(str(e))
        error_msg = str(e)[:150]
        try:
            bot.edit_message_text(
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id,
                text=f"❌ Error: {error_msg}\n\nTry again or check link."
            )
        except:
            pass

# ========================= START FLASK + WEBHOOK =========================
if __name__ == "__main__":
    # Auto set webhook (Render ke liye perfect)
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if hostname:
        webhook_url = f"https://{hostname}/{BOT_TOKEN}"
        try:
            bot.set_webhook(url=webhook_url)
            logger.info(f"✅ Webhook successfully set: {webhook_url}")
        except Exception as e:
            logger.error(f"Webhook set failed: {e}")

    # Run Flask (Render iska port expect karta hai)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
