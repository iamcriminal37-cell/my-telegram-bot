import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from aiohttp import web

# --- CONFIGURATION ---
API_TOKEN = '8779215618:AAGrO46Vahb7tP2SGwL0GHV2uLpgbK9oi3Y'
ADMIN_ID = 8539013019
# താഴെയുള്ള വരിയിൽ നിങ്ങളുടെ പാസ്‌വേഡ് കൃത്യമായി ചേർക്കുക
MONGO_URL = "mongodb+srv://BIBIN:Bibin@123@cluster0.mnpq2pv.mongodb.net/?appName=Cluster0"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
client = AsyncIOMotorClient(MONGO_URL)
db = client['chat_bot_db']
users_col = db['users']

async def handle(request): return web.Response(text="Bot is running!")
app = web.Application()
app.router.add_get('/', handle)

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="⚡ Find a Partner")],
    [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="🔗 Refer & Earn")]
], resize_keyboard=True)

# --- അപ്‌ഡേറ്റ് ചെയ്ത അഡ്മിൻ പാനൽ ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            total = await users_col.count_documents({})
            active = await users_col.count_documents({"partner": {"$ne": None}})
            text = (
                "📊 **Live Stats**\n\n"
                f"👤 Users: {total}\n"
                f"💬 Chats: {active // 2}"
            )
            await message.answer(text)
        except Exception as e:
            await message.answer(f"Error: {e}")
    else:
        await message.answer("അഡ്മിന് മാത്രം!")

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        await users_col.insert_one({"user_id": user_id, "referrals": 0, "partner": None})
    await message.answer("സ്വാഗതം! ചാറ്റ് തുടങ്ങാൻ ബട്ടൺ അമർത്തുക.", reply_markup=main_menu)

async def main():
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 10000).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 
