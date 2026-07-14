import os
import telebot
from flask import Flask, request

# جلب توكن البوت من متغيرات البيئة في فيرسل
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# استقبال الطلبات من تليجرام (Webhook)
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Error', 403

# منطق الردود داخل القنوات (channel_post_handler)
@bot.channel_post_handler(func=lambda message: True)
def handle_channel_post(message):
    # التأكد من وجود نص في المنشور
    if not message.text:
        return

    text = message.text

    # --- أمثلة للردود التلقائية ---
    if "السلام عليكم" in text:
        bot.reply_to(message, "وعليكم السلام ورحمة الله وبركاته")
        
    elif "رابط" in text:
        bot.reply_to(message, "تفضل، هذا هو الرابط: https://example.com")
        
    elif "القوانين" in text:
        # إرسال رسالة للقناة بدون الرد على المنشور نفسه
        bot.send_message(message.chat.id, "قوانين القناة:\n1. عدم السب\n2. احترام الجميع")

# ضروري لعمل Flask على Vercel
if __name__ == '__main__':
    app.run(debug=True)
