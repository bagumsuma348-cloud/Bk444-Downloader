import telebot
from telebot import types
import yt_dlp
import os
import logging
from flask import Flask, request

# ========================= CONFIGURATION =========================
BOT_TOKEN = "8916971089:AAGdbevtF44LK5WYgDZWo_yms00aPHX_b2w"

YOUTUBE_CHANNEL = "https://www.youtube.com/@Bk_Mia444"
SUPPORT_CHANNEL = "https://youtube.com/shorts/0vG9W7j17k0?si=DRMzAGsgShed5kIH"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Bot is LIVE 24/7!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

# ========================= PROGRESS =========================
def update_progress(d, status_msg):
    if d['status'] == 'downloading':
        try:
            percent = d.get('_percent_str', '0%')
            bot.edit_message_text(chat_id=status_msg.chat.id, message_id=status_msg.message_id, text=f"⚡ Downloading... {percent}")
        except:
            pass

# ========================= START =========================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = "😱 <b>BK444 Video Downloader Bot</b>\n\nSend any supported link..."
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 SUBSCRIBE", url=YOUTUBE_CHANNEL))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ========================= MAIN =========================
@bot.message_handler(func=lambda m: True)
def handle_video_link(message):
    url = message.text.strip()
    if not url.startswith(('http', 'https')):
        bot.reply_to(message, "❌ Valid URL দাও")
        return

    status_msg = bot.reply_to(message, "🔍 Processing...")

    try:
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'outtmpl': 'video_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36'},
            
            'extractor_args': {
                'youtube': {'player_client': ['ios', 'android', 'web']},
                'instagram': {'player_client': ['ios', 'android']},
            },
            
            'retries': 10,
            'fragment_retries': 10,
            'progress_hooks': [lambda d: update_progress(d, status_msg)],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)

            bot.edit_message_text(chat_id=status_msg.chat.id, message_id=status_msg.message_id, text="⚡ Downloading...")

            ydl.download([url])

        with open(filename, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="✅ Done! @Bk_Mia444_BOT", supports_streaming=True)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        error = str(e)[:300]
        bot.edit_message_text(chat_id=status_msg.chat.id, message_id=status_msg.message_id, text=f"❌ Error:\n{error}")

# ========================= RUN =========================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if hostname:
        bot.set_webhook(url=f"https://{hostname}/{BOT_TOKEN}")
    app.run(host='0.0.0.0', port=port)
