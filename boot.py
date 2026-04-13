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
MONGO_URL = "mongodb+srv://BIBIN:Bibin123@cluster0.mnpq2pv.mongodb.net/?appName=Cluster0&tlsAllowInvalidCertificates=true"

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

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        await users_col.insert_one({"user_id": user_id, "referrals": 0, "partner": None, "searching": False})
    await message.answer("സ്വാഗതം! ചാറ്റ് തുടങ്ങാൻ ബട്ടൺ അമർത്തുക.", reply_markup=main_menu)

@dp.message(F.text == "⚡ Find a Partner")
async def find_partner(message: types.Message):
    user_id = message.from_user.id
    # ആദ്യം യൂസറെ searching ലിസ്റ്റിലേക്ക് മാറ്റുന്നു
    await users_col.update_one({"user_id": user_id}, {"$set": {"searching": True, "partner": None}})
    
    # മാച്ചിനായി തിരയുന്നു
    partner = await users_col.find_one({"searching": True, "user_id": {"$ne": user_id}, "partner": None})
    
    if partner:
        # രണ്ടുപേരെയും തമ്മിൽ കണക്ട് ചെയ്യുന്നു
        await users_col.update_one({"user_id": user_id}, {"$set": {"partner": partner['user_id'], "searching": False}})
        await users_col.update_one({"user_id": partner['user_id']}, {"$set": {"partner": user_id, "searching": False}})
        
        await bot.send_message(user_id, "Partner found! സംസാരം തുടങ്ങാം.. 💬\nനിർത്താൻ /stop അടിക്കുക.")
        await bot.send_message(partner['user_id'], "Partner found! സംസാരം തുടങ്ങാം.. 💬\nനിർത്താൻ /stop അടിക്കുക.")
    else:
        await message.answer("Searching... ആരെങ്കിലും വരുന്നത് വരെ കാത്തിരിക്കൂ. 🔎")

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
            await message.answer("മെസ്സേജ് അയക്കാൻ പറ്റിയില്ല.")

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = await users_col.count_documents({})
        active = await users_col.count_documents({"partner": {"$ne": None}})
        await message.answer(f"📊 **Live Stats**\n\n👤 Users: {total}\n💬 Active Chats: {active // 2}")

async def main():
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 10000).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    async def main():
    # Render നൽകുന്ന പോർട്ട് എടുക്കാൻ os ഇമ്പോർട്ട് ചെയ്യുന്നു
    import os
    port = int(os.environ.get("PORT", 10000))
    
    # വെബ് സർവർ സെറ്റപ്പ് (Render ബോട്ട് ലൈവ് ആണോ എന്ന് ചെക്ക് ചെയ്യാൻ ഇത് നോക്കും)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Server started on port {port}") # ലോഗ്സിൽ ഇത് കാണാൻ പറ്റും
    
    # ബോട്ട് പോളിംഗ് സ്റ്റാർട്ട് ചെയ്യുന്നു
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
