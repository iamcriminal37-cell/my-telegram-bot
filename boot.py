import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from aiohttp import web

# --- CONFIGURATION ---
API_TOKEN = '8779215618:AAGrO46Vahb7tP2SGwL0GHV2uLpgbK9oi3Y'
ADMIN_ID = 8539013019
MONGO_URL = "mongodb+srv://BIBIN:Bibin@123@cluster0.mnpq2pv.mongodb.net/?appName=Cluster0"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
client = AsyncIOMotorClient(MONGO_URL)
db = client['chat_bot_db']
users_col = db['users']

# --- WEB SERVER FOR RENDER ---
async def handle(request): return web.Response(text="Bot is Live!")
app = web.Application()
app.router.add_get('/', handle)

# --- KEYBOARDS ---
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="⚡ Find a Partner")],
    [KeyboardButton(text="👩 Match with girls"), KeyboardButton(text="👦 Match with boys")],
    [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="🔗 Refer & Earn")],
    [KeyboardButton(text="💎 Premium")]
], resize_keyboard=True)

# --- LOGIC ---
@dp.message(Command("start"))
async def start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    args = command.args # referral id
    
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        new_user = {
            "user_id": user_id,
            "referrals": 0,
            "is_premium": False,
            "partner": None,
            "referred_by": int(args) if args and args.isdigit() else None
        }
        await users_col.insert_one(new_user)
        if new_user["referred_by"]:
            await users_col.update_one({"user_id": new_user["referred_by"]}, {"$inc": {"referrals": 1}})
            # Check for premium unlock
            ref_user = await users_col.find_one({"user_id": new_user["referred_by"]})
            if ref_user and ref_user['referrals'] >= 100:
                await users_col.update_one({"user_id": ref_user['user_id']}, {"$set": {"is_premium": True}})

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    await message.answer(f"സ്വാഗതം! 😊\nനിങ്ങളുടെ റഫറൽ ലിങ്ക്: {ref_link}\n\n100 പേരെ റഫർ ചെയ്താൽ പ്രീമിയം സൗജന്യമായി ലഭിക്കും!", reply_markup=main_menu)

@dp.message(F.text == "👤 My Profile")
async def profile(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    status = "💎 Premium" if user.get("is_premium") else "🆓 Free"
    text = (f"👤 **പ്രൊഫൈൽ**\n\nID: `{user['user_id']}`\n"
            f"റഫറലുകൾ: {user.get('referrals', 0)}\n"
            f"സ്റ്റാറ്റസ്: {status}")
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "⚡ Find a Partner")
async def find_partner(message: types.Message):
    user_id = message.from_user.id
    await users_col.update_one({"user_id": user_id}, {"$set": {"searching": True}})
    
    # Simple Matching Logic
    partner = await users_col.find_one({"searching": True, "user_id": {"$ne": user_id}, "partner": None})
    
    if partner:
        await users_col.update_one({"user_id": user_id}, {"$set": {"partner": partner['user_id'], "searching": False}})
        await users_col.update_one({"user_id": partner['user_id']}, {"$set": {"partner": user_id, "searching": False}})
        await bot.send_message(user_id, "Partner found! സംസാരം തുടങ്ങാം.. 💬\nനിർത്താൻ /stop അടിക്കുക.")
        await bot.send_message(partner['user_id'], "Partner found! സംസാരം തുടങ്ങാം.. 💬\nനിർത്താൻ /stop അടിക്കുക.")
    else:
        await message.answer("Searching... ആരെങ്കിലും വരുന്നത് വരെ കാത്തിരിക്കൂ. 🔎")

@dp.message(Command("stop"))
async def stop_chat(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    if user.get("partner"):
        partner_id = user["partner"]
        await users_col.update_one({"user_id": message.from_user.id}, {"$set": {"partner": None}})
        await users_col.update_one({"user_id": partner_id}, {"$set": {"partner": None}})
        await message.answer("Chat stopped.")
        await bot.send_message(partner_id, "Partner chat അവസാനിപ്പിച്ചു.")
    else:
        await message.answer("നിങ്ങൾ ഇപ്പോൾ ചാറ്റിൽ അല്ല.")

@dp.message()
async def chat_handler(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    if user and user.get("partner"):
        try:
            await bot.send_message(user["partner"], message.text)
        except:
            await message.answer("മെസ്സേജ് അയക്കാൻ കഴിഞ്ഞില്ല.")

async def main():
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 10000).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
