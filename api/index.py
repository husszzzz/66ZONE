import os
import telebot
from flask import Flask, request

# توكن البوت الخاص بك
TOKEN = os.environ.get('BOT_TOKEN', '8024861151:AAFMtkIuF-yABGkkhzNogR5WcQ8ofHscs8k')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# كلمة سر لوحة التحكم
ADMIN_PASSWORD = "Hassany_66"

admins = set()
user_steps = {}  
temp_reply_data = {}  

# قائمة الردود الافتراضية
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

def get_admin_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    btn_add = telebot.types.InlineKeyboardButton("➕ أضف رد جديد", callback_data="add_reply")
    btn_list = telebot.types.InlineKeyboardButton("📋 عرض الردود الحالية", callback_data="list_replies")
    btn_edit_del = telebot.types.InlineKeyboardButton("✏️ تحرير/حذف رد", callback_data="edit_delete_reply")
    markup.row(btn_add)
    markup.row(btn_list)
    markup.row(btn_edit_del)
    return markup

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

    if user_steps.get(chat_id) == "waiting_password":
        if text == ADMIN_PASSWORD:
            admins.add(chat_id)
            user_steps[chat_id] = None
            bot.send_message(chat_id, "✅ تم التحقق بنجاح! مرحباً بك في لوحة التحكم.", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(chat_id, "❌ كلمة السر خاطئة! يرجى المحاولة مجدداً:")
        return

    if chat_id in admins:
        current_step = user_steps.get(chat_id)
        
        # --- إضافة رد ---
        if current_step == "waiting_keyword":
            temp_reply_data[chat_id] = {"keyword": text.strip()}
            user_steps[chat_id] = "waiting_match_type"
            
            markup = telebot.types.InlineKeyboardMarkup()
            btn_partial = telebot.types.InlineKeyboardButton("نعم (مدمجة ضمن الكلام)", callback_data="match_partial")
            btn_exact = telebot.types.InlineKeyboardButton("لا (تطابق تام فقط)", callback_data="match_exact")
            markup.row(btn_partial)
            markup.row(btn_exact)
            
            bot.send_message(chat_id, f"لقد اخترت الكلمة المفتاحية: *{text}*\n\nهل تريد أن يرسل البوت الرد إذا كانت الكلمة مدموجة داخل الجملة؟", parse_mode="Markdown", reply_markup=markup)
            return
            
        elif current_step == "waiting_response":
            keyword = temp_reply_data[chat_id]["keyword"]
            partial = temp_reply_data[chat_id]["partial"]
            
            replies[keyword] = {"response": text, "partial": partial}
            match_type_str = "مدمجة" if partial else "تطابق تام"
            
            bot.send_message(chat_id, f"✅ تم حفظ الرد بنجاح!\n🔹 *الكلمة:* {keyword}\n🔹 *التطابق:* {match_type_str}\n🔹 *الرد:* {text}", parse_mode="Markdown", reply_markup=get_admin_keyboard())
            user_steps[chat_id] = None
            return

        # --- تحرير / حذف رد ---
        elif current_step == "waiting_keyword_to_edit":
            keyword = text.strip()
            if keyword in replies:
                temp_reply_data[chat_id] = {"keyword": keyword}
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row(
                    telebot.types.InlineKeyboardButton("🗑️ حذف الرد", callback_data="action_delete"),
                    telebot.types.InlineKeyboardButton("📝 تعديل النص", callback_data="action_edit")
                )
                bot.send_message(chat_id, f"الكلمة المفتاحية: *{keyword}*\nماذا تريد أن تفعل؟", parse_mode="Markdown", reply_markup=markup)
                user_steps[chat_id] = None
            else:
                bot.send_message(chat_id, "❌ هذه الكلمة غير موجودة في الردود. استخدم 'عرض الردود' للتأكد من الإملاء:", reply_markup=get_admin_keyboard())
                user_steps[chat_id] = None
            return

        elif current_step == "waiting_new_response":
            keyword = temp_reply_data[chat_id]["keyword"]
            replies[keyword]["response"] = text
            bot.send_message(chat_id, f"✅ تم تحديث الرد بنجاح!\nالرد الجديد لـ ({keyword}) هو:\n{text}", reply_markup=get_admin_keyboard())
            user_steps[chat_id] = None
            return


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    
    if chat_id not in admins:
        bot.answer_callback_query(call.id, "❌ يرجى تسجيل الدخول أولاً.", show_alert=True)
        return

    if call.data == "add_reply":
        user_steps[chat_id] = "waiting_keyword"
        bot.edit_message_text("📥 أرسل لي الكلمة المفتاحية المطلوبة:", chat_id, call.message.message_id)
        
    elif call.data == "list_replies":
        if not replies:
            bot.send_message(chat_id, "⚠️ لا توجد ردود حالياً.")
            return
        msg = "📋 *الردود الحالية:*\n\n"
        for kw, data in replies.items():
            m_type = "مدمجة" if data['partial'] else "تطابق تام"
            msg += f"• *{kw}* ({m_type}) 👈 {data['response']}\n"
        bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=get_admin_keyboard())
        
    elif call.data == "edit_delete_reply":
        user_steps[chat_id] = "waiting_keyword_to_edit"
        bot.edit_message_text("✏️ أرسل الكلمة المفتاحية للرد الذي تريد تعديله أو حذفه (كما هي مكتوبة بالضبط):", chat_id, call.message.message_id)

    elif call.data == "action_delete":
        keyword = temp_reply_data.get(chat_id, {}).get("keyword")
        if keyword and keyword in replies:
            del replies[keyword]
            bot.edit_message_text(f"✅ تم حذف الرد الخاص بكلمة ({keyword}) بنجاح.", chat_id, call.message.message_id)
            bot.send_message(chat_id, "اختر إجراء آخر:", reply_markup=get_admin_keyboard())
            
    elif call.data == "action_edit":
        keyword = temp_reply_data.get(chat_id, {}).get("keyword")
        if keyword:
            user_steps[chat_id] = "waiting_new_response"
            bot.edit_message_text(f"📝 أرسل النص الجديد لرد ({keyword}):", chat_id, call.message.message_id)

    elif call.data == "match_partial":
        temp_reply_data[chat_id]["partial"] = True
        user_steps[chat_id] = "waiting_response"
        bot.edit_message_text("👍 مدمج. أرسل نص الرد:", chat_id, call.message.message_id)
        
    elif call.data == "match_exact":
        temp_reply_data[chat_id]["partial"] = False
        user_steps[chat_id] = "waiting_response"
        bot.edit_message_text("👍 تطابق تام. أرسل نص الرد:", chat_id, call.message.message_id)


# فحص المنشورات في الكروبات حصراً
@bot.message_handler(chat_types=['group', 'supergroup'])
def group_post(message):
    if not message.text:
        return
    text = message.text.strip()
    for keyword, data in replies.items():
        if data["partial"]:
            if keyword in text:
                bot.reply_to(message, data["response"])
                break
        else:
            if text == keyword:
                bot.reply_to(message, data["response"])
                break

if __name__ == '__main__':
    app.run(debug=True)
