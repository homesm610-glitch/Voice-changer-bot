import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from pydub import AudioSegment
import librosa
import soundfile as sf

TOKEN = os.environ.get("BOT_TOKEN") or "8633336282:AAFMyvBtppuz--k7rfzz7DJdu2g5e9jz7sE"

VOICES = {
    "girl_hindi_soft": {"pitch": 4, "speed": 0.98, "label": "🇮🇳 Hindi Girl Soft"},
    "girl_hinglish_cute": {"pitch": 6, "speed": 1.0, "label": "🥰 Cute Hinglish Girl"},
    "girl_baddie": {"pitch": 3.5, "speed": 1.05, "label": "😈 Baddie Girl"},
    "girl_punjabi": {"pitch": 4.5, "speed": 1.0, "label": "💃 Punjabi Girl"},
    "girl_tamil": {"pitch": 5, "speed": 0.97, "label": "🌸 Tamil Girl"},
    "girl_bengali": {"pitch": 4, "speed": 0.98, "label": "✨ Bengali Girl"},
    "boy_hindi": {"pitch": -2, "speed": 1.0, "label": "👦 Hindi Boy"},
    "boy_deep": {"pitch": -5, "speed": 0.95, "label": "🎙️ Deep Boy"},
    "boy_english": {"pitch": -1, "speed": 1.02, "label": "🇬🇧 English Boy"},
    "chipmunk": {"pitch": 8, "speed": 1.1, "label": "🐹 Funny"},
}

def change_voice_pro(i,o,p,s):
    y,sr=librosa.load(i,sr=16000)
    y=librosa.effects.pitch_shift(y,sr=sr,n_steps=p)
    y=librosa.effects.time_stretch(y,rate=s)
    sf.write(o,y,sr)

def get_keyboard():
    btns=[]
    items=list(VOICES.items())
    for x in range(0,len(items),2):
        row=[]
        for y in range(2):
            if x+y < len(items):
                k,v=items[x+y]
                row.append(InlineKeyboardButton(v["label"],callback_data=k))
        btns.append(row)
    return InlineKeyboardMarkup(btns)

async def start(update, context):
    context.user_data["voice"]="girl_hinglish_cute"
    await update.message.reply_text("🎤 Voice Changer Ready!\n1. Choose voice below\n2. Send voice", reply_markup=get_keyboard())

async def button_click(update, context):
    q=update.callback_query; await q.answer()
    context.user_data["voice"]=q.data
    await q.edit_message_text(f"✅ {VOICES[q.data]['label']} selected! Send voice now.", reply_markup=get_keyboard())

async def handle_voice(update, context):
    cfg=VOICES[context.user_data.get("voice","girl_hinglish_cute")]
    await update.message.reply_text(f"⏳ Changing to {cfg['label']}...")
    f=await update.message.voice.get_file(); await f.download_to_drive("input.ogg")
    AudioSegment.from_ogg("input.ogg").export("input.wav",format="wav")
    change_voice_pro("input.wav","output.wav",cfg["pitch"],cfg["speed"])
    AudioSegment.from_wav("output.wav").export("output.ogg",format="ogg",codec="libopus")
    await update.message.reply_voice(voice=open("output.ogg","rb"), caption=f"Done: {cfg['label']}")
    for file in ["input.ogg","input.wav","output.wav","output.ogg"]:
        if os.path.exists(file): os.remove(file)

app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("voices", start))
app.add_handler(CallbackQueryHandler(button_click))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.AUDIO, handle_voice))
app.run_polling()
