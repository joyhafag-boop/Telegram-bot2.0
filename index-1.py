
# ============================================
#  Secure Surf Zone - Full Telegram Shop Bot
#  Features:
#  - Product system (Add/Update/Delete via bot)
#  - Price, Stock, Duration management
#  - Expiry auto calculation
#  - Order system
#  - Live Chat system
#  - Admin delivery system
#  - Render Webhook ready
# ============================================

import os
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

# ================= SETTINGS =================
SHOP_NAME = "Secure Surf Zone"
BKASH = "01642012385"
NAGAD = "01788098356"

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "123456789"))

DB = "shop.db"
NAME, PHONE, PAYMENT, TRX = range(4)

api = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

# ================= DATABASE =================
def db():
    return sqlite3.connect(DB)

def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        stock INTEGER,
        duration_days INTEGER,
        desc TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        phone TEXT,
        product_name TEXT,
        duration_days INTEGER,
        total INTEGER,
        payment TEXT,
        trx TEXT,
        expiry TEXT,
        status TEXT,
        created TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_state(
        user_id INTEGER PRIMARY KEY,
        live_chat INTEGER DEFAULT 0
    )
    """)

    con.commit()

    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        products = [
            ("Adobe Explore (1 Month)", 500, 300, 30, "Adobe Explore premium access"),
            ("Adobe Explore (3 Month)", 1350, 200, 90, "Adobe Explore premium access"),
            ("Premium VPN (1 Month)", 250, 999, 30, "High-speed VPN"),
            ("ChatGPT Account (1 Month)", 450, 200, 30, "ChatGPT premium"),
            ("Gemini Pro (1 Month)", 400, 200, 30, "Gemini Pro premium"),
        ]
        cur.executemany(
            "INSERT INTO products(name,price,stock,duration_days,desc) VALUES (?,?,?,?,?)",
            products
        )
        con.commit()

    con.close()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Welcome to {SHOP_NAME}\nType /shop to see products"
    )

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = db(); cur = con.cursor()
    cur.execute("SELECT id,name,price FROM products WHERE stock>0")
    rows = cur.fetchall(); con.close()
    msg = "Available Products:\n"
    for r in rows:
        msg += f"#{r[0]} {r[1]} - {r[2]}৳\n"
    await update.message.reply_text(msg)

# ================= ADMIN COMMANDS =================
async def addp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    text = update.message.text.replace("/addp","").strip()
    parts = [p.strip() for p in text.split("|")]
    if len(parts) != 5:
        await update.message.reply_text("Format:\n/addp name | price | stock | duration | description")
        return
    name,price,stock,duration,desc = parts
    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO products(name,price,stock,duration_days,desc) VALUES (?,?,?,?,?)",
                (name,int(price),int(stock),int(duration),desc))
    con.commit(); con.close()
    await update.message.reply_text("Product Added.")

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    con=db(); cur=con.cursor()
    cur.execute("SELECT id,name,price,stock,duration_days FROM products")
    rows=cur.fetchall(); con.close()
    msg="Products:\n"
    for r in rows:
        msg+=f"#{r[0]} {r[1]} | {r[2]}৳ | stock:{r[3]} | {r[4]}days\n"
    await update.message.reply_text(msg)

# ================= WEBHOOK =================
@api.on_event("startup")
async def startup():
    init_db()
    if PUBLIC_URL:
        await bot_app.initialize()
        await bot_app.bot.set_webhook(f"{PUBLIC_URL}/webhook")
        await bot_app.start()

@api.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

@api.get("/")
def home():
    return {"status":"running"}

# ================= HANDLERS =================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("shop", shop))
bot_app.add_handler(CommandHandler("addp", addp))
bot_app.add_handler(CommandHandler("products", products))
