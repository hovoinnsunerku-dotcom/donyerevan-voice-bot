import os
import json
from flask import Flask
from threading import Thread

from telegram import (
    Update,
    InlineQueryResultCachedVoice,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = 475863730

app = Flask(__name__)
voices = {}
pending = {}

@app.route("/")
def home():
    return "OK"

def load():
    global voices
    try:
        with open("voices.json","r",encoding="utf-8") as f:
            voices = json.load(f)
    except:
        voices = {}

def save():
    with open("voices.json","w",encoding="utf-8") as f:
        json.dump(voices,f,ensure_ascii=False,indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text(
            "🎙 Owner panel\n\n"
            "Ուղարկիր voice → հետո գրիր անունը.\n"
            "/manage - կառավարել\n"
            "/clear - ջնջել բոլորը"
        )
    else:
        await update.message.reply_text("🎙 Voice Bot")

async def receive_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    pending[update.effective_user.id] = update.message.voice.file_id
    await update.message.reply_text("✏️ Հիմա գրիր voice-ի անունը")

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    uid = update.effective_user.id
    if uid not in pending:
        return

    name = update.message.text
    voices[name] = pending.pop(uid)
    save()

    await update.message.reply_text(f"✅ Պահվեց՝ {name}")

async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not voices:
        await update.message.reply_text("Դատարկ է")
        return

    for name in voices:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✏️ Rename", callback_data=f"r|{name}"),
            InlineKeyboardButton("🗑 Delete", callback_data=f"d|{name}")
        ]])
        await update.message.reply_text(name, reply_markup=kb)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != OWNER_ID:
        return

    action, name = q.data.split("|",1)

    if action == "d":
        voices.pop(name,None)
        save()
        await q.edit_message_text(f"🗑 Ջնջվեց՝ {name}")

    if action == "r":
        context.user_data["rename"] = name
        await q.edit_message_text(f"Գրիր նոր անուն `{name}`-ի համար")

async def rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    old = context.user_data.get("rename")
    if not old:
        return

    new = update.message.text
    voices[new] = voices.pop(old)
    save()
    context.user_data.pop("rename")

    await update.message.reply_text(f"✅ Անունը փոխվեց՝ {new}")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    voices.clear()
    save()
    await update.message.reply_text("🧹 Բոլոր voice-երը ջնջվեցին")

async def inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = []
    for name,file_id in voices.items():
        results.append(
            InlineQueryResultCachedVoice(
                id=name,
                voice_file_id=file_id,
                title=name,
            )
        )

    await update.inline_query.answer(results, cache_time=0, is_personal=False)

def web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))

def main():
    load()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("manage", manage))
    application.add_handler(CommandHandler("clear", clear))

    application.add_handler(CallbackQueryHandler(buttons))

    application.add_handler(MessageHandler(filters.VOICE, receive_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rename), group=0)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text), group=1)

    application.add_handler(InlineQueryHandler(inline))

    Thread(target=web).start()
    application.run_polling()

if __name__ == "__main__":
    main()