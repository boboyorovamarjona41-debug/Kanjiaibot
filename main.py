import asyncio
import logging
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

BOT_TOKEN = "8842632927:AAFdmB4hJoz1fuovQNnpXrph11uyUoPTids"
ADMIN_ID = 6992041213
CARD_NUMBER = "5614 6835 1687 0326"
CARD_HOLDER = "B. M"
PRICE = "99 900 UZS"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_NAME = "kanji_ai.db"

# Render HTTP server (port to'qnashuvining oldini olish uchun)
async def handle_ping(request):
    return web.Response(text="Kanji AI Bot Active 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_vip INTEGER DEFAULT 0,
                free_questions INTEGER DEFAULT 3
            )
        """)
        await db.commit()

def main_keyboard(is_vip: bool):
    buttons = [
        [InlineKeyboardButton(text="🈁 Kanji Qidirish va AI Mnemonika", callback_data="search_kanji")],
        [InlineKeyboardButton(text="⛩ JLPT Darajalari (N5-N1)", callback_data="jlpt_levels")],
        [InlineKeyboardButton(text="👤 Profil va Status", callback_data="my_profile")]
    ]
    if not is_vip:
        buttons.append([InlineKeyboardButton(text=f"👑 VIP Obuna ({PRICE}/oy)", callback_data="buy_vip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, is_vip, free_questions) VALUES (?, 0, 3)",
            (message.from_user.id,)
        )
        await db.commit()
        async with db.execute("SELECT is_vip FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            is_vip = bool(row[0]) if row else False

    await message.answer(
        f"Konnichiwa, {message.from_user.first_name}! 🇯🇵\n\n"
        "<b>Kanji AI</b> platformasiga xush kelibsiz!\n"
        "Men yapon tili kanjilarini tez va oson eslab qolishingiz uchun AI yordamchisiman.\n\n"
        "JLPT N5-N1 kanjilarini ma'nosi, o'qilishi (Onyomi/Kunyomi) va mnemonika usulida o'rganishingiz mumkin!",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_vip)
    )

@dp.callback_query(F.data == "buy_vip")
async def buy_vip_info(callback: types.CallbackQuery):
    text = (
        "👑 <b>Kanji AI — 1 Oylik VIP Obuna</b>\n\n"
        "VIP imkoniyatlari:\n"
        "✅ Barcha JLPT (N5-N1) kanjilariga cheksiz kirish\n"
        "✅ Har bir kanji uchun AI tomonidan mnemonika va eslab qolish hikoyalari\n"
        "✅ Misollar va so'z birikmalari tahlili\n\n"
        f"💰 <b>Narxi:</b> {PRICE} / 1 oy\n"
        f"💳 <b>Karta:</b> <code>{CARD_NUMBER}</code> ({CARD_HOLDER})\n\n"
        "📸 To'lov qilgach, chek skrinshotini botga yuboring!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data="main_menu")]])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "search_kanji")
async def search_kanji_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_vip, free_questions FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            is_vip = bool(row[0]) if row else False
            free_q = row[1] if row else 0

    if not is_vip and free_q <= 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"👑 VIP Obuna ({PRICE})", callback_data="buy_vip")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")]
        ])
        await callback.message.edit_text(
            "🔒 <b>Bepul savollar limitingiz tugadi!</b>\nCheksiz kanji qidirish va AI mnemonika uchun VIP obunani faollashtiring.",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    status_text = "👑 VIP (Cheksiz)" if is_vip else f"🆓 Bepul: {free_q} ta savol qoldi"
    await callback.message.edit_text(
        f"🈁 <b>Kanji belgisini yoki ma'nosini yuboring!</b>\n\n"
        f"Status: <b>{status_text}</b>\n"
        "Masalan: <i>'日'</i> yoki <i>'quyosh'</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data="main_menu")]])
    )

@dp.message(F.photo)
async def handle_receipt(message: types.Message):
    user = message.from_user
    photo_id = message.photo[-1].file_id
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ VIP Yoqish ({user.id})", callback_data=f"approve_vip_{user.id}")]
    ])
    
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=f"💳 <b>Yangi to'lov cheki (Kanji AI)</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {user.full_name} (@{user.username})\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
                f"💰 <b>Tarif:</b> {PRICE}",
        parse_mode="HTML",
        reply_markup=admin_kb
    )
    
    await message.answer("📩 To'lov chekingiz adminga yuborildi. Tez orada VIP obunangiz faollashtiriladi!")

@dp.callback_query(F.data.startswith("approve_vip_"))
async def approve_vip(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Siz admin emassiz!", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_vip = 1 WHERE user_id = ?", (target_user_id,))
        await db.commit()

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ <b>VIP Obuna Faollashtirildi!</b>",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text="🎉 <b>Tabriklaymiz!</b> Kanji AI VIP obunangiz faollashtirildi. Cheksiz foydalanishingiz mumkin!",
            parse_mode="HTML"
        )
    except Exception:
        pass

@dp.callback_query(F.data == "my_profile")
async def show_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_vip, free_questions FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            is_vip = bool(row[0]) if row else False
            free_q = row[1] if row else 0

    status = "👑 VIP (1 oylik faol)" if is_vip else "🔒 Bepul Tarif"
    text = (
        f"👤 <b>Profilingiz:</b>\n\n"
        f"Status: <b>{status}</b>\n"
        f"Qolgan bepul savollar: <b>{free_q} ta</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data="main_menu")]])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "jlpt_levels")
async def show_jlpt(callback: types.CallbackQuery):
    text = (
        "⛩ <b>JLPT Kanji Darajalari:</b>\n\n"
        "🔹 <b>N5:</b> ~100 ta asosiy kanji\n"
        "🔹 <b>N4:</b> ~300 ta kanji\n"
        "🔹 <b>N3:</b> ~650 ta kanji\n"
        "🔹 <b>N2:</b> ~1000 ta kanji\n"
        "🔹 <b>N1:</b> ~2000 ta kanji"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data="main_menu")]])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_vip FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            is_vip = bool(row[0]) if row else False
    await callback.message.edit_text("Yo'nalishni tanlang:", reply_markup=main_keyboard(is_vip))

async def main():
    await init_db()
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

