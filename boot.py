import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from aiohttp import web

# --- CONFIGURATION ---
API_TOKEN = '8779215618:AAGrO46Vahb7tP2SGwL0GHV2uLpgbK9oi3Y'
ADMIN_ID = 8539013019
# താഴെ നിങ്ങളുടെ ശരിക്കുള്ള പാസ്‌വേഡ് ചേർക്കാൻ മറക്കരുത്
MONGO_URL = "mongodb+srv://BIBIN:Bibin123@cluster0.mnpq2pv.mongodb.net/?retryWrites=true&w=majority"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
client = AsyncIOMotorClient(MONGO_URL)
db = client['chat_bot_db']
users_col = db['users']

# --- WEB SERVER FOR RENDER ---
async def handle(request):
    return web.Response(text="Bot is Live!")

app = web.Application()
app.router.add_get('/', handle)

# --- KEYBOARDS ---
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="⚡ Find a Partner")],
    [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="🔗 Refer & Earn")]
], resize_keyboard=True)

# --- LOGIC ---
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        await users_col.insert_one({"user_id": user_id, "referrals": 0, "partner": None, "searching": False})
    await message.answer("സ്വാഗതം! ചാറ്റ് തുടങ്ങാൻ താഴെ കാണുന്ന ബട്ടൺ അമർത്തുക.", reply_markup=main_menu)

@dp.message(F.text == "⚡ Find a Partner")
async def find_partner(message: types.Message):
    user_id = message.from_user.id
    await users_col.update_one({"user_id": user_id}, {"$set": {"searching": True, "partner": None}})
    partner = await users_col.find_one({"searching": True, "user_id": {"$ne": user_id}, "partner": None})
    
    if partner:
        await users_col.update_one({"user_id": user_id}, {"$set": {"partner": partner['user_id'], "searching": False}})
        await users_col.update_one({"user_id": partner['user_id']}, {"$set": {"partner": user_id, "searching": False}})
        await bot.send_message(user_id, "Partner found! 💬\nനിർത്താൻ /stop അടിക്കുക.")
        await bot.send_message(partner['user_id'], "Partner found! 💬\nനിർത്താൻ /stop അടിക്കുക.")
    else:
        await message.answer("Searching for a partner... 🔎")

@dp.message(Command("stop"))
async def stop_chat(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    if user and user.get("partner"):
        p_id = user["partner"]
        await users_col.update_many({"user_id": {"$in": [message.from_user.id, p_id]}}, {"$set": {"partner": None, "searching": False}})
        await message.answer("Chat stopped.")
        await bot.send_message(p_id, "Partner chat അവസാനിപ്പിച്ചു.")
    else:
        await message.answer("നിങ്ങൾ ഇപ്പോൾ ചാറ്റിലല്ല.")

@dp.message(F.text)
async def chat_handler(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    if user and user.get("partner"):
        try:
            await bot.send_message(user["partner"], message.text)
        except:
            pass

# --- MAIN RUNNER ---
async def main():
    # Render പോർട്ട് സെറ്റപ്പ്
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Server started on port {port}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
