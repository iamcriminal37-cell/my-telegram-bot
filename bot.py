import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# നിങ്ങളുടെ വിവരങ്ങൾ
API_TOKEN = '8779215618:AAGrO46Vahb7tP2SGwL0GHV2uLpgbK9oi3Y'
ADMIN_ID = 8539013019 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# മെനു ബട്ടണുകൾ
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ Find a Partner")],
        [KeyboardButton(text="👩 Match with girls"), KeyboardButton(text="👦 Match with boys")],
        [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="⚙️ Settings")],
        [KeyboardButton(text="💎 Premium")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    refer_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    welcome_text = (
        "സ്വാഗതം! 😊\n\n"
        "അപരിചിതരുമായി സംസാരിക്കാൻ താഴെ കാണുന്ന ബട്ടണുകൾ ഉപയോഗിക്കുക.\n\n"
        "🚀 **Premium Offer:**\n"
        "100 പേരെ റഫർ ചെയ്താൽ 1 മാസം പ്രീമിയം സൗജന്യമായി ലഭിക്കും!\n\n"
        f"🔗 നിങ്ങളുടെ റഫറൽ ലിങ്ക്: {refer_link}"
    )
    await message.answer(welcome_text, reply_markup=main_menu)

@dp.message(F.text == "👤 My Profile")
async def my_profile(message: types.Message):
    await message.answer(f"👤 **നിങ്ങളുടെ പ്രൊഫൈൽ**\n\nID: {message.from_user.id}\nപേര്: {message.from_user.first_name}\nറഫറൽ കൗണ്ട്: 0\nസ്റ്റാറ്റസ്: ഫ്രീ മെമ്പർ 🆓")

@dp.message(F.text == "💎 Premium")
async def premium_info(message: types.Message):
    await message.answer("💎 **Tikible Premium**\n\n✅ Gender-based matching\n✅ No Ads\n\nപ്രീമിയം ലഭിക്കാൻ 100 പേരെ റഫർ ചെയ്യുക!")

@dp.message(F.text == "⚡ Find a Partner")
async def find_partner(message: types.Message):
    await message.answer("Searching for a partner... 🔎\nകുറച്ചു സമയം കാത്തിരിക്കൂ.")

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 **Welcome Admin!**")
    else:
        await message.answer("നിങ്ങൾക്ക് ഇതിനുള്ള അനുവാദമില്ല.")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot is starting on Render...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
