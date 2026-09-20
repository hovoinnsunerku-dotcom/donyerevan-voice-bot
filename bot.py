import os
import json
from flask import Flask
from threading import Thread

from telegram import Update, InlineQueryResultCachedVoice
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = 475863730

app = Flask(__name__)

voices = {}


@app.route("/")
def home():
    return "Bot is running!"


def load_voices():
    global voices
    try:
        with open("voices.json", "r", encoding="utf-8") as f:
            voices = json.load(f)
    except FileNotFoundError:
        voices = {}


def save_voices():
    with open("voices.json", "w", encoding="utf-8") as f:
        json.dump(voices, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙 Բարև։\n\n"
        "Ես քո voice պահոցն եմ։\n"
        "Voice ավելացնելու համար պարզապես ուղարկիր ինձ voice։"
    )


async def receive_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Դու չես կարող voice ավելացնել։")
        return

    voice = update.message.voice

    if not voice:
        return

    name = f"Voice {len(voices) + 1}"

    voices[name] = voice.file_id
    save_voices()

    await update.message.reply_text(
        f"✅ Պահվեց՝ {name}\n\n"
        "Հիմա կարող ես ցանկացած chat-ում գրել՝\n"
        "@donyerevanvoice_bot"
    )


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = []

    for name, file_id in voices.items():
        results.append(
            InlineQueryResultCachedVoice(
                id=name,
                voice_file_id=file_id,
                title=name,
            )
        )

    await update.inline_query.answer(
        results,
        cache_time=0,
        is_personal=True,
    )


def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


def main():
    load_voices()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(
            filters.VOICE,
            receive_voice
        )
    )

    application.add_handler(
        InlineQueryHandler(inline_query)
    )

    Thread(target=run_web).start()

    application.run_polling()


if __name__ == "__main__":
    main()