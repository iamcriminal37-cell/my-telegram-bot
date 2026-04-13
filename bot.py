import asyncio
import os
import logging
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from aiohttp import web

# --- CONFIGURATION ---
API_TOKEN = '8779215618:AAGrO46Vahb7tP2SGwL0GHV2uLpgbK9oi3Y'
ADMIN_ID = 8539013019
MONGO_URL = "mongodb+srv://BIBIN:Bibin123@cluster0.mnpq2pv.mongodb.net/?retryWrites=true&w=majority"
GEMINI_API_KEY = "AIzaSyBwhgq6UKAq8erxejPhmx8fJFqR3NR5aVw"

# Gemini Setup & Personality (Female Character)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
client = AsyncIOMotorClient(MONGO_URL)
db = client['chat_bot_db']
users_col = db['users']

# Web Server for Render Health Check
async def handle(request): return web.Response(text="Bot is running with Female AI!")
app = web.Application(); app.router.add_get('/', handle)

# --- KEYBOARDS ---
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="⚡ Find a Partner")],
    [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="🔗 Refer & Earn")],
    [KeyboardButton(text="💎 Premium")]
], resize_keyboard=True)

# --- AI RESPONSE FUNCTION (Female Character Logic) ---
async def get_ai_response(text):
    try:
        # പ്രോംപ്റ്റ് വഴി ഒരു പെൺകുട്ടിയുടെ സ്വഭാവം നൽകുന്നു
        prompt = (f"You are a friendly and cool Malayali girl chat partner. "
                  f"Your name is Maya. Talk in a friendly, natural way using Malayalam (mostly) or English. "
                  f"Be engaging and fun. User says: {text}")
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return "എനിക്ക് ഇപ്പോൾ ചെറിയൊരു തിരക്കുണ്ട്, നമുക്ക് അല്പം കഴിഞ്ഞ് സംസാരിക്കാം! 😊"

# --- COMMANDS ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username or "No Username"
    args = command.args
    
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        new_user = {
            "user_id": user_id, "full_name": full_name, "username": username,
            "referrals": 0, "is_premium": False, "partner": None, 
            "searching": False, "referred_by": int(args) if args and args.isdigit() else None
        }
        await users_col.insert_one(new_user)
        if new_user["referred_by"]:
            await users_col.update_one({"user_id": new_user["referred_by"]}, {"$inc": {"referrals": 1}})
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    await message.answer(f"ഹലോ {full_name}! 😊\n\nനിങ്ങളുടെ റഫറൽ ലിങ്ക്: {ref_link}", reply_markup=main_menu)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = await users_col.count_documents({})
        last_users = users_col.find().sort("_id", -1).limit(10)
        stats = f"📊 **ADMIN DASHBOARD**\n👤 ആകെ യൂസർമാർ: {total}\n\n🆕 **പുതിയവർ:**\n"
        async for u in last_users:
            stats += f"• {u.get('full_name')} (@{u.get('username')}) - `{u.get('user_id')}`\n"
        await message.answer(stats, parse_mode="Markdown")

@dp.message(F.text == "💎 Premium")
async def premium_check(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    refs = user.get('referrals', 0)
    if refs >= 100:
        await users_col.update_one({"user_id": message.from_user.id}, {"$set": {"is_premium": True}})
        await message.answer("🎉 അഭിനന്ദനങ്ങൾ! നിങ്ങൾ 100 റഫറലുകൾ പൂർത്തിയാക്കി പ്രീമിയം മെമ്പറായി. 💎")
    else:
        await message.answer(f"💎 പ്രീമിയം ലഭിക്കാൻ 100 റഫറലുകൾ വേണം.\n\nനിങ്ങളുടെ റഫറലുകൾ: {refs}\nഇനി വേണ്ടത്: {100 - refs}")

@dp.message(F.text == "⚡ Find a Partner")
async def find_partner(message: types.Message):
    user_id = message.from_user.id
    await users_col.update_one({"user_id": user_id}, {"$set": {"searching": True, "partner": None}})
    
    await message.answer("Searching for a partner... 🔎")
    await asyncio.sleep(8) 
    
    partner = await users_col.find_one({"searching": True, "user_id": {"$ne": user_id}, "partner": None})
    if partner:
        await users_col.update_one({"user_id": user_id}, {"$set": {"partner": partner['user_id'], "searching": False}})
        await users_col.update_one({"user_id": partner['user_id']}, {"$set": {"partner": user_id, "searching": False}})
        await bot.send_message(user_id, "Partner found! സംസാരം തുടങ്ങാം.. 💬")
        await bot.send_message(partner['user_id'], "Partner found! സംസാരം തുടങ്ങാം.. 💬")
    else:
        # ആരുമില്ലെങ്കിൽ Female AI കണക്ട് ചെയ്യുന്നു
        await users_col.update_one({"user_id": user_id}, {"$set": {"partner": "AI_BOT", "searching": False}})
        await message.answer("നിങ്ങളെ ഞങ്ങളുടെ ഫ്രണ്ട് മായയുമായി കണക്ട് ചെയ്തിരിക്കുന്നു! 👧💬\nസംസാരിച്ചു തുടങ്ങിക്കോളൂ..")

@dp.message(Command("stop"))
async def stop_chat(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    if user and user.get("partner"):
        p_id = user["partner"]
        await users_col.update_one({"user_id": message.from_user.id}, {"$set": {"partner": None}})
        if p_id != "AI_BOT":
            await users_col.update_one({"user_id": p_id}, {"$set": {"partner": None}})
            await bot.send_message(p_id, "Partner chat അവസാനിപ്പിച്ചു.")
        await message.answer("Chat stopped.")

@dp.message(F.text == "👤 My Profile")
async def profile_info(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    status = "💎 Premium" if user.get("is_premium") else "🆓 Free"
    await message.answer(f"👤 **പ്രൊഫൈൽ**\n\nറഫറലുകൾ: {user.get('referrals', 0)}\nസ്റ്റാറ്റസ്: {status}", parse_mode="Markdown")

@dp.message(F.text == "🔗 Refer & Earn")
async def refer_info(message: types.Message):
    bot_user = await bot.get_me()
    ref_link = f"https://t.me/{bot_user.username}?start={message.from_user.id}"
    await message.answer(f"🎁 **Referral Link**\n\nഈ ലിങ്ക് വഴി 100 പേരെ ജോയിൻ ചെയ്യിച്ചാൽ പ്രീമിയം ലഭിക്കും:\n\n{ref_link}")

@dp.message(F.text)
async def chat_relay(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    if user and user.get("partner"):
        if user["partner"] == "AI_BOT":
            ai_reply = await get_ai_response(message.text)
            await message.answer(ai_reply)
        else:
            try: await bot.send_message(user["partner"], message.text)
            except: pass

async def main():
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())            
