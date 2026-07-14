import os
import telebot
from flask import Flask, request

# توكن البوت الخاص بك
TOKEN = os.environ.get('BOT_TOKEN', '8024861151:AAFMtkIuF-yABGkkhzNogR5WcQ8ofHscs8k')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# كلمة سر لوحة التحكم الافتراضية التي اخترتها لك
ADMIN_PASSWORD = "Hassany_66"

# تخزين مؤقت لإدارة الجلسات والبيانات
# (تنبيه: منصة Vercel تعمل بنظام Serverless، مما يعني أن الذاكرة قد يتم تصفيرها عند خمول البوت. 
# لحل هذه المشكلة بشكل نهائي، يفضل مستقبلاً ربط البوت بقاعدة بيانات سحابية بسيطة)
admins = set()
user_steps = {}  # {chat_id: step}
temp_reply_data = {}  # {chat_id: {keyword: ..., partial: ...}}

# قائمة الردود (مع رد افتراضي كمثال)
replies = {
    "ايفون": {"response": "الآيفون جهاز قوي وممتاز جداً!", "partial": True}
}

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Error', 403

# إنشاء لوحة التحكم (أزرار مدمجة)
def get_admin_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    btn_add = telebot.types.InlineKeyboardButton("➕ أضف رد جديد", callback_data="add_reply")
    btn_list = telebot.types.InlineKeyboardButton("📋 عرض الردود الحالية", callback_data="list_replies")
    markup.row(btn_add)
    markup.row(btn_list)
    return markup

# معالجة الرسائل الخاصة (المشرفين وإدخال كلمة السر)
@bot.message_handler(chat_types=['private'])
def handle_private_messages(message):
    chat_id = message.chat.id
    text = message.text

    if text == '/start':
        if chat_id in admins:
            bot.send_message(chat_id, "✨ أهلاً بك مجدداً في لوحة تحكم البوت!", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(chat_id, "🔒 مرحباً! يرجى إدخال كلمة سر الوصول للوحة التحكم للبدء:")
            user_steps[chat_id] = "waiting_password"
        return

    # التحقق من كلمة السر
    if user_steps.get(chat_id) == "waiting_password":
        if text == ADMIN_PASSWORD:
            admins.add(chat_id)
            user_steps[chat_id] = None
            bot.send_message(chat_id, "✅ تم التحقق بنجاح! مرحباً بك في لوحة التحكم.", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(chat_id, "❌ كلمة السر خاطئة! يرجى المحاولة مجدداً:")
        return

    # منطق إضافة رد جديد (للمشرفين فقط)
    if chat_id in admins:
        current_step = user_steps.get(chat_id)
        
        # خطوة استقبال الكلمة المفتاحية
        if current_step == "waiting_keyword":
            temp_reply_data[chat_id] = {"keyword": text.strip()}
            user_steps[chat_id] = "waiting_match_type"
            
            # سؤال المشرف عن نوع التطابق (مدمج أو كامل)
            markup = telebot.types.InlineKeyboardMarkup()
            btn_partial = telebot.types.InlineKeyboardButton("نعم (مدمجة ضمن الكلام)", callback_data="match_partial")
            btn_exact = telebot.types.InlineKeyboardButton("لا (تطابق تام فقط)", callback_data="match_exact")
            markup.row(btn_partial)
            markup.row(btn_exact)
            
            bot.send_message(
                chat_id, 
                f"لقد اخترت الكلمة المفتاحية: *{text}*\n\n"
                f"هل تريد أن يرسل البوت الرد إذا كانت الكلمة مدموجة داخل الجملة؟\n"
                f"*(مثال: إذا كتب شخص 'لدي ايفون ممتاز' يشتغل الرد)*", 
                parse_mode="Markdown", 
                reply_markup=markup
            )
            return
            
        # خطوة استقبال نص الرد
        elif current_step == "waiting_response":
            keyword = temp_reply_data[chat_id]["keyword"]
            partial = temp_reply_data[chat_id]["partial"]
            
            # حفظ الرد في القائمة
            replies[keyword] = {
                "response": text,
                "partial": partial
            }
            
            match_type_str = "مدمجة (ضمن الكلام)" if partial else "تطابق تام (الكلمة فقط)"
            bot.send_message(
                chat_id, 
                f"✅ تم حفظ الرد بنجاح وبدأ العمل به!\n\n"
                f"🔹 *الكلمة المطلوب الرد عليها:* {keyword}\n"
                f"🔹 *نوع التطابق:* {match_type_str}\n"
                f"🔹 *نص الرد:* {text}", 
                parse_mode="Markdown", 
                reply_markup=get_admin_keyboard()
            )
            
            # تصفير الخطوات للتجهيز لعملية أخرى
            user_steps[chat_id] = None
            temp_reply_data.pop(chat_id, None)
            return

# معالجة الضغط على الأزرار التفاعلية
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    
    if chat_id not in admins:
        bot.answer_callback_query(call.id, "❌ يرجى تسجيل الدخول أولاً بإرسال كلمة السر.", show_alert=True)
        return

    # عند الضغط على "أضف رد جديد"
    if call.data == "add_reply":
        user_steps[chat_id] = "waiting_keyword"
        bot.edit_message_text("📥 حسناً، أرسل لي الكلمة المفتاحية المطلوبة (مثل: ايفون):", chat_id, call.message.message_id)
        
    # عند الضغط على "عرض الردود الحالية"
    elif call.data == "list_replies":
        if not replies:
            bot.send_message(chat_id, "⚠️ لا توجد ردود مضافة حالياً في القائمة.")
            return
        
        msg = "📋 *قائمة الردود الحالية المفعلة:*\n\n"
        for kw, data in replies.items():
            m_type = "مدمجة" if data['partial'] else "تطابق تام"
            msg += f"• *{kw}* ({m_type}) 👈 {data['response']}\n"
            
        bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=get_admin_keyboard())
        
    # تحديد نوع التطابق: مدمج
    elif call.data == "match_partial":
        temp_reply_data[chat_id]["partial"] = True
        user_steps[chat_id] = "waiting_response"
        bot.edit_message_text("👍 تم اختيار تطابق مدمج.\n\nالآن أرسل لي الرد الذي تود أن يرسله البوت (مثل: ايفون جهاز قوي):", chat_id, call.message.message_id)
        
    # تحديد نوع التطابق: تام
    elif call.data == "match_exact":
        temp_reply_data[chat_id]["partial"] = False
        user_steps[chat_id] = "waiting_response"
        bot.edit_message_text("👍 تم اختيار تطابق تام.\n\nالآن أرسل لي الرد الذي تود أن يرسله البوت (مثل: ايفون جهاز قوي):", chat_id, call.message.message_id)

# فحص المنشورات والرد التلقائي داخل القنوات
@bot.channel_post_handler(func=lambda message: True)
def handle_channel_post(message):
    if not message.text:
        return

    text = message.text.strip()

    # التحقق من الكلمات المفتاحية المخزنة
    for keyword, data in replies.items():
        if data["partial"]:
            # إذا كانت مدمجة في أي مكان من النص
            if keyword in text:
                bot.reply_to(message, data["response"])
                break
        else:
            # إذا كانت مطابقة تماماً للرسالة
            if text == keyword:
                bot.reply_to(message, data["response"])
                break

if __name__ == '__main__':
    app.run(debug=True)
