import asyncio
import logging
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

BOT_TOKEN = "8842632927:AAHT1_55_gaXKrktCmeg6ja0qlB9h96BCZI"
ADMIN_ID = 6992041213  # Sizning Telegram ID ingiz
CARD_NUMBER = "5614 6835 1687 0326"  # Karta raqamingiz
CARD_HOLDER = "B. M"  # Karta egasi ismi

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_NAME = "kanji_bot.db"

# Render uchun dummy HTTP server (Bepul Web Service uchun)
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

# Bazani yaratish
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                current_index INTEGER DEFAULT 0,
                learned_count INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0
            )
        """)
        await db.commit()

# Kanji Ma'lumotlar Bazasi (VIP va Free belgilangan)
KANJI_DATA = [
    {
        "id": 0,
        "kanji": "休",
        "meaning": "Dam olmoq (Rest)",
        "onyomi": "キュウ (Kyuu)",
        "kunyomi": "やす-む (Yasu-mu)",
        "mnemonic": "👤 Odam (亻) 🌳 daraxt (木) tagida suyanib dam olmoqda.",
        "example": "休日 (Kyuujitsu) - Dam olish kuni",
        "is_vip": False
    },
    {
        "id": 1,
        "kanji": "木",
        "meaning": "Daraxt (Tree)",
        "onyomi": "モク (Moku), ボク (Boku)",
        "kunyomi": "き (Ki)",
        "mnemonic": "🌴 Shoxlari va ildizlari tarqalgan daraxt shakli.",
        "example": "木曜日 (Mokuyoubi) - Payshanba",
        "is_vip": False
    },
    {
        "id": 2,
        "kanji": "明",
        "meaning": "Yorug', ochiq (Bright - Premium)",
        "onyomi": "メイ (Mei)",
        "kunyomi": "あか-るい (Aka-rui)",
        "mnemonic": "☀️ Quyosh (日) va 🌙 Oy (月) birga osmonda tursa, tevarak yorug' bo'ladi.",
        "example": "明日 (Ashita) - Ertaga",
        "is_vip": True
    }
]

def main_keyboard(is_vip: bool):
    buttons = [
        [InlineKeyboardButton(text="🧠 Kanji Mnemonika", callback_data="learn_kanji")],
        [InlineKeyboardButton(text="📊 Mening natijam", callback_data="my_stats")]
    ]
    if not is_vip:
        buttons.append([InlineKeyboardButton(text="👑 VIP Obuna Sotib Olish (99 900 so'm)", callback_data="buy_vip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, current_index, learned_count, is_vip) VALUES (?, 0, 0, 0)",
            (message.from_user.id,)
        )
        await db.commit()
        async with db.execute("SELECT is_vip FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            is_vip = bool(row[0]) if row else False

    await message.answer(
        f"Konnichiwa, {message.from_user.first_name}! 🇯🇵\n\n"
        "Kanji AI Botiga xush kelibsiz!\n"
        "Mnemonika usulida kanjilarni tez va oson yodlang.",
        reply_markup=main_keyboard(is_vip)
    )

@dp.callback_query(F.data == "buy_vip")
async def buy_vip_info(callback: types.CallbackQuery):
    text = (
        "👑 <b>Kanji AI VIP Obuna</b>\n\n"
        "VIP a'zolarga quyidagilar ochiladi:\n"
        "✅ Barcha JLPT N5, N4, N3, N2, N1 kanjilari va vizual mnemonikasi\n"
        "✅ Imtihon testlari va interaktiv mashqlar\n"
        "✅ Cheksiz 24/7 foydalanish\n\n"
        "💰 <b>Narxi:</b> 99 900 so'm / 1 oy\n\n"
        f"💳 <b>To'lov uchun karta raqami:</b>\n"
        f"<code>{CARD_NUMBER}</code> ({CARD_HOLDER})\n\n"
        "📸 <b>Qanday faollashtiriladi?</b>\n"
        "To'lovni amalga oshirgach, to'lov cheki skrinshotini (rasmini) <b>to'g'ridan-to'g'ri ushbu botga yuboring</b>. Admin tasdiqlashi bilan VIP billingingiz faollashadi!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "learn_kanji")
async def show_kanji(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT current_index, is_vip FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            idx = row[0] if row else 0
            is_vip = bool(row[1]) if row else False

    if idx >= len(KANJI_DATA):
        await callback.message.edit_text(
            "🎉 Barcha mavjud kanjilarni o'rganib chiqdingiz!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Qayta boshlash", callback_data="reset_progress")]
            ])
        )
        return

    item = KANJI_DATA[idx]

    # VIP Cheklovi
    if item["is_vip"] and not is_vip:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👑 VIP Obunani Olish (99 900 so'm)", callback_data="buy_vip")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")]
        ])
        await callback.message.edit_text(
            "🔒 <b>Bu kanji VIP obunachilar uchun!</b>\n\n"
            "Keyingi barcha kanjilar va mnemonika kartalarini ochish uchun VIP obunani faollashtiring.",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    text = (
        f"⛩ <b>Kanji:</b> {item['kanji']}\n\n"
        f"📖 <b>Ma'nosi:</b> {item['meaning']}\n"
        f"🔊 <b>Onyomi:</b> {item['onyomi']}\n"
        f"🗣 <b>Kunyomi:</b> {item['kunyomi']}\n\n"
        f"🧩 <b>Mnemonika:</b>\n{item['mnemonic']}\n\n"
        f"💡 <b>Misol:</b> {item['example']}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Keyingisi ➡️", callback_data="next_kanji")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "next_kanji")
async def next_kanji(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET current_index = current_index + 1, learned_count = learned_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
    await show_kanji(callback)

# Foydalanuvchi Chek (Rasm) yuborganda Admin panelga jo'natish
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
        caption=f"💳 <b>Yangi to'lov cheki keldi!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {user.full_name} (@{user.username})\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
                f"💰 <b>Tarif:</b> 99 900 so'm",
        parse_mode="HTML",
        reply_markup=admin_kb
    )
    
    await message.answer("📩 To'lov chekingiz adminga yuborildi. Tez orada ko'rib chiqilib, VIP obunangiz faollashtiriladi!")

# Admin VIP statusni tasdiqlaganda
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
        caption=callback.message.caption + "\n\n✅ <b>VIP Muvaffaqiyatli Aktivlashtirildi!</b>",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text="🎉 <b>Tabriklaymiz!</b> Sizning VIP obunangiz faollashtirildi. Barcha kanjilardan cheksiz foydalanishingiz mumkin!",
            parse_mode="HTML"
        )
    except Exception:
        pass

@dp.callback_query(F.data == "my_stats")
async def show_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT learned_count, is_vip FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            learned = row[0] if row else 0
            is_vip = bool(row[1]) if row else False

    status = "👑 VIP A'zo" if is_vip else "🔒 Bepul Tarif"
    text = (
        f"📊 <b>Sizning natijangiz:</b>\n\n"
        f"Status: <b>{status}</b>\n"
        f"O'rganilgan kanjilar: <b>{learned} / {len(KANJI_DATA)}</b> ta"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "reset_progress")
async def reset_progress(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET current_index = 0 WHERE user_id = ?", (user_id,))
        await db.commit()
    await show_kanji(callback)

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

