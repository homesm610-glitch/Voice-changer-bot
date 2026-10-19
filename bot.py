import os, subprocess
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import librosa
import soundfile as sf

TOKEN = "8633336282:AAFMyvBtppuz--k7rfzz7DJdu2g5e9jz7sE"

VOICES = {
    "girl_soft": {"pitch": 4, "speed": 0.98, "label": "🇮🇳 Hindi Girl Soft"},
    "girl_cute": {"pitch": 6, "speed": 1.0, "label": "🥰 Cute Hinglish Girl"},
    "girl_baddie": {"pitch": 3.5, "speed": 1.05, "label": "😈 Baddie Girl"},
    "boy_hindi": {"pitch": -2, "speed": 1.0, "label": "👦 Hindi Boy"},
    "boy_deep": {"pitch": -5, "speed": 0.95, "label": "🎙️ Deep Boy Voice"},
}

def run(cmd):
    subprocess.run(cmd, shell=True)

def change_voice(input_path, output_path, pitch, speed):
    y, sr = librosa.load(input_path, sr=16000)
    y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch)
    y = librosa.effects.time_stretch(y, rate=speed)
    sf.write(output_path, y, sr)

def get_kb():
    buttons = []
    for key, data in VOICES.items():
        buttons.append([InlineKeyboardButton(data["label"], callback_data=key)])
    return InlineKeyboardMarkup(buttons)

async def start(update, context):
    context.user_data["voice"] = "girl_cute"
    await update.message.reply_text("🎤 Bot Ready! Choose your voice then send a voice note:", reply_markup=get_kb())

async def button(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data["voice"] = query.data
    await query.edit_message_text(f"✅ {VOICES[query.data]['label']} selected! Now send your voice note.", reply_markup=get_kb())

async def handle_voice(update, context):
    voice_key = context.user_data.get("voice", "girl_cute")
    cfg = VOICES[voice_key]
    await update.message.reply_text(f"⏳ Changing to {cfg['label']}...")
    file = await update.message.voice.get_file()
    await file.download_to_drive("input.ogg")
    run("ffmpeg -y -i input.ogg -ar 16000 input.wav")
    change_voice("input.wav", "output.wav", cfg["pitch"], cfg["speed"])
    run("ffmpeg -y -i output.wav -c:a libopus output.ogg")
    await update.message.reply_voice(voice=open("output.ogg", "rb"), caption=f"Done: {cfg['label']}")
    for f in ["input.ogg", "input.wav", "output.wav", "output.ogg"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO, handle_voice))
    app.run_polling()
