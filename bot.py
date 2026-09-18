# ============================================================
# DARK SMM PANEL
# COMPLETE ONE-FILE VERSION (PYTHON + TELEBOT + SQLITE)
# ============================================================

import sqlite3
import threading
import time
import math
import os
import hashlib
from decimal import Decimal, ROUND_HALF_UP

import requests
import telebot
from telebot import types


# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = "8554102086:AAGT_YljbCzHKrmGWtCei-X-IUTmgQgWIKA"
ADMIN_ID = 8103866669

SMM_API_URL = "https://mjboost.top/api/v2"
SMM_API_KEY = "f534b86eb7ff4650391d501729082c5d"

BOT_NAME = "As Smm Panel "
SUPPORT_USERNAME = "@Developer_Asanur"

BKASH = "01942418965"
NAGAD = "01942418965"

MIN_DEPOSIT = 10.0

# প্রতি ১০০০ কোয়ান্টিটিতে প্রোভাইডার দামের চেয়ে ১৫ টাকা বেশি (প্রফিট)
DEFAULT_PROFIT = 0.0  # No service markup; use API/website rate exactly

REFERRAL_REWARD = 10.0
DEPOSIT_CREDIT_PERCENT = 0.80
ORDER_CHANNEL = "@all_paymant"

FORCE_CHANNELS = [
    "@all_paymant",
    "@zx_community",
    "@As_Smm_proof",
    "@as_tipsbd",
    "@free_income990",
]

DB_FILE = "darksmm.db"
SERVICE_PER_PAGE = 6
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORCE_JOIN_IMAGE = os.path.join(BASE_DIR, "force_join.png")
ORDER_IMAGE = os.path.join(BASE_DIR, "order_banner.jpg")

# ============================================================
# BOT INITIALIZATION
# ============================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)
db_lock = threading.RLock()


def styled_button(text, url=None, callback_data=None, style="primary", **kwargs):
    params = dict(kwargs)
    if url is not None:
        params["url"] = url
    if callback_data is not None:
        params["callback_data"] = callback_data
    params["style"] = style
    return types.InlineKeyboardButton(text, **params)


# ============================================================
# DATABASE SETUP
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn, table, column, definition):
    cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def migrate_db(conn):
    ensure_column(conn, "users", "referral_rewarded", "INTEGER DEFAULT 0")
    ensure_column(conn, "orders", "refunded", "INTEGER DEFAULT 0")
    ensure_column(conn, "orders", "refunded_amount", "REAL DEFAULT 0")
    ensure_column(conn, "orders", "refund_reason", "TEXT DEFAULT ''")
    ensure_column(conn, "payments", "credited_amount", "REAL DEFAULT 0")
    ensure_column(conn, "payments", "commission", "REAL DEFAULT 0")


