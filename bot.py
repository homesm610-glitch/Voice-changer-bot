import os, subprocess, traceback, requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = "8633336282:AAFMyvBtppuz--k7rfzz7DJdu2g5e9jz7sE"

MODEL_FILE = "girl.pth"
# Working Hindi Girl RVC model - auto download
MODEL_URL = "https://huggingface.co/Jackky2/RVC-Models/resolve/main/Hindi%20Female/Hindi-Female-1000.pth"

def download():
    if not os.path.exists(MODEL_FILE):
        print("Downloading Hindi Girl model 50MB...")
        r = requests.get(MODEL_URL, stream=True, timeout=120)
        with open(MODEL_FILE, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk: f.write(chunk)
        print("Download done")

download()

# Try load RVC
try:
    from rvc_python.infer import RVCInference
    rvc = RVCInference(device="cpu")
    rvc.load_model(MODEL_FILE)
    RVC_OK = True
    print("RVC OK - Real Girl Ready")
except Exception as e:
    print(f"RVC fallback: {e}")
    RVC_OK = False
    import librosa, soundfile as sf

VOICES = {
    "girl_soft": {"pitch": 0, "index": 0.75, "label": "🇮🇳 Soft Hindi Girl"},
    "girl_cute": {"pitch": 3, "index": 0.75, "label": "🥰 Cute Hinglish Girl"},
    "girl_baddie": {"pitch": 5, "index": 0.85, "label": "😈 Baddie Girl"},
}

def run(cmd):
    subprocess.run(cmd, shell=True)

def rvc_change(inp, out, pitch, idx):
    if RVC_OK:
        rvc.infer_file(input_path=inp, output_path=out, pitch=pitch, index_rate=idx, protect=0.33, f0_method="rmvpe")
    else:
        import librosa, soundfile as sf
        y, sr = librosa.load(inp, sr=40000)
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch+7, res_type='soxr_vhq')
        sf.write(out, y, sr)

def get_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton(v["label"], callback_data=k)] for k,v in VOICES.items()])

async def start(update, context):
    context.user_data["voice"] = "girl_cute"
    await update.message.reply_text("🎤 *RVC Hindi Girl Bot Ready*\n\nSelect voice then send 3-5 sec voice:", reply_markup=get_kb(), parse_mode="Markdown")

async def btn(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["voice"] = q.data
    await q.edit_message_text(f"✅ {VOICES[q.data]['label']} selected! Now send voice (3-5 sec)", reply_markup=get_kb())

async def voice_handle(update, context):
    try:
        key = context.user_data.get("voice", "girl_cute")
        cfg = VOICES[key]
        await update.message.reply_text(f"⏳ Converting to {cfg['label']}... 10 sec")
        f = await (update.message.voice or update.message.audio).get_file()
        await f.download_to_drive("in.ogg")
        run("ffmpeg -y -i in.ogg -ar 40000 -ac 1 in.wav")
        rvc_change("in.wav", "out.wav", cfg["pitch"], cfg["index"])
        run("ffmpeg -y -i out.wav -c:a libopus out.ogg")
        await update.message.reply_voice(voice=open("out.ogg","rb"), caption=f"Done: {cfg['label']} - RVC Real Girl")
        for x in ["in.ogg","in.wav","out.wav","out.ogg"]:
            if os.path.exists(x): os.remove(x)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}\n{traceback.format_exc()[-1000:]}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_handle))
app.run_polling()
