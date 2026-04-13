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
# ഇതിൽ നിങ്ങളുടെ പാസ്‌വേഡ് മാത്രം മാറ്റുക. @ പോലുള്ള ചിഹ്നങ്ങൾ പാസ്‌വേഡിൽ ഉണ്ടെങ്കിൽ ഒഴിവാക്കുക.
MONGO_URL = "mongodb+srv://BIBIN:Bibin123@cluster0.mnpq2pv.mongodb.net/?retryWrites=true&w=majority"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# MongoDB Connection
client = AsyncIOMotorClient(MONGO_URL)
db = client['chat_bot_db']
users_col = db['users']

# --- WEB SERVER FOR RENDER HEALTH CHECK ---
async def handle(request):
    return web.Response(text="Bot is running perfectly!")

app = web.Application()
app.router.add_get('/', handle)

# --- KEYBOARDS ---
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="⚡ Find a Partner")],
    [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="🔗 Refer & Earn")],
    [KeyboardButton(text="💎 Premium")]
], resize_keyboard=True)

# --- BOT LOGIC ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    args = command.args
    
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        new_user = {
            "user_id": user_id,
            "referrals": 0,
            "is_premium": False,
            "partner": None,
            "searching": False,
            "referred_by": int(args) if args and args.isdigit() else None
        }
        await users_col.insert_one(new_user)
        if new_user["referred_by"]:
            await users_col.update_one({"user_id": new_user["referred_by"]}, {"$inc": {"referrals": 1}})

    bot_user = await bot.get_me()
    ref_link = f"https://t.me/{bot_user.username}?start={user_id}"
    await message.answer(f"സ്വാഗതം! 😊\n\nനിങ്ങളുടെ റഫറൽ ലിങ്ക്: {ref_link}", reply_markup=main_menu)

@dp.message(F.text == "⚡ Find a Partner")
async def find_partner(message: types.Message):
    user_id = message.from_user.id
    await users_col.update_one({"user_id": user_id}, {"$set": {"searching": True, "partner": None}})
    
    # Matching process
    partner = await users_col.find_one({"searching": True, "user_id": {"$ne": user_id}, "partner": None})
    
    if partner:
        await users_col.update_one({"user_id": user_id}, {"$set": {"partner": partner['user_id'], "searching": False}})
        await users_col.update_one({"user_id": partner['user_id']}, {"$set": {"partner": user_id, "searching": False}})
        
        await bot.send_message(user_id, "Partner found! സംസാരം തുടങ്ങാം.. 💬\nനിർത്താൻ /stop അടിക്കുക.")
        await bot.send_message(partner['user_id'], "Partner found! സംസാരം തുടങ്ങാം.. 💬\nനിർത്താൻ /stop അടിക്കുക.")
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

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = await users_col.count_documents({})
        active_chats = await users_col.count_documents({"partner": {"$ne": None}})
        await message.answer(f"📊 **Admin Panel**\n\nUsers: {total}\nLive Chats: {active_chats // 2}")

@dp.message(F.text)
async def chat_relay(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    if user and user.get("partner"):
        try:
            await bot.send_message(user["partner"], message.text)
        except:
            pass

# --- RUNNER ---
async def main():
    # Render Port Configuration
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Web server started on port {port}")
    
    # Start Telegram Polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