def init_db():
    with db_lock:
        conn = get_db()
        conn.execute("PRAGMA journal_mode=WAL")

        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            balance REAL DEFAULT 0,
            coins REAL DEFAULT 0,
            referred_by INTEGER,
            referral_count INTEGER DEFAULT 0,
            referral_rewarded INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0,
            total_orders INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_service_id TEXT UNIQUE,
            name TEXT,
            category TEXT,
            type TEXT,
            rate REAL DEFAULT 0,
            min_qty INTEGER DEFAULT 1,
            max_qty INTEGER DEFAULT 1,
            refill INTEGER DEFAULT 0,
            cancel INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1,
            profit REAL DEFAULT 15,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            api_order_id TEXT,
            service_id INTEGER,
            service_name TEXT,
            link TEXT,
            quantity INTEGER,
            cost REAL,
            provider_cost REAL,
            profit REAL,
            status TEXT DEFAULT 'Processing',
            remains TEXT DEFAULT '',
            start_count TEXT DEFAULT '',
            refunded INTEGER DEFAULT 0,
            refunded_amount REAL DEFAULT 0,
            refund_reason TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            method TEXT,
            trx_id TEXT,
            status TEXT DEFAULT 'pending',
            credited_amount REAL DEFAULT 0,
            commission REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_orders (
            user_id INTEGER PRIMARY KEY,
            service_id INTEGER,
            link TEXT,
            quantity INTEGER
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS referral_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_user_id INTEGER NOT NULL UNIQUE,
            reward REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        migrate_db(conn)
        conn.commit()
        conn.close()


# ============================================================
# SETTINGS & HELPERS
# ============================================================

def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_db()
    conn.execute("""
    INSERT INTO settings(key, value) VALUES(?, ?)
    ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, str(value)))
    conn.commit()
    conn.close()


def get_profit():
    try:
        return float(get_setting("default_profit", DEFAULT_PROFIT))
    except Exception:
        return DEFAULT_PROFIT


def get_referral_reward():
    try:
        return float(get_setting("referral_reward", REFERRAL_REWARD))
    except Exception:
        return REFERRAL_REWARD


def save_user(user, referral=None):
    """Create/update user. Referral is recorded only; reward is paid after first successful order."""
    with db_lock:
        conn = get_db()
        existing = conn.execute("SELECT * FROM users WHERE id=?", (user.id,)).fetchone()
        if existing:
            conn.execute("UPDATE users SET username=?, first_name=? WHERE id=?",
                         (user.username or "", user.first_name or "", user.id))
        else:
            valid_referral = None
            if referral and referral != user.id:
                ref = conn.execute("SELECT id FROM users WHERE id=?", (referral,)).fetchone()
                if ref:
                    valid_referral = referral
            conn.execute(
                "INSERT INTO users(id, username, first_name, referred_by, balance, coins, referral_count, referral_rewarded) VALUES(?,?,?,?,0,0,0,0)",
                (user.id, user.username or "", user.first_name or "", valid_referral)
            )
        conn.commit()
        conn.close()


def reward_referrer_once(referred_user_id):
    """Pay one referral reward after the referred user's first successful order."""
    reward = float(get_referral_reward())
    if reward <= 0:
        return False, None, 0.0
    with db_lock:
        conn = get_db()
        row = conn.execute("SELECT referred_by FROM users WHERE id=?", (referred_user_id,)).fetchone()
        if not row or not row["referred_by"]:
            conn.close()
            return False, None, 0.0
        ref_id = int(row["referred_by"])
        # Unique referred_user_id guarantees exactly one reward per referral.
        try:
            conn.execute(
                "INSERT INTO referral_rewards(referrer_id,referred_user_id,reward) VALUES(?,?,?)",
                (ref_id, referred_user_id, reward)
            )
        except sqlite3.IntegrityError:
            conn.close()
            return False, ref_id, 0.0
        ref = conn.execute("SELECT id FROM users WHERE id=?", (ref_id,)).fetchone()
        if not ref:
            conn.execute("DELETE FROM referral_rewards WHERE referred_user_id=?", (referred_user_id,))
            conn.close()
            return False, None, 0.0
        conn.execute("UPDATE users SET balance=balance+?, coins=coins+?, referral_count=referral_count+1 WHERE id=?",
                     (reward, reward, ref_id))
        conn.execute("UPDATE users SET referral_rewarded=1 WHERE id=?", (referred_user_id,))
        conn.commit()
        conn.close()
    try:
        bot.send_message(ref_id, f"🎉 <b>REFERRAL REWARD</b>\n\nআপনার referral-এর প্রথম successful order সম্পন্ন হয়েছে।\n💰 Reward: <b>৳{reward:.2f}</b>")
    except Exception:
        pass
    return True, ref_id, reward


def get_user(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row


# ============================================================
# KEYBOARDS
# ============================================================

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row(
        types.KeyboardButton("🛒 New Order", style="primary"),
        types.KeyboardButton("📋 Services List", style="primary")
    )
    kb.row(
        types.KeyboardButton("📦 My Orders", style="primary"),
        types.KeyboardButton("💰 Balance", style="success")
    )
    kb.row(
        types.KeyboardButton("➕ Add Balance", style="success"),
        types.KeyboardButton("🎁 Refer & Earn", style="success")
    )
    kb.row(
        types.KeyboardButton("📊 Statistics", style="primary"),
        types.KeyboardButton("🔄 Order Status", style="primary")
    )
    kb.row(types.KeyboardButton("📞 Support", style="success"))
    return kb


def admin_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row(types.KeyboardButton("📊 Dashboard", style="primary"), types.KeyboardButton("👥 Users", style="primary"))
    kb.row(types.KeyboardButton("🛒 Orders", style="primary"), types.KeyboardButton("📋 Services", style="primary"))
    kb.row(types.KeyboardButton("🔄 Sync Services", style="success"), types.KeyboardButton("💰 Balance Manager", style="success"))
    kb.row(types.KeyboardButton("💳 Payments", style="success"), types.KeyboardButton("🎁 Referral Settings", style="primary"))
    kb.row(types.KeyboardButton("📢 Broadcast", style="primary"), types.KeyboardButton("🔌 API Settings", style="primary"))
    kb.row(types.KeyboardButton("⚙️ Settings", style="primary"), types.KeyboardButton("🧹 Reset Balances", style="danger"))
    kb.row(types.KeyboardButton("⬅️ Main Menu", style="danger"))
    return kb


# ============================================================
# FORCE JOIN
# ============================================================

def check_joined(user_id):
    for channel in FORCE_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            return False
    return True


def force_join_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for i, channel in enumerate(FORCE_CHANNELS, 1):
        username = channel.lstrip("@")
        kb.add(styled_button(f"📢 JOIN CHANNEL {i}", url=f"https://t.me/{username}", style="primary"))
    kb.row(styled_button("✅ VERIFY JOINED", callback_data="verify_join", style="success"))
    return kb


def force_join_message(chat_id):
    caption = f"""
🌟 <b>WELCOME TO {BOT_NAME}</b> 🌟

🔐 <b>SECURE ACCESS GATE</b>
👋 Premium SMM services ব্যবহার করতে নিচের <b>সবগুলো channel</b>-এ Join করুন।

━━━━━━━━━━━━━━━━━━━━━━
📢 <b>STEP 1:</b> সব channel Join করুন
✅ <b>STEP 2:</b> VERIFY JOINED চাপুন
⚡ <b>STEP 3:</b> তারপর Order Panel ব্যবহার করুন
━━━━━━━━━━━━━━━━━━━━━━
💎 <b>Fast • Secure • Professional</b>
"""
    try:
        if os.path.exists(FORCE_JOIN_IMAGE):
            with open(FORCE_JOIN_IMAGE, "rb") as photo:
                bot.send_photo(chat_id, photo, caption=caption, reply_markup=force_join_keyboard())
        else:
            bot.send_message(chat_id, caption, reply_markup=force_join_keyboard())
    except Exception:
        bot.send_message(chat_id, caption, reply_markup=force_join_keyboard())


# ============================================================
# SMM API REQUESTS & SYNC
# ============================================================

def smm_request(data):
    if not SMM_API_KEY:
        return {"error": "SMM API key is not configured."}
    payload = {"key": SMM_API_KEY}
    payload.update(data)
    try:
        response = requests.post(SMM_API_URL, data=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def api_services():
    return smm_request({"action": "services"})


def api_balance():
    return smm_request({"action": "balance"})


def api_add_order(service, link, quantity):
    return smm_request({"action": "add", "service": service, "link": link, "quantity": quantity})


def api_status(order):
    return smm_request({"action": "status", "order": order})


def sync_services():
    result = api_services()
    if not isinstance(result, list):
        return False, result

    conn = get_db()
    imported = 0
    profit = get_profit()

    for item in result:
        try:
            service_id = str(item["service"])
            name = str(item.get("name", "Unnamed Service"))
            category = str(item.get("category", "Other"))
            service_type = str(item.get("type", "Default"))
            rate = float(item.get("rate", 0))
            minimum = int(item.get("min", 1))
            maximum = int(item.get("max", 1))
            refill = int(bool(item.get("refill", False)))
            cancel = int(bool(item.get("cancel", False)))

            conn.execute("""
            INSERT INTO services(api_service_id, name, category, type, rate, min_qty, max_qty, refill, cancel, enabled, profit)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(api_service_id)
            DO UPDATE SET
                name=excluded.name,
                category=excluded.category,
                type=excluded.type,
                rate=excluded.rate,
                min_qty=excluded.min_qty,
                max_qty=excluded.max_qty,
                refill=excluded.refill,
                cancel=excluded.cancel,
                updated_at=CURRENT_TIMESTAMP
            """, (service_id, name, category, service_type, rate, minimum, maximum, refill, cancel, 1, profit))
            imported += 1
        except Exception:
            continue

    conn.commit()
    conn.close()
    return True, imported


# ============================================================
# PRICE CALCULATION (PROVIDER + PROFIT)
# ============================================================

def provider_cost(service, quantity):
    return float(service["rate"]) * quantity / 1000


def selling_price(service, quantity):
    # Website/provider API rate exactly as synced; no extra markup.
    rate_per_1000 = Decimal(str(float(service["rate"])))
    total = (rate_per_1000 * Decimal(quantity)) / Decimal(1000)
    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def display_service_id(api_service_id):
    # Public-facing service IDs use DARK/DARKSMM instead of the provider's CSB prefix.
    value = str(api_service_id)
    if value.upper().startswith("CSBSMM-"):
        return "DARKSMM-" + value.split("-", 1)[1]
    if value.upper().startswith("CSB-"):
        return "DARK-" + value.split("-", 1)[1]
    return value.replace("CSBSMM", "DARKSMM").replace("CSB", "DARK")


# ============================================================
# PLATFORM & CATEGORY CLASSIFICATION
# ============================================================

PLATFORMS = [
    ("facebook", "📘", "FACEBOOK"),
    ("instagram", "📸", "INSTAGRAM"),
    ("tiktok", "🎵", "TIKTOK"),
    ("youtube", "▶️", "YOUTUBE"),
    ("telegram", "✈️", "TELEGRAM"),
    ("twitter", "🐦", "TWITTER"),
    ("free fire", "🔥", "FREE FIRE"),
]


def get_categories():
    conn = get_db()
    rows = conn.execute("SELECT category, COUNT(*) AS total FROM services WHERE enabled=1 GROUP BY category ORDER BY category COLLATE NOCASE").fetchall()
    conn.close()
    return rows


def detect_platform(category_name):
    cat_lower = category_name.lower()
    for key, icon, label in PLATFORMS:
        if key in cat_lower:
            return label, icon
    return "OTHERS", "📦"


def get_platforms_summary():
    categories = get_categories()
    platform_map = {}
    for item in categories:
        cat_name = item["category"]
        total_svcs = item["total"]
        label, icon = detect_platform(cat_name)
        if label not in platform_map:
            platform_map[label] = {"icon": icon, "count": 0, "categories": []}
        platform_map[label]["count"] += total_svcs
        platform_map[label]["categories"].append(cat_name)
    return platform_map


def category_hash(category):
    return hashlib.sha1(category.encode("utf-8")).hexdigest()[:10]


def find_category_by_hash(value):
    for row in get_categories():
        if category_hash(row["category"]) == value:
            return row["category"]
    return None


def get_category_services(category):
    conn = get_db()
    rows = conn.execute("SELECT * FROM services WHERE enabled=1 AND category=? ORDER BY id ASC", (category,)).fetchall()
    conn.close()
    return rows


# ============================================================
# INTERACTIVE MENUS (PLATFORM -> SUB-CATEGORY -> SERVICES)
# ============================================================

def tier_services_keyboard(category, page=1):
    """Build the service buttons for one category with safe pagination."""
    rows = get_category_services(category)
    per_page = 8
    total = len(rows)
    total_pages = max(1, math.ceil(total / per_page))
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    page_rows = rows[start:start + per_page]

    kb = types.InlineKeyboardMarkup(row_width=1)

    for service in page_rows:
        name = str(service["name"] or "Unnamed Service")
        rate = selling_price(service, 1000)
        sid = display_service_id(service["api_service_id"])
        # Keep callback data short and use the local DB id for lookup.
        label = f"▫️ {name[:55]} • ৳{rate:.2f}/1K • {sid}"
        kb.add(styled_button(
            label,
            callback_data=f"order_service:{int(service['id'])}",
            style="primary"
        ))

    nav = []
    cat_hash = category_hash(category)
    if page > 1:
        nav.append(styled_button(
            "⬅️ Previous",
            callback_data=f"tier:{cat_hash}:{page - 1}",
            style="primary"
        ))
    if page < total_pages:
        nav.append(styled_button(
            "Next ➡️",
            callback_data=f"tier:{cat_hash}:{page + 1}",
            style="primary"
        ))
    if nav:
        kb.row(*nav)

    kb.row(styled_button(
        "⬅️ Back to Categories",
        callback_data=f"platform_back_category:{category_hash(category)}",
        style="primary"
    ))
    kb.row(styled_button(
        "🏠 Main Menu",
        callback_data="main_menu",
        style="primary"
    ))
    return kb


@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_back_category:"))
def platform_back_category_callback(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id):
        force_join_message(call.message.chat.id)
        return

    # Recover the category, then return to its platform category screen.
    category = find_category_by_hash(call.data.split(":", 1)[1])
    if not category:
        bot.answer_callback_query(call.id, "❌ Category পাওয়া যায়নি।", show_alert=True)
        return

    platform_label, _ = detect_platform(category)
    text = f"""
📱 <b>{platform_label} SERVICES</b>

━━━━━━━━━━━━━━━━━━━━━━
📂 আপনার প্রয়োজনীয় <b>Service Type</b> সিলেক্ট করুনঃ
━━━━━━━━━━━━━━━━━━━━━━
"""
    kb = platform_categories_keyboard(platform_label)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


def platforms_keyboard():
    p_map = get_platforms_summary()
    kb = types.InlineKeyboardMarkup(row_width=2)
    row = []
    ordered_keys = [p[2] for p in PLATFORMS] + ["OTHERS"]

    for label in ordered_keys:
        if label in p_map:
            data = p_map[label]
            row.append(
                styled_button(
                    f"{data['icon']} {label} ({data['count']})",
                    callback_data=f"platform:{label}",
                    style="primary"
                )
            )
            if len(row) == 2:
                kb.row(*row)
                row = []
    if row:
        kb.row(*row)

    kb.row(styled_button("🏠 Main Menu", callback_data="main_menu", style="primary"))
    return kb


def platform_categories_keyboard(platform_label):
    categories = get_categories()
    kb = types.InlineKeyboardMarkup(row_width=1)

    for item in categories:
        cat_name = item["category"]
        lbl, icon = detect_platform(cat_name)
        if lbl == platform_label:
            total = item["total"]
            sub_name = cat_name
            for k, _, l in PLATFORMS:
                sub_name = sub_name.replace(k, "").replace(l, "").strip(" -|")
            if not sub_name:
                sub_name = cat_name

            kb.add(
                styled_button(
                    f"▫️ {sub_name} • ({total} Services)",
                    callback_data=f"category:{category_hash(cat_name)}:1",
                    style="primary"
                )
            )

    kb.add(styled_button("⬅️ Back to Platforms", callback_data="back_platforms", style="primary"))
    kb.add(styled_button("🏠 Main Menu", callback_data="main_menu", style="primary"))
    return kb


def service_list_text(page=1):
    """Render services in the requested numbered-list style."""
    conn=get_db(); total=conn.execute("SELECT COUNT(*) c FROM services WHERE enabled=1").fetchone()["c"]
    total_pages=max(1,math.ceil(total/SERVICE_PER_PAGE)); page=max(1,min(page,total_pages)); offset=(page-1)*SERVICE_PER_PAGE
    rows=conn.execute("SELECT * FROM services WHERE enabled=1 ORDER BY id ASC LIMIT ? OFFSET ?",(SERVICE_PER_PAGE,offset)).fetchall(); conn.close()
    lines=["▫️ <b>সার্ভিস মূল্য তালিকা</b>","• <b>[Regular Tier]</b>",f"📄 <b>পৃষ্ঠা:</b> {page} / {total_pages}","━━━━━━━━━━━━━━━━━━━━━━"]
    last_category=None
    for service in rows:
        category=str(service["category"] or "OTHER").upper()
        if category!=last_category:
            if last_category is not None: lines.append("━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"▫️ <b>{category}</b>"); last_category=category
        refill_text="𝗥𝗘𝗙𝗜𝗟𝗟 30D" if int(service["refill"] or 0) else "𝐍𝐎 𝗥𝗘𝗙𝗜𝗟𝗟"
        rate=selling_price(service,1000); sid=display_service_id(service["api_service_id"])
        name=str(service["name"] or "Unnamed Service").replace("<","&lt;").replace(">","&gt;")
        lines.append(f"▫️ <b>{name}</b>\n└ ▫️ {sid} • ▫️ <b>{rate:.2f} ৳</b> / 1K\n└ ▫️ Max {int(service['max_qty']):,} • Min {int(service['min_qty']):,} • Instant • {refill_text}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines),page,total_pages

def service_list_keyboard(page=1):
    text,page,total_pages=service_list_text(page); kb=types.InlineKeyboardMarkup(row_width=2); nav=[]
    if page>1: nav.append(styled_button("⬅️ Previous",callback_data=f"services_page:{page-1}",style="primary"))
    if page<total_pages: nav.append(styled_button("Next ➡️",callback_data=f"services_page:{page+1}",style="primary"))
    if nav: kb.row(*nav)
    kb.row(styled_button("🛒 New Order",callback_data="services_new_order",style="success"),styled_button("🏠 Main Menu",callback_data="main_menu",style="primary"))
    return text,kb


# ============================================================
# MESSAGE HANDLERS: START & GATE
# ============================================================

@bot.message_handler(func=lambda m: not check_joined(m.from_user.id) and m.from_user.id != ADMIN_ID)
def force_join_gate(message):
    force_join_message(message.chat.id)


@bot.message_handler(commands=["start"])
def start(message):
    referral = None
    parts = message.text.split()
    if len(parts) > 1:
        try:
            referral = int(parts[1])
        except Exception:
            referral = None

    save_user(message.from_user, referral)
    if not check_joined(message.from_user.id):
        force_join_message(message.chat.id)
        return

    bot.send_message(
        message.chat.id,
        f"""
<b>🔥 {BOT_NAME}</b>

━━━━━━━━━━━━━━━━━━━━━━
👋 স্বাগতম, <b>{message.from_user.first_name}</b>!
⚡ প্রিমিয়াম SMM সার্ভিস এবং অটোমেটেড অর্ডার সিস্টেম।
━━━━━━━━━━━━━━━━━━━━━━
""",
        reply_markup=main_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join_callback(call):
    if check_joined(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.send_message(call.message.chat.id, "🎉 এক্সেস কনফার্ম হয়েছে!", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ সব চ্যানেলে জয়াইন করুন!", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def main_menu_callback(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id):
        force_join_message(call.message.chat.id)
        return
    bot.send_message(call.message.chat.id, "🏠 <b>DARK SMM PANEL</b>", reply_markup=main_keyboard())


# ============================================================
# SERVICES LIST & NEW ORDER FLOW
# ============================================================

def send_platform_menu(chat_id, message_id=None):
    text = """
🛒 <b>SMM SERVICES LIST & ORDER</b>

━━━━━━━━━━━━━━━━━━━━━━
📱 <b>প্রথমে আপনার পছন্দের প্ল্যাটফর্ম (Platform) সিলেক্ট করুনঃ</b>
━━━━━━━━━━━━━━━━━━━━━━
"""
    kb = platforms_keyboard()
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, reply_markup=kb)


@bot.message_handler(func=lambda m: m.text == "📋 Services List")
def handle_services_list(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        force_join_message(message.chat.id); return
    text,kb=service_list_keyboard(1); bot.send_message(message.chat.id,text,reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🛒 New Order")
def handle_new_order(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        force_join_message(message.chat.id); return
    send_platform_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("services_page:"))
def services_page_callback(call):
    if not check_joined(call.from_user.id) and call.from_user.id != ADMIN_ID:
        force_join_message(call.message.chat.id); return
    try: page=int(call.data.split(":")[1])
    except Exception: page=1
    text,kb=service_list_keyboard(page); bot.answer_callback_query(call.id)
    try: bot.edit_message_text(text,call.message.chat.id,call.message.message_id,reply_markup=kb)
    except Exception: bot.send_message(call.message.chat.id,text,reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "services_new_order")
def services_new_order_callback(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id): force_join_message(call.message.chat.id); return
    send_platform_menu(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("platform:"))
def platform_selected_callback(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id):
        force_join_message(call.message.chat.id)
        return
    platform_label = call.data.split(":", 1)[1]

    text = f"""
📱 <b>{platform_label} SERVICES</b>

━━━━━━━━━━━━━━━━━━━━━━
📂 এখন আপনার প্রয়োজনীয় <b>Service Type (যেমন: Likes, Followers, Views)</b> সিলেক্ট করুন:
━━━━━━━━━━━━━━━━━━━━━━
"""
    kb = platform_categories_keyboard(platform_label)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data.startswith("category:"))
def category_selected_callback(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id):
        force_join_message(call.message.chat.id)
        return
    parts = call.data.split(":")
    category = find_category_by_hash(parts[1])
    if not category:
        bot.answer_callback_query(call.id, "❌ Category পাওয়া যায়নি।", show_alert=True)
        return

    text = f"""
📂 <b>{category}</b>

━━━━━━━━━━━━━━━━━━━━━━
নিচের তালিকা থেকে আপনার পছন্দের সার্ভিসটিতে ক্লিক করুনঃ
━━━━━━━━━━━━━━━━━━━━━━
"""
    kb = tier_services_keyboard(category, 1)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("tier:"))
def tier_selected_callback(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id):
        force_join_message(call.message.chat.id)
        return
    parts = call.data.split(":")
    category = find_category_by_hash(parts[1])
    try:
        page = int(parts[2])
    except Exception:
        page = 1

    if not category:
        bot.answer_callback_query(call.id, "❌ Category পাওয়া যায়নি।", show_alert=True)
        return

    text = f"📂 <b>{category} — Services</b>\n\nনিচের তালিকা থেকে সার্ভিস বেছে নিন:"
    kb = tier_services_keyboard(category, page)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "back_platforms")
def back_platforms_callback(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id):
        force_join_message(call.message.chat.id)
        return
    send_platform_menu(call.message.chat.id, call.message.message_id)


# ============================================================
# ORDER PLACEMENT STEPS
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("order_service:"))
def select_service(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id):
        force_join_message(call.message.chat.id)
        return

    try:
        service_id = int(call.data.split(":")[1])
    except Exception:
        return

    conn = get_db()
    service = conn.execute("SELECT * FROM services WHERE id=? AND enabled=1", (service_id,)).fetchone()
    conn.close()

    if not service:
        bot.answer_callback_query(call.id, "Service unavailable.", show_alert=True)
        return

    price = selling_price(service, 1000)

    msg = bot.send_message(
        call.message.chat.id,
        f"""
🛒 <b>ORDER SERVICE</b>

━━━━━━━━━━━━━━━━━━━━
📂 Category: <b>{service['category']}</b>
📌 Service: <b>{service['name']}</b>
🆔 ID: <code>DARKSMM-{service['api_service_id']}</code>
💰 Rate: <b>৳{price:.2f} / 1000</b>
📉 Min: <b>{service['min_qty']:,}</b> | 📈 Max: <b>{service['max_qty']:,}</b>
━━━━━━━━━━━━━━━━━━━━

🔗 আপনার Post / Profile Link পাঠান:
"""
    )
    bot.register_next_step_handler(msg, receive_link, service_id)


def receive_link(message, service_id):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        return
    if not message.text:
        bot.send_message(message.chat.id, "❌ সঠিক লিংক পাঠান।")
        return

    link = message.text.strip()
    conn = get_db()
    service = conn.execute("SELECT * FROM services WHERE id=? AND enabled=1", (service_id,)).fetchone()
    conn.close()

    if not service:
        bot.send_message(message.chat.id, "❌ Service পাওয়া যায়নি।")
        return

    msg = bot.send_message(message.chat.id, f"🔢 <b>Quantity লিখুন</b>\nMin: {service['min_qty']:,} | Max: {service['max_qty']:,}")
    bot.register_next_step_handler(msg, receive_quantity, service_id, link)


def receive_quantity(message, service_id, link):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        return

    try:
        quantity = int(message.text.strip())
    except Exception:
        bot.send_message(message.chat.id, "❌ Quantity শুধু সংখ্যা হতে হবে।")
        return

    conn = get_db()
    service = conn.execute("SELECT * FROM services WHERE id=? AND enabled=1", (service_id,)).fetchone()
    conn.close()

    if not (service["min_qty"] <= quantity <= service["max_qty"]):
        bot.send_message(message.chat.id, f"❌ সীমার মধ্যে quantity দিন!\nMin: {service['min_qty']:,} | Max: {service['max_qty']:,}")
        return

    price = selling_price(service, quantity)
    user = get_user(message.from_user.id)

    if user["balance"] < price:
        bot.send_message(message.chat.id, f"❌ পর্যাপ্ত ব্যালেন্স নেই!\nপ্রয়োজন: ৳{price:.2f}\nআপনার আছে: ৳{user['balance']:.2f}")
        return

    conn = get_db()
    conn.execute("""
    INSERT INTO pending_orders(user_id, service_id, link, quantity) VALUES(?,?,?,?)
    ON CONFLICT(user_id) DO UPDATE SET service_id=excluded.service_id, link=excluded.link, quantity=excluded.quantity
    """, (message.from_user.id, service_id, link, quantity))
    conn.commit()
    conn.close()

    kb = types.InlineKeyboardMarkup()
    kb.row(
        styled_button("✅ Confirm Order", callback_data="confirm_order", style="success"),
        styled_button("❌ Cancel", callback_data="cancel_order", style="danger")
    )

    bot.send_message(
        message.chat.id,
        f"""
🧾 <b>ORDER CONFIRMATION</b>

━━━━━━━━━━━━━━━━━━━━
📌 Service: <b>{service['name']}</b>
🔗 Link: <code>{link}</code>
🔢 Quantity: <b>{quantity:,}</b>
💰 Total Cost: <b>৳{price:.2f}</b>
💳 Your Balance: <b>৳{user['balance']:.2f}</b>
━━━━━━━━━━━━━━━━━━━━
""",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda call: call.data == "confirm_order")
def confirm_order(call):
    bot.answer_callback_query(call.id, "⏳ Processing...")
    user_id = call.from_user.id

    if not check_joined(user_id):
        force_join_message(call.message.chat.id)
        return

    with db_lock:
        conn = get_db()
        pending = conn.execute("SELECT * FROM pending_orders WHERE user_id=?", (user_id,)).fetchone()
        if not pending:
            conn.close()
            bot.send_message(call.message.chat.id, "⚠️ <b>Order session expired.</b>\nআবার New Order থেকে চেষ্টা করুন।")
            return

        service = conn.execute("SELECT * FROM services WHERE id=? AND enabled=1", (pending["service_id"],)).fetchone()
        if not service:
            conn.close()
            bot.send_message(call.message.chat.id, "❌ এই service এখন admin দ্বারা disabled করা হয়েছে।")
            return

        quantity = int(pending["quantity"])
        link = pending["link"].strip()
        price = selling_price(service, quantity)

        cur = conn.execute(
            """UPDATE users
               SET balance=balance-?, total_spent=total_spent+?, total_orders=total_orders+1
               WHERE id=? AND balance>=?""",
            (price, price, user_id, price)
        )
        if cur.rowcount != 1:
            conn.close()
            bot.send_message(call.message.chat.id, f"❌ <b>Insufficient balance.</b>\nপ্রয়োজন: ৳{price:.2f}")
            return
        conn.commit()
        conn.close()

    result = api_add_order(service["api_service_id"], link, quantity)

    if not isinstance(result, dict) or "order" not in result:
        with db_lock:
            conn = get_db()
            conn.execute(
                "UPDATE users SET balance=balance+?, total_spent=MAX(0,total_spent-?), total_orders=MAX(0,total_orders-1) WHERE id=?",
                (price, price, user_id)
            )
            conn.execute("DELETE FROM pending_orders WHERE user_id=?", (user_id,))
            conn.commit()
            conn.close()
        err = result.get("error", "Provider rejected the order") if isinstance(result, dict) else "Provider API error"
        bot.send_message(call.message.chat.id, f"❌ <b>ORDER FAILED</b>\n\nReason: <code>{str(err)[:300]}</code>\n💰 <b>৳{price:.2f} refunded.</b>")
        return

    api_order_id = str(result["order"])
    provider = provider_cost(service, quantity)

    with db_lock:
        conn = get_db()
        conn.execute(
            """INSERT INTO orders(
                user_id, api_order_id, service_id, service_name, link, quantity,
                cost, provider_cost, profit, status, refunded, refunded_amount
            ) VALUES(?,?,?,?,?,?,?,?,?,?,0,0)""",
            (user_id, api_order_id, service["id"], service["name"], link, quantity,
             price, provider, 0.0, "Processing")
        )
        order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("DELETE FROM pending_orders WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

    bot.send_message(
        call.message.chat.id,
        f"""🎉 <b>ORDER SUBMITTED SUCCESSFULLY</b>

━━━━━━━━━━━━━━━━━━━━
🆔 Order ID: <code>{order_id}</code>
🛠️ Service: <b>{service["name"]}</b>
🔢 Quantity: <b>{quantity:,}</b>
💰 Charged: <b>৳{price:.2f}</b>
📊 Status: <b>Processing</b>
━━━━━━━━━━━━━━━━━━━━"""
    )

    caption = f"""✅ <b>নতুন অর্ডার গ্রহণ করা হয়েছে!</b>

━━━━━━━━━━━━━━━━━━━━
👤 <b>Customer:</b> {call.from_user.first_name or 'User'}
🆔 <b>User ID:</b> <code>{user_id}</code>
🆔 <b>Order ID:</b> <code>{order_id}</code>
━━━━━━━━━━━━━━━━━━━━
🛠️ <b>Service:</b> {service["name"]}
🔢 <b>পরিমাণ:</b> {quantity:,}
🔗 <b>লিংক:</b> {link}
💰 <b>মোট খরচ:</b> ৳{price:.2f}
📊 <b>Status:</b> Processing
━━━━━━━━━━━━━━━━━━━━
⚡ <i>Powered by {BOT_NAME}</i>"""
    try:
        if os.path.exists(ORDER_IMAGE):
            with open(ORDER_IMAGE, "rb") as photo:
                bot.send_photo(ORDER_CHANNEL, photo, caption=caption)
        else:
            bot.send_message(ORDER_CHANNEL, caption)
    except Exception as e:
        print("Order group post error:", e)

    # Referral reward is issued only after a successful provider order.
    reward_referrer_once(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_order(call):
    conn = get_db()
    conn.execute("DELETE FROM pending_orders WHERE user_id=?", (call.from_user.id,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "Order cancelled.")
    try:
        bot.edit_message_text("❌ <b>Order Cancelled</b>", call.message.chat.id, call.message.message_id)
    except Exception:
        pass


# ============================================================
# BALANCE & OTHER SECTIONS
# ============================================================

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        return
    user = get_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"""
💰 <b>MY BALANCE</b>
━━━━━━━━━━━━━━━━━━━━━━
💵 Balance: <b>৳{user['balance']:.2f}</b>
🪙 Coins: <b>{user['coins']:.2f}</b>
📦 Orders: <b>{user['total_orders']}</b>
💸 Total Spent: <b>৳{user['total_spent']:.2f}</b>
👥 Referrals: <b>{user['referral_count']}</b>
━━━━━━━━━━━━━━━━━━━━━━
""",
        reply_markup=main_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "➕ Add Balance")
def add_balance(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, f"➕ <b>ADD BALANCE</b>\n\nকত টাকা যোগ করবেন লিখুন (Minimum: ৳{MIN_DEPOSIT:.2f}):")
    bot.register_next_step_handler(msg, process_payment_amount)


def process_payment_amount(message):
    try:
        amount = float(message.text.strip())
        if amount < MIN_DEPOSIT:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, f"❌ সর্বনিম্ন ৳{MIN_DEPOSIT:.2f} দিন:")
        bot.register_next_step_handler(msg, process_payment_amount)
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        styled_button("💳 bKash", callback_data=f"paymethod:bKash:{amount}", style="success"),
        styled_button("💵 Nagad", callback_data=f"paymethod:Nagad:{amount}", style="success")
    )
    bot.send_message(message.chat.id, f"💰 Amount: <b>৳{amount:.2f}</b>\nমেথড সিলেক্ট করুন:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data.startswith("paymethod:"))
def paymethod_callback(call):
    bot.answer_callback_query(call.id)
    if not check_joined(call.from_user.id):
        force_join_message(call.message.chat.id)
        return
    _, method, amount_text = call.data.split(":", 2)
    amount = float(amount_text)
    msg = bot.send_message(call.message.chat.id, f"💳 <b>{method}</b>\nনম্বর: <code>{BKASH if method == 'bKash' else NAGAD}</code>\n\nটাকা পাঠিয়ে <b>Transaction ID (TrxID)</b> দিন:")
    bot.register_next_step_handler(msg, process_payment_trx, amount, method)
    bot.answer_callback_query(call.id)


def process_payment_trx(message, amount, method):
    trx_id = message.text.strip()
    if not trx_id:
        msg = bot.send_message(message.chat.id, "❌ TrxID দিন:")
        bot.register_next_step_handler(msg, process_payment_trx, amount, method)
        return

    conn = get_db()
    conn.execute("INSERT INTO payments(user_id,amount,method,trx_id) VALUES(?,?,?,?)", (message.from_user.id, amount, method, trx_id))
    payment_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"⏳ <b>Pending Verification</b>\nTrxID: <code>{trx_id}</code>")
    if ADMIN_ID:
        kb = types.InlineKeyboardMarkup()
        kb.row(styled_button("✅ Approve", callback_data=f"payment_ok:{payment_id}", style="success"), styled_button("❌ Reject", callback_data=f"payment_no:{payment_id}", style="danger"))
        bot.send_message(ADMIN_ID, f"💳 <b>NEW PAYMENT</b>\n🆔 #{payment_id}\n👤 <code>{message.from_user.id}</code>\n৳{amount:.2f} ({method})\nTrx: <code>{trx_id}</code>", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data.startswith("payment_ok:") or call.data.startswith("payment_no:"))
def payment_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    approve = call.data.startswith("payment_ok:")
    payment_id = int(call.data.split(":")[1])

    conn = get_db()
    payment = conn.execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone()
    if not payment or payment["status"] != "pending":
        conn.close()
        return

    if approve:
        gross = float(payment["amount"])
        credited = round(gross * DEPOSIT_CREDIT_PERCENT, 2)
        commission = round(gross - credited, 2)
        conn.execute(
            "UPDATE payments SET status='approved', credited_amount=?, commission=? WHERE id=?",
            (credited, commission, payment_id)
        )
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (credited, payment["user_id"]))
        conn.commit()
        conn.close()
        bot.send_message(
            payment["user_id"],
            f"✅ <b>Payment Approved</b>\n\n"
            f"💳 Deposited: ৳{gross:.2f}\n"
            f"💰 Added to balance: <b>৳{credited:.2f}</b>\n"
            f"⚙️ Processing fee: ৳{commission:.2f}"
        )
        bot.answer_callback_query(call.id, "Approved.")
    else:
        conn.execute("UPDATE payments SET status='rejected' WHERE id=?", (payment_id,))
        conn.commit()
        conn.close()
        bot.send_message(payment["user_id"], "❌ পেমেন্ট রিজেক্ট করা হয়েছে।")
        bot.answer_callback_query(call.id, "Rejected.")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text == "📦 My Orders")
def my_orders(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        return
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (message.from_user.id,)).fetchall()
    conn.close()
    if not rows:
        bot.send_message(message.chat.id, "📦 আপনার কোনো অর্ডার নেই।")
        return
    text = "📦 <b>MY ORDERS</b>\n\n"
    for o in rows:
        text += f"🆔 <code>{o['id']}</code>\n📌 {o['service_name'][:30]}\n🔢 {o['quantity']:,} | ৳{o['cost']:.2f}\n📊 {o['status']}\n━━━━━━━━━━━━\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "🎁 Refer & Earn")
def referral(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        return
    user = get_user(message.from_user.id)
    me = bot.get_me()
    link = f"https://t.me/{me.username}?start={user['id']}"
    share_url = f"https://t.me/share/url?url={requests.utils.quote(link, safe='')}&text={requests.utils.quote('DARK SMM PANEL এ Join করুন এবং SMM Service নিন!', safe='')}"
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(styled_button("📤 Share Referral Link", url=share_url, style="success"))
    kb.add(styled_button("🏆 আজকের Top Referrers", callback_data="top_referrers", style="primary"))
    bot.send_message(
        message.chat.id,
        f"""🎁 <b>REFER & EARN</b>

🔗 <b>Your Referral Link</b>
<code>{link}</code>

💰 <b>Reward:</b> ৳{get_referral_reward():.2f}
📌 Referral user-কে channel join করে প্রথম successful service order করতে হবে।
🎯 একজন referral থেকে reward <b>শুধু ১ বার</b>।
👥 Successful Referrals: <b>{user['referral_count']}</b>

বন্ধুদের link-টি share করুন 👇""",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda call: call.data == "top_referrers")
def top_referrers(call):
    if not check_joined(call.from_user.id) and call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "আগে সব channel join করুন।", show_alert=True)
        return
    conn = get_db()
    rows = conn.execute("""
        SELECT u.id, u.username, u.first_name, COUNT(rr.id) AS daily_referrals,
               COALESCE(SUM(rr.reward),0) AS daily_earned
        FROM users u
        JOIN referral_rewards rr ON rr.referrer_id=u.id
        WHERE date(rr.created_at, 'localtime') = date('now', 'localtime')
        GROUP BY u.id, u.username, u.first_name
        ORDER BY daily_referrals DESC, u.id ASC
        LIMIT 10
    """).fetchall()
    conn.close()
    text = "🏆 <b>আজকের TOP REFERRERS</b>\n📅 আজকের successful referral অনুযায়ী\n\n"
    if not rows:
        text += "এখনও কোনো successful referral নেই।"
    else:
        for i, r in enumerate(rows, 1):
            name = (r['first_name'] or r['username'] or str(r['id']))[:22]
            text += f"<b>#{i}</b> {name} — 👥 {r['daily_referrals']} | 💰 ৳{float(r['daily_earned'] or 0):.2f}\n"
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "📞 Support")
def support(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        force_join_message(message.chat.id); return
    kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(styled_button("👨‍💻 ADMIN CANNET",url=f"tg://user?id={ADMIN_ID}",style="primary"))
    bot.send_message(message.chat.id,"📞 <b>SUPPORT</b>\n\nআপনার যেকোনো সমস্যা হলে এডমিনের সাথে যোগাযোগ করুন।\n\nনিচের <b>ADMIN CANNET</b> বাটনে ক্লিক করে সরাসরি এডমিনের সাথে যোগাযোগ করুন।",reply_markup=kb)


@bot.message_handler(func=lambda m: m.text == "⬅️ Main Menu")
def main_menu(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "🏠 <b>DARK SMM PANEL</b>", reply_markup=main_keyboard())


# ============================================================
# ADMIN COMMANDS
# ============================================================

@bot.message_handler(commands=["admin"])
def admin_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "👑 <b>ADMIN PANEL</b>", reply_markup=admin_keyboard())


@bot.message_handler(func=lambda m: m.text == "🔄 Sync Services")
def admin_sync(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "⏳ Syncing...")
    ok, res = sync_services()
    if ok:
        bot.send_message(message.chat.id, f"✅ Sync Complete! Imported: <b>{res}</b> services.")
    else:
        bot.send_message(message.chat.id, f"❌ Sync Failed: {res}")


@bot.message_handler(func=lambda m: m.text == "📋 Services")
def admin_services(message):
    if message.from_user.id != ADMIN_ID:
        return
    send_admin_services(message.chat.id, 1)


def build_admin_service_markup(page=1):
    conn = get_db()
    offset = (page - 1) * 10
    rows = conn.execute(
        "SELECT id, name, enabled FROM services ORDER BY id ASC LIMIT 10 OFFSET ?",
        (offset,)
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) c FROM services").fetchone()["c"]
    conn.close()

    kb = types.InlineKeyboardMarkup(row_width=1)
    for s in rows:
        mark = "🟢" if int(s["enabled"]) else "🔴"
        kb.add(styled_button(
            f"{mark} #{s['id']} | {s['name'][:38]}",
            callback_data=f"svc_toggle:{s['id']}:{page}",
            style="success" if s["enabled"] else "danger"
        ))
    nav=[]
    if page > 1:
        nav.append(styled_button("⬅️ Previous", callback_data=f"svc_page:{page-1}", style="primary"))
    if offset + len(rows) < total:
        nav.append(styled_button("Next ➡️", callback_data=f"svc_page:{page+1}", style="primary"))
    if nav:
        kb.row(*nav)
    return kb


def send_admin_services(chat_id, page=1):
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) c FROM services").fetchone()["c"]
    conn.close()
    bot.send_message(
        chat_id,
        f"""⚙️ <b>SERVICE CONTROL</b>

🟢 Allowed = users can see/order
🔴 Disabled = hidden from users

📦 Total: <b>{total}</b>
📄 Page: <b>{page}</b>

Tap a service to allow/disable it.""",
        reply_markup=build_admin_service_markup(page)
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("svc_toggle:"))
def admin_service_toggle(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Admin only.", show_alert=True)
        return
    try:
        _, sid, page = call.data.split(":")
        sid, page = int(sid), max(1, int(page))
    except Exception:
        bot.answer_callback_query(call.id, "Invalid service.", show_alert=True)
        return

    with db_lock:
        conn = get_db()
        row = conn.execute("SELECT enabled, name FROM services WHERE id=?", (sid,)).fetchone()
        if not row:
            conn.close()
            bot.answer_callback_query(call.id, "Service not found.", show_alert=True)
            return
        new_state = 0 if int(row["enabled"]) else 1
        conn.execute("UPDATE services SET enabled=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_state, sid))
        conn.commit()
        conn.close()

    bot.answer_callback_query(call.id, "🟢 Allowed" if new_state else "🔴 Disabled")
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id, call.message.message_id,
            reply_markup=build_admin_service_markup(page)
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("svc_page:"))
def admin_service_page(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Admin only.", show_alert=True)
        return
    try:
        page=max(1,int(call.data.split(":")[1]))
    except Exception:
        page=1
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id, call.message.message_id,
            reply_markup=build_admin_service_markup(page)
        )
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text == "💰 Balance Manager")
def admin_balance_manager(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(
        message.chat.id,
        "💰 <b>BALANCE MANAGER</b>\\n\\n"
        "Format: <code>USER_ID AMOUNT</code>\\n"
        "Add: <code>123456789 500</code>\\n"
        "Deduct: <code>123456789 -100</code>"
    )
    bot.register_next_step_handler(msg, admin_balance_process)


def admin_balance_process(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts=message.text.strip().split()
        uid=int(parts[0]); amount=float(parts[1])
    except Exception:
        bot.send_message(message.chat.id, "❌ Format ভুল: <code>USER_ID AMOUNT</code>")
        return
    with db_lock:
        conn=get_db()
        user=conn.execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
        if not user:
            conn.close()
            bot.send_message(message.chat.id, "❌ User পাওয়া যায়নি।")
            return
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (amount,uid))
        conn.commit()
        new_balance=float(user["balance"])+amount
        conn.close()
    bot.send_message(message.chat.id, f"✅ Balance updated\\nUser: <code>{uid}</code>\\nNew Balance: <b>৳{new_balance:.2f}</b>")
    try:
        bot.send_message(uid, f"💰 <b>Balance Updated</b>\\n{'➕ Added' if amount >= 0 else '➖ Deducted'}: ৳{abs(amount):.2f}\\nNew: <b>৳{new_balance:.2f}</b>")
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text == "📊 Dashboard")
def dashboard(message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = get_db()
    users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    orders = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    commission = conn.execute("SELECT COALESCE(SUM(commission),0) c FROM payments WHERE status='approved'").fetchone()["c"]
    conn.close()
    prov = api_balance()
    prov_bal = prov.get("balance", "N/A") if isinstance(prov, dict) else "N/A"
    bot.send_message(message.chat.id, f"📊 <b>Dashboard</b>\n\n👥 Users: <b>{users}</b>\n📦 Orders: <b>{orders}</b>\n💼 Deposit Commission: <b>৳{float(commission or 0):.2f}</b>\n🏦 Provider Balance: <b>{prov_bal}</b>")


@bot.message_handler(func=lambda m: m.text == "👥 Users")
def admin_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = get_db()
    rows = conn.execute("SELECT id, first_name, username, balance, referral_count FROM users ORDER BY id DESC LIMIT 20").fetchall()
    total = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    conn.close()
    text = f"👥 <b>USERS</b> — Total: <b>{total}</b>\n\n"
    for r in rows:
        name = (r["first_name"] or r["username"] or "User")[:18]
        text += f"<code>{r['id']}</code> • {name}\n💰 ৳{float(r['balance'] or 0):.2f} | 👥 {r['referral_count']}\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "🛒 Orders")
def admin_orders(message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = get_db()
    rows = conn.execute("SELECT id,user_id,service_name,quantity,cost,status,created_at FROM orders ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    text = "🛒 <b>RECENT ORDERS</b>\n\n"
    if not rows:
        text += "No orders yet."
    else:
        for o in rows:
            text += f"🆔 <code>{o['id']}</code> | 👤 <code>{o['user_id']}</code>\n📌 {o['service_name'][:28]}\n📦 {o['quantity']:,} | ৳{o['cost']:.2f}\n📊 {o['status']}\n━━━━━━━━━━━━\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "💳 Payments")
def admin_payments(message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = get_db()
    rows = conn.execute("SELECT id,user_id,amount,credited_amount,commission,method,trx_id,status,created_at FROM payments ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    text = "💳 <b>PAYMENTS</b>\n\n"
    if not rows:
        text += "No payments yet."
    else:
        for p in rows:
            text += f"🆔 #{p['id']} | 👤 <code>{p['user_id']}</code>\n💵 Paid ৳{p['amount']:.2f} | Added ৳{float(p['credited_amount'] or 0):.2f}\n📌 {p['method']} | {p['status']}\nTrx: <code>{p['trx_id']}</code>\n━━━━━━━━━━━━\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "🎁 Referral Settings")
def admin_referral_settings(message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        styled_button("💰 Set Reward", callback_data="admin_set_ref_reward", style="success"),
        styled_button("🏆 Today Top", callback_data="top_referrers", style="primary")
    )
    bot.send_message(message.chat.id, f"🎁 <b>REFERRAL SETTINGS</b>\n\n💰 Reward: <b>৳{get_referral_reward():.2f}</b>\n📌 Reward only after channel join + first successful provider order.\n🔒 One referred user = one reward.", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "admin_set_ref_reward")
def admin_set_ref_reward(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 নতুন referral reward লিখুন (যেমন: 10):")
    bot.register_next_step_handler(msg, process_ref_reward)

def process_ref_reward(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        value = float(message.text.strip())
        if value < 0 or value > 100000:
            raise ValueError
    except Exception:
        bot.send_message(message.chat.id, "❌ সঠিক amount দিন।")
        return
    set_setting("referral_reward", round(value, 2))
    bot.send_message(message.chat.id, f"✅ Referral reward set to <b>৳{value:.2f}</b>")


@bot.message_handler(func=lambda m: m.text == "⚙️ Settings")
def admin_settings(message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        styled_button("💰 Set Profit", callback_data="admin_set_profit", style="primary"),
        styled_button("🎁 Set Referral", callback_data="admin_set_ref_reward", style="success")
    )
    bot.send_message(message.chat.id, f"⚙️ <b>BOT SETTINGS</b>\n\n💰 Service markup: <b>৳{get_profit():.2f}/1K</b>\n💳 Deposit credit: <b>{DEPOSIT_CREDIT_PERCENT*100:.0f}%</b>\n💼 Deposit commission: <b>{(1-DEPOSIT_CREDIT_PERCENT)*100:.0f}%</b>\n🎁 Referral reward: <b>৳{get_referral_reward():.2f}</b>\n💵 Minimum deposit: <b>৳{MIN_DEPOSIT:.2f}</b>", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "admin_set_profit")
def admin_set_profit(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 প্রতি 1K-তে markup লিখুন (0 হলে provider/website rate):")
    bot.register_next_step_handler(msg, process_profit)

def process_profit(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        value = float(message.text.strip())
        if value < 0 or value > 100000:
            raise ValueError
    except Exception:
        bot.send_message(message.chat.id, "❌ সঠিক amount দিন।")
        return
    set_setting("default_profit", round(value, 2))
    bot.send_message(message.chat.id, f"✅ Profit/markup set to <b>৳{value:.2f}/1K</b>\n⚠️ Service sync-এর পরও এই setting ব্যবহার হবে।")


@bot.message_handler(func=lambda m: m.text == "🔌 API Settings")
def admin_api_settings(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, f"🔌 <b>API SETTINGS</b>\n\nURL: <code>{SMM_API_URL}</code>\nKey: <code>{SMM_API_KEY[:4]}••••••••{SMM_API_KEY[-4:]}</code>")


@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "📢 <b>BROADCAST</b>\n\nআপনার broadcast message পাঠান:")
    bot.register_next_step_handler(msg, process_broadcast)


def process_broadcast(message):
    if message.from_user.id != ADMIN_ID or not message.text:
        return
    conn = get_db()
    ids = [r["id"] for r in conn.execute("SELECT id FROM users").fetchall()]
    conn.close()
    ok = 0
    for uid in ids:
        try:
            bot.send_message(uid, message.text)
            ok += 1
        except Exception:
            pass
        time.sleep(0.03)
    bot.send_message(message.chat.id, f"📢 Broadcast complete: <b>{ok}/{len(ids)}</b>")


@bot.message_handler(func=lambda m: m.text == "🧹 Reset Balances")
def admin_reset_balances(message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        styled_button("⚠️ YES, RESET ALL", callback_data="confirm_reset_balances", style="danger"),
        styled_button("❌ Cancel", callback_data="cancel_reset_balances", style="primary")
    )
    bot.send_message(message.chat.id, "⚠️ <b>WARNING</b>\n\nএটি সব user-এর current balance 0.00 করে দেবে। Existing balance ফেরত আনার automatic উপায় থাকবে না।\n\nনিশ্চিত হলে নিচের button চাপুন।", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_reset_balances")
def confirm_reset_balances(call):
    if call.from_user.id != ADMIN_ID:
        return
    with db_lock:
        conn = get_db()
        cur = conn.execute("UPDATE users SET balance=0, coins=0")
        conn.commit()
        conn.close()
    bot.answer_callback_query(call.id, "All balances reset.", show_alert=True)
    bot.send_message(call.message.chat.id, f"✅ সব user-এর balance ও referral coins 0 করা হয়েছে।\n👥 Updated users: <b>{cur.rowcount}</b>")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_reset_balances")
def cancel_reset_balances(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id, "Cancelled")
    try:
        bot.edit_message_text("❌ Balance reset cancelled.", call.message.chat.id, call.message.message_id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def statistics(message):
    if not check_joined(message.from_user.id) and message.from_user.id != ADMIN_ID:
        return
    conn = get_db()
    users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    orders = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    total = conn.execute("SELECT COALESCE(SUM(cost),0) s FROM orders").fetchone()["s"]
    conn.close()
    bot.send_message(message.chat.id, f"📊 <b>STATISTICS</b>\n\n👥 Users: <b>{users}</b>\n📦 Orders: <b>{orders}</b>\n💰 Order Volume: <b>৳{float(total or 0):.2f}</b>")


@bot.message_handler(commands=["topref"])
def topref_command(message):
    top_referrers(message)


# ============================================================
# WORKER & RUNNING
# ============================================================

def refund_order_if_needed(order_id, reason, remaining=None):
    with db_lock:
        conn=get_db()
        order=conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order or int(order["refunded"] or 0):
            conn.close()
            return 0.0
        charged=float(order["cost"] or 0)
        qty=int(order["quantity"] or 0)
        if remaining is None:
            refund=charged
        else:
            try: rem=max(0,int(float(remaining)))
            except Exception: rem=0
            refund=charged*(rem/qty) if qty else 0.0
        refund=round(max(0.0,min(charged,refund)),2)
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (refund,order["user_id"]))
        conn.execute("UPDATE orders SET refunded=1, refunded_amount=?, refund_reason=? WHERE id=? AND refunded=0",
                     (refund,reason[:200],order_id))
        conn.commit(); conn.close()
    if refund>0:
        try:
            bot.send_message(order["user_id"],f"💸 <b>REFUND PROCESSED</b>\\n\\n🆔 Order: <code>{order_id}</code>\\n💰 Refunded: <b>৳{refund:.2f}</b>\\n📌 {reason}")
        except Exception: pass
    return refund


def status_worker():
    while True:
        try:
            conn=get_db()
            orders=conn.execute(
                """SELECT id, api_order_id FROM orders
                   WHERE refunded=0
                     AND status NOT IN ('Completed','Canceled','Cancelled','Partial','Failed')
                   ORDER BY id ASC LIMIT 50"""
            ).fetchall()
            conn.close()
            for o in orders:
                try:
                    res=api_status(o["api_order_id"])
                    if isinstance(res,dict) and "status" in res:
                        st=str(res["status"]); rem=str(res.get("remains","")); start=str(res.get("start_count",""))
                        with db_lock:
                            conn=get_db()
                            conn.execute("UPDATE orders SET status=?, remains=?, start_count=? WHERE id=?",(st,rem,start,o["id"]))
                            conn.commit(); conn.close()
                        low=st.strip().lower()
                        if low in ("canceled","cancelled","failed"):
                            refund_order_if_needed(o["id"],f"Provider status: {st}")
                        elif low=="partial":
                            refund_order_if_needed(o["id"],"Provider marked order Partial",remaining=rem)
                except Exception as e:
                    print("Status check error:",e)
                time.sleep(0.15)
        except Exception as e:
            print("Status worker error:",e)
        time.sleep(45)


if __name__ == "__main__":
    init_db()
    set_setting("default_profit", DEFAULT_PROFIT)
    print("🔥 DARK SMM PANEL STARTED SUCCESSFULLY!")
    threading.Thread(target=status_worker, daemon=True).start()
    
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)
