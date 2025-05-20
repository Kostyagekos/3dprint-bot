import os
import sys
sys.path.append(os.path.dirname(__file__))
import uuid
import logging
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import sqlite3
from dotenv import load_dotenv

from renderer import render_model_screenshot
# render_model_screenshot(filename, screenshot_path)
screenshot_path = "stub.png"  # или заглушка
from gsheet import append_order_row
import trimesh

# Загрузка .env
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

def load_prices():
    conn = sqlite3.connect("settings.db")
    cur = conn.cursor()
    cur.execute("SELECT tech, price FROM prices")
    result = dict(cur.fetchall())
    conn.close()
    return result

def update_price(tech, new_price):
    conn = sqlite3.connect("settings.db")
    cur = conn.cursor()
    cur.execute("UPDATE prices SET price = ? WHERE tech = ?", (new_price, tech))
    conn.commit()
    conn.close()

PRICES = load_prices()
price_change_state = {}


PRICES = {
    "FDM": 2.0,
    "SLA": 5.0,
    "SLS": 7.0,
    "Projet 2500W": 10.0,
}

user_data = {}

def parse_quantity(text):
    digits = ''.join(c for c in text if c.isdigit())
    return int(digits) if digits else 1

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    user_data[message.from_user.id] = {}
    await message.answer("👋 Пришли STL-файл для расчёта 3D-печати.")

@dp.message(F.document)
async def handle_model(message: Message):
    user_id = message.from_user.id
    print(f"📥 Загружаем файл от {user_id}")

    file = await bot.get_file(message.document.file_id)
    filename = f"temp/{uuid.uuid4()}.stl"
    os.makedirs("temp", exist_ok=True)
    await bot.download_file(file.file_path, filename)

    try:
        mesh = trimesh.load(filename, force='mesh')
        if not isinstance(mesh, trimesh.Trimesh):
            raise ValueError("Загруженный файл не является mesh-объектом")

        volume = mesh.volume / 1000
        screenshot_path = filename.replace('.stl', '.png')
        render_model_screenshot(filename, screenshot_path)

        user_data[user_id] = {
            "filename": filename,
            "volume": volume,
            "screenshot": screenshot_path}

        await message.answer_photo(FSInputFile(screenshot_path, filename="screenshot.png"), caption=f"📦 Объем модели: {volume:.2f} см³")
        await message.answer("Сколько копий нужно?")
    except Exception as e:
        logging.exception(e)
        print(f"❌ Ошибка загрузки STL: {e}")
        await message.answer("❌ Ошибка обработки STL-файла.")

@dp.message(lambda m: m.from_user.id in user_data and "quantity" not in user_data[m.from_user.id])
async def handle_quantity(message: Message):
    user_id = message.from_user.id
    qty = parse_quantity(message.text)
    user_data[user_id]["quantity"] = qty

    kb = InlineKeyboardBuilder()
    for tech in PRICES:
        kb.button(text=tech, callback_data=f"tech_{tech}")
    kb.adjust(2)

    await message.answer(f"Вы указали {qty} шт. Выберите технологию:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("tech_"))
async def handle_technology(callback: CallbackQuery):
    tech = callback.data.split("_")[1]
    user_id = callback.from_user.id
    data = user_data[user_id]
    total_volume = data["volume"] * data["quantity"]
    price = total_volume * PRICES[tech]

    await callback.message.answer(
        f"✅ Технология: {tech}\n📦 Объём: {total_volume:.2f} см³\n💰 Цена: {price:.2f} грн"
    )

    append_order_row({
        "user_id": user_id,
        "model": os.path.basename(data["filename"]),
        "technology": tech,
        "quantity": data["quantity"],
        "volume": data["volume"],
        "total_volume": total_volume,
        "price": price,
        "screenshot_url": data["screenshot"]
    })

    await callback.answer()

# ========== Webhook запуск ==========

# ========== Webhook ==========

from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

WEBHOOK_PATH = "/webhook"

async def on_startup(app):
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")

async def on_shutdown(app):
    await bot.delete_webhook()

async def create_app():
    print("🟢 create_app() called")
    logging.basicConfig(level=logging.INFO)
    print("🟢 create_app() called")

    app = web.Application()
    app["bot"] = bot

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    print("✅ Webhook handler registered at", WEBHOOK_PATH)

    setup_application(app, dp)
    return app

print("🔥 __main__ section executing...")
app = asyncio.run(create_app())
web.run_app(app, host="0.0.0.0", port=10000)







@dp.message(F.text.lower() == "/цены")
async def show_prices(message: Message):
    kb = InlineKeyboardBuilder()
    for tech in PRICES:
        kb.button(text=f"{tech} ({PRICES[tech]} грн/см³)", callback_data=f"editprice_{tech}")
    kb.adjust(1)
    await message.answer("Выберите технологию для изменения цены:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("editprice_"))
async def edit_price_prompt(callback: CallbackQuery):
    tech = callback.data.split("_")[1]
    price_change_state[callback.from_user.id] = tech
    await callback.message.answer(f"Введите новую цену для технологии <b>{tech}</b> (текущая: {PRICES[tech]} грн/см³):")
    await callback.answer()

@dp.message(lambda m: m.from_user.id in price_change_state)
async def set_new_price(message: Message):
    tech = price_change_state.pop(message.from_user.id)
    try:
        new_price = float(message.text.replace(",", "."))
        update_price(tech, new_price)
        PRICES[tech] = new_price
        await message.answer(f"✅ Цена для <b>{tech}</b> обновлена: {new_price} грн/см³")
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте снова командой /цены.")
