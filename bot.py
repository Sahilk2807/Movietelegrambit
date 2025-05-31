import os
import json
import gspread
import requests
from aiogram import Bot, Dispatcher, types
from oauth2client.service_account import ServiceAccountCredentials

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

ADMIN_ID = int(os.getenv("ADMIN_ID"))
GPLINKS_API = os.getenv("GPLINKS_API")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME")

def get_google_credentials():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = os.getenv("GOOGLE_CREDS_JSON")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return creds

def get_google_sheet_data():
    creds = get_google_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    return sheet.get_all_records()

def shorten_link_gplinks(url):
    try:
        response = requests.get(f"https://gplinks.in/api?api={GPLINKS_API}&url={url}")
        return response.json().get("shortenedUrl", url)
    except:
        return url

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("🎬 *Welcome to the Movie Bot!*\n\nSend me a movie name to search.", parse_mode="Markdown")

@dp.message_handler(commands=["add"])
async def add_movie(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("🚫 You are not authorized.")
    try:
        _, name, link = message.text.split(maxsplit=2)
        creds = get_google_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        sheet.append_row([name, link])
        await message.reply("✅ Movie added successfully!")
    except Exception:
        await message.reply("❌ Failed to add. Format:\n/add Movie_Name https://link")

@dp.message_handler(commands=["remove"])
async def remove_movie(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("🚫 You are not authorized.")
    try:
        _, movie = message.text.split(maxsplit=1)
        sheet_data = get_google_sheet_data()
        creds = get_google_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        for i, row in enumerate(sheet_data, start=2):
            if row["Name"].lower().startswith(movie.lower()[:3]):
                sheet.delete_rows(i)
                await message.reply("🗑️ Movie removed.")
                return
        await message.reply("❌ Movie not found.")
    except Exception:
        await message.reply("❌ Error removing movie.")

@dp.message_handler()
async def search_movie(message: types.Message):
    query = message.text.strip().lower()
    data = get_google_sheet_data()
    found = []

    for row in data:
        movie_name = row.get("Name", "")
        if movie_name.lower().startswith(query[:3]):
            short_link = shorten_link_gplinks(row.get("Link", ""))
            found.append(f"🍿 *{movie_name}*\n🔗 {short_link}")

    if found:
        reply_text = "\n\n".join(found)
        await message.reply(f"✨ Found {len(found)} result(s):\n\n{reply_text}", parse_mode="Markdown")
    else:
        await message.reply("😢 No matching movies found.")