import asyncio
import os
import logging
import random
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
GEMINI_API_KEY = "AIzaSyBWhgqBUKAq8erxejPhnx0fJFqR3NR5aVw" 

# Gemini Setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
client = AsyncIOMotorClient(MONGO_URL)
db = client['chat_bot_db']
users_col = db['users']

# AI Characters List
ai_characters = [
    {"name": "മായ", "place": "കൊച്ചി", "age": "21"},
    {"name": "ദിയ", "place": "കോഴിക്കോട്", "age": "22"},
    {"name": "സ്നേഹ", "place": "തൃശൂർ", "age": "20"},
    {"name": "അഞ്ജലി", "place": "കണ്ണൂർ", "age": "23"},
    {"name": "റിൻഷ", "place": "മലപ്പുറം", "age": "21"},
    {"name": "റിയ ", "place": " ഇടുക്കി", "age": "18"},
    {"name": "അൽക്ക ", "place": " ഇടുക്കി", "age": "19"}
]

async def handle(request): return web.Response(text="Bot is Live!")
app = web.Application(); app.router.add_get('/', handle)

# --- KEYBOARDS ---
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="⚡ Find a Partner")],
    [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="🔗 Refer & Earn")],
    [KeyboardButton(text="💎 Premium")]
], resize_keyboard=True)

# --- AI RESPONSE FUNCTION ---
async def get_ai_response(user_text, char_info):
    try:
        prompt = (
            f"You are a Malayali girl named {char_info['name']} from {char_info['place']}, age {char_info['age']}. "
            "Talk in a friendly, natural way using Malayalam-English mix (Manglish). "
            "If the user asks who you are, your name, place, or gender, answer based on this profile. "
            "Be fun and keep the conversation going like a real human girl. "
            f"User says: {user_text}"
        )
        response = model.generate_content(prompt)
        return response.text
    except:
        return "എന്താ പറഞ്ഞേ? എനിക്ക് മനസ്സിലായില്ല.. ഒന്നുകൂടി പറയൂ! 😊"

# --- COMMANDS ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        new_user = {"user_id": user_id, "referrals": 0, "is_premium": False, "partner": None, "searching": False}
        await users_col.insert_one(new_user)
    
    bot_info = await bot.get_me()
    await message.answer(f"ഹലോ {message.from_user.full_name}! 😊\nസ്വാഗതം!", reply_markup=main_menu)

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
        await bot.send_message(user_id, "Partner found! 💬")
        await bot.send_message(partner['user_id'], "Partner found! 💬")
    else:
        # ആരുമില്ലെങ്കിൽ ഒരു റാൻഡം AI ക്യാരക്ടറെ സെലക്ട് ചെയ്യുന്നു
        char = random.choice(ai_characters)
        await users_col.update_one({"user_id": user_id}, {"$set": {"partner": "AI_BOT", "searching": False, "ai_profile": char}})
        await message.answer(f"നിങ്ങളെ {char['name']}യുമായി കണക്ട് ചെയ്തിരിക്കുന്നു! 👧💬\nസംസാരിച്ചു തുടങ്ങിക്കോളൂ..")

@dp.message(Command("stop"))
async def stop_chat(message: types.Message):
    await users_col.update_one({"user_id": message.from_user.id}, {"$set": {"partner": None, "searching": False}})
    await message.answer("Chat stopped.")

@dp.message(F.text)
async def chat_relay(message: types.Message):
    user = await users_col.find_one({"user_id": message.from_user.id})
    if user and user.get("partner"):
        if user["partner"] == "AI_BOT":
            char_info = user.get("ai_profile", ai_characters[0])
            ai_reply = await get_ai_response(message.text, char_info)
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
