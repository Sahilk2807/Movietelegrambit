import logging, gspread, requests, random, os
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GPLINK_API = os.getenv("GPLINK_API")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("movie-downlod-461506-1e54d630195d.json", scope)

emojis = ["🍿", "🎬", "🎞️", "✨", "🔍", "🚀"]

def shorten_link(url):
    try:
        res = requests.get(f"https://gplinks.in/api?api={GPLINK_API}&url={url}")
        return res.json().get("shortenedUrl") or url
    except:
        return url

@dp.message_handler(commands=['start'])
async def start_cmd(msg: types.Message):
    await msg.reply("🎬 *Welcome to Movie Bot!*\nSend me the *movie name* (min 3 letters) to get links.", parse_mode="Markdown")

@dp.message_handler(commands=['add'])
async def add_movie(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.reply("⛔ Not allowed.")
    try:
        _, name, link = msg.text.split(" ", 2)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        sheet.append_row([name, link])
        await msg.reply(f"✅ Added: *{name}*", parse_mode="Markdown")
    except:
        await msg.reply("❌ Format: `/add Movie_Name Movie_Link`", parse_mode="Markdown")

@dp.message_handler(commands=['remove'])
async def remove_movie(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.reply("⛔ Not allowed.")
    name = msg.get_args().strip().lower()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_values()
    for idx, row in enumerate(data, 1):
        if row[0].strip().lower() == name:
            sheet.delete_rows(idx)
            return await msg.reply(f"🗑️ Removed: *{row[0]}*", parse_mode="Markdown")
    await msg.reply("❌ Movie not found.")

@dp.message_handler()
async def search_movie(msg: types.Message):
    query = msg.text.strip().lower()
    if len(query) < 3:
        return await msg.reply("❗ Type at least 3 letters.")
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_values()
    matches = []
    for row in data:
        movie_name = row[0].strip()
        if movie_name.lower().startswith(query[:3]):
            short_url = shorten_link(row[1].strip())
            emoji = random.choice(emojis)
            link_output = short_url if " " not in short_url else "\n" + short_url
            result = f"{emoji} *{movie_name}*\n🎥 Link:\n{link_output}"
            matches.append(result)
    if matches:
        await msg.reply("\n\n".join(matches), parse_mode="Markdown")
    else:
        await msg.reply("❌ No movie found.")