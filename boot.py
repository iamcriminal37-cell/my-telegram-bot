import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web # ഇത് പുതിയതായി ചേർത്തതാണ്

# നിങ്ങളുടെ വിവരങ്ങൾ
API_TOKEN = '8779215618:AAGrO46Vahb7tP2SGwL0GHV2uLpgbK9oi3Y'
ADMIN_ID = 8539013019 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ലളിതമായ ഒരു വെബ് സെർവർ (Render എറർ ഒഴിവാക്കാൻ)
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

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
        "സ്വാഗതം! 😊\n\n🔗 റഫറൽ ലിങ്ക്: {refer_link}"
    )
    await message.answer(welcome_text, reply_markup=main_menu)

@dp.message(F.text == "⚡ Find a Partner")
async def find_partner(message: types.Message):
    await message.answer("Searching for a partner... 🔎")

async def main():
    logging.basicConfig(level=logging.INFO)
    # ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുന്നു
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    
    print("Bot is starting on Render...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
