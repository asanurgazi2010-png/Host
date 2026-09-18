#!/usr/bin/env python3
"""
QURESHIxOTP Hype V10.7 — Project Management + Reliability Edition

WARNING:
This bot executes uploaded Python/Node.js projects and connected GitHub repositories. Run it only inside an isolated
container or VM. It is not a security sandbox.

Recommended:
Python 3.11+
python-telegram-bot[job-queue]>=22,<23
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
import shutil
import shlex
import signal
import subprocess
import secrets
import hashlib
import base64
import sqlite3
import platform
import sys
import time
import zipfile
import threading
import urllib.request
import urllib.error
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from telegram import (
    InlineKeyboardButton as TelegramInlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    KeyboardButton as TelegramKeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    BotCommand,
)

def _button_style(text: Any) -> str:
    label = str(text).casefold()
    if any(x in label for x in ("delete", "stop", "ban", "remove", "🗑", "🛑", "🚫", "🧨")):
        return "danger"
    if any(x in label for x in ("start", "verify", "join", "approve", "restore", "▶", "✅", "🟢")):
        return "success"
    return "primary"

def InlineKeyboardButton(*args: Any, **kwargs: Any) -> TelegramInlineKeyboardButton:
    kwargs.setdefault("style", _button_style(args[0] if args else kwargs.get("text", "")))
    return TelegramInlineKeyboardButton(*args, **kwargs)

def KeyboardButton(*args: Any, **kwargs: Any) -> TelegramKeyboardButton:
    kwargs.setdefault("style", _button_style(args[0] if args else kwargs.get("text", "")))
    return TelegramKeyboardButton(*args, **kwargs)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — EDIT HERE
# ═════════════════════════════════════════════════════════════════════════════

# Revoke every token previously shared in chat and paste a NEW BotFather token.
TOKEN = os.getenv("BOT_TOKEN", "8554102086:AAGT_YljbCzHKrmGWtCei-X-IUTmgQgWIKA")

OWNER_ID = int(os.getenv("OWNER_ID", "8103866669"))
ACCESS_PASSWORD = "558800"

BRAND_NAME = "ASANUR BRO "
OWNER_NAME = "ASANUR BRO"
OWNER_USERNAME = "@Developer_Asanur"

CHANNEL_LINKS = [
    "https://t.me/zx_community",
    "https://t.me/eran_bd1",
    "https://t.me/As_Smm_proof",
    "https://t.me/all_paymant",
]
CHANNEL_USERNAMES = ["@zx_community", "@all_paymant", "@eran_bd1", "@As_Smm_proof"]
CHANNEL_NAMES = ["JOIN", "JOIN", "JOIN", "JOIN"]
MAIN_CHANNEL_NAME = CHANNEL_NAMES[0]
MAIN_CHANNEL_LINK = CHANNEL_LINKS[0]
MAIN_CHANNEL_USERNAME = CHANNEL_USERNAMES[0]
SUPPORT_GROUP_NAME = CHANNEL_NAMES[1]
SUPPORT_GROUP_LINK = CHANNEL_LINKS[1]
SUPPORT_GROUP_USERNAME = CHANNEL_USERNAMES[1]
SUPPORT_LINK = CHANNEL_LINKS[0]
BACKUP_CHAT_ID = 0
BACKUP_CHAT_LINK = ""

MAX_FILE_MB = 20
MAX_ZIP_EXPANDED_MB = 100

DEFAULT_CREDITS = 2
CREDIT_PER_UPLOAD = 1
PREMIUM_BONUS_CREDITS = 100

DAILY_UPLOAD_LIMIT = 1
PREMIUM_DAILY_UPLOAD_LIMIT = 50

MAX_RUNNING_PER_USER = 2
PREMIUM_MAX_RUNNING_PER_USER = 10

LAUNCH_CHECK_SECONDS = 2.0
MAX_LOG_CHARS = 3000
MAX_RESTARTS = 3
INSTALL_TIMEOUT_SECONDS = 180
MAX_INSTALL_OUTPUT_CHARS = 3500
DEPENDENCY_TIMEOUT_SECONDS = int(os.getenv("DEPENDENCY_TIMEOUT_SECONDS", "300"))
DEFAULT_PROJECT_RAM_MB = int(os.getenv("DEFAULT_PROJECT_RAM_MB", "256"))
DEFAULT_PROJECT_CPU_PERCENT = int(os.getenv("DEFAULT_PROJECT_CPU_PERCENT", "50"))
AUTO_INSTALL_DEPENDENCIES = os.getenv("AUTO_INSTALL_DEPENDENCIES", "1") == "1"
SECURITY_SCAN_ENABLED = os.getenv("SECURITY_SCAN_ENABLED", "1") == "1"
DOCKER_MODE = os.getenv("DOCKER_MODE", "0") == "1"
ENFORCE_RESOURCE_LIMITS = os.getenv("ENFORCE_RESOURCE_LIMITS", "1") == "1"
# RLIMIT_NPROC is counted per Linux UID on many hosts, not per project. A low
# value can prevent Telegram/httpx from creating DNS/helper threads when
# several bots share the same panel account. Keep it disabled by default.
PROJECT_PROCESS_LIMIT = int(os.getenv("PROJECT_PROCESS_LIMIT", "0"))
# RLIMIT_AS limits virtual address space rather than real RSS and can break
# modern Python runtimes even when actual RAM usage is low. Opt in explicitly.
ENFORCE_ADDRESS_SPACE_LIMIT = os.getenv("ENFORCE_ADDRESS_SPACE_LIMIT", "0") == "1"
PROJECT_OPEN_FILES_LIMIT = int(os.getenv("PROJECT_OPEN_FILES_LIMIT", "512"))
DOCKER_IMAGE_PYTHON = os.getenv("DOCKER_IMAGE_PYTHON", "python:3.11-slim")
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
WATCHDOG_INTERVAL_DEFAULT = max(20, int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "40")))
LOG_ROTATE_MAX_MB = max(1, int(os.getenv("LOG_ROTATE_MAX_MB", "2")))
LOG_ROTATE_KEEP_MB = max(1, int(os.getenv("LOG_ROTATE_KEEP_MB", "1")))
DEFAULT_STORAGE_QUOTA_MB = max(50, int(os.getenv("DEFAULT_STORAGE_QUOTA_MB", "500")))
PANEL_REMINDER_HOURS = max(24, int(os.getenv("PANEL_REMINDER_HOURS", "72")))
CRASH_WINDOW_SECONDS = max(60, int(os.getenv("CRASH_WINDOW_SECONDS", "600")))
CRASH_LIMIT = max(2, int(os.getenv("CRASH_LIMIT", "5")))

# Python-only runtime + built-in health/keep-alive service
PYTHON_ONLY_MODE = False
GITHUB_POLL_SECONDS = max(60, int(os.getenv("GITHUB_POLL_SECONDS", "90")))
OWNER_UPLOAD_LIMIT_BYPASS = True
HEALTH_PORT = int(os.getenv("PORT", os.getenv("HEALTH_PORT", "8080")))
KEEPALIVE_INTERVAL_DEFAULT = max(30, min(45, int(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "40"))))
KEEPALIVE_URL_ENV = os.getenv("KEEPALIVE_URL", "").strip()

def _auto_public_url() -> str:
    direct = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if direct:
        return direct.rstrip("/") + "/health"
    for key in ("RAILWAY_PUBLIC_DOMAIN", "KOYEB_PUBLIC_DOMAIN"):
        domain = os.getenv(key, "").strip()
        if domain:
            if not domain.startswith(("http://", "https://")):
                domain = "https://" + domain
            return domain.rstrip("/") + "/health"
    fly = os.getenv("FLY_APP_NAME", "").strip()
    if fly:
        return f"https://{fly}.fly.dev/health"
    return ""

KEEPALIVE_URL_DEFAULT = KEEPALIVE_URL_ENV or _auto_public_url()

FORCE_JOIN_ENABLED = True
AUTO_RESTART_ENABLED = False
MAINTENANCE_MODE_DEFAULT = False

# ═════════════════════════════════════════════════════════════════════════════
# PATHS & LOGGING
# ═════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DATA_FILE = BASE_DIR / "bot_data.json"
PROJECTS_FILE = BASE_DIR / "projects.json"
V7_DATA_FILE = BASE_DIR / "v7_data.json"
V9_DB_FILE = BASE_DIR / "QURESHIxOTP_v9.db"
PROJECT_BACKUPS_DIR = BASE_DIR / "project_backups"
BACKUPS_DIR = BASE_DIR / "backups"
GITHUB_TOKENS_FILE = BASE_DIR / ".github_tokens.json"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

START_TIME = time.time()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("QURESHIxOTPHostV1073")

# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class ScriptProcess:
    display_name: str
    entry_file: str
    folder: str
    log_path: str
    proc: subprocess.Popen[Any] | None = None
    started_at: float = field(default_factory=time.time)
    restarts: int = 0
    auto_restart: bool = AUTO_RESTART_ENABLED
    desired_running: bool = False
    runtime: str = "python"
    source_type: str = "upload"
    repo_url: str = ""
    branch: str = "main"
    commit_sha: str = ""

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    @property
    def pid(self) -> str:
        return str(self.proc.pid) if self.proc else "—"

    @property
    def exit_code(self) -> str:
        if self.proc is None:
            return "Not started"
        if self.proc.poll() is None:
            return "Running"
        return str(self.proc.returncode)

    def serialize(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name,
            "entry_file": self.entry_file,
            "folder": self.folder,
            "log_path": self.log_path,
            "started_at": self.started_at,
            "restarts": self.restarts,
            "auto_restart": self.auto_restart,
            "was_running": bool(self.running or self.desired_running),
            "runtime": self.runtime,
            "source_type": self.source_type,
            "repo_url": self.repo_url,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
        }


approved_users: set[int] = set()
premium_users: set[int] = set()
banned_users: set[int] = set()

user_stats: dict[str, dict[str, Any]] = {}
user_credits: dict[str, int] = {}
custom_daily_limits: dict[str, int] = {}
custom_running_limits: dict[str, int] = {}

maintenance_mode = MAINTENANCE_MODE_DEFAULT

# V7 premium state (kept separately for safe migration from V6)
premium_expiry: dict[str, str] = {}
user_plans: dict[str, str] = {}
redeem_codes: dict[str, dict[str, Any]] = {}
project_envs: dict[str, dict[str, str]] = {}
project_settings: dict[str, dict[str, Any]] = {}
audit_log: list[dict[str, Any]] = []
admin_roles: dict[str, str] = {}
user_storage_limits: dict[str, int] = {}
watchdog_enabled: bool = True
watchdog_interval: int = WATCHDOG_INTERVAL_DEFAULT
watchdog_last_epoch: float = 0.0
watchdog_restarts: int = 0
panel_reminder_enabled: bool = True
panel_last_confirmed_at: float = time.time()
panel_last_reminder_at: float = 0.0
brand_footer: str = "⚡ QURESHIxOTP"

keepalive_enabled: bool = False
keepalive_url: str = KEEPALIVE_URL_DEFAULT
keepalive_interval: int = KEEPALIVE_INTERVAL_DEFAULT
keepalive_last_status: str = "Not run yet"
keepalive_last_at: str = "—"
keepalive_failures: int = 0
keepalive_last_epoch: float = 0.0
health_server_started: bool = False

running_scripts: dict[int, list[ScriptProcess]] = {}
pending_project_names: dict[int, ScriptProcess] = {}
user_locks: dict[int, asyncio.Lock] = {}

# ═════════════════════════════════════════════════════════════════════════════
# STORAGE
# ═════════════════════════════════════════════════════════════════════════════

def lock_for(user_id: int) -> asyncio.Lock:
    return user_locks.setdefault(user_id, asyncio.Lock())


def load_data() -> None:
    global approved_users, premium_users, banned_users
    global user_stats, user_credits
    global custom_daily_limits, custom_running_limits, maintenance_mode

    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text("utf-8"))
            approved_users = {int(x) for x in data.get("approved_users", [])}
            premium_users = {int(x) for x in data.get("premium_users", [])}
            banned_users = {int(x) for x in data.get("banned_users", [])}
            user_stats = dict(data.get("user_stats", {}))
            user_credits = {
                str(k): int(v)
                for k, v in data.get("user_credits", {}).items()
            }
            custom_daily_limits = {
                str(k): int(v)
                for k, v in data.get("custom_daily_limits", {}).items()
            }
            custom_running_limits = {
                str(k): int(v)
                for k, v in data.get("custom_running_limits", {}).items()
            }
            maintenance_mode = bool(
                data.get("maintenance_mode", MAINTENANCE_MODE_DEFAULT)
            )
        except Exception:
            logger.exception("Could not load bot data")

    if PROJECTS_FILE.exists():
        try:
            data = json.loads(PROJECTS_FILE.read_text("utf-8"))
            for uid, rows in data.items():
                items: list[ScriptProcess] = []
                for row in rows:
                    entry = Path(row["entry_file"])
                    folder = Path(row["folder"])
                    if entry.exists() and folder.exists():
                        items.append(
                            ScriptProcess(
                                display_name=row.get(
                                    "display_name", entry.name
                                ),
                                entry_file=str(entry),
                                folder=str(folder),
                                log_path=row.get(
                                    "log_path",
                                    str(folder / "runtime.log"),
                                ),
                                started_at=float(
                                    row.get("started_at", time.time())
                                ),
                                restarts=int(row.get("restarts", 0)),
                                auto_restart=bool(
                                    row.get(
                                        "auto_restart",
                                        AUTO_RESTART_ENABLED,
                                    )
                                ),
                                desired_running=bool(row.get("was_running", False)),
                                runtime=str(row.get("runtime", runtime_for_entry(entry))),
                                source_type=str(row.get("source_type", "upload")),
                                repo_url=str(row.get("repo_url", "")),
                                branch=str(row.get("branch", "main")),
                                commit_sha=str(row.get("commit_sha", "")),
                            )
                        )
                running_scripts[int(uid)] = items
        except Exception:
            logger.exception("Could not load project registry")


def save_data() -> None:
    payload = {
        "approved_users": sorted(approved_users),
        "premium_users": sorted(premium_users),
        "banned_users": sorted(banned_users),
        "user_stats": user_stats,
        "user_credits": user_credits,
        "custom_daily_limits": custom_daily_limits,
        "custom_running_limits": custom_running_limits,
        "maintenance_mode": maintenance_mode,
    }

    temp = DATA_FILE.with_suffix(".tmp")
    try:
        temp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            "utf-8",
        )
        temp.replace(DATA_FILE)
        if V9_DB_FILE.exists(): sync_v9_database()
    except Exception:
        logger.exception("Could not save bot data")
        temp.unlink(missing_ok=True)


def save_projects() -> None:
    payload = {
        str(uid): [item.serialize() for item in items]
        for uid, items in running_scripts.items()
    }

    temp = PROJECTS_FILE.with_suffix(".tmp")
    try:
        temp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            "utf-8",
        )
        temp.replace(PROJECTS_FILE)
        if V9_DB_FILE.exists(): sync_v9_database()
    except Exception:
        logger.exception("Could not save project registry")
        temp.unlink(missing_ok=True)


def load_v7_data() -> None:
    global premium_expiry, user_plans, redeem_codes, project_envs
    global project_settings, audit_log, admin_roles
    global keepalive_enabled, keepalive_url, keepalive_interval
    global user_storage_limits, watchdog_enabled, watchdog_interval
    global panel_reminder_enabled, panel_last_confirmed_at, panel_last_reminder_at, brand_footer
    if not V7_DATA_FILE.exists():
        return
    try:
        data = json.loads(V7_DATA_FILE.read_text("utf-8"))
        premium_expiry = dict(data.get("premium_expiry", {}))
        user_plans = dict(data.get("user_plans", {}))
        redeem_codes = dict(data.get("redeem_codes", {}))
        project_envs = {str(k): dict(v) for k, v in data.get("project_envs", {}).items()}
        project_settings = {str(k): dict(v) for k, v in data.get("project_settings", {}).items()}
        audit_log = list(data.get("audit_log", []))[-2000:]
        admin_roles = dict(data.get("admin_roles", {}))
        user_storage_limits = {str(k): int(v) for k, v in data.get("user_storage_limits", {}).items()}
        wd = data.get("watchdog", {})
        watchdog_enabled = bool(wd.get("enabled", True))
        watchdog_interval = max(20, int(wd.get("interval", WATCHDOG_INTERVAL_DEFAULT)))
        pr = data.get("panel_reminder", {})
        panel_reminder_enabled = bool(pr.get("enabled", True))
        panel_last_confirmed_at = float(pr.get("last_confirmed_at", time.time()))
        panel_last_reminder_at = float(pr.get("last_reminder_at", 0.0))
        brand_footer = str(data.get("brand_footer", brand_footer))
        ka = data.get("keepalive", {})
        keepalive_enabled = bool(ka.get("enabled", False))
        keepalive_url = str(ka.get("url", KEEPALIVE_URL_DEFAULT) or KEEPALIVE_URL_DEFAULT)
        keepalive_interval = max(30, min(45, int(ka.get("interval", KEEPALIVE_INTERVAL_DEFAULT))))
    except Exception:
        logger.exception("Could not load V7 data")


def save_v7_data() -> None:
    payload = {
        "premium_expiry": premium_expiry,
        "user_plans": user_plans,
        "redeem_codes": redeem_codes,
        "project_envs": project_envs,
        "project_settings": project_settings,
        "audit_log": audit_log[-2000:],
        "admin_roles": admin_roles,
        "user_storage_limits": user_storage_limits,
        "watchdog": {"enabled": watchdog_enabled, "interval": watchdog_interval},
        "panel_reminder": {
            "enabled": panel_reminder_enabled,
            "last_confirmed_at": panel_last_confirmed_at,
            "last_reminder_at": panel_last_reminder_at,
        },
        "brand_footer": brand_footer,
        "keepalive": {
            "enabled": keepalive_enabled,
            "url": keepalive_url,
            "interval": keepalive_interval,
        },
    }
    temp = V7_DATA_FILE.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")
        temp.replace(V7_DATA_FILE)
        if V9_DB_FILE.exists(): sync_v9_database()
    except Exception:
        logger.exception("Could not save V7 data")
        temp.unlink(missing_ok=True)



def init_v9_database() -> None:
    """Create a durable SQLite mirror while retaining JSON backward compatibility."""
    try:
        with sqlite3.connect(V9_DB_FILE) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS snapshots (name TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, actor INTEGER, action TEXT, target TEXT, detail TEXT)")
            db.commit()
    except Exception:
        logger.exception("Could not initialize V9 SQLite database")


def sync_v9_database() -> None:
    try:
        snapshots = {
            "users": {
                "approved_users": sorted(approved_users), "premium_users": sorted(premium_users),
                "banned_users": sorted(banned_users), "user_stats": user_stats,
                "user_credits": user_credits, "custom_daily_limits": custom_daily_limits,
                "custom_running_limits": custom_running_limits, "maintenance_mode": maintenance_mode,
            },
            "projects": {str(uid): [x.serialize() for x in rows] for uid, rows in running_scripts.items()},
            "premium": {
                "premium_expiry": premium_expiry, "user_plans": user_plans,
                "redeem_codes": redeem_codes, "project_envs": project_envs,
                "project_settings": project_settings, "admin_roles": admin_roles,
                "user_storage_limits": user_storage_limits,
            },
        }
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(V9_DB_FILE) as db:
            for name, payload in snapshots.items():
                db.execute(
                    "INSERT INTO snapshots(name,payload,updated_at) VALUES(?,?,?) "
                    "ON CONFLICT(name) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at",
                    (name, json.dumps(payload, ensure_ascii=False), now),
                )
            db.commit()
    except Exception:
        logger.exception("Could not sync V9 SQLite database")


def db_event(actor: int, action: str, target: str = "", detail: str = "") -> None:
    try:
        with sqlite3.connect(V9_DB_FILE) as db:
            db.execute(
                "INSERT INTO events(created_at,actor,action,target,detail) VALUES(?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), actor, action, target, detail[:1000]),
            )
            db.commit()
    except Exception:
        logger.exception("Could not write V9 database event")


def user_storage_mb(user_id: int) -> float:
    total = 0
    for item in scripts_for(user_id):
        folder = Path(item.folder)
        if not folder.exists():
            continue
        try:
            for f in folder.rglob("*"):
                if f.is_file() and ".venv" not in f.parts:
                    total += f.stat().st_size
        except OSError:
            pass
    return total / (1024 * 1024)


def storage_limit_mb(user_id: int) -> int:
    if is_owner(user_id): return 999999999
    if str(user_id) in user_storage_limits: return int(user_storage_limits[str(user_id)])
    plan=user_plans.get(str(user_id), "premium" if user_id in premium_users else "free")
    catalog=project_settings.get("__v10_global__",{}).get("plan_catalog",{})
    if plan in catalog: return int(catalog[plan].get("storage",DEFAULT_STORAGE_QUOTA_MB))
    return DEFAULT_STORAGE_QUOTA_MB


def project_setting(item: ScriptProcess) -> dict[str, Any]:
    return project_settings.setdefault(project_key(item), {})


def clean_project_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_. -]+", "_", value).strip()[:80] or "project"


def diagnose_log_text(text: str) -> list[str]:
    checks = [
        ("ModuleNotFoundError", "Missing Python package — repair/reinstall requirements."),
        ("SyntaxError", "Python syntax error — inspect the referenced file/line."),
        ("event loop is already running", "Async startup conflict — avoid nesting run_polling() inside asyncio.run()."),
        ("can't start new thread", "Host thread/process resource pressure detected."),
        ("InvalidToken", "Telegram bot token is invalid or revoked."),
        ("Unauthorized", "Authentication/token permission error detected."),
        ("Conflict", "Another instance may already be polling with the same Telegram token."),
        ("PermissionError", "Project tried to access a path/resource without permission."),
        ("No space left on device", "Server disk is full or quota is exhausted."),
        ("MemoryError", "Project ran out of available Python memory."),
    ]
    found = [msg for key, msg in checks if key.casefold() in text.casefold()]
    return found or ["No known signature detected. Review the latest runtime log manually."]


def audit(actor: int, action: str, target: str = "", detail: str = "") -> None:
    audit_log.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "actor": actor,
        "action": action,
        "target": target,
        "detail": detail[:500],
    })
    save_v7_data()
    db_event(actor, action, target, detail)


def project_key(item_or_folder: Any) -> str:
    folder = item_or_folder.folder if hasattr(item_or_folder, "folder") else str(item_or_folder)
    return hashlib.sha256(str(Path(folder).resolve()).encode()).hexdigest()[:24]


def expiry_active(user_id: int) -> bool:
    raw = premium_expiry.get(str(user_id), "")
    if not raw or raw == "lifetime":
        return bool(raw == "lifetime" or user_id in premium_users)
    try:
        return datetime.fromisoformat(raw) > datetime.now()
    except ValueError:
        return False


def expire_plans() -> None:
    changed = False
    for uid, raw in list(premium_expiry.items()):
        if raw in ("", "lifetime"):
            continue
        try:
            if datetime.fromisoformat(raw) <= datetime.now():
                premium_users.discard(int(uid))
                user_plans[uid] = "free"
                premium_expiry.pop(uid, None)
                changed = True
        except (ValueError, TypeError):
            premium_expiry.pop(uid, None)
            changed = True
    if changed:
        save_data(); save_v7_data()


def parse_duration(value: str) -> timedelta | None:
    m = re.fullmatch(r"(\d+)([mhd])", value.strip().lower())
    if not m:
        return None
    amount, unit = int(m.group(1)), m.group(2)
    return {"m": timedelta(minutes=amount), "h": timedelta(hours=amount), "d": timedelta(days=amount)}[unit]


def plan_limits(user_id: int) -> tuple[int, int, int]:
    plan = user_plans.get(str(user_id), "premium" if user_id in premium_users else "free")
    legacy = {"free": (DAILY_UPLOAD_LIMIT, 1, 128), "basic": (5,3,256), "premium": (25,10,512), "business": (100,30,1024), "lifetime": (100,30,1024)}
    catalog = project_settings.get("__v10_global__", {}).get("plan_catalog", {})
    if plan in catalog:
        row=catalog[plan]; return (int(row.get("daily", legacy.get(plan, legacy["free"])[0])), int(row.get("projects", legacy.get(plan, legacy["free"])[1])), int(row.get("ram", legacy.get(plan, legacy["free"])[2])))
    return legacy.get(plan, legacy["free"])


def scan_project(folder: Path) -> tuple[str, list[str]]:
    findings: list[str] = []
    patterns = {
        "Shell execution": r"(?:os\.system|subprocess\.(?:Popen|run|call))",
        "Dynamic code execution": r"(?:\beval\s*\(|\bexec\s*\(|Function\s*\()",
        "Environment access": r"(?:os\.environ|os\.getenv)",
        "Encoded payload": r"(?:base64\.(?:b64decode|decodebytes))",
        "Reverse-shell indicator": r"(?:/bin/sh|/bin/bash|nc\s+-e|socket\.socket)",
        "Destructive filesystem operation": r"(?:shutil\.rmtree|rm\s+-rf|os\.remove)",
        "Crypto-mining indicator": r"(?:xmrig|stratum\+tcp|monero)",
    }
    for file in sum((list(folder.rglob(p)) for p in ("*.py","*.js","*.mjs","*.cjs","*.php","*.sh","*.rb")), []):
        if file.stat().st_size > 2_000_000:
            continue
        try:
            text = file.read_text("utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in patterns.items():
            if re.search(pattern, text, re.I):
                findings.append(f"{label}: {file.relative_to(folder)}")
    findings = sorted(set(findings))
    high = any("Reverse" in x or "mining" in x or "Destructive" in x for x in findings)
    risk = "HIGH" if high else ("MEDIUM" if findings else "LOW")
    return risk, findings[:20]



def prepare_compatible_requirements(req: Path, folder: Path) -> tuple[Path, list[str]]:
    """Create a runtime-compatible requirements file without modifying user files."""
    notes: list[str] = []
    try:
        lines = req.read_text("utf-8", errors="replace").splitlines()
    except OSError:
        return req, notes

    # python-telegram-bot 20.x has a known slots/Updater initialization failure on
    # Python 3.13. Keep the user's API generation close while selecting a release
    # that officially added Python 3.13 support.
    if sys.version_info >= (3, 13):
        changed = False
        output: list[str] = []
        ptb_pattern = re.compile(r"^\s*python-telegram-bot(?:\[[^]]+\])?\s*(?:==|~=|<=|<)\s*20(?:\.[^;\s]+)?(.*)$", re.I)
        for line in lines:
            stripped = line.strip()
            match = ptb_pattern.match(stripped)
            if match and not stripped.startswith("#"):
                extras_match = re.match(r"^\s*python-telegram-bot(\[[^]]+\])?", stripped, re.I)
                extras = extras_match.group(1) if extras_match and extras_match.group(1) else ""
                marker = match.group(1) or ""
                output.append(f"python-telegram-bot{extras}>=21.4,<22{marker}")
                changed = True
            else:
                output.append(line)
        if changed:
            compatible = folder / ".QURESHIxOTP-requirements.txt"
            compatible.write_text("\n".join(output) + "\n", encoding="utf-8")
            notes.append("python-telegram-bot 20.x adjusted to >=21.4,<22 for Python 3.13 compatibility")
            return compatible, notes

    return req, notes

def install_project_dependencies(folder: Path, entry: Path, log_path: Path) -> str:
    notes: list[str] = []
    blacklist={str(x).lower() for x in project_settings.get("__v10_global__",{}).get("package_blacklist",[])}
    if blacklist:
        manifests=[]
        manifests += list(folder.rglob("requirements.txt"))
        manifests += list(folder.rglob("package.json"))
        blob="\n".join(x.read_text("utf-8",errors="ignore").lower() for x in manifests[:20])
        hit=next((pkg for pkg in blacklist if pkg and pkg in blob),None)
        if hit: raise RuntimeError(f"Dependency blocked by host policy: {hit}")
    if entry.suffix.lower() == ".py":
        req = next(iter(folder.rglob("requirements.txt")), None)
        if req and AUTO_INSTALL_DEPENDENCIES:
            install_req, compatibility_notes = prepare_compatible_requirements(req, folder)
            notes.extend(compatibility_notes)
            venv_dir = folder / ".venv"
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, timeout=60)
            py = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            result = subprocess.run([str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", str(install_req)], cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=DEPENDENCY_TIMEOUT_SECONDS)
            out = result.stdout.decode("utf-8", errors="replace")
            with log_path.open("a", encoding="utf-8", errors="replace") as log_file:
                log_file.write("\n\n===== Dependency Installation =====\n")
                log_file.write(out)
                if out and not out.endswith("\n"):
                    log_file.write("\n")
            if result.returncode != 0:
                raise RuntimeError("requirements.txt installation failed; check runtime.log")
            notes.append("Python dependencies installed in private .venv")
    elif entry.suffix.lower() in {".js", ".mjs", ".cjs"}:
        package = next(iter(folder.rglob("package.json")), None)
        if package and AUTO_INSTALL_DEPENDENCIES:
            node = shutil.which("node")
            npm = shutil.which("npm")
            if not node:
                raise RuntimeError("Node.js runtime is not installed on this host. Ask the panel provider to enable Node.js.")
            if not npm:
                # If node_modules was bundled, allow launch without forcing an impossible install.
                if (package.parent / "node_modules").exists():
                    notes.append("npm unavailable; bundled node_modules detected, dependency install skipped")
                else:
                    raise RuntimeError("npm is not installed on this host. Node.js exists but npm is unavailable; enable npm in the panel runtime.")
            else:
                attempts=[]
                lock=package.parent / "package-lock.json"
                if lock.exists():
                    attempts.append([npm,"ci","--ignore-scripts","--no-audit","--no-fund"])
                attempts += [
                    [npm,"install","--ignore-scripts","--legacy-peer-deps","--no-audit","--no-fund"],
                    [npm,"install","--ignore-scripts","--force","--no-audit","--no-fund"],
                ]
                combined=[]; ok=False
                for cmd in attempts:
                    try:
                        result=subprocess.run(cmd,cwd=package.parent,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=DEPENDENCY_TIMEOUT_SECONDS)
                        out=result.stdout.decode("utf-8",errors="replace")
                        combined.append("$ "+" ".join(cmd[1:])+"\n"+out)
                        if result.returncode==0:
                            ok=True; break
                    except subprocess.TimeoutExpired:
                        combined.append("$ "+" ".join(cmd[1:])+"\nTimed out")
                with log_path.open("a",encoding="utf-8",errors="replace") as log_file:
                    log_file.write("\n\n===== Node Dependency Installation =====\n"+"\n\n".join(combined)+"\n")
                if not ok:
                    tail=("\n".join(combined))[-1200:]
                    raise RuntimeError("Node dependency installation failed after npm ci/install recovery attempts. Last output: "+tail)
                notes.append("Node dependencies installed with npm recovery mode")
    return "; ".join(notes) or "No dependency manifest detected"


def project_resources(item: ScriptProcess) -> dict[str, str]:
    result = {"cpu": "N/A", "ram": "N/A", "disk": "0 MB"}
    try:
        total = sum(f.stat().st_size for f in Path(item.folder).rglob("*") if f.is_file())
        result["disk"] = f"{total / 1024 / 1024:.1f} MB"
    except OSError:
        pass
    if item.running and item.proc:
        try:
            import psutil  # optional
            proc = psutil.Process(item.proc.pid)
            result["cpu"] = f"{proc.cpu_percent(interval=0.1):.1f}%"
            result["ram"] = f"{proc.memory_info().rss / 1024 / 1024:.1f} MB"
        except Exception:
            pass
    return result


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def esc(value: Any) -> str:
    return html.escape(str(value))


def premium_box(title: str, lines: list[str]) -> str:
    """Render the requested premium Telegram frame."""
    body = "\n".join(f"┃ {line}" if line else "┃" for line in lines)
    footer = globals().get("brand_footer", "")
    footer_line = f"\n┃ {esc(footer)}" if footer else ""
    return (
        f"<b>╭━━〔 {esc(title)} 〕━━┈⊷</b>\n"
        f"{body}{footer_line}\n"
        f"<b>╰━━━━━━━━━━━━━━━┈⊷</b>"
    )


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_approved(user_id: int) -> bool:
    return is_owner(user_id) or user_id in approved_users


def is_premium(user_id: int) -> bool:
    expire_plans()
    return is_owner(user_id) or (user_id in premium_users and expiry_active(user_id))


def plan_name(user_id: int) -> str:
    if is_owner(user_id):
        return "👑 Owner"
    if is_premium(user_id):
        plan = user_plans.get(str(user_id), "premium").title()
        return f"💎 {plan}"
    if is_approved(user_id):
        return "✅ Approved"
    return "🔒 Guest"


def get_credits(user_id: int) -> int:
    return int(user_credits.get(str(user_id), DEFAULT_CREDITS))


def set_credits(user_id: int, value: int) -> None:
    user_credits[str(user_id)] = max(0, int(value))
    save_data()


def get_stat(user_id: int) -> dict[str, Any]:
    key = str(user_id)
    if key not in user_stats:
        user_stats[key] = {
            "uploads_total": 0,
            "uploads_today": 0,
            "last_upload_date": "",
            "last_active": "",
            "username": "",
            "first_name": "",
        }
    return user_stats[key]


def touch_user(user: Any) -> None:
    stat = get_stat(user.id)
    stat["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stat["username"] = user.username or ""
    stat["first_name"] = user.first_name or ""
    save_data()


def reset_daily(user_id: int) -> None:
    stat = get_stat(user_id)
    today = date.today().isoformat()
    if stat.get("last_upload_date") != today:
        stat["last_upload_date"] = today
        stat["uploads_today"] = 0
        save_data()


def daily_limit(user_id: int) -> int:
    if is_owner(user_id):
        return 999_999
    if str(user_id) in custom_daily_limits:
        return custom_daily_limits[str(user_id)]
    return plan_limits(user_id)[0]


def running_limit(user_id: int) -> int:
    if is_owner(user_id):
        return 999_999
    if str(user_id) in custom_running_limits:
        return custom_running_limits[str(user_id)]
    return plan_limits(user_id)[1]


def user_folder(user_id: int) -> Path:
    folder = DOWNLOADS_DIR / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def clean_filename(name: str) -> str:
    name = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)[:120] or "upload.bin"


def clean_project_name(name: str) -> str:
    cleaned = re.sub(r"[\x00-\x1f<>]", "", name).strip()
    return cleaned[:40]


def uptime(started_at: float = START_TIME) -> str:
    seconds = max(0, int(time.time() - started_at))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def scripts_for(user_id: int) -> list[ScriptProcess]:
    return running_scripts.setdefault(user_id, [])


def active_count(user_id: int) -> int:
    return sum(item.running for item in scripts_for(user_id))


def find_project(
    user_id: int,
    target: str,
) -> tuple[int, ScriptProcess] | None:
    target_folded = target.casefold()
    for index, item in enumerate(scripts_for(user_id)):
        if (
            item.display_name.casefold() == target_folded
            or Path(item.entry_file).name.casefold() == target_folded
        ):
            return index, item
    return None


def safe_remove_folder(folder_value: str) -> None:
    folder = Path(folder_value)
    try:
        folder.resolve().relative_to(DOWNLOADS_DIR.resolve())
    except (ValueError, OSError):
        raise ValueError("Unsafe project path")
    shutil.rmtree(folder, ignore_errors=True)


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    max_uncompressed = MAX_ZIP_EXPANDED_MB * 1024 * 1024
    total = 0

    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            total += info.file_size
            if total > max_uncompressed:
                raise ValueError(
                    f"ZIP expands beyond {MAX_ZIP_EXPANDED_MB} MB"
                )

            target = (destination / info.filename).resolve()
            try:
                target.relative_to(destination.resolve())
            except ValueError:
                raise ValueError("Unsafe ZIP path detected")

            file_type = (info.external_attr >> 16) & 0o170000
            if file_type == 0o120000:
                raise ValueError("ZIP symlinks are not allowed")

        archive.extractall(destination)



def safe_extract_zip_owner(zip_path: Path, destination: Path) -> None:
    """Owner bypasses QURESHIxOTP expanded-size quota, never path/symlink safety."""
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            target = (destination / info.filename).resolve()
            try:
                target.relative_to(destination.resolve())
            except ValueError:
                raise ValueError("Unsafe ZIP path detected")
            file_type = (info.external_attr >> 16) & 0o170000
            if file_type == 0o120000:
                raise ValueError("ZIP symlinks are not allowed")
        archive.extractall(destination)

def detect_entries(folder: Path) -> list[Path]:
    """Return likely Python/Node entry files in priority order."""
    priority = ("main.py", "bot.py", "app.py", "index.py", "server.py", "run.py",
                "main.js", "bot.js", "app.js", "index.js", "server.js", "index.mjs", "index.cjs",
                "index.php", "main.php", "run.sh", "start.sh", "main.rb", "app.rb")
    found: list[Path] = []
    seen: set[str] = set()
    for name in priority:
        for match in sorted(folder.rglob(name)):
            key = str(match.resolve())
            if key not in seen and ".venv" not in match.parts and "node_modules" not in match.parts:
                found.append(match); seen.add(key)
    for pattern in ("*.py", "*.js", "*.mjs", "*.cjs", "*.php", "*.sh", "*.rb", "*.jar"):
        for match in sorted(folder.rglob(pattern)):
            key = str(match.resolve())
            if key not in seen and ".venv" not in match.parts and "node_modules" not in match.parts:
                found.append(match); seen.add(key)
    return found


def detect_entry(folder: Path) -> Path | None:
    entries = detect_entries(folder)
    return entries[0] if entries else None


def runtime_for_entry(entry: Path) -> str:
    ext=entry.suffix.lower()
    return {".py":"python",".js":"node",".mjs":"node",".cjs":"node",".php":"php",".sh":"bash",".rb":"ruby",".jar":"java"}.get(ext,"unknown")


def run_command(entry: Path) -> list[str] | None:
    suffix=entry.suffix.lower()
    if suffix == ".py":
        private_py=None
        for parent in (entry.parent,*entry.parents):
            candidate=parent/".venv"/("Scripts/python.exe" if os.name=="nt" else "bin/python")
            if candidate.exists(): private_py=candidate; break
        return [str(private_py) if private_py else sys.executable,"-u",str(entry)]
    if suffix in {".js",".mjs",".cjs"}:
        exe=shutil.which("node")
        if not exe: raise RuntimeError("Node.js runtime is not installed on this host")
        return [exe,str(entry)]
    if suffix == ".php":
        exe=shutil.which("php")
        if not exe: raise RuntimeError("PHP CLI is not installed on this host")
        return [exe,str(entry)]
    if suffix == ".sh":
        exe=shutil.which("bash") or shutil.which("sh")
        if not exe: raise RuntimeError("Bash/sh is not installed on this host")
        return [exe,str(entry)]
    if suffix == ".rb":
        exe=shutil.which("ruby")
        if not exe: raise RuntimeError("Ruby is not installed on this host")
        return [exe,str(entry)]
    if suffix == ".jar":
        exe=shutil.which("java")
        if not exe: raise RuntimeError("Java runtime is not installed on this host")
        return [exe,"-jar",str(entry)]
    return None


def spawn_script(
    item: ScriptProcess | None,
    entry: Path,
    folder: Path,
    log_path: Path,
) -> ScriptProcess:
    cmd = run_command(entry)
    if not cmd:
        raise ValueError("Unsupported project entry")
    if item is not None and project_locked(item):
        item.desired_running = False
        raise RuntimeError("PROJECT_LOCKED: this project is locked by an administrator")

    log_handle = open(
        log_path,
        "a",
        encoding="utf-8",
        errors="replace",
        buffering=1,
    )
    log_handle.write(
        f"\n===== Launch {datetime.now().isoformat(timespec='seconds')} =====\n"
    )

    # V10.7: hosted projects never inherit manager secrets.
    ready, missing = ensure_project_env_ready(item, folder)
    if not ready:
        if item is not None:
            item.desired_running = False
            save_projects()
        raise RuntimeError("ENV_SETUP_REQUIRED: missing " + ", ".join(missing) + ". Use /setenv PROJECT KEY VALUE then start again.")
    env = sanitized_host_environment()
    env.update({"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"})
    env.update(_active_project_env(item, folder))

    preexec_fn = None
    if os.name != "nt" and ENFORCE_RESOURCE_LIMITS:
        def apply_limits() -> None:
            try:
                import resource
                settings = project_settings.get(project_key(folder), {})
                ram_mb = int(settings.get("ram_mb", DEFAULT_PROJECT_RAM_MB))
                max_bytes = max(128, ram_mb) * 1024 * 1024
                if entry.suffix.lower() == ".py" and ENFORCE_ADDRESS_SPACE_LIMIT:
                    resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
                if PROJECT_PROCESS_LIMIT > 0:
                    resource.setrlimit(
                        resource.RLIMIT_NPROC,
                        (PROJECT_PROCESS_LIMIT, PROJECT_PROCESS_LIMIT),
                    )
                if PROJECT_OPEN_FILES_LIMIT > 0:
                    resource.setrlimit(
                        resource.RLIMIT_NOFILE,
                        (PROJECT_OPEN_FILES_LIMIT, PROJECT_OPEN_FILES_LIMIT),
                    )
            except Exception:
                pass
        preexec_fn = apply_limits

    proc = subprocess.Popen(
        cmd,
        cwd=str(folder),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        env=env,
        start_new_session=(os.name != "nt"),
        close_fds=(os.name != "nt"),
        preexec_fn=preexec_fn,
    )

    if item is None:
        item = ScriptProcess(
            display_name=entry.name,
            entry_file=str(entry),
            folder=str(folder),
            log_path=str(log_path),
            proc=proc,
            runtime=runtime_for_entry(entry),
        )
    else:
        item.proc = proc
        item.started_at = time.time()
    item.desired_running = True

    save_projects()
    return item


def kill_process(item: ScriptProcess) -> bool:
    if not item.running:
        return True

    assert item.proc is not None
    proc = item.proc

    try:
        if os.name == "nt":
            proc.terminate()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                proc.kill()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)

        save_projects()
        return True

    except Exception:
        logger.exception("Failed stopping PID %s", proc.pid)
        return False


async def edit_message(
    query: Any,
    text: str,
    markup: InlineKeyboardMarkup | None = None,
) -> None:
    try:
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
    except BadRequest as exc:
        if "Message is not modified" not in str(exc):
            raise


# ═════════════════════════════════════════════════════════════════════════════
# PREMIUM UI
# ═════════════════════════════════════════════════════════════════════════════

def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton("🚀 ʜᴏsᴛ ᴘʀᴏᴊᴇᴄᴛ"),
            KeyboardButton("📂 ᴍʏ ᴘʀᴏᴊᴇᴄᴛs"),
        ],
        [
            KeyboardButton("🧾 ʟɪᴠᴇ ʟᴏɢs"),
            KeyboardButton("⚙️ ᴄᴏɴᴛʀᴏʟs"),
        ],
        [
            KeyboardButton("💳 ᴡᴀʟʟᴇᴛ"),
            KeyboardButton("📊 ᴀᴄᴄᴏᴜɴᴛ"),
        ],
        [
            KeyboardButton("💎 ᴘʟᴀɴs"),
            KeyboardButton("🆘 sᴜᴘᴘᴏʀᴛ"),
        ],
    ]

    if is_owner(user_id):
        rows.append([KeyboardButton("👑 ᴀᴅᴍɪɴ ᴄᴇɴᴛᴇʀ")])

    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        is_persistent=True,
    )


def home_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 QURESHIxOTP • 1", url=CHANNEL_LINKS[0]),
         InlineKeyboardButton("📢 QURESHIxOTP • 2", url=CHANNEL_LINKS[1])],
        [InlineKeyboardButton("📢 QURESHIxOTP • 3", url=CHANNEL_LINKS[2]),
         InlineKeyboardButton("📢 QURESHIxOTP • 4", url=CHANNEL_LINKS[3])],
    ])


def join_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join • QURESHIxOTP 1", url=CHANNEL_LINKS[0])],
        [InlineKeyboardButton("📢 Join • QURESHIxOTP 2", url=CHANNEL_LINKS[1])],
        [InlineKeyboardButton("📢 Join • QURESHIxOTP 3", url=CHANNEL_LINKS[2])],
        [InlineKeyboardButton("📢 Join • QURESHIxOTP 4", url=CHANNEL_LINKS[3])],
        [InlineKeyboardButton("✅ Verify Membership", callback_data="join:check")],
    ])


def project_list_buttons(user_id: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    for index, item in enumerate(scripts_for(user_id)):
        icon = "🟢" if item.running else "🔴"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} {item.display_name[:28]}",
                    callback_data=f"project:view:{index}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="project:list",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def project_control_buttons(
    index: int,
    running: bool,
) -> InlineKeyboardMarkup:
    primary = (
        InlineKeyboardButton(
            "🛑 Stop",
            callback_data=f"project:stop:{index}",
        )
        if running
        else InlineKeyboardButton(
            "▶️ Start",
            callback_data=f"project:start:{index}",
        )
    )

    return InlineKeyboardMarkup(
        [
            [
                primary,
                InlineKeyboardButton(
                    "🔁 Restart",
                    callback_data=f"project:restart:{index}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🧾 Logs",
                    callback_data=f"project:logs:{index}",
                ),
                InlineKeyboardButton(
                    "📄 Log File",
                    callback_data=f"project:logfile:{index}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "✏️ Rename",
                    callback_data=f"project:rename:{index}",
                ),
                InlineKeyboardButton(
                    "🗑 Delete",
                    callback_data=f"project:delete:{index}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Projects",
                    callback_data="project:list",
                )
            ],
        ]
    )


def admin_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📊 Overview",
                    callback_data="admin:overview",
                ),
                InlineKeyboardButton(
                    "👥 Users",
                    callback_data="admin:users",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🚀 Processes",
                    callback_data="admin:processes",
                ),
                InlineKeyboardButton(
                    "💎 Premium",
                    callback_data="admin:premium",
                ),
            ],
            [
                InlineKeyboardButton(
                    "💳 Credits",
                    callback_data="admin:credits",
                ),
                InlineKeyboardButton(
                    "🚫 Banned",
                    callback_data="admin:banned",
                ),
            ],
            [
                InlineKeyboardButton(
                    "▶️ Start Everything",
                    callback_data="admin:startall",
                ),
                InlineKeyboardButton(
                    "🧨 Stop Everything",
                    callback_data="admin:stopall",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔐 Force Join",
                    callback_data="admin:forcejoin",
                ),
                InlineKeyboardButton(
                    "🛠 Maintenance",
                    callback_data="admin:maintenance",
                ),
            ],
            [
                InlineKeyboardButton("💓 Keep Alive", callback_data="admin:keepalive"),
                InlineKeyboardButton("🖥 Host Status", callback_data="admin:hoststatus"),
            ],
            [InlineKeyboardButton("📊 Analytics", callback_data="admin:analytics"), InlineKeyboardButton("🛡 Watchdog", callback_data="admin:watchdog")],
            [InlineKeyboardButton("👥 Active Users", callback_data="admin:users"), InlineKeyboardButton("🐙 GitHub", callback_data="admin:v10github")],
            [InlineKeyboardButton("🚨 Emergency", callback_data="admin:v10emergency"), InlineKeyboardButton("📦 Backup Vault", callback_data="admin:backupinfo")],
            [InlineKeyboardButton("🛡 Security", callback_data="admin:security"), InlineKeyboardButton("💾 Backup Now", callback_data="admin:backupnow")],
            [
                InlineKeyboardButton(
                    "🧹 Cleanup",
                    callback_data="admin:cleanup",
                ),
                InlineKeyboardButton(
                    "📖 Commands",
                    callback_data="admin:commands",
                ),
            ],
            [InlineKeyboardButton("❌ Close", callback_data="admin:close")],
        ]
    )


def home_text(user_id: int) -> str:
    reset_daily(user_id)
    stat = get_stat(user_id)
    return premium_box(
        f"⚡ {BRAND_NAME.upper()} ⚡",
        [
            "<i>ᴘʀᴇᴍɪᴜᴍ ᴛᴇʟᴇɢʀᴀᴍ ʜᴏsᴛɪɴɢ</i>",
            "",
            f"👤 <b>ᴘʟᴀɴ</b>  •  {esc(plan_name(user_id))}",
            f"🆔 <b>ᴜsᴇʀ ɪᴅ</b>  •  <code>{user_id}</code>",
            f"🟢 <b>ʀᴜɴɴɪɴɢ</b>  •  <code>{active_count(user_id)}/{running_limit(user_id)}</code>",
            f"📤 <b>ᴜᴘʟᴏᴀᴅs</b>  •  <code>{stat['uploads_today']}/{daily_limit(user_id)}</code>",
            f"💳 <b>ᴄʀᴇᴅɪᴛs</b>  •  <code>{get_credits(user_id)}</code>",
            f"⏱ <b>ᴜᴘᴛɪᴍᴇ</b>  •  <code>{uptime()}</code>",
            "",
            "📦 Upload Python/Node/PHP/Bash/Ruby/Java projects or connect GitHub.",
        ],
    )


def projects_text(user_id: int) -> str:
    items = scripts_for(user_id)

    if not items:
        return (
            "<b>📂 ᴍʏ ᴘʀᴏᴊᴇᴄᴛs</b>\n\n"
            "No hosted projects found.\n"
            "Send a <code>.py</code>, <code>.js</code>, or <code>.zip</code> file — or use <code>/connectrepo</code>."
        )

    lines = ["<b>📂 ᴍʏ ᴘʀᴏᴊᴇᴄᴛs</b>", ""]

    for index, item in enumerate(items, start=1):
        status = (
            "🟢 Online"
            if item.running
            else f"🔴 Offline ({esc(item.exit_code)})"
        )

        lines.append(
            f"<b>{index}. {esc(item.display_name)}</b>\n"
            f"   {status}\n"
            f"   PID: <code>{esc(item.pid)}</code>"
        )

    return "\n\n".join(lines)


def admin_overview() -> str:
    all_items = [item for items in running_scripts.values() for item in items]
    active = sum(item.running for item in all_items)
    crashed = sum(1 for item in all_items if not item.running and item.proc is not None)
    try:
        import psutil
        ram=f"{psutil.virtual_memory().percent:.0f}%"; disk=f"{psutil.disk_usage(str(BASE_DIR)).percent:.0f}%"
    except Exception:
        ram=disk="N/A"

    return (
        f"<b>╭── 👑 {esc(BRAND_NAME)} Admin ──╮</b>\n"
        f"<b>╰────────────────────────╯</b>\n\n"
        f"👥 Total Users: <code>{len(user_stats)}</code>\n"
        f"🟢 Active Today: <code>{sum(1 for x in user_stats.values() if str(x.get('last_active','')).startswith(date.today().isoformat()))}</code>\n"
        f"💎 Premium: <code>{len(premium_users)}</code>\n"
        f"🚫 Banned: <code>{len(banned_users)}</code>\n"
        f"💳 Credit wallets: <code>{len(user_credits)}</code>\n"
        f"🧩 Registered projects: <code>{len(all_items)}</code>\n"
        f"🟢 Active processes: <code>{active}</code>\n"
        f"🔐 Force Join: "
        f"<code>{'ON' if FORCE_JOIN_ENABLED else 'OFF'}</code>\n"
        f"🛠 Maintenance: "
        f"<code>{'ON' if maintenance_mode else 'OFF'}</code>\n"
        f"🐍 Runtime: <code>Python {platform.python_version()}</code>\n"
        f"💓 Keep Alive: <code>{'ON' if keepalive_enabled else 'OFF'}</code> / <code>{keepalive_interval}s</code>\n"
        f"🌐 Health Port: <code>{HEALTH_PORT}</code>\n"
        f"⏱ Uptime: <code>{uptime()}</code>"
    )


def admin_commands_text() -> str:
    return (
        "<b>📖 Owner Commands</b>\n\n"
        "<code>/admin</code> — Admin panel\n"
        "<code>/approve USER_ID</code> — Approve user\n"
        "<code>/revoke USER_ID</code> — Remove access\n"
        "<code>/premium USER_ID</code> — Give premium\n"
        "<code>/unpremium USER_ID</code> — Remove premium\n"
        "<code>/ban USER_ID</code> — Ban and stop projects\n"
        "<code>/unban USER_ID</code> — Unban user\n"
        "<code>/userinfo USER_ID</code> — User information\n"
        "<code>/addcredits USER_ID AMOUNT</code>\n"
        "<code>/setcredits USER_ID AMOUNT</code>\n"
        "<code>/takecredits USER_ID AMOUNT</code>\n"
        "<code>/credits USER_ID</code>\n"
        "<code>/setdaily USER_ID LIMIT</code>\n"
        "<code>/setrunning USER_ID LIMIT</code>\n"
        "<code>/broadcast MESSAGE</code>\n"
        "<code>/maintenance on|off</code>\n"
        "<code>/startall</code> — Start all stopped projects\n"
        "<code>/stopalladmin</code> — Stop all projects\n"
        "<code>/cleanup</code> — Remove missing/stopped registry\n"
        "<code>/backup</code> — Download bot data backup\n"
        "<code>/install PACKAGE</code> — Safe owner package installer\n"
        "<code>/installed</code> — List Python packages\n"
        "<code>/keepalive [on|off]</code> — Keep-alive status/toggle\n"
        "<code>/setkeepalive URL [30-45]</code> — Set ping URL/interval\n"
        "<code>/hoststats</code> — Server health & resources\n"
        "<code>/security</code> — Security/runtime status\n"
        "<code>/finduser QUERY</code> — Find stored user\n"
        "<code>/allprojects</code> — All hosted Python projects\n"
        "<code>/restartall</code> — Restart all registered projects\n"
        "<code>/requests</code> — Pending access queue\n"
        "<code>/approve1|approve10|approveall</code> — Bulk approve\n"
        "<code>/reject1|reject10|rejectall</code> — Bulk reject\n"
        "<code>/emergency KEY on|off</code> — Server controls\n"
        "<code>/restartcrashed</code> — Restart offline projects\n"
        "<code>/planbuilder ...</code> — Dynamic plans\n\n"
        "<b>User Commands</b>\n\n"
        "<code>/start</code>\n"
        "<code>/projects</code>\n"
        "<code>/logs [PROJECT]</code>\n"
        "<code>/restart PROJECT</code>\n"
        "<code>/stop PROJECT</code>\n"
        "<code>/delete PROJECT</code>\n"
        "<code>/rename OLD NEW</code>\n"
        "<code>/credits</code>\n"
        "<code>/connectrepo URL [branch]</code> — GitHub deploy\n"
        "<code>/repos</code> / <code>/syncrepo</code> / <code>/autodeploy</code>\n"
        "<code>/redeploy PROJECT</code> / <code>/rollback PROJECT</code>\n"
        "<code>/notifications</code> / <code>/ticket</code> / <code>/usage</code>\n"
        "<code>/skip</code>"
    )


# ═════════════════════════════════════════════════════════════════════════════
# ACCESS CONTROL
# ═════════════════════════════════════════════════════════════════════════════

async def check_join(
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    if not FORCE_JOIN_ENABLED or is_owner(user_id):
        return True

    try:
        valid = {"member", "administrator", "creator"}
        statuses = []
        for username in CHANNEL_USERNAMES:
            member = await context.bot.get_chat_member(username, user_id)
            statuses.append(member.status)
        return all(status in valid for status in statuses)

    except TelegramError:
        logger.warning(
            "Force-join failed. Make the bot admin in both required chats."
        )
        return False


async def guard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return False

    touch_user(user)
    if context.args and context.args[0].startswith("ref_") and context.args[0][4:].isdigit():
        ref=int(context.args[0][4:]); refs=global_cfg().setdefault("referrals",{}); claimed=global_cfg().setdefault("ref_claimed",{})
        if ref != user.id and str(user.id) not in claimed:
            refs.setdefault(str(ref),[]).append(user.id); claimed[str(user.id)]=ref; set_credits(ref,get_credits(ref)+1); save_v7_data()

    if user.id in banned_users:
        await message.reply_text("🚫 Your access has been suspended.")
        return False

    if maintenance_mode and not is_owner(user.id):
        await message.reply_text(
            "🛠 Service maintenance is active. Try again later."
        )
        return False

    if not await check_join(user.id, context):
        await message.reply_text(
            "<b>🔒 Membership Required</b>\n\n"
            "Join both communities, then verify.",
            parse_mode=ParseMode.HTML,
            reply_markup=join_buttons(),
        )
        return False

    if not is_approved(user.id):
        approved_users.add(user.id)
        user_credits.setdefault(str(user.id), DEFAULT_CREDITS)
        save_data()

    return True


def owner_only(update: Update) -> bool:
    return bool(
        update.effective_user
        and is_owner(update.effective_user.id)
    )


def admin_or_owner(update: Update) -> bool:
    if not update.effective_user:
        return False
    uid = update.effective_user.id
    return is_owner(uid) or str(uid) in admin_roles


def admin_role(user_id: int) -> str:
    return "owner" if is_owner(user_id) else admin_roles.get(str(user_id), "none")


# ═════════════════════════════════════════════════════════════════════════════
# BASIC COMMANDS
# ═════════════════════════════════════════════════════════════════════════════

async def start_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user

    if not user:
        return

    touch_user(user)

    if user.id in banned_users:
        await update.effective_message.reply_text(
            "🚫 Your access has been suspended."
        )
        return

    if not await check_join(user.id, context):
        await update.effective_message.reply_text(
            premium_box("🔒 ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ʀᴇǫᴜɪʀᴇᴅ", ["Join the required channel/community first.", "Then tap <b>Verify Membership</b> below."]),
            parse_mode=ParseMode.HTML,
            reply_markup=join_buttons(),
        )
        return

    if not is_approved(user.id):
        approved_users.add(user.id)
        user_credits.setdefault(str(user.id), DEFAULT_CREDITS)
        save_data()

    await update.effective_message.reply_text(
        home_text(user.id),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu(user.id),
        disable_web_page_preview=True,
    )
    ann=v105_cfg().get("announcement","").strip()
    if ann:
        await update.effective_message.reply_text(premium_box("📢 ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ",[esc(ann)]),parse_mode=ParseMode.HTML)


async def help_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await guard(update, context):
        return

    text = (
        "<b>ℹ️ QURESHIxOTP Host Help</b>\n\n"
        "<code>/projects</code> — Open premium Project Control Center\n<code>/connectrepo URL [branch]</code> — Deploy GitHub repo\n<code>/repos</code> — Connected GitHub repos\n<code>/autodeploy PROJECT on|off</code> — GitHub auto deploy\n<code>/syncrepo PROJECT</code> — Pull + redeploy now\n<code>/deployhistory PROJECT</code> — Deployment history\n<code>/rollback PROJECT</code> — Roll back latest snapshot\n<code>/notifications</code> — Alert preferences\n<code>/ticket ISSUE</code> — Support ticket\n"
        "<code>/logs [name]</code> — Latest logs\n"
        "<code>/restart NAME</code> — Restart project\n"
        "<code>/stop NAME</code> — Stop project\n"
        "<code>/delete NAME</code> — Delete stopped project\n"
        "<code>/rename OLD NEW</code> — Rename project\n"
        "<code>/credits</code> — Wallet\n"
        "<code>/skip</code> — Skip project name prompt\n\n"
        "You can also use the premium menu buttons."
    )

    if is_owner(update.effective_user.id):
        text += "\n\n" + admin_commands_text()

    await update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def request_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user

    if not user or user.id in banned_users:
        return

    reason = " ".join(context.args).strip() or "No reason provided"
    rows = pending_requests()
    if not any(int(r.get("id",0)) == user.id for r in rows):
        rows.append({"id": user.id, "username": user.username or "", "name": user.full_name, "reason": reason, "time": datetime.now().isoformat(timespec="seconds")})
        save_v7_data()

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"request:approve:{user.id}",
                ),
                InlineKeyboardButton(
                    "❌ Reject",
                    callback_data=f"request:reject:{user.id}",
                ),
            ]
        ]
    )

    await context.bot.send_message(
        OWNER_ID,
        f"<b>📩 New Access Request</b>\n\n"
        f"👤 {esc(user.full_name)}\n"
        f"🔗 @{esc(user.username or 'not_set')}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📝 {esc(reason)}",
        parse_mode=ParseMode.HTML,
        reply_markup=buttons,
    )

    await update.effective_message.reply_text(
        "✅ Request sent to the owner."
    )


async def projects_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await guard(update, context):
        return

    uid = update.effective_user.id

    await update.effective_message.reply_text(
        projects_text(uid),
        parse_mode=ParseMode.HTML,
        reply_markup=project_list_buttons(uid),
    )


async def logs_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await guard(update, context):
        return

    uid = update.effective_user.id
    items = scripts_for(uid)

    if not items:
        await update.effective_message.reply_text(
            "🧾 No logs are available."
        )
        return

    item = items[-1]

    if context.args:
        found = find_project(uid, " ".join(context.args))
        if not found:
            await update.effective_message.reply_text(
                "❌ Project not found."
            )
            return
        _, item = found

    path = Path(item.log_path)
    content = (
        path.read_text("utf-8", errors="replace")[-MAX_LOG_CHARS:]
        if path.exists()
        else "No output yet."
    )

    await update.effective_message.reply_text(
        f"<b>🧾 {esc(item.display_name)}</b>\n\n"
        f"<pre>{esc(content)}</pre>",
        parse_mode=ParseMode.HTML,
    )


async def credits_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    caller = update.effective_user.id
    uid = caller

    if context.args:
        if not is_owner(caller):
            await update.effective_message.reply_text(
                "❌ Owner only."
            )
            return

        try:
            uid = int(context.args[0])
        except ValueError:
            await update.effective_message.reply_text(
                "❌ Invalid user ID."
            )
            return

    await update.effective_message.reply_text(
        "<b>💳 Credit Wallet</b>\n\n"
        f"User ID: <code>{uid}</code>\n"
        f"Plan: {esc(plan_name(uid))}\n"
        f"Credits: <code>{get_credits(uid)}</code>\n"
        f"Upload cost: <code>{CREDIT_PER_UPLOAD}</code>",
        parse_mode=ParseMode.HTML,
    )


async def skip_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    uid = update.effective_user.id

    if uid not in pending_project_names:
        await update.effective_message.reply_text(
            "ℹ️ No project name is pending."
        )
        return

    pending_project_names.pop(uid, None)
    await update.effective_message.reply_text(
        "✅ Original project name kept."
    )


async def rename_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context): return
    fields=pipe_fields(update)
    if len(fields)>=2:
        old_name,new_raw=fields[0],fields[1]
    elif len(context.args)>=2:
        old_name=context.args[0]; new_raw=" ".join(context.args[1:])
    else:
        await update.effective_message.reply_text("Usage: /rename OLD PROJECT | NEW PROJECT\nExample: /rename QURESHIxOTP Like | QURESHIxOTP Like2"); return
    uid=update.effective_user.id; found=find_project(uid,old_name); new_name=clean_project_name(new_raw)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; old=item.display_name; item.display_name=new_name; save_projects(); audit(uid,"rename_project",new_name,f"{old} -> {new_name}")
    await update.effective_message.reply_text(f"✅ Project renamed to <b>{esc(new_name)}</b>.",parse_mode=ParseMode.HTML)


async def stop_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await guard(update, context):
        return

    if not context.args:
        await projects_cmd(update, context)
        return

    uid = update.effective_user.id
    found = find_project(uid, " ".join(context.args))

    if not found:
        await update.effective_message.reply_text(
            "❌ Project not found."
        )
        return

    _, item = found
    item.desired_running = False
    project_setting(item)["autostart"] = False
    ok = kill_process(item)
    save_projects(); save_v7_data()

    await update.effective_message.reply_text(
        (
            f"🛑 Stopped <b>{esc(item.display_name)}</b>."
            if ok
            else "❌ Could not stop project."
        ),
        parse_mode=ParseMode.HTML,
    )


async def restart_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await guard(update, context):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /restart PROJECT_NAME"
        )
        return

    uid = update.effective_user.id
    found = find_project(uid, " ".join(context.args))

    if not found:
        await update.effective_message.reply_text(
            "❌ Project not found."
        )
        return

    _, item = found

    async with lock_for(uid):
        if item.running:
            kill_process(item)

        item.restarts += 1

        try:
            spawn_script(
                item,
                Path(item.entry_file),
                Path(item.folder),
                Path(item.log_path),
            )
            await asyncio.sleep(0.5)

            await update.effective_message.reply_text(
                (
                    f"✅ Restarted <b>{esc(item.display_name)}</b>.\n"
                    f"PID: <code>{item.pid}</code>"
                    if item.running
                    else "❌ Project exited after restart."
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            await update.effective_message.reply_text(
                f"❌ Restart failed: <code>{esc(exc)}</code>",
                parse_mode=ParseMode.HTML,
            )


async def delete_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await guard(update, context):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /delete PROJECT_NAME"
        )
        return

    uid = update.effective_user.id
    found = find_project(uid, " ".join(context.args))

    if not found:
        await update.effective_message.reply_text(
            "❌ Project not found."
        )
        return

    index, item = found

    if item.running:
        await update.effective_message.reply_text(
            "⚠️ Stop the project before deleting it."
        )
        return

    key = project_key(item)
    trash_root = BASE_DIR / "trash" / str(uid)
    trash_root.mkdir(parents=True, exist_ok=True)
    src = Path(item.folder)
    trash_name = f"{int(time.time())}_{clean_project_name(item.display_name)}"
    dest = trash_root / trash_name
    try:
        shutil.move(str(src), str(dest))
    except Exception:
        safe_remove_folder(item.folder)
        dest = Path("")
    row = {"trash_id": trash_name, "deleted_at": time.time(), "expires_at": time.time()+48*3600,
           "project": item.serialize(), "settings": project_settings.get(key, {}), "envs": project_envs.get(key, {}),
           "trash_folder": str(dest) if dest else ""}
    global_cfg().setdefault("trash", {}).setdefault(str(uid), []).append(row)
    scripts_for(uid).pop(index)
    project_settings.pop(key, None); project_envs.pop(key, None)
    audit(uid, "trash_project", item.display_name, trash_name)
    save_projects(); save_v7_data()
    await update.effective_message.reply_text(
        f"🗑 <b>{esc(item.display_name)}</b> moved to Trash for 48 hours.\nUse <code>/trash</code> or <code>/restoretrash {esc(trash_name)}</code>.",
        parse_mode=ParseMode.HTML,
    )


# ═════════════════════════════════════════════════════════════════════════════
# OWNER COMMANDS
# ═════════════════════════════════════════════════════════════════════════════

async def admin_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not admin_or_owner(update):
        await update.effective_message.reply_text("❌ Admin only.")
        return

    await update.effective_message.reply_text(
        admin_overview(),
        parse_mode=ParseMode.HTML,
        reply_markup=admin_buttons(),
    )


async def approve_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /approve USER_ID"
        )
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID."
        )
        return

    approved_users.add(uid)
    banned_users.discard(uid)
    user_credits.setdefault(str(uid), DEFAULT_CREDITS)
    save_data()

    await update.effective_message.reply_text(
        f"✅ Approved <code>{uid}</code>.",
        parse_mode=ParseMode.HTML,
    )

    try:
        await context.bot.send_message(
            uid,
            f"✅ Access approved for {BRAND_NAME}. Send /start.",
        )
    except TelegramError:
        pass


async def revoke_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /revoke USER_ID"
        )
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID."
        )
        return

    approved_users.discard(uid)
    premium_users.discard(uid)
    save_data()

    await update.effective_message.reply_text(
        f"✅ Access revoked from <code>{uid}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def premium_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /premium USER_ID"
        )
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID."
        )
        return

    approved_users.add(uid)
    premium_users.add(uid)
    banned_users.discard(uid)

    set_credits(
        uid,
        get_credits(uid) + PREMIUM_BONUS_CREDITS,
    )
    save_data()

    await update.effective_message.reply_text(
        f"<b>💎 Premium Activated</b>\n\n"
        f"User: <code>{uid}</code>\n"
        f"Bonus credits: <code>{PREMIUM_BONUS_CREDITS}</code>\n"
        f"Daily uploads: <code>{daily_limit(uid)}</code>\n"
        f"Running limit: <code>{running_limit(uid)}</code>",
        parse_mode=ParseMode.HTML,
    )

    try:
        await context.bot.send_message(
            uid,
            f"💎 Premium activated on {BRAND_NAME}.\n"
            f"Credits: {get_credits(uid)}\n"
            f"Daily uploads: {daily_limit(uid)}\n"
            f"Running limit: {running_limit(uid)}",
        )
    except TelegramError:
        pass


async def unpremium_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /unpremium USER_ID"
        )
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID."
        )
        return

    premium_users.discard(uid)
    save_data()

    await update.effective_message.reply_text(
        f"✅ Premium removed from <code>{uid}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def ban_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /ban USER_ID"
        )
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID."
        )
        return

    banned_users.add(uid)
    approved_users.discard(uid)
    premium_users.discard(uid)

    stopped = 0
    for item in scripts_for(uid):
        if item.running and kill_process(item):
            stopped += 1

    save_data()

    await update.effective_message.reply_text(
        f"🚫 Banned <code>{uid}</code>.\n"
        f"Stopped projects: <code>{stopped}</code>",
        parse_mode=ParseMode.HTML,
    )


async def unban_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /unban USER_ID"
        )
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID."
        )
        return

    banned_users.discard(uid)
    save_data()

    await update.effective_message.reply_text(
        f"✅ Unbanned <code>{uid}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def addcredits_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Usage: /addcredits USER_ID AMOUNT"
        )
        return

    try:
        uid = int(context.args[0])
        amount = int(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID or amount."
        )
        return

    set_credits(uid, get_credits(uid) + amount)

    await update.effective_message.reply_text(
        f"✅ Added <code>{amount}</code> credits to "
        f"<code>{uid}</code>.\n"
        f"Total: <code>{get_credits(uid)}</code>",
        parse_mode=ParseMode.HTML,
    )


async def setcredits_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Usage: /setcredits USER_ID AMOUNT"
        )
        return

    try:
        uid = int(context.args[0])
        amount = int(context.args[1])
        if amount < 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID or amount."
        )
        return

    set_credits(uid, amount)

    await update.effective_message.reply_text(
        f"✅ Credits for <code>{uid}</code> set to "
        f"<code>{amount}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def takecredits_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Usage: /takecredits USER_ID AMOUNT"
        )
        return

    try:
        uid = int(context.args[0])
        amount = int(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID or amount."
        )
        return

    set_credits(uid, get_credits(uid) - amount)

    await update.effective_message.reply_text(
        f"✅ Removed <code>{amount}</code> credits from "
        f"<code>{uid}</code>.\n"
        f"Remaining: <code>{get_credits(uid)}</code>",
        parse_mode=ParseMode.HTML,
    )


async def setdaily_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Usage: /setdaily USER_ID LIMIT"
        )
        return

    try:
        uid = int(context.args[0])
        limit = int(context.args[1])
        if limit < 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid input."
        )
        return

    custom_daily_limits[str(uid)] = limit
    save_data()

    await update.effective_message.reply_text(
        f"✅ Daily upload limit for <code>{uid}</code> "
        f"set to <code>{limit}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def setrunning_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Usage: /setrunning USER_ID LIMIT"
        )
        return

    try:
        uid = int(context.args[0])
        limit = int(context.args[1])
        if limit < 1:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid input."
        )
        return

    custom_running_limits[str(uid)] = limit
    save_data()

    await update.effective_message.reply_text(
        f"✅ Running limit for <code>{uid}</code> "
        f"set to <code>{limit}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def userinfo_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /userinfo USER_ID"
        )
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID."
        )
        return

    stat = get_stat(uid)

    await update.effective_message.reply_text(
        "<b>👤 User Information</b>\n\n"
        f"ID: <code>{uid}</code>\n"
        f"Username: @{esc(stat.get('username') or 'not_set')}\n"
        f"Name: {esc(stat.get('first_name') or 'Unknown')}\n"
        f"Plan: {esc(plan_name(uid))}\n"
        f"Approved: <code>{'YES' if is_approved(uid) else 'NO'}</code>\n"
        f"Premium: <code>{'YES' if is_premium(uid) else 'NO'}</code>\n"
        f"Banned: <code>{'YES' if uid in banned_users else 'NO'}</code>\n"
        f"Credits: <code>{get_credits(uid)}</code>\n"
        f"Running: <code>{active_count(uid)}/{running_limit(uid)}</code>\n"
        f"Uploads today: "
        f"<code>{stat.get('uploads_today', 0)}/{daily_limit(uid)}</code>\n"
        f"Total uploads: <code>{stat.get('uploads_total', 0)}</code>\n"
        f"Last active: <code>{esc(stat.get('last_active') or 'Unknown')}</code>",
        parse_mode=ParseMode.HTML,
    )


async def broadcast_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    body = " ".join(context.args).strip()

    if not body:
        await update.effective_message.reply_text(
            "Usage: /broadcast MESSAGE"
        )
        return

    targets = approved_users | premium_users | {OWNER_ID}
    sent = 0
    failed = 0

    status = await update.effective_message.reply_text(
        "📣 Sending broadcast…"
    )

    for uid in targets:
        try:
            await context.bot.send_message(
                uid,
                f"<b>📣 {esc(BRAND_NAME)}</b>\n\n{esc(body)}",
                parse_mode=ParseMode.HTML,
            )
            sent += 1
            await asyncio.sleep(0.05)
        except (Forbidden, TelegramError):
            failed += 1

    await status.edit_text(
        f"✅ Sent: {sent}\n❌ Failed: {failed}"
    )


async def maintenance_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    global maintenance_mode

    if not owner_only(update):
        return

    if (
        not context.args
        or context.args[0].lower() not in {"on", "off"}
    ):
        await update.effective_message.reply_text(
            "Usage: /maintenance on|off"
        )
        return

    maintenance_mode = context.args[0].lower() == "on"
    save_data()

    await update.effective_message.reply_text(
        f"🛠 Maintenance "
        f"{'ON' if maintenance_mode else 'OFF'}"
    )


async def startall_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    started = 0
    failed = 0

    for uid, items in running_scripts.items():
        async with lock_for(uid):
            for item in items:
                if item.running:
                    continue

                try:
                    spawn_script(
                        item,
                        Path(item.entry_file),
                        Path(item.folder),
                        Path(item.log_path),
                    )
                    await asyncio.sleep(0.15)

                    if item.running:
                        started += 1
                    else:
                        failed += 1

                except Exception:
                    logger.exception(
                        "Failed starting %s",
                        item.display_name,
                    )
                    failed += 1

    await update.effective_message.reply_text(
        f"▶️ Start All Complete\n\n"
        f"✅ Started: {started}\n"
        f"❌ Failed: {failed}"
    )


async def stopalladmin_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    stopped = 0

    for items in running_scripts.values():
        for item in items:
            if item.running and kill_process(item):
                stopped += 1

    await update.effective_message.reply_text(
        f"🧨 Stopped <code>{stopped}</code> projects.",
        parse_mode=ParseMode.HTML,
    )


async def cleanup_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return

    removed = 0

    for uid, items in list(running_scripts.items()):
        kept: list[ScriptProcess] = []

        for item in items:
            folder = Path(item.folder)
            entry = Path(item.entry_file)

            if folder.exists() and entry.exists():
                kept.append(item)
            else:
                removed += 1

        running_scripts[uid] = kept

    save_projects()

    await update.effective_message.reply_text(
        f"🧹 Cleanup complete.\n"
        f"Removed missing project records: <code>{removed}</code>",
        parse_mode=ParseMode.HTML,
    )


async def install_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Install Python packages without invoking a shell."""
    if not owner_only(update):
        await update.effective_message.reply_text("❌ Owner only.")
        return

    raw = " ".join(context.args).strip()
    if not raw:
        await update.effective_message.reply_text(
            premium_box(
                "📦 ᴘᴀᴄᴋᴀɢᴇ ɪɴsᴛᴀʟʟᴇʀ",
                [
                    "<b>Python:</b> <code>/install beautifulsoup4</code>",
                    "<b>Python:</b> <code>/install pip3 install requests</code>",
                    "<b>Node:</b> <code>/install npm install axios</code>",
                    "",
                    "🔐 Owner-only • no shell execution",
                ],
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        args = shlex.split(raw)
    except ValueError as exc:
        await update.effective_message.reply_text(f"❌ Invalid syntax: {exc}")
        return

    install_kind = "pip"
    if args[:2] in (["pip", "install"], ["pip3", "install"]):
        packages = args[2:]
    elif len(args) >= 4 and args[0] in {"python", "python3"} and args[1:4] == ["-m", "pip", "install"]:
        packages = args[4:]
    elif args[:2] == ["npm", "install"]:
        install_kind = "npm"
        packages = args[2:]
    elif args and args[0].lower() in {"node", "yarn", "pnpm"}:
        await update.effective_message.reply_text("❌ Use npm syntax: /install npm install PACKAGE")
        return
    else:
        packages = args

    package_pattern = re.compile(r"^[A-Za-z0-9@._/+:-]+(?:[<>=!~]{1,2}[A-Za-z0-9.*+_-]+)?$")
    if not packages or len(packages) > 15 or any(not package_pattern.fullmatch(x) for x in packages):
        await update.effective_message.reply_text(
            "❌ Only valid package names/version specs are accepted. Shell operators and arbitrary flags are blocked."
        )
        return

    if install_kind == "npm":
        npm = shutil.which("npm")
        if not npm:
            await update.effective_message.reply_text("❌ npm is not installed on this host.")
            return
        cmd = [npm, "install", "--ignore-scripts", "--no-audit", "--no-fund", *packages]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *packages]

    status = await update.effective_message.reply_text(
        premium_box("⏳ ɪɴsᴛᴀʟʟɪɴɢ", [f"📦 <code>{esc(' '.join(packages))}</code>", "Please check the result below."]),
        parse_mode=ParseMode.HTML,
    )
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=str(BASE_DIR), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=INSTALL_TIMEOUT_SECONDS)
        output = stdout.decode("utf-8", errors="replace")[-MAX_INSTALL_OUTPUT_CHARS:]
        title = "✅ ɪɴsᴛᴀʟʟᴇᴅ" if proc.returncode == 0 else "❌ ɪɴsᴛᴀʟʟ ғᴀɪʟᴇᴅ"
        await status.edit_text(
            premium_box(title, [f"📦 <code>{esc(' '.join(packages))}</code>", "", f"<pre>{esc(output or 'No output')}</pre>"]),
            parse_mode=ParseMode.HTML,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        await status.edit_text(premium_box("⏱ ᴛɪᴍᴇᴏᴜᴛ", [f"Installation exceeded {INSTALL_TIMEOUT_SECONDS} seconds."]), parse_mode=ParseMode.HTML)
    except FileNotFoundError:
        await status.edit_text("❌ Package manager is not installed on this panel.")
    except Exception as exc:
        logger.exception("Package installation failed")
        await status.edit_text(f"❌ Installation error: <code>{esc(exc)}</code>", parse_mode=ParseMode.HTML)


async def installed_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        await update.effective_message.reply_text("❌ Owner only.")
        return
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "pip", "list", "--format=columns",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace")[-MAX_INSTALL_OUTPUT_CHARS:]
    await update.effective_message.reply_text(
        premium_box("📚 ɪɴsᴛᴀʟʟᴇᴅ ᴘᴀᴄᴋᴀɢᴇs", [f"<pre>{esc(output)}</pre>"]),
        parse_mode=ParseMode.HTML,
    )


async def send_real_file(bot, chat_id: int, path: Path, caption: str = "", parse_mode=None) -> None:
    """Send the actual file bytes, never the filesystem path as document content."""
    path = Path(path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(str(path))
    with path.open("rb") as fh:
        await bot.send_document(
            chat_id=chat_id,
            document=fh,
            filename=path.name,
            caption=caption or None,
            parse_mode=parse_mode,
        )


def create_full_source_backup() -> Path:
    """Create a real ZIP containing host source/data and stored project source files."""
    save_data(); save_projects(); save_v7_data()
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    archive=BACKUPS_DIR/f"QURESHIxOTP_full_source_backup_{stamp}.zip"
    excluded_dirs={".venv","node_modules",".git","__pycache__",".QURESHIxOTP_history"}
    excluded_files={"runtime.log"}
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        host_files=(Path(__file__), DATA_FILE, PROJECTS_FILE, V7_DATA_FILE, V9_DB_FILE, BASE_DIR/"requirements.txt", BASE_DIR/"README.md", BASE_DIR/"ADMIN_COMMANDS.txt", BASE_DIR/".env.example")
        for f in host_files:
            if f.exists() and f.is_file():
                z.write(f, f"host/{f.name}")
        # User-uploaded project files are deliberately excluded from admin/vault backups.
    return archive


async def send_full_backup_to_vault(context: ContextTypes.DEFAULT_TYPE, archive: Path, title: str = "💾 ᴘʀɪᴠᴀᴛᴇ ʙᴀᴄᴋᴜᴘ") -> None:
    # Intentionally disabled: backups are never sent to an admin/group/channel.
    return


async def backup_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not owner_only(update):
        return
    status=await update.effective_message.reply_text(
        premium_box("💾 ʙᴀᴄᴋᴜᴘ ɴᴏᴡ",["① Saving database…","② Packing actual source files…"]),
        parse_mode=ParseMode.HTML,
    )
    try:
        archive=await asyncio.to_thread(create_full_source_backup)
        await status.edit_text(
            premium_box("💾 ʙᴀᴄᴋᴜᴘ ɴᴏᴡ",["✅ Archive created","③ Uploading actual ZIP to Backup Vault…"]),
            parse_mode=ParseMode.HTML,
        )
        await send_full_backup_to_vault(context,archive,"💾 ᴍᴀɴᴜᴀʟ ғᴜʟʟ ʙᴀᴄᴋᴜᴘ")
        await send_real_file(context.bot, update.effective_chat.id, archive, f"💾 {BRAND_NAME} full source backup")
        await status.edit_text(
            premium_box("✅ ʙᴀᴄᴋᴜᴘ ᴄᴏᴍᴘʟᴇᴛᴇ",[f"Archive • <code>{esc(archive.name)}</code>","✅ Actual ZIP sent here","✅ Actual ZIP mirrored to Backup Vault"]),
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        logger.exception("Manual full backup failed")
        await status.edit_text(premium_box("❌ ʙᴀᴄᴋᴜᴘ ғᴀɪʟᴇᴅ",[f"Reason • <code>{esc(exc)}</code>"]),parse_mode=ParseMode.HTML)


# ═════════════════════════════════════════════════════════════════════════════
# FILE HOSTING
# ═════════════════════════════════════════════════════════════════════════════

async def handle_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await guard(update, context):
        return
    if (not v10_flags()["deployments"]) or v10_flags()["readonly"]:
        await update.effective_message.reply_text("⏸ New deployments are paused/read-only by admin.")
        return

    user_id = update.effective_user.id
    document = update.effective_message.document

    if not document:
        return

    # V10.7: replace one project file without touching databases/runtime data.
    pending_file=v106_cfg().setdefault("pending_file_replacements",{}).pop(str(user_id),None)
    if pending_file:
        save_v7_data()
        owner_uid=int(pending_file.get("owner_uid",user_id)); found=find_project(owner_uid,str(pending_file.get("project","")))
        if not found:
            await update.effective_message.reply_text("❌ Replacement target project no longer exists."); return
        _,item=found; rel=str(pending_file.get("path",""))
        try:
            target=safe_inside_project(item,rel)
            if _secret_project_path(target): raise ValueError("Secret/.env files are not replaceable; use ENV commands")
            tg=await context.bot.get_file(document.file_id)
            incoming=Path(item.folder)/(".QURESHIxOTP_replace_"+clean_filename(document.file_name or target.name))
            await tg.download_to_drive(str(incoming))
            old_bytes=target.read_bytes() if target.exists() else None
            if target.exists(): save_file_version(item, rel)
            was=item.running
            if was: kill_process(item)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(incoming,target); incoming.unlink(missing_ok=True)
            if target.suffix.lower() in V105_EDITABLE_EXTS or target == Path(item.entry_file):
                ok,why=syntax_test_entry(target) if target.suffix.lower() in {'.py','.js','.mjs','.cjs','.php','.rb','.sh','.jar'} else (True,'File accepted')
                if not ok: raise RuntimeError("Validation failed: "+why)
            ensure_project_env_ready(item,Path(item.folder))
            if was:
                spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
            record_deploy(item,"success",f"Single file replaced: {rel}")
            await update.effective_message.reply_text(premium_box("✅ ғɪʟᴇ ᴜᴘᴅᴀᴛᴇᴅ",[f"Project • <b>{esc(item.display_name)}</b>",f"File • <code>{esc(rel)}</code>","✅ Only selected file replaced.","💾 Existing project data/database preserved.",f"Status • <code>{'ONLINE' if item.running else 'OFFLINE'}</code>"]),parse_mode=ParseMode.HTML)
        except Exception as exc:
            try:
                incoming.unlink(missing_ok=True)
            except Exception: pass
            try:
                if 'target' in locals() and 'old_bytes' in locals():
                    if old_bytes is None: target.unlink(missing_ok=True)
                    else: target.write_bytes(old_bytes)
                if 'was' in locals() and was and not item.running:
                    spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
            except Exception: logger.exception("Could not restore previous file after replacement failure")
            await update.effective_message.reply_text(premium_box("❌ ғɪʟᴇ ᴜᴘᴅᴀᴛᴇ ғᴀɪʟᴇᴅ",[f"Reason • <code>{esc(exc)}</code>","↩️ Previous file restored where possible.","💾 Other project data was not touched."]),parse_mode=ParseMode.HTML)
        return

    if v105_cfg().setdefault("pending_imports",{}).pop(str(user_id),None):
        save_v7_data()
        if not (document.file_name or "").lower().endswith(".zip"):
            await update.effective_message.reply_text("❌ QURESHIxOTP import must be a .zip file."); return
        tmp=user_folder(user_id)/("import_"+clean_filename(document.file_name or "project.zip"))
        try:
            tg=await context.bot.get_file(document.file_id); await tg.download_to_drive(str(tmp))
            extract=tmp.with_suffix(""); extract.mkdir(parents=True,exist_ok=True); safe_extract_zip_owner(tmp,extract) if is_owner(user_id) else safe_extract_zip(tmp,extract)
            meta=extract/"QURESHIxOTP-project.json"; src=extract/"source"
            if not meta.exists() or not src.exists(): raise RuntimeError("Not a valid QURESHIxOTP export")
            info=json.loads(meta.read_text()); name=clean_project_name(info.get("name","ImportedProject")); dest=user_folder(user_id)/(datetime.now().strftime("%Y%m%d_%H%M%S_%f")+"_"+name); shutil.copytree(src,dest)
            entry=detect_entry(dest);
            if not entry: raise RuntimeError("No runnable entry in imported project")
            log=dest/"runtime.log"; install_project_dependencies(dest,entry,log) if v10_flags()["dependencies"] else None
            item=spawn_script(None,entry,dest,log); item.display_name=name; scripts_for(user_id).append(item); project_settings[project_key(item)]=info.get("settings",{}); save_projects(); save_v7_data(); record_deploy(item,"success","Portable import")
            await update.effective_message.reply_text(premium_box("✅ ᴘʀᴏᴊᴇᴄᴛ ɪᴍᴘᴏʀᴛᴇᴅ",[f"Project • <b>{esc(name)}</b>",f"Runtime • <code>{esc(item.runtime)}</code>","Status • 🟢 Online"]),parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Import failed: {e}")
        finally:
            tmp.unlink(missing_ok=True); shutil.rmtree(tmp.with_suffix(""),ignore_errors=True)
        return

    # Uploaded files stay private to the uploader/project storage. No admin/group/channel mirror.
    pending_replace = global_cfg().setdefault("pending_replace", {})
    if str(user_id) in pending_replace:
        idx=int(pending_replace.pop(str(user_id))); save_v7_data()
        items=scripts_for(user_id)
        if idx<0 or idx>=len(items):
            await update.effective_message.reply_text("❌ Replacement target no longer exists."); return
        item=items[idx]; msg=await update.effective_message.reply_text("♻️ <b>Replacement Deploy</b>\n\n① Downloading replacement…",parse_mode=ParseMode.HTML)
        temp=Path(item.folder)/(".replacement_"+clean_filename(document.file_name or "project.zip"))
        try:
            tg=await context.bot.get_file(document.file_id); await tg.download_to_drive(str(temp)); snapshot_project(item,"pre_replace")
            if item.running: kill_process(item)
            root=Path(item.folder); keep={".venv","node_modules",".git",".QURESHIxOTP_history","runtime.log",temp.name}
            for child in list(root.iterdir()):
                if child.name in keep: continue
                if child.is_dir(): shutil.rmtree(child,ignore_errors=True)
                else: child.unlink(missing_ok=True)
            if temp.suffix.lower()==".zip": safe_extract_zip_owner(temp,root) if is_owner(user_id) else safe_extract_zip(temp,root); temp.unlink(missing_ok=True)
            else:
                final=root/clean_filename(document.file_name or temp.name); temp.replace(final)
            entry=detect_entry(root)
            if not entry: raise RuntimeError("No supported entry in replacement")
            item.entry_file=str(entry); item.runtime=runtime_for_entry(entry); install_project_dependencies(root,entry,Path(item.log_path)) if v10_flags()["dependencies"] else None; spawn_script(item,entry,root,Path(item.log_path)); record_deploy(item,"success","Replacement upload"); save_projects()
            await msg.edit_text("✅ Replacement deployed successfully. Rollback snapshot saved.")
        except Exception as e:
            await msg.edit_text(f"❌ Replacement failed: {e}\nUse /rollback {item.display_name} to restore the snapshot.")
        return

    async with lock_for(user_id):
        reset_daily(user_id)
        stat = get_stat(user_id)

        if stat["uploads_today"] >= daily_limit(user_id):
            await update.effective_message.reply_text(
                "⚠️ Your daily upload limit has been reached."
            )
            return

        if (
            not is_premium(user_id)
            and get_credits(user_id) < CREDIT_PER_UPLOAD
        ):
            await update.effective_message.reply_text(
                "💳 Not enough credits."
            )
            return

        if active_count(user_id) >= running_limit(user_id):
            await update.effective_message.reply_text(
                f"⚠️ Running limit reached: "
                f"{running_limit(user_id)}."
            )
            return

        used_mb = user_storage_mb(user_id)
        quota_mb = storage_limit_mb(user_id)
        incoming_mb = (document.file_size or 0) / (1024 * 1024)
        if not is_owner(user_id) and used_mb + incoming_mb > quota_mb:
            await update.effective_message.reply_text(
                f"💾 Storage quota exceeded. Used: {used_mb:.1f} MB / {quota_mb} MB."
            )
            return

        filename = clean_filename(
            document.file_name or "project"
        )
        suffix = Path(filename).suffix.lower()

        allowed_exts=set(global_cfg().get("allowed_extensions", [".py",".js",".mjs",".cjs",".php",".sh",".rb",".jar",".zip"]))
        if suffix not in allowed_exts:
            await update.effective_message.reply_text(
                "❌ This file type is not currently enabled by the host administrator."
            )
            return

        size = document.file_size or 0

        if (not is_owner(user_id)) and size > MAX_FILE_MB * 1024 * 1024:
            await update.effective_message.reply_text(
                f"❌ Maximum file size is {MAX_FILE_MB} MB."
            )
            return

        progress = await update.effective_message.reply_text(
            f"<b>📥 Upload Received</b>\n\n"
            f"📄 <code>{esc(filename)}</code>\n"
            f"📦 Size: <code>{size / (1024 * 1024):.2f} MB</code>\n\n"
            "Preparing premium hosting environment…",
            parse_mode=ParseMode.HTML,
        )

        stamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
        folder = (
            user_folder(user_id)
            / f"{stamp}_{Path(filename).stem}"
        )
        folder.mkdir(parents=True)
        uploaded = folder / filename

        try:
            tg_file = await context.bot.get_file(
                document.file_id
            )
            await tg_file.download_to_drive(str(uploaded))

            await progress.edit_text("🚀 <b>Deployment Progress</b>\n\n✅ Upload received\n⏳ Extracting / inspecting…\n⬜ Security scan\n⬜ Runtime detection\n⬜ Dependencies\n⬜ Starting", parse_mode=ParseMode.HTML)

            if suffix == ".zip":
                safe_extract_zip(uploaded, folder) if not is_owner(user_id) else safe_extract_zip_owner(uploaded, folder)
                uploaded.unlink(missing_ok=True)
                entry = detect_entry(folder)
            else:
                entry = uploaded

            if not entry:
                raise ValueError(
                    "No supported runnable entry found in this project."
                )

            log_path = folder / "runtime.log"

            risk, findings = scan_project(folder) if SECURITY_SCAN_ENABLED else ("DISABLED", [])
            if risk == "HIGH" and not is_owner(user_id):
                raise ValueError("High-risk code detected: " + "; ".join(findings[:3]))

            dependency_note = (await asyncio.to_thread(install_project_dependencies, folder, entry, log_path)) if v10_flags()["dependencies"] else "Dependency installation disabled by admin"

            await progress.edit_text("🚀 <b>Deployment Progress</b>\n\n✅ Extracted\n✅ Security checked\n✅ Runtime detected\n✅ Dependencies ready\n⏳ Starting…", parse_mode=ParseMode.HTML)
            item = spawn_script(None, entry, folder, log_path)
            scripts_for(user_id).append(item)
            record_deploy(item, "success", "Telegram upload")
            save_projects()

            await asyncio.sleep(LAUNCH_CHECK_SECONDS)

            if not item.running:
                error = (
                    log_path.read_text(
                        "utf-8",
                        errors="replace",
                    )[-MAX_LOG_CHARS:]
                    if log_path.exists()
                    else "No error output."
                )

                scripts_for(user_id).remove(item)
                save_projects()
                safe_remove_folder(item.folder)

                await progress.edit_text(
                    f"<b>❌ Launch Failed</b>\n\n"
                    f"<pre>{esc(error)}</pre>",
                    parse_mode=ParseMode.HTML,
                )
                return

            if not is_premium(user_id):
                set_credits(
                    user_id,
                    get_credits(user_id)
                    - CREDIT_PER_UPLOAD,
                )

            stat["uploads_today"] += 1
            stat["uploads_total"] += 1
            stat["last_upload_date"] = (
                date.today().isoformat()
            )
            save_data()

            pending_project_names[user_id] = item

            await progress.edit_text(
                f"<b>╭── ✅ Hosting Started ──╮</b>\n"
                f"<b>╰────────────────────╯</b>\n\n"
                f"🧩 <b>Entry:</b> "
                f"<code>{esc(entry.name)}</code>\n"
                f"🆔 <b>PID:</b> "
                f"<code>{item.pid}</code>\n"
                f"🟢 <b>Status:</b> Online\n"
                f"🛡 <b>Scan:</b> <code>{esc(risk)}</code>\n"
                f"📦 <b>Dependencies:</b> {esc(dependency_note)}\n"
                f"💳 <b>Credits:</b> "
                f"<code>{get_credits(user_id)}</code>\n\n"
                "<b>Now send a custom project name.</b>\n"
                "Example: <code>My WhatsApp Bot</code>\n\n"
                "Or send <code>/skip</code> to keep the file name.",
                parse_mode=ParseMode.HTML,
                reply_markup=project_control_buttons(
                    len(scripts_for(user_id)) - 1,
                    True,
                ),
            )

        except Exception as exc:
            logger.exception("Upload failed")
            shutil.rmtree(folder, ignore_errors=True)

            await progress.edit_text(
                f"<b>❌ Upload Failed</b>\n\n"
                f"<code>{esc(exc)}</code>",
                parse_mode=ParseMode.HTML,
            )


# ═════════════════════════════════════════════════════════════════════════════
# TEXT HANDLER
# ═════════════════════════════════════════════════════════════════════════════

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        update.effective_message.text or ""
    ).strip()
    user = update.effective_user

    if not user:
        return

    touch_user(user)

    pending_env=v107_cfg().setdefault("pending_env_values",{}).pop(str(user.id),None)
    if pending_env:
        found=find_project(user.id,str(pending_env.get("project","")))
        if not found:
            save_v7_data(); await update.effective_message.reply_text("❌ ENV Wizard target project no longer exists."); return
        _,env_item=found; key=str(pending_env.get("key",""))
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,80}",key):
            save_v7_data(); await update.effective_message.reply_text("❌ Invalid ENV key."); return
        cfg=project_settings.setdefault(project_key(env_item),{}); cfg.setdefault("env",{})[key]=text
        project_envs.setdefault(project_key(env_item),{})[key]=text; _rewrite_generated_env(env_item); save_v7_data()
        _,missing=required_env_summary(env_item)
        await update.effective_message.reply_text(premium_box("✅ ᴇɴᴠ sᴀᴠᴇᴅ",[f"Project • <b>{esc(env_item.display_name)}</b>",f"Key • <code>{esc(key)}</code>",f"Remaining • <code>{len(missing)}</code>","Value remains masked."]),parse_mode=ParseMode.HTML)
        return

    pending_edit=v105_cfg().setdefault("pending_edits",{}).get(str(user.id))
    if pending_edit:
        found=find_project(user.id,pending_edit.get("project",""))
        if not found:
            v105_cfg()["pending_edits"].pop(str(user.id),None); save_v7_data(); await update.effective_message.reply_text("❌ Edit target project no longer exists."); return
        _,edit_item=found
        try:
            edit_path=safe_inside_project(edit_item,pending_edit.get("path",""))
            edit_path.parent.mkdir(parents=True,exist_ok=True)
            if len(text.encode("utf-8"))>V105_MAX_EDIT_BYTES: raise ValueError("Text exceeds editor size limit")
            snapshot_project(edit_item,"pre_edit")
            if edit_path.exists(): save_file_version(edit_item, pending_edit.get("path",""))
            edit_path.write_text(text,encoding="utf-8")
            ok,why=syntax_test_entry(edit_path) if edit_path==Path(edit_item.entry_file) else (True,"Saved")
            if not ok: raise ValueError("Syntax check failed: "+why)
            v105_cfg()["pending_edits"].pop(str(user.id),None); save_v7_data()
            await update.effective_message.reply_text(premium_box("✅ ᴄᴏᴅᴇ sᴀᴠᴇᴅ",[f"File • <code>{esc(pending_edit.get('path',''))}</code>","Rollback snapshot created.","Restart project to apply if needed."]),parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Edit failed: {e}")
        return

    if user.id in pending_project_names:
        item = pending_project_names.pop(user.id)
        project_name = clean_project_name(text)

        if not project_name:
            await update.effective_message.reply_text(
                "❌ Invalid name. Send a valid project name."
            )
            pending_project_names[user.id] = item
            return

        item.display_name = project_name
        save_projects()

        await update.effective_message.reply_text(
            f"<b>✅ Project Name Saved</b>\n\n"
            f"Project: <b>{esc(project_name)}</b>\n"
            f"Status: {'🟢 Online' if item.running else '🔴 Offline'}",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu(user.id),
        )
        return

    if not is_approved(user.id):
        if not await check_join(user.id, context):
            await update.effective_message.reply_text(
                premium_box("🔒 ᴊᴏɪɴ ʀᴇǫᴜɪʀᴇᴅ", ["Join the required channel/community to use QURESHIxOTP Host."]),
                parse_mode=ParseMode.HTML,
                reply_markup=join_buttons(),
            )
            return
        approved_users.add(user.id)
        user_credits.setdefault(str(user.id), DEFAULT_CREDITS)
        save_data()

    if text == "🚀 ʜᴏsᴛ ᴘʀᴏᴊᴇᴄᴛ":
        await update.effective_message.reply_text(
            "<b>🚀 Host New Project</b>\n\n"
            "Send one of these formats:\n"
            "• <code>.py</code>\n"
            "• <code>.js</code>\n"
            "• <code>.zip</code>\n"
            "• <code>/connectrepo GITHUB_URL</code>\n\n"
            "ZIP projects should contain "
            "<code>main.py</code>, <code>bot.py</code>, "
            "<code>app.py</code>, or <code>server.py</code>.",
            parse_mode=ParseMode.HTML,
        )

    elif text in {"📂 ᴍʏ ᴘʀᴏᴊᴇᴄᴛs", "⚙️ ᴄᴏɴᴛʀᴏʟs"}:
        await projects_cmd(update, context)

    elif text == "🧾 ʟɪᴠᴇ ʟᴏɢs":
        await logs_cmd(update, context)

    elif text == "💳 ᴡᴀʟʟᴇᴛ":
        await credits_cmd(update, context)

    elif text == "📊 ᴀᴄᴄᴏᴜɴᴛ":
        await update.effective_message.reply_text(
            home_text(user.id),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    elif text == "💎 ᴘʟᴀɴs":
        await update.effective_message.reply_text(
            f"<b>💎 {esc(BRAND_NAME)} Plans</b>\n\n"
            f"<b>✅ Approved</b>\n"
            f"• Daily uploads: <code>{DAILY_UPLOAD_LIMIT}</code>\n"
            f"• Running projects: <code>{MAX_RUNNING_PER_USER}</code>\n"
            f"• Upload cost: <code>{CREDIT_PER_UPLOAD}</code> credit\n\n"
            f"<b>💎 Premium</b>\n"
            f"• Daily uploads: "
            f"<code>{PREMIUM_DAILY_UPLOAD_LIMIT}</code>\n"
            f"• Running projects: "
            f"<code>{PREMIUM_MAX_RUNNING_PER_USER}</code>\n"
            f"• Uploads do not consume credits\n"
            f"• Premium bonus: "
            f"<code>{PREMIUM_BONUS_CREDITS}</code> credits",
            parse_mode=ParseMode.HTML,
        )

    elif text == "🆘 sᴜᴘᴘᴏʀᴛ":
        await update.effective_message.reply_text(
            f"<b>🆘 QURESHIxOTP sᴜᴘᴘᴏʀᴛ</b>\n\n"
            f"1️⃣ {esc(CHANNEL_LINKS[0])}\n"
            f"2️⃣ {esc(CHANNEL_LINKS[1])}\n"
            f"3️⃣ {esc(CHANNEL_LINKS[2])}\n"
            f"4️⃣ {esc(CHANNEL_LINKS[3])}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    elif text == "👑 ᴀᴅᴍɪɴ ᴄᴇɴᴛᴇʀ":
        await admin_cmd(update, context)

    else:
        await update.effective_message.reply_text(
            "Use the premium menu or upload a project file."
        )


# ═════════════════════════════════════════════════════════════════════════════
# CALLBACK HANDLER
# ═════════════════════════════════════════════════════════════════════════════

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if query.message and getattr(query.message.chat, "type", "private") != "private":
        return
    await query.answer()
    data=query.data or ""
    if data.startswith("v1073:"):
        if await v1073_callback(update, context): return
    if data.startswith("v107:"):
        if await v107_callback(update, context): return
    if data.startswith("v106:"):
        uid=query.from_user.id; parts=data.split(":"); action=parts[1] if len(parts)>1 else ""
        try: index=int(parts[2]); item=scripts_for(uid)[index]
        except Exception: await query.answer("Project not found",show_alert=True); return
        if action=="files":
            rows=[]
            for x in sorted(Path(item.folder).iterdir(),key=lambda z:(not z.is_dir(),z.name.lower()))[:40]:
                if x.name in {'.venv','node_modules','.git','__pycache__','.QURESHIxOTP_history','.QURESHIxOTP_data_sync'}: continue
                icon='📁' if x.is_dir() else ('🔐' if _secret_project_path(x) else '📄')
                rows.append(f"{icon} <code>{esc(x.name)}</code>")
            await edit_message(query,premium_box("📁 ᴘʀᴏᴊᴇᴄᴛ ғɪʟᴇs",[f"Project • <b>{esc(item.display_name)}</b>",*rows,"","Use <code>/replacefile PROJECT PATH</code> to replace one file without deleting project data."]),project_center_buttons(index,item)); return
        if action=="replacehelp":
            await edit_message(query,premium_box("📤 ʀᴇᴘʟᴀᴄᴇ ғɪʟᴇ",[f"Project • <b>{esc(item.display_name)}</b>","Example:",f"<code>/replacefile {esc(item.display_name)} bot.py</code>","Then upload your updated <b>bot.py</b>.","✅ Only that file changes.","💾 Database/runtime data stays untouched."]),project_center_buttons(index,item)); return
    if await v10_callback(update, context):
        return

    uid = query.from_user.id
    data = query.data or ""

    if data == "join:check":
        if await check_join(uid, context):
            if not is_approved(uid):
                approved_users.add(uid)
                user_credits.setdefault(str(uid), DEFAULT_CREDITS)
                save_data()
            await edit_message(
                query,
                premium_box("✅ ᴠᴇʀɪғɪᴇᴅ", ["Membership verified successfully.", "Your hosting access is now active.", "Send <code>/start</code> to open the dashboard."]),
            )
        else:
            await edit_message(
                query,
                "❌ Membership could not be verified.",
                join_buttons(),
            )
        return

    if data.startswith("request:"):
        if not is_owner(uid):
            await query.answer(
                "Owner only",
                show_alert=True,
            )
            return

        _, action, raw_id = data.split(":")
        target = int(raw_id)
        pending_requests()[:] = [r for r in pending_requests() if int(r.get("id",0)) != target]
        save_v7_data()

        if action == "approve":
            approved_users.add(target)
            banned_users.discard(target)
            user_credits.setdefault(
                str(target),
                DEFAULT_CREDITS,
            )
            save_data()

            try:
                await context.bot.send_message(
                    target,
                    f"✅ Access approved for {BRAND_NAME}. "
                    "Send /start.",
                )
            except TelegramError:
                pass

            await edit_message(
                query,
                f"✅ Approved <code>{target}</code>.",
            )

        else:
            try:
                await context.bot.send_message(
                    target,
                    "❌ Your access request was rejected.",
                )
            except TelegramError:
                pass

            await edit_message(
                query,
                f"❌ Rejected <code>{target}</code>.",
            )

        return

    if data.startswith("admin:"):
        if not (is_owner(uid) or str(uid) in admin_roles):
            await query.answer("Admin only", show_alert=True); return

        action = data.split(":", 1)[1]
        if not is_owner(uid) and action not in {"close","overview","users","premium","credits","banned","processes","analytics","watchdog","panelreminder","codes","hoststatus","security","backupinfo","backupnow","v10requests","v10github","v10emergency"}:
            await query.answer("Owner required for this action", show_alert=True); return

        if action == "v10requests":
            rows=pending_requests(); lines=[f"• <code>{r['id']}</code> @{esc(r.get('username') or 'not_set')}" for r in rows[:50]]
            await edit_message(query,premium_box("📩 ᴘᴇɴᴅɪɴɢ ʀᴇǫᴜᴇsᴛs",lines or ["No pending requests.","Use /approve1 /approve10 /approveall or reject variants."]),admin_buttons())
        elif action == "v10github":
            rows=[i for items in running_scripts.values() for i in items if i.source_type=='github']; await edit_message(query,premium_box("🐙 ɢɪᴛʜᴜʙ ᴅᴇᴘʟᴏʏs",[f"Connected projects • <code>{len(rows)}</code>",f"Polling • <code>{GITHUB_POLL_SECONDS}s</code>","Auto deploy checks new commit SHA and redeploys changed repos."]),admin_buttons())
        elif action == "v10emergency":
            f=v10_flags(); await edit_message(query,premium_box("🚨 ᴇᴍᴇʀɢᴇɴᴄʏ",[f"Deployments • <code>{f['deployments']}</code>",f"Dependencies • <code>{f['dependencies']}</code>",f"Queue • <code>{f['queue']}</code>",f"Read Only • <code>{f['readonly']}</code>","Use /emergency KEY on|off"]),admin_buttons())
        elif action == "close":
            await edit_message(
                query,
                "✅ Admin Center closed.",
            )

        elif action == "overview":
            await edit_message(
                query,
                admin_overview(),
                admin_buttons(),
            )

        elif action == "users":
            rows = []

            for user_id in sorted(approved_users):
                stat = get_stat(user_id)
                rows.append(
                    f"• <code>{user_id}</code> "
                    f"@{esc(stat.get('username') or 'not_set')}"
                )

            await edit_message(
                query,
                "<b>👥 Approved Users</b>\n\n"
                + ("\n".join(rows[:80]) or "None"),
                admin_buttons(),
            )

        elif action == "premium":
            rows = [
                f"• <code>{x}</code>"
                for x in sorted(premium_users)
            ]

            await edit_message(
                query,
                "<b>💎 Premium Users</b>\n\n"
                + ("\n".join(rows) or "None"),
                admin_buttons(),
            )

        elif action == "credits":
            rows = [
                f"• <code>{uid}</code>: "
                f"<code>{amount}</code>"
                for uid, amount in sorted(
                    user_credits.items()
                )
            ]

            await edit_message(
                query,
                "<b>💳 Credit Wallets</b>\n\n"
                + ("\n".join(rows[:100]) or "None"),
                admin_buttons(),
            )

        elif action == "banned":
            rows = [
                f"• <code>{x}</code>"
                for x in sorted(banned_users)
            ]

            await edit_message(
                query,
                "<b>🚫 Banned Users</b>\n\n"
                + ("\n".join(rows) or "None"),
                admin_buttons(),
            )

        elif action == "processes":
            rows = []

            for user_id, items in running_scripts.items():
                for item in items:
                    rows.append(
                        f"• <code>{user_id}</code> — "
                        f"{esc(item.display_name)} "
                        f"{'🟢' if item.running else '🔴'}"
                    )

            await edit_message(
                query,
                "<b>🚀 Hosted Projects</b>\n\n"
                + ("\n".join(rows[:100]) or "None"),
                admin_buttons(),
            )

        elif action == "startall":
            started = 0
            failed = 0

            for user_id, items in running_scripts.items():
                async with lock_for(user_id):
                    for item in items:
                        if item.running:
                            continue

                        try:
                            spawn_script(
                                item,
                                Path(item.entry_file),
                                Path(item.folder),
                                Path(item.log_path),
                            )
                            await asyncio.sleep(0.1)

                            if item.running:
                                started += 1
                            else:
                                failed += 1

                        except Exception:
                            logger.exception(
                                "Start-all failure"
                            )
                            failed += 1

            await edit_message(
                query,
                f"▶️ Start Everything Complete\n\n"
                f"✅ Started: <code>{started}</code>\n"
                f"❌ Failed: <code>{failed}</code>",
                admin_buttons(),
            )

        elif action == "stopall":
            stopped = 0

            for items in running_scripts.values():
                for item in items:
                    if item.running and kill_process(item):
                        stopped += 1

            await edit_message(
                query,
                f"🧨 Stopped <code>{stopped}</code> projects.",
                admin_buttons(),
            )

        elif action == "forcejoin":
            await edit_message(
                query,
                "<b>🔐 Force Join Status</b>\n\n"
                f"Status: "
                f"<code>{'ON' if FORCE_JOIN_ENABLED else 'OFF'}</code>\n"
                f"Channels: <code>{esc(', '.join(CHANNEL_USERNAMES))}</code>\n\n"
                "To change it, edit "
                "<code>FORCE_JOIN_ENABLED</code> in main.py.\n"
                "The bot must be admin in both chats.",
                admin_buttons(),
            )

        elif action == "maintenance":
            global maintenance_mode
            maintenance_mode = not maintenance_mode
            save_data()

            await edit_message(
                query,
                admin_overview(),
                admin_buttons(),
            )

        elif action == "keepalive":
            await edit_message(query, keepalive_text(), admin_buttons())

        elif action == "hoststatus":
            await edit_message(query, host_stats_text(), admin_buttons())

        elif action == "security":
            await edit_message(query, security_text(), admin_buttons())

        elif action == "backupinfo":
            backups = sorted(BACKUPS_DIR.glob("QURESHIxOTP_full_source_backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
            lines = [f"Automatic interval: <code>24h</code>", f"Stored full backups: <code>{len(backups)}</code>", "Use <code>/backup</code> or tap <b>Backup Now</b>."]
            if backups: lines.append(f"Latest: <code>{esc(backups[0].name)}</code>")
            await edit_message(query, premium_box("💾 ʙᴀᴄᴋᴜᴘ ᴠᴀᴜʟᴛ", lines), admin_buttons())

        elif action == "backupnow":
            if not is_owner(uid):
                await query.answer("Owner only",show_alert=True); return
            await query.answer("Creating full backup…")
            try:
                archive=await asyncio.to_thread(create_full_source_backup)
                await send_full_backup_to_vault(context,archive,"💾 ᴀᴅᴍɪɴ ʙᴀᴄᴋᴜᴘ ɴᴏᴡ")
                await send_real_file(context.bot,uid,archive,f"💾 {BRAND_NAME} full source backup")
                await edit_message(query,premium_box("✅ ʙᴀᴄᴋᴜᴘ ᴄᴏᴍᴘʟᴇᴛᴇ",[f"Archive • <code>{esc(archive.name)}</code>","✅ Actual ZIP sent to owner","✅ Actual ZIP sent to Backup Vault"]),admin_buttons())
            except Exception as exc:
                logger.exception("Admin backup now failed")
                await edit_message(query,premium_box("❌ ʙᴀᴄᴋᴜᴘ ғᴀɪʟᴇᴅ",[f"Reason • <code>{esc(exc)}</code>"]),admin_buttons())

        elif action == "analytics":
            total_projects=sum(len(x) for x in running_scripts.values()); running=sum(i.running for x in running_scripts.values() for i in x)
            await edit_message(query,premium_box("📈 ᴀɴᴀʟʏᴛɪᴄs",[f"Users: <code>{len(user_stats)}</code>",f"Projects: <code>{total_projects}</code>",f"Running: <code>{running}</code>",f"Codes: <code>{len(redeem_codes)}</code>"]),admin_buttons())

        elif action == "watchdog":
            await edit_message(query,premium_box("🛡 ᴡᴀᴛᴄʜᴅᴏɢ",[f"Status: <code>{'ON' if watchdog_enabled else 'OFF'}</code>",f"Interval: <code>{watchdog_interval}s</code>",f"Restarts: <code>{watchdog_restarts}</code>"]),admin_buttons())

        elif action == "panelreminder":
            await edit_message(query,premium_box("⏰ ᴘᴀɴᴇʟ ʀᴇᴍɪɴᴅᴇʀ",[f"Status: <code>{'ON' if panel_reminder_enabled else 'OFF'}</code>",f"Cycle: <code>{PANEL_REMINDER_HOURS}h</code>","Use <code>/panelvisited</code> after visiting."]),admin_buttons())

        elif action == "panelvisited":
            if not is_owner(uid):
                await query.answer("Owner only",show_alert=True); return
            global panel_last_confirmed_at, panel_last_reminder_at
            panel_last_confirmed_at=time.time(); panel_last_reminder_at=0.0; save_v7_data()
            await edit_message(query,premium_box("✅ ᴘᴀɴᴇʟ ᴠɪsɪᴛ",["Visit confirmed.","Next reminder: <code>3 days</code>"]),admin_buttons())

        elif action == "codes":
            rows=[f"• <code>{esc(c)}</code> — {'OFF' if r.get('disabled') else 'ON'}" for c,r in list(redeem_codes.items())[:25]]
            await edit_message(query,premium_box("🎟 ᴄᴏᴅᴇs",rows or ["No redeem codes."]),admin_buttons())

        elif action == "cleanup":
            removed = 0

            for user_id, items in list(
                running_scripts.items()
            ):
                kept = []

                for item in items:
                    if (
                        Path(item.folder).exists()
                        and Path(item.entry_file).exists()
                    ):
                        kept.append(item)
                    else:
                        removed += 1

                running_scripts[user_id] = kept

            save_projects()

            await edit_message(
                query,
                f"🧹 Removed <code>{removed}</code> "
                "missing project records.",
                admin_buttons(),
            )

        elif action == "commands":
            await edit_message(
                query,
                admin_commands_text(),
                admin_buttons(),
            )

        return

    if not is_approved(uid) or uid in banned_users:
        await query.answer(
            "Access restricted",
            show_alert=True,
        )
        return

    if data == "project:list":
        await edit_message(
            query,
            projects_text(uid),
            project_list_buttons(uid),
        )
        return

    parts = data.split(":")

    if len(parts) != 3 or parts[0] != "project":
        return

    action = parts[1]

    try:
        index = int(parts[2])
        item = scripts_for(uid)[index]
    except (ValueError, IndexError):
        await query.answer(
            "Project not found",
            show_alert=True,
        )
        return

    async with lock_for(uid):
        if action == "view":
            status = (
                "🟢 Online"
                if item.running
                else f"🔴 Offline ({esc(item.exit_code)})"
            )

            text = (
                f"<b>🧩 {esc(item.display_name)}</b>\n\n"
                f"Status: {status}\n"
                f"Entry: "
                f"<code>{esc(Path(item.entry_file).name)}</code>\n"
                f"PID: <code>{esc(item.pid)}</code>\n"
                f"Uptime: "
                f"<code>{uptime(item.started_at) if item.running else '—'}</code>\n"
                f"Restarts: <code>{item.restarts}</code>"
            )

            await edit_message(query, project_center_text(item), project_center_buttons(index, item))

        elif action == "stop":
            ok = kill_process(item)

            await edit_message(
                query,
                (
                    f"🛑 Stopped <b>{esc(item.display_name)}</b>."
                    if ok
                    else "❌ Could not stop project."
                ),
                project_center_buttons(index, item),
            )

        elif action in {"start", "restart"}:
            if item.running:
                kill_process(item)

            item.restarts += 1

            try:
                spawn_script(
                    item,
                    Path(item.entry_file),
                    Path(item.folder),
                    Path(item.log_path),
                )
                await asyncio.sleep(0.5)

                await edit_message(
                    query,
                    (
                        f"✅ Started "
                        f"<b>{esc(item.display_name)}</b>.\n"
                        f"PID: <code>{item.pid}</code>"
                        if item.running
                        else "❌ Project exited after launch."
                    ),
                    project_control_buttons(
                        index,
                        item.running,
                    ),
                )

            except Exception as exc:
                await edit_message(
                    query,
                    f"❌ Start failed: "
                    f"<code>{esc(exc)}</code>",
                    project_control_buttons(
                        index,
                        False,
                    ),
                )

        elif action == "logs":
            path = Path(item.log_path)
            content = (
                path.read_text(
                    "utf-8",
                    errors="replace",
                )[-MAX_LOG_CHARS:]
                if path.exists()
                else "No output."
            )

            await edit_message(
                query,
                f"<b>🧾 {esc(item.display_name)}</b>\n\n"
                f"<pre>{esc(content)}</pre>",
                project_center_buttons(index, item),
            )

        elif action == "logfile":
            path = Path(item.log_path)

            if path.exists():
                await send_real_file(context.bot, uid, path, f"Logs: {item.display_name}")
                await query.answer("Log file sent")
            else:
                await query.answer(
                    "Log file not found",
                    show_alert=True,
                )

        elif action == "rename":
            pending_project_names[uid] = item

            await query.message.reply_text(
                "✏️ Send the new project name now.\n"
                "Maximum 40 characters."
            )

        elif action == "delete":
            if item.running:
                await query.answer(
                    "Stop the project first",
                    show_alert=True,
                )
                return

            safe_remove_folder(item.folder)
            scripts_for(uid).pop(index)
            save_projects()

            await edit_message(
                query,
                projects_text(uid),
                project_list_buttons(uid),
            )



# ═════════════════════════════════════════════════════════════════════════════
# V10 PREMIUM PLATFORM MODULE
# ═════════════════════════════════════════════════════════════════════════════

def global_cfg() -> dict[str, Any]:
    return project_settings.setdefault("__v10_global__", {})

def pending_requests() -> list[dict[str, Any]]:
    return global_cfg().setdefault("pending_requests", [])

def deployment_history(item: ScriptProcess) -> list[dict[str, Any]]:
    return project_settings.setdefault(project_key(item), {}).setdefault("deploy_history", [])

def record_deploy(item: ScriptProcess, status: str, detail: str = "") -> None:
    hist = deployment_history(item)
    hist.append({"time": datetime.now().isoformat(timespec="seconds"), "status": status,
                 "commit": item.commit_sha[:10], "detail": detail[:300]})
    del hist[:-10]
    save_v7_data()

def v10_flags() -> dict[str, bool]:
    cfg=global_cfg()
    return {"deployments": bool(cfg.get("deployments_enabled", True)),
            "dependencies": bool(cfg.get("dependencies_enabled", True)),
            "queue": bool(cfg.get("queue_mode", False)),
            "readonly": bool(cfg.get("readonly_mode", False))}

def plan_catalog() -> dict[str, dict[str, Any]]:
    defaults={
        "free":{"projects":1,"storage":100,"backups":False,"autorestart":False,"priority":False},
        "basic":{"projects":3,"storage":500,"backups":True,"autorestart":True,"priority":False},
        "premium":{"projects":10,"storage":2048,"backups":True,"autorestart":True,"priority":True},
        "business":{"projects":30,"storage":5120,"backups":True,"autorestart":True,"priority":True},
        "lifetime":{"projects":30,"storage":5120,"backups":True,"autorestart":True,"priority":True},
    }
    return global_cfg().setdefault("plan_catalog", defaults)

def project_notifications(uid:int) -> dict[str,bool]:
    return project_settings.setdefault(f"__notify__:{uid}", {}).setdefault("prefs", {
        "crash":True,"restart":True,"deploy":True,"storage":True,"expiry":True,"maintenance":True})

def github_safe_url(url:str)->str:
    url=url.strip()
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?", url):
        raise ValueError("Only standard https://github.com/OWNER/REPO URLs are accepted.")
    return url.rstrip("/")

def github_repo_parts(url:str)->tuple[str,str]:
    safe=github_safe_url(url)
    path=safe.removeprefix("https://github.com/").removesuffix(".git")
    owner,repo=path.split("/",1)
    return owner,repo

def _load_github_tokens()->dict[str,str]:
    try:
        if GITHUB_TOKENS_FILE.exists():
            data=json.loads(GITHUB_TOKENS_FILE.read_text("utf-8"))
            return {str(k):str(v) for k,v in data.items() if v}
    except Exception:
        logger.exception("Could not load GitHub token store")
    return {}

_GITHUB_TOKEN_CACHE: dict[str,str] = _load_github_tokens()

def _save_github_token_db(uid:int,token:str)->None:
    try:
        with sqlite3.connect(V9_DB_FILE) as db:
            db.execute("CREATE TABLE IF NOT EXISTS github_tokens (user_id INTEGER PRIMARY KEY, token TEXT NOT NULL, updated_at TEXT NOT NULL)")
            if token:
                db.execute("INSERT OR REPLACE INTO github_tokens(user_id,token,updated_at) VALUES(?,?,?)",(int(uid),token,datetime.now(timezone.utc).isoformat()))
            else:
                db.execute("DELETE FROM github_tokens WHERE user_id=?",(int(uid),))
            db.commit()
        try: os.chmod(V9_DB_FILE,0o600)
        except OSError: pass
    except Exception:
        logger.exception("Could not mirror GitHub token into SQLite")

def _load_github_token_db(uid:int)->str:
    try:
        if not V9_DB_FILE.exists(): return ""
        with sqlite3.connect(V9_DB_FILE) as db:
            db.execute("CREATE TABLE IF NOT EXISTS github_tokens (user_id INTEGER PRIMARY KEY, token TEXT NOT NULL, updated_at TEXT NOT NULL)")
            row=db.execute("SELECT token FROM github_tokens WHERE user_id=?",(int(uid),)).fetchone()
            return str(row[0]).strip() if row and row[0] else ""
    except Exception:
        return ""

def github_token_for(uid:int)->str:
    saved=_GITHUB_TOKEN_CACHE.get(str(uid),"").strip()
    if not saved:
        saved=_load_github_token_db(uid)
        if saved: _GITHUB_TOKEN_CACHE[str(uid)]=saved
    if saved: return saved
    per_user=os.getenv(f"GITHUB_TOKEN_{uid}","").strip()
    if per_user: return per_user
    if int(uid)==int(OWNER_ID): return os.getenv("GITHUB_TOKEN","").strip()
    return ""

def save_github_token(uid:int,token:str)->None:
    token=token.strip()
    data=_load_github_tokens()
    if token:
        data[str(uid)]=token; _GITHUB_TOKEN_CACHE[str(uid)]=token
    else:
        data.pop(str(uid),None); _GITHUB_TOKEN_CACHE.pop(str(uid),None)
    tmp=GITHUB_TOKENS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2),"utf-8")
    try: os.chmod(tmp,0o600)
    except OSError: pass
    tmp.replace(GITHUB_TOKENS_FILE)
    try: os.chmod(GITHUB_TOKENS_FILE,0o600)
    except OSError: pass
    _save_github_token_db(uid,token)

def github_api_json(url:str,token:str="",timeout:int=30)->dict:
    headers={"User-Agent":"QURESHIxOTP-Host/10.1","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    if token: headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8","replace"))
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","replace")[-500:]
        if e.code in (401,403): raise RuntimeError("GitHub authentication/permission failed. Check your token and repo access.")
        if e.code==404: raise RuntimeError("Repository/branch not found or private repo token is missing.")
        raise RuntimeError(f"GitHub API HTTP {e.code}: {body}")

def github_default_branch(url:str,token:str="")->str:
    owner,repo=github_repo_parts(url)
    data=github_api_json(f"https://api.github.com/repos/{owner}/{repo}",token)
    return str(data.get("default_branch") or "main")

def github_remote_sha(url:str,branch:str,token:str="")->str:
    owner,repo=github_repo_parts(url)
    data=github_api_json(f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}",token)
    sha=str(data.get("sha") or "")
    if not sha: raise RuntimeError("Could not read latest GitHub commit SHA")
    return sha

def git_cmd(args:list[str], cwd:Path|None=None, timeout:int=120)->str:
    git=shutil.which("git")
    if not git: raise RuntimeError("git is not installed on this host")
    cp=subprocess.run([git,*args], cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, timeout=timeout)
    out=cp.stdout.decode("utf-8",errors="replace")
    if cp.returncode!=0: raise RuntimeError(out[-1800:] or "git command failed")
    return out.strip()

def _flatten_github_archive(extracted:Path)->Path:
    children=[x for x in extracted.iterdir() if x.name!="__MACOSX"]
    if len(children)==1 and children[0].is_dir(): return children[0]
    return extracted

def github_archive_download(url:str,branch:str,destination:Path,token:str="")->str:
    owner,repo=github_repo_parts(url)
    sha=github_remote_sha(url,branch,token)
    archive_url=f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
    headers={"User-Agent":"QURESHIxOTP-Host/10.1","Accept":"application/vnd.github+json"}
    if token: headers["Authorization"]="Bearer "+token
    tmp_root=destination.parent/(destination.name+"_gh_tmp")
    zip_path=destination.parent/(destination.name+"_repo.zip")
    shutil.rmtree(tmp_root,ignore_errors=True); zip_path.unlink(missing_ok=True)
    try:
        req=urllib.request.Request(archive_url,headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=90) as r, zip_path.open("wb") as out:
                shutil.copyfileobj(r,out)
        except urllib.error.HTTPError as e:
            if e.code in (401,403): raise RuntimeError("Private GitHub repo authentication failed. Use /setgithubtoken with a fine-grained token that can read this repo.")
            if e.code==404: raise RuntimeError("Repository/branch not found or private repo token is missing. Use /setgithubtoken first.")
            raise RuntimeError(f"GitHub archive download failed (HTTP {e.code}).")
        tmp_root.mkdir(parents=True,exist_ok=True)
        safe_extract_zip_owner(zip_path,tmp_root)
        src=_flatten_github_archive(tmp_root)
        destination.mkdir(parents=True,exist_ok=True)
        for child in src.iterdir():
            target=destination/child.name
            if child.is_dir(): shutil.copytree(child,target,dirs_exist_ok=True)
            else: shutil.copy2(child,target)
        return sha
    finally:
        zip_path.unlink(missing_ok=True); shutil.rmtree(tmp_root,ignore_errors=True)

def github_initial_checkout(url:str,branch:str,destination:Path,token:str="")->tuple[str,str]:
    git=shutil.which("git")
    # Use native git for public repos when available. Tokens are deliberately not embedded in clone URLs.
    if git and not token:
        git_cmd(["clone","--depth","1","--branch",branch,url,str(destination)],None,180)
        return git_cmd(["rev-parse","HEAD"],destination,30).strip(),"Native Git"
    sha=github_archive_download(url,branch,destination,token)
    return sha,"GitHub Archive API"

def repo_head(folder:Path)->str:
    if (folder/".git").exists() and shutil.which("git"):
        return git_cmd(["rev-parse","HEAD"],folder,30).strip()
    return ""

def snapshot_project(item:ScriptProcess, label:str="deploy") -> str:
    hist_dir=Path(item.folder)/".QURESHIxOTP_history"; hist_dir.mkdir(exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    out=hist_dir/f"{stamp}_{label}.zip"
    root=Path(item.folder)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for f in root.rglob("*"):
            if not f.is_file() or ".venv" in f.parts or "node_modules" in f.parts or ".QURESHIxOTP_history" in f.parts or ".git" in f.parts: continue
            z.write(f, f.relative_to(root))
    return out.name

def restore_snapshot(item:ScriptProcess, snap_name:str)->None:
    root=Path(item.folder); snap=root/".QURESHIxOTP_history"/Path(snap_name).name
    if not snap.exists(): raise FileNotFoundError("Snapshot not found")
    was=item.running
    if was: kill_process(item)
    keep={".venv","node_modules",".git",".QURESHIxOTP_history","runtime.log"}
    for child in root.iterdir():
        if child.name in keep: continue
        if child.is_dir(): shutil.rmtree(child,ignore_errors=True)
        else: child.unlink(missing_ok=True)
    safe_extract_zip_owner(snap,root)
    entry=detect_entry(root)
    if not entry: raise RuntimeError("No runnable entry after rollback")
    item.entry_file=str(entry); item.runtime=runtime_for_entry(entry)
    if was: spawn_script(item,entry,root,Path(item.log_path))
    save_projects()

def project_center_text(item:ScriptProcess)->str:
    r=project_resources(item); settings=project_settings.get(project_key(item),{})
    return premium_box("🚀 ᴘʀᴏᴊᴇᴄᴛ ᴄᴏɴᴛʀᴏʟ",[
        f"📦 <b>{esc(item.display_name)}</b>",
        f"🟢 Status • <code>{'ONLINE' if item.running else 'OFFLINE'}</code>",
        f"⚙️ Runtime • <code>{esc(item.runtime.title())}</code>",
        f"🆔 PID • <code>{esc(item.pid)}</code>",
        f"🧠 RAM • <code>{esc(r['ram'])}</code>", f"🔥 CPU • <code>{esc(r['cpu'])}</code>",
        f"💾 Disk • <code>{esc(r['disk'])}</code>", f"⏱ Uptime • <code>{uptime(item.started_at) if item.running else '—'}</code>",
        f"♻️ Restarts • <code>{item.restarts}</code>", f"🐙 Source • <code>{esc(item.source_type)}</code>",
        f"🔐 ENV Guard • <code>{'BLOCKED' if settings.get('env_blocked') else 'READY'}</code>",
        f"☁️ Data Sync • <code>{'ON' if settings.get('github_data_sync',{}).get('enabled') else 'OFF'}</code>",
        f"🔔 Auto Deploy • <code>{'ON' if settings.get('github_autodeploy') else 'OFF'}</code>"])

def github_project_buttons(index:int,item:ScriptProcess)->InlineKeyboardMarkup:
    auto=bool(project_settings.get(project_key(item),{}).get("github_autodeploy",False))
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Check Updates",callback_data=f"v1073:ghcheck:{index}"),InlineKeyboardButton("⬇️ Pull Latest",callback_data=f"v1073:ghsync:{index}")],
        [InlineKeyboardButton("🚀 Force Redeploy",callback_data=f"v1073:ghforce:{index}"),InlineKeyboardButton(f"🔔 Auto Deploy {'ON' if auto else 'OFF'}",callback_data=f"v1073:ghtoggle:{index}")],
        [InlineKeyboardButton("🔄 Refresh",callback_data=f"v1073:github:{index}"),InlineKeyboardButton("⬅️ Project",callback_data=f"v10:center:{index}")]
    ])

def project_center_buttons(index:int,item:ScriptProcess)->InlineKeyboardMarkup:
    primary=InlineKeyboardButton("⏹ Stop",callback_data=f"project:stop:{index}") if item.running else InlineKeyboardButton("▶️ Start",callback_data=f"project:start:{index}")
    return InlineKeyboardMarkup([
        [primary,InlineKeyboardButton("♻️ Restart",callback_data=f"project:restart:{index}"),InlineKeyboardButton("📊 Health",callback_data=f"v10:health:{index}")],
        [InlineKeyboardButton("🧾 Logs",callback_data=f"project:logs:{index}"),InlineKeyboardButton("📄 Download Log",callback_data=f"project:logfile:{index}")],
        [InlineKeyboardButton("🧹 Clear Log",callback_data=f"v10:clearlog:{index}"),InlineKeyboardButton("🔄 Refresh",callback_data=f"v10:center:{index}")],
        [InlineKeyboardButton("📦 Packages",callback_data=f"v10:packages:{index}"),InlineKeyboardButton("🔐 ENV",callback_data=f"v10:env:{index}"),InlineKeyboardButton("💾 Backup",callback_data=f"v10:backup:{index}")],
        [InlineKeyboardButton("📜 Deploys",callback_data=f"v10:history:{index}"),InlineKeyboardButton("⏪ Rollback",callback_data=f"v10:rollback:{index}")],
        [InlineKeyboardButton("🐙 GitHub",callback_data=f"v10:github:{index}"),InlineKeyboardButton("🔔 Notify",callback_data=f"v10:notify:{index}"),InlineKeyboardButton("⚙️ Settings",callback_data=f"v10:settings:{index}")],
        [InlineKeyboardButton("📁 Files",callback_data=f"v106:files:{index}"),InlineKeyboardButton("📤 Replace File",callback_data=f"v106:replacehelp:{index}")],
        [InlineKeyboardButton("🧙 Setup",callback_data=f"v107:setup:{index}"),InlineKeyboardButton("🔐 ENV Wizard",callback_data=f"v107:setup:{index}")],
        [InlineKeyboardButton("🗑 Delete Project",callback_data=f"project:delete:{index}"),InlineKeyboardButton("⬅️ Projects",callback_data="project:list")]])

async def group_silent_handler(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    raise ApplicationHandlerStop

async def requests_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    rows=pending_requests()
    lines=[f"{i+1}. <code>{r['id']}</code> @{esc(r.get('username') or 'not_set')} — {esc(r.get('reason',''))[:60]}" for i,r in enumerate(rows[:50])]
    await update.effective_message.reply_text(premium_box("📩 ᴘᴇɴᴅɪɴɢ ʀᴇǫᴜᴇsᴛs",lines or ["No pending requests."]),parse_mode=ParseMode.HTML)

async def _bulk_access(update:Update,approve:bool,count:int|None)->None:
    if not owner_only(update): return
    rows=pending_requests(); selected=rows[:] if count is None else rows[:count]
    if not selected:
        await update.effective_message.reply_text("📭 No pending requests."); return
    for r in selected:
        uid=int(r["id"])
        if approve:
            approved_users.add(uid); banned_users.discard(uid); user_credits.setdefault(str(uid),DEFAULT_CREDITS)
        try: await update.get_bot().send_message(uid,"✅ Your QURESHIxOTP Host access request was approved." if approve else "❌ Your QURESHIxOTP Host access request was rejected.")
        except TelegramError: pass
    del rows[:len(selected)]; save_data(); save_v7_data()
    await update.effective_message.reply_text(premium_box("✅ ʙᴜʟᴋ ᴀᴄᴄᴇss",[f"Action • <b>{'APPROVE' if approve else 'REJECT'}</b>",f"Processed • <code>{len(selected)}</code>",f"Remaining • <code>{len(rows)}</code>"]),parse_mode=ParseMode.HTML)

async def approve1_cmd(u,c): await _bulk_access(u,True,1)
async def approve10_cmd(u,c): await _bulk_access(u,True,10)
async def approveall_cmd(u,c): await _bulk_access(u,True,None)
async def reject1_cmd(u,c): await _bulk_access(u,False,1)
async def reject10_cmd(u,c): await _bulk_access(u,False,10)
async def rejectall_cmd(u,c): await _bulk_access(u,False,None)

async def setgithubtoken_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    uid=update.effective_user.id
    if not context.args:
        await update.effective_message.reply_text("Usage: /setgithubtoken YOUR_GITHUB_TOKEN\n\nSupports fine-grained or classic PAT. Use the minimum repository permissions required.")
        return
    token=context.args[0].strip()
    # Remove the message carrying the secret as early as possible.
    try: await update.effective_message.delete()
    except TelegramError: pass
    try:
        # Validate token before storing it.
        account=github_api_json("https://api.github.com/user",token,20)
        save_github_token(uid,token)
        await context.bot.send_message(uid,premium_box("✅ ɢɪᴛʜᴜʙ ᴛᴏᴋᴇɴ ʀᴇᴍᴇᴍʙᴇʀᴇᴅ",[f"Account • <code>{esc(str(account.get('login') or 'GitHub'))}</code>","✅ Token verified and saved for future repositories.","♻️ You do NOT need to enter it again for every new project.","🔒 Token value is never shown in status/log messages.","⚠️ The saved token must have access to each private repository you deploy."]),parse_mode=ParseMode.HTML)
    except Exception as e:
        await context.bot.send_message(uid,f"❌ GitHub token validation failed: {esc(e)}")

async def githubtoken_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    configured=bool(github_token_for(update.effective_user.id))
    await update.effective_message.reply_text(premium_box("🔐 ɢɪᴛʜᴜʙ ᴀᴄᴄᴇss",[f"Token • <code>{'REMEMBERED' if configured else 'NOT SET'}</code>","One saved token is reused automatically for all repositories that token can access.","Private repositories require that the saved token has permission for that specific repo.","Commands • <code>/setgithubtoken TOKEN</code> • <code>/delgithubtoken</code>"]),parse_mode=ParseMode.HTML)

async def delgithubtoken_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    save_github_token(update.effective_user.id,"")
    await update.effective_message.reply_text("✅ Saved GitHub token removed.")

async def connectrepo_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    flags=v10_flags()
    if (not flags["deployments"]) or flags["readonly"]:
        await update.effective_message.reply_text("⏸ New deployments are paused/read-only by admin."); return
    if not context.args:
        await update.effective_message.reply_text("Usage: /connectrepo https://github.com/OWNER/REPO [branch] [project name]\nPrivate repo: first use /setgithubtoken YOUR_TOKEN"); return
    uid=update.effective_user.id
    if active_count(uid)>=running_limit(uid): await update.effective_message.reply_text("⚠️ Running project limit reached."); return
    try: url=github_safe_url(context.args[0])
    except ValueError as e: await update.effective_message.reply_text(f"❌ {e}"); return
    token=github_token_for(uid)
    try:
        branch=context.args[1] if len(context.args)>1 else await asyncio.to_thread(github_default_branch,url,token)
    except Exception as e:
        remembered=bool(github_token_for(uid))
        await update.effective_message.reply_text(premium_box("❌ ɢɪᴛʜᴜʙ ʀᴇᴘᴏ ᴄʜᴇᴄᴋ ғᴀɪʟᴇᴅ",[f"Reason • <code>{esc(e)}</code>",f"Saved Token • <code>{'REMEMBERED' if remembered else 'NOT SET'}</code>","If this is a private repository, the saved token must have access to this specific repo.","You only need /setgithubtoken again if the token expired/revoked or does not include this repository."]),parse_mode=ParseMode.HTML); return
    name=clean_project_name(" ".join(context.args[2:]) or url.rsplit('/',1)[-1].removesuffix('.git'))
    progress=await update.effective_message.reply_text(premium_box("🐙 ɢɪᴛʜᴜʙ ᴅᴇᴘʟᴏʏ",["① Repository access check • ✅",f"🌿 Branch • <code>{esc(branch)}</code>","② Downloading source…"]),parse_mode=ParseMode.HTML)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S_%f"); folder=user_folder(uid)/f"{stamp}_{name}"; folder.parent.mkdir(parents=True,exist_ok=True)
    try:
        sha,method=await asyncio.to_thread(github_initial_checkout,url,branch,folder,token)
        await progress.edit_text(premium_box("🐙 ɢɪᴛʜᴜʙ ᴅᴇᴘʟᴏʏ",[f"✅ Source ready • <code>{esc(method)}</code>",f"🔖 Commit • <code>{esc(sha[:10])}</code>","③ Detecting runtime…"]),parse_mode=ParseMode.HTML)
        entry=detect_entry(folder)
        if not entry: raise RuntimeError("No supported runnable entry found. Use /setentry after adding a supported startup file.")
        entries=detect_entries(folder)
        if len(entries)>1: project_settings.setdefault(project_key(folder),{})["entry_candidates"]=[str(x.relative_to(folder)) for x in entries[:20]]
        risk,findings=scan_project(folder) if SECURITY_SCAN_ENABLED else ("DISABLED",[])
        if risk=="HIGH" and not is_owner(uid): raise RuntimeError("High-risk code detected: "+"; ".join(findings[:3]))
        await progress.edit_text(premium_box("🐙 ɢɪᴛʜᴜʙ ᴅᴇᴘʟᴏʏ",["✅ Runtime detected",f"🛡 Scan • <code>{risk}</code>","④ Preparing dependencies…"]),parse_mode=ParseMode.HTML)
        log=folder/"runtime.log"
        note="Dependency installation disabled by admin" if not flags["dependencies"] else await asyncio.to_thread(install_project_dependencies,folder,entry,log)
        await progress.edit_text(premium_box("🐙 ɢɪᴛʜᴜʙ ᴅᴇᴘʟᴏʏ",[f"✅ Dependencies • <code>{esc(note[:90])}</code>","⑤ Checking ENV requirements…"]),parse_mode=ParseMode.HTML)
        # Register first so missing ENV never destroys a successfully connected repository.
        item=ScriptProcess(display_name=name,entry_file=str(entry),folder=str(folder),log_path=str(log),runtime=runtime_for_entry(entry),source_type="github",repo_url=url,branch=branch,commit_sha=sha)
        scripts_for(uid).append(item); save_projects()
        cfg=project_settings.setdefault(project_key(item),{}); cfg["github_autodeploy"]=True; cfg["github_last_sha"]=item.commit_sha; cfg["github_method"]=method
        # Per-user preference: optionally skip ENV guard automatically for future GitHub projects.
        if global_cfg().setdefault("github_env_skip_default",{}).get(str(uid),False):
            cfg["env_setup_skipped"]=True
            cfg["env_blocked"]=False
        save_v7_data()
        ready,missing=ensure_project_env_ready(item,folder)
        if not ready:
            item.desired_running=False; save_projects(); record_deploy(item,"blocked","ENV required: "+", ".join(missing))
            await progress.edit_text(premium_box("🔐 ᴇɴᴠ sᴇᴛᴜᴘ ʀᴇǫᴜɪʀᴇᴅ",[f"Project • <b>{esc(name)}</b>","Repository connected successfully.","🚫 Project was NOT started.","Missing ENV • "+", ".join(f"<code>{esc(x)}</code>" for x in missing[:20]),"","Use the buttons below to add values, skip once, or remember ENV skip for future GitHub projects.","🛡 QURESHIxOTP manager BOT_TOKEN/GITHUB_TOKEN were not shared with this project."]),parse_mode=ParseMode.HTML,reply_markup=env_wizard_keyboard(len(scripts_for(uid))-1,item))
            return
        spawn_script(item,entry,folder,log); record_deploy(item,"success","Initial GitHub deploy via "+method)
        await asyncio.sleep(LAUNCH_CHECK_SECONDS)
        if not item.running: raise RuntimeError("Project exited after launch. Open Logs/Diagnose from Project Control Center.")
        await progress.edit_text(project_center_text(item),parse_mode=ParseMode.HTML,reply_markup=project_center_buttons(len(scripts_for(uid))-1,item))
    except Exception as e:
        if not any(str(Path(x.folder).resolve()) == str(folder.resolve()) for x in scripts_for(uid)):
            shutil.rmtree(folder,ignore_errors=True)
        await progress.edit_text(premium_box("❌ ɢɪᴛʜᴜʙ ᴅᴇᴘʟᴏʏ ғᴀɪʟᴇᴅ",[f"Reason • <code>{esc(e)}</code>","💡 Public repos work without git using GitHub Archive API.",f"🔐 GitHub token • <code>{'REMEMBERED' if github_token_for(uid) else 'NOT SET'}</code>","💡 Re-enter token only if it expired/revoked or lacks access to this repo.","🧾 Node dependency failures are written to runtime.log."]),parse_mode=ParseMode.HTML)

async def repos_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    rows=[]
    for item in scripts_for(update.effective_user.id):
        if item.source_type=="github": rows.append(f"• <b>{esc(item.display_name)}</b> — <code>{esc(item.branch)}</code> — <code>{esc(item.commit_sha[:10] or 'unknown')}</code>")
    await update.effective_message.reply_text(premium_box("🐙 ɢɪᴛʜᴜʙ ʀᴇᴘᴏs",rows or ["No connected repositories."]),parse_mode=ParseMode.HTML)

async def autodeploy_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if len(context.args)<2: await update.effective_message.reply_text("Usage: /autodeploy PROJECT on|off"); return
    found=find_project(update.effective_user.id," ".join(context.args[:-1])); mode=context.args[-1].lower()
    if not found or mode not in {"on","off"}: await update.effective_message.reply_text("❌ Project/mode invalid."); return
    _,item=found
    if item.source_type!="github": await update.effective_message.reply_text("❌ This project is not connected to GitHub."); return
    project_settings.setdefault(project_key(item),{})["github_autodeploy"]=(mode=="on"); save_v7_data()
    await update.effective_message.reply_text(f"✅ GitHub auto deploy {mode.upper()}.")

async def syncrepo_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text("Usage: /syncrepo PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args));
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found
    if item.source_type!="github": await update.effective_message.reply_text("❌ Not a GitHub project."); return
    msg=await update.effective_message.reply_text("🐙 Syncing repository…")
    try:
        await asyncio.to_thread(sync_github_item,item); await msg.edit_text("✅ Repository synced and redeployed.")
    except Exception as e: await msg.edit_text(f"❌ Sync failed: {e}")

async def githubcheck_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /githubcheck PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found
    if item.source_type!="github": await update.effective_message.reply_text("❌ This is not a GitHub project."); return
    try:
        token=github_token_for(update.effective_user.id)
        remote=await asyncio.to_thread(github_remote_sha,item.repo_url,item.branch,token)
        current=item.commit_sha or project_settings.get(project_key(item),{}).get("github_last_sha","")
        changed=bool(remote and remote!=current)
        text=premium_box("🐙 ɢɪᴛʜᴜʙ ᴜᴘᴅᴀᴛᴇ ᴄʜᴇᴄᴋ",[f"Project • <b>{esc(item.display_name)}</b>",f"Current • <code>{esc((current or '—')[:10])}</code>",f"Latest • <code>{esc((remote or '—')[:10])}</code>",f"Update • <code>{'AVAILABLE' if changed else 'UP TO DATE'}</code>",f"Auto Deploy • <code>{'ON' if project_settings.get(project_key(item),{}).get('github_autodeploy') else 'OFF'}</code>"])
        await update.effective_message.reply_text(text,parse_mode=ParseMode.HTML,reply_markup=github_project_buttons(scripts_for(update.effective_user.id).index(item),item))
    except Exception as e:
        await update.effective_message.reply_text(premium_box("❌ ɢɪᴛʜᴜʙ ᴄʜᴇᴄᴋ ғᴀɪʟᴇᴅ",[f"Reason • <code>{esc(e)}</code>",f"Token remembered • <code>{'YES' if github_token_for(update.effective_user.id) else 'NO'}</code>","If this is a different private repo, make sure the saved token has access to that repo."]),parse_mode=ParseMode.HTML)

async def forceredeploy_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /forceredeploy PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found
    if item.source_type!="github": await update.effective_message.reply_text("❌ This is not a GitHub project."); return
    msg=await update.effective_message.reply_text("🐙 Force redeploying latest GitHub source…")
    try:
        await asyncio.to_thread(sync_github_item,item,True)
        await msg.edit_text("✅ Latest GitHub source force-redeployed successfully.")
    except Exception as e:
        await msg.edit_text(f"❌ Force redeploy failed: {e}")

async def envskipdefault_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    mode=(context.args[0].lower() if context.args else "status")
    store=global_cfg().setdefault("github_env_skip_default",{})
    uid=str(update.effective_user.id)
    if mode in {"on","off"}:
        store[uid]=(mode=="on"); save_v7_data()
    enabled=bool(store.get(uid,False))
    await update.effective_message.reply_text(premium_box("🔐 ɢɪᴛʜᴜʙ ᴇɴᴠ ᴅᴇғᴀᴜʟᴛ",[f"Auto Skip ENV • <code>{'ON' if enabled else 'OFF'}</code>","When ON, future GitHub projects are allowed to start even if static ENV detection finds missing variables.","QURESHIxOTP Host BOT_TOKEN/GITHUB_TOKEN/secrets are still NEVER injected.","Use • <code>/envskipdefault on</code> or <code>/envskipdefault off</code>"]),parse_mode=ParseMode.HTML)

def _replace_source_from_archive(item:ScriptProcess,token:str,remote:str)->None:
    folder=Path(item.folder)
    staging=folder.parent/(folder.name+"_sync_stage")
    shutil.rmtree(staging,ignore_errors=True)
    github_archive_download(item.repo_url,item.branch,staging,token)
    preserve={".venv","node_modules",".QURESHIxOTP_history","runtime.log"}
    for child in list(folder.iterdir()):
        if child.name in preserve: continue
        if child.is_dir(): shutil.rmtree(child,ignore_errors=True)
        else: child.unlink(missing_ok=True)
    for child in staging.iterdir():
        target=folder/child.name
        if child.is_dir(): shutil.copytree(child,target,dirs_exist_ok=True)
        else: shutil.copy2(child,target)
    shutil.rmtree(staging,ignore_errors=True)

def sync_github_item(item:ScriptProcess, force:bool=False)->bool:
    if project_locked(item): raise RuntimeError("PROJECT_LOCKED: GitHub sync/redeploy disabled until admin unlocks this project")
    folder=Path(item.folder); cfg=project_settings.setdefault(project_key(item),{})
    uid=next((u for u,items in running_scripts.items() if item in items),OWNER_ID)
    token=github_token_for(uid)
    old=item.commit_sha or cfg.get("github_last_sha","")
    remote=github_remote_sha(item.repo_url,item.branch,token)
    if remote==old and not force: return False

    # V10.5: stage and validate before touching the live deployment.
    staging=folder.parent/(folder.name+"_predeploy_stage")
    shutil.rmtree(staging,ignore_errors=True)
    github_archive_download(item.repo_url,item.branch,staging,token)
    staged_entry=detect_entry(staging)
    if not staged_entry:
        shutil.rmtree(staging,ignore_errors=True)
        raise RuntimeError("Pre-deploy test failed: no supported startup entry")
    ok,why=syntax_test_entry(staged_entry)
    if not ok:
        shutil.rmtree(staging,ignore_errors=True)
        raise RuntimeError("Pre-deploy test failed: "+why)

    # V10.7 Owner-controlled Data Sync: capture runtime state before replacing GitHub source.
    if data_sync_settings(item).get("enabled"):
        github_data_sync_push(item)
    rollback_snapshot=snapshot_project(item,"pre_git")
    was=item.running
    if was: kill_process(item)
    try:
        preserve={".venv","node_modules",".QURESHIxOTP_history","runtime.log"}
        for child in list(folder.iterdir()):
            if child.name in preserve: continue
            if child.is_dir(): shutil.rmtree(child,ignore_errors=True)
            else: child.unlink(missing_ok=True)
        for child in staging.iterdir():
            target=folder/child.name
            if child.is_dir(): shutil.copytree(child,target,dirs_exist_ok=True)
            else: shutil.copy2(child,target)
        shutil.rmtree(staging,ignore_errors=True)
        entry=detect_entry(folder)
        if not entry: raise RuntimeError("No supported entry after staged deploy")
        if v10_flags()["dependencies"]: install_project_dependencies(folder,entry,Path(item.log_path))
        item.entry_file=str(entry); item.runtime=runtime_for_entry(entry); item.commit_sha=remote
        cfg["github_last_sha"]=remote; cfg["github_method"]="GitHub Archive/API Staged"
        if data_sync_settings(item).get("enabled"):
            github_data_sync_restore(item)
        spawn_script(item,entry,folder,Path(item.log_path))
        time.sleep(1.5)
        if not item.running: raise RuntimeError("New deployment exited during health check")
        mark_last_good(item)
        record_deploy(item,"success",f"GitHub {remote[:10]} staged")
        save_projects(); save_v7_data(); return True
    except Exception as exc:
        # Automatic last-working-source recovery.
        try:
            restore_snapshot(item,rollback_snapshot)
            if was and not item.running:
                spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
            record_deploy(item,"rollback",f"Automatic rollback after failed GitHub deploy: {exc}")
        except Exception:
            logger.exception("Automatic GitHub rollback failed for %s",item.display_name)
        raise

_server_alert_last: dict[str,float] = {}

async def server_alert_job(context:ContextTypes.DEFAULT_TYPE)->None:
    try:
        import psutil
        checks={"RAM":psutil.virtual_memory().percent,"DISK":psutil.disk_usage(str(BASE_DIR)).percent}
        now=time.time()
        for name,val in checks.items():
            threshold=85 if name=="RAM" else 90
            if val>=threshold and now-_server_alert_last.get(name,0)>3600:
                _server_alert_last[name]=now
                await context.bot.send_message(OWNER_ID,premium_box("🚨 sᴇʀᴠᴇʀ ᴀʟᴇʀᴛ",[f"{name} usage • <code>{val:.0f}%</code>",f"Threshold • <code>{threshold}%</code>","Check running projects and storage immediately."]),parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("Server alert monitor failed")

async def github_autodeploy_job(context:ContextTypes.DEFAULT_TYPE)->None:
    for uid,items in list(running_scripts.items()):
        for item in list(items):
            cfg=project_settings.get(project_key(item),{})
            if item.source_type!="github" or not cfg.get("github_autodeploy",False): continue
            try:
                changed=await asyncio.to_thread(sync_github_item,item)
                if changed and project_notifications(uid).get("deploy",True):
                    await context.bot.send_message(uid,premium_box("🐙 ᴀᴜᴛᴏ ʀᴇᴅᴇᴘʟᴏʏ",[f"Project • <b>{esc(item.display_name)}</b>",f"Commit • <code>{esc(item.commit_sha[:10])}</code>","Status • ✅ Online"]),parse_mode=ParseMode.HTML)
            except Exception as e:
                record_deploy(item,"failed",str(e))
                logger.exception("GitHub auto-deploy failed for %s",item.display_name)

async def deployhistory_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text("Usage: /deployhistory PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args));
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; rows=deployment_history(item)
    lines=[f"• <code>{esc(r.get('time',''))}</code> — <b>{esc(r.get('status',''))}</b> {esc(r.get('commit',''))} {esc(r.get('detail',''))}" for r in rows[-10:][::-1]]
    await update.effective_message.reply_text(premium_box("📜 ᴅᴇᴘʟᴏʏ ʜɪsᴛᴏʀʏ",lines or ["No deployment history yet."]),parse_mode=ParseMode.HTML)

async def rollback_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update); project=f[0] if f else command_payload(update); snap=f[1] if len(f)>1 else ''
    if not project: await update.effective_message.reply_text('Usage: /rollback PROJECT NAME | snapshot.zip(optional)'); return
    found=find_project(update.effective_user.id,project)
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; snaps=sorted((Path(item.folder)/'.QURESHIxOTP_history').glob('*.zip'),reverse=True) if (Path(item.folder)/'.QURESHIxOTP_history').exists() else []
    target=snap or (snaps[0].name if snaps else '')
    if not target: await update.effective_message.reply_text('❌ No rollback snapshot available.'); return
    try: await asyncio.to_thread(restore_snapshot,item,target); record_deploy(item,'rollback',target); await update.effective_message.reply_text('✅ Rollback completed.')
    except Exception as e: await update.effective_message.reply_text(f'❌ Rollback failed: {e}')


async def cloneproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /cloneproject SOURCE PROJECT | NEW PROJECT NAME'); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Source project not found.'); return
    _,src=found; name=clean_project_name(f[1]); dest=user_folder(update.effective_user.id)/(datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'_'+name)
    shutil.copytree(src.folder,dest,ignore=shutil.ignore_patterns('.venv','node_modules','.git','.QURESHIxOTP_history','runtime.log','.QURESHIxOTP_file_history'))
    entry=detect_entry(dest)
    if not entry: shutil.rmtree(dest,ignore_errors=True); await update.effective_message.reply_text('❌ No runnable entry in clone.'); return
    log=dest/'runtime.log'; install_project_dependencies(dest,entry,log) if v10_flags()['dependencies'] else None
    item=spawn_script(None,entry,dest,log); item.display_name=name; scripts_for(update.effective_user.id).append(item); save_projects(); record_deploy(item,'success','Cloned project'); await update.effective_message.reply_text('✅ Project cloned and started.')


async def notifications_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    prefs=project_notifications(update.effective_user.id)
    if len(context.args)>=2 and context.args[0].lower() in prefs and context.args[1].lower() in {"on","off"}:
        prefs[context.args[0].lower()]=context.args[1].lower()=="on"; save_v7_data()
    lines=[f"{'✅' if v else '❌'} {k.title()}" for k,v in prefs.items()]
    await update.effective_message.reply_text(premium_box("🔔 ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs",lines+["Use: <code>/notifications crash off</code>"]),parse_mode=ParseMode.HTML)

async def usage_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    uid=update.effective_user.id; st=get_stat(uid); exp=premium_expiry.get(str(uid),"—")
    await update.effective_message.reply_text(premium_box("👤 ᴍʏ ᴀᴄᴄᴏᴜɴᴛ",[f"Plan • <b>{esc(plan_name(uid))}</b>",f"Expiry • <code>{esc(exp)}</code>",f"Credits • <code>{get_credits(uid)}</code>",f"Storage • <code>{user_storage_mb(uid):.1f}/{storage_limit_mb(uid)} MB</code>",f"Uploads • <code>{st['uploads_today']}/{daily_limit(uid)}</code>",f"Running • <code>{active_count(uid)}/{running_limit(uid)}</code>"]),parse_mode=ParseMode.HTML)

async def compareplans_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    rows=[]
    for name,p in plan_catalog().items(): rows.append(f"💎 <b>{name.title()}</b> • Projects <code>{p['projects']}</code> • Storage <code>{p['storage']}MB</code> • Backup <code>{'Yes' if p['backups'] else 'No'}</code>")
    await update.effective_message.reply_text(premium_box("💎 ᴘʟᴀɴ ᴄᴏᴍᴘᴀʀɪsᴏɴ",rows),parse_mode=ParseMode.HTML)

async def expiry_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    uid=update.effective_user.id; await update.effective_message.reply_text(f"Plan: <b>{esc(plan_name(uid))}</b>\nExpiry: <code>{esc(premium_expiry.get(str(uid),'No expiry set'))}</code>",parse_mode=ParseMode.HTML)

async def planbuilder_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    if len(context.args)<4: await update.effective_message.reply_text("Usage: /planbuilder PLAN PROJECTS STORAGE_MB backups:on|off"); return
    name=context.args[0].lower()
    try: projects=int(context.args[1]); storage=int(context.args[2])
    except ValueError: await update.effective_message.reply_text("❌ PROJECTS/STORAGE must be numbers."); return
    backups=context.args[3].split(':')[-1].lower()=="on"; plan_catalog()[name]={"projects":projects,"storage":storage,"backups":backups,"autorestart":True,"priority":name in {'premium','business','lifetime'}}; save_v7_data(); await update.effective_message.reply_text("✅ Plan definition updated.")

async def ticket_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not context.args: await update.effective_message.reply_text("Usage: /ticket Describe your issue"); return
    tickets=global_cfg().setdefault("tickets",[]); tid=(max([int(x.get('id',0)) for x in tickets] or [0])+1); u=update.effective_user
    row={"id":tid,"user_id":u.id,"username":u.username or "","text":" ".join(context.args)[:1500],"status":"open","time":datetime.now().isoformat(timespec="seconds")}; tickets.append(row); save_v7_data()
    await context.bot.send_message(OWNER_ID,premium_box("🎫 ɴᴇᴡ sᴜᴘᴘᴏʀᴛ ᴛɪᴄᴋᴇᴛ",[f"ID • <code>#{tid}</code>",f"User • <code>{u.id}</code>",f"Issue • {esc(row['text'])}"]),parse_mode=ParseMode.HTML)
    await update.effective_message.reply_text(f"✅ Ticket #{tid} created.")

async def tickets_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    tickets=global_cfg().setdefault("tickets",[]); uid=update.effective_user.id
    rows=tickets if admin_or_owner(update) else [x for x in tickets if int(x.get('user_id',0))==uid]
    lines=[f"#{x['id']} • <b>{esc(x['status'])}</b> • <code>{x['user_id']}</code> • {esc(x['text'])[:70]}" for x in rows[-30:][::-1]]
    await update.effective_message.reply_text(premium_box("🎫 sᴜᴘᴘᴏʀᴛ ᴛɪᴄᴋᴇᴛs",lines or ["No tickets."]),parse_mode=ParseMode.HTML)

async def closeticket_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not admin_or_owner(update) or not context.args or not context.args[0].isdigit(): return
    tid=int(context.args[0]); tickets=global_cfg().setdefault("tickets",[])
    for x in tickets:
        if int(x.get('id',0))==tid: x['status']='closed'; save_v7_data(); await update.effective_message.reply_text("✅ Ticket closed."); return
    await update.effective_message.reply_text("❌ Ticket not found.")

async def emergency_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    cfg=global_cfg()
    if len(context.args)>=2:
        key=context.args[0].lower(); val=context.args[1].lower()=="on"
        mapping={"deployments":"deployments_enabled","dependencies":"dependencies_enabled","queue":"queue_mode","readonly":"readonly_mode"}
        if key in mapping: cfg[mapping[key]]=val; save_v7_data()
    f=v10_flags(); await update.effective_message.reply_text(premium_box("🚨 ᴇᴍᴇʀɢᴇɴᴄʏ ᴄᴏɴᴛʀᴏʟ",[f"Deployments • <code>{'ON' if f['deployments'] else 'PAUSED'}</code>",f"Dependencies • <code>{'ON' if f['dependencies'] else 'OFF'}</code>",f"Queue Mode • <code>{'ON' if f['queue'] else 'OFF'}</code>",f"Read Only • <code>{'ON' if f['readonly'] else 'OFF'}</code>","Use: <code>/emergency deployments off</code>"]),parse_mode=ParseMode.HTML)

async def restartcrashed_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    n=0
    for items in running_scripts.values():
        for item in items:
            if not item.running:
                try: spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path)); n+=1
                except Exception: pass
    await update.effective_message.reply_text(f"♻️ Restarted {n} offline projects.")

async def referral_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    me=await context.bot.get_me(); uid=update.effective_user.id
    refs=global_cfg().setdefault("referrals",{}); count=len(refs.get(str(uid),[]))
    await update.effective_message.reply_text(premium_box("🎁 ʀᴇғᴇʀʀᴀʟ",[f"Link • <code>https://t.me/{esc(me.username)}?start=ref_{uid}</code>",f"Successful • <code>{count}</code>","Reward • <code>1 credit</code> per new user"]),parse_mode=ParseMode.HTML)

async def v10_callback(update:Update,context:ContextTypes.DEFAULT_TYPE)->bool:
    q=update.callback_query; data=q.data or ""; uid=q.from_user.id
    if not data.startswith("v10:"): return False
    parts=data.split(":"); action=parts[1]; idx=int(parts[2]) if len(parts)>2 and parts[2].isdigit() else -1
    items=scripts_for(uid)
    if idx<0 or idx>=len(items): await q.answer("Project not found",show_alert=True); return True
    item=items[idx]
    if action=="center": await edit_message(q,project_center_text(item),project_center_buttons(idx,item))
    elif action=="health": await edit_message(q,project_center_text(item),project_center_buttons(idx,item))
    elif action=="clearlog":
        Path(item.log_path).write_text("",encoding="utf-8"); await q.answer("Log cleared"); await edit_message(q,project_center_text(item),project_center_buttons(idx,item))
    elif action=="packages":
        info="requirements.txt" if next(iter(Path(item.folder).rglob('requirements.txt')),None) else ("package.json" if next(iter(Path(item.folder).rglob('package.json')),None) else "No manifest")
        await edit_message(q,premium_box("📦 ᴘᴀᴄᴋᴀɢᴇs",[f"Runtime • <code>{esc(item.runtime)}</code>",f"Manifest • <code>{esc(info)}</code>"]),project_center_buttons(idx,item))
    elif action=="env":
        envs=project_envs.get(project_key(item),{}); rows=[f"• <code>{esc(k)}</code> = <code>••••••</code>" for k in envs] or ["No environment variables."]
        await edit_message(q,premium_box("🔐 sᴇᴄʀᴇᴛs",rows+["Use <code>/setenv PROJECT KEY VALUE</code>"]),project_center_buttons(idx,item))
    elif action=="backup":
        path=await asyncio.to_thread(create_project_backup_file,uid,item); await send_real_file(context.bot,uid,path,f"💾 {item.display_name} backup"); await q.answer("Backup sent")
    elif action=="history":
        rows=deployment_history(item); lines=[f"• <b>{esc(x.get('status',''))}</b> {esc(x.get('commit',''))} — {esc(x.get('time',''))}" for x in rows[-10:][::-1]]
        await edit_message(q,premium_box("📜 ᴅᴇᴘʟᴏʏs",lines or ["No history."]),project_center_buttons(idx,item))
    elif action=="rollback":
        snaps=sorted((Path(item.folder)/'.QURESHIxOTP_history').glob('*.zip'),reverse=True) if (Path(item.folder)/'.QURESHIxOTP_history').exists() else []
        if not snaps: await q.answer("No rollback snapshot",show_alert=True)
        else: await asyncio.to_thread(restore_snapshot,item,snaps[0].name); await q.answer("Rolled back latest snapshot"); await edit_message(q,project_center_text(item),project_center_buttons(idx,item))
    elif action=="github":
        await edit_message(q,premium_box("🐙 ɢɪᴛʜᴜʙ",[f"Connected • <code>{'YES' if item.source_type=='github' else 'NO'}</code>",f"Repo • <code>{esc(item.repo_url or '—')}</code>",f"Branch • <code>{esc(item.branch)}</code>",f"Commit • <code>{esc(item.commit_sha[:10] or '—')}</code>",f"Token • <code>{'REMEMBERED' if github_token_for(uid) else 'NOT SET'}</code>",f"Auto Deploy • <code>{'ON' if project_settings.get(project_key(item),{}).get('github_autodeploy') else 'OFF'}</code>",f"Method • <code>{esc(project_settings.get(project_key(item),{}).get('github_method','Auto'))}</code>"]),github_project_buttons(idx,item) if item.source_type=='github' else project_center_buttons(idx,item))
    elif action=="notify": await edit_message(q,premium_box("🔔 ɴᴏᴛɪғʏ",[f"Crash • <code>{project_notifications(uid)['crash']}</code>",f"Deploy • <code>{project_notifications(uid)['deploy']}</code>","Use /notifications to change preferences."]),project_center_buttons(idx,item))
    elif action=="settings": await edit_message(q,premium_box("⚙️ sᴇᴛᴛɪɴɢs",[f"Auto Restart • <code>{item.auto_restart}</code>",f"Auto Start • <code>{project_settings.get(project_key(item),{}).get('autostart',False)}</code>",f"Auto Deploy • <code>{project_settings.get(project_key(item),{}).get('github_autodeploy',False)}</code>"]),project_center_buttons(idx,item))
    return True

def create_project_backup_file(uid:int,item:ScriptProcess)->Path:
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); out=PROJECT_BACKUPS_DIR/f"{uid}_{clean_project_name(item.display_name)}_{stamp}.zip"
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        root=Path(item.folder)
        for f in root.rglob('*'):
            if f.is_file() and '.venv' not in f.parts and 'node_modules' not in f.parts and '.git' not in f.parts: z.write(f,f.relative_to(root))
    return out


async def replaceproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text("Usage: /replaceproject PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    idx,item=found; global_cfg().setdefault("pending_replace",{})[str(update.effective_user.id)]=idx; save_v7_data()
    await update.effective_message.reply_text(f"📤 Send the replacement project file now for <b>{esc(item.display_name)}</b>. A rollback snapshot will be created first.",parse_mode=ParseMode.HTML)

async def repostatus_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text("Usage: /repostatus PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; cfg=project_settings.get(project_key(item),{})
    await update.effective_message.reply_text(premium_box("🐙 ʀᴇᴘᴏ sᴛᴀᴛᴜs",[f"Project • <b>{esc(item.display_name)}</b>",f"Connected • <code>{item.source_type=='github'}</code>",f"Repo • <code>{esc(item.repo_url or '—')}</code>",f"Branch • <code>{esc(item.branch)}</code>",f"Commit • <code>{esc(item.commit_sha[:10] or '—')}</code>",f"Method • <code>{esc(project_settings.get(project_key(item),{}).get('github_method','Auto'))}</code>",f"Auto Deploy • <code>{cfg.get('github_autodeploy',False)}</code>"]),parse_mode=ParseMode.HTML)

async def disconnectrepo_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text("Usage: /disconnectrepo PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; item.source_type='upload'; item.repo_url=''; item.commit_sha=''; project_settings.get(project_key(item),{}).pop('github_autodeploy',None); save_projects(); save_v7_data(); await update.effective_message.reply_text("✅ GitHub disconnected; project files remain hosted.")

async def setbranch_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /setbranch PROJECT NAME | BRANCH'); return
    found=find_project(update.effective_user.id,f[0]); branch=f[1]
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked.'); return
    if item.source_type!='github': await update.effective_message.reply_text('❌ Not a GitHub project.'); return
    item.branch=branch; save_projects(); await update.effective_message.reply_text(f'✅ Branch set to <code>{esc(branch)}</code>. Use /syncrepo to deploy it.',parse_mode=ParseMode.HTML)


async def redeploy_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text("Usage: /redeploy PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; msg=await update.effective_message.reply_text("♻️ Redeploying…")
    try:
        if item.source_type=='github': await asyncio.to_thread(sync_github_item,item)
        else:
            snapshot_project(item,'pre_redeploy');
            if item.running: kill_process(item)
            entry=Path(item.entry_file); install_project_dependencies(Path(item.folder),entry,Path(item.log_path)) if v10_flags()['dependencies'] else None; spawn_script(item,entry,Path(item.folder),Path(item.log_path)); mark_last_good(item); record_deploy(item,'success','Manual redeploy')
        await msg.edit_text("✅ Redeploy complete.")
    except Exception as e: record_deploy(item,'failed',str(e)); await msg.edit_text(f"❌ Redeploy failed: {e}")

async def setentry_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /setentry PROJECT NAME | RELATIVE_FILE.py"); return
    found=find_project(update.effective_user.id,f[0]); rel=f[1]
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked by admin.'); return
    root=Path(item.folder); target=(root/rel).resolve()
    try: target.relative_to(root.resolve())
    except ValueError: await update.effective_message.reply_text("❌ Unsafe path."); return
    if not target.exists() or target.suffix.lower() not in {'.py','.js','.mjs','.cjs','.php','.sh','.rb','.jar'}: await update.effective_message.reply_text("❌ Entry must be an existing supported runtime file."); return
    ok,why=syntax_test_entry(target)
    if not ok: await update.effective_message.reply_text(f'❌ Entry validation failed: {why}'); return
    was=item.running
    if was: kill_process(item)
    item.entry_file=str(target); item.runtime=runtime_for_entry(target); save_projects()
    if was: spawn_script(item,target,root,Path(item.log_path))
    await update.effective_message.reply_text(f"✅ Startup entry changed to <code>{esc(rel)}</code>.",parse_mode=ParseMode.HTML)


async def setplan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if len(context.args) < 3:
        await update.effective_message.reply_text("Usage: /setplan USER_ID free|basic|premium|business|lifetime 30d|lifetime")
        return
    try: uid = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Invalid user ID"); return
    plan, duration = context.args[1].lower(), context.args[2].lower()
    if plan not in {"free","basic","premium","business","lifetime"}:
        await update.effective_message.reply_text("Invalid plan"); return
    if plan == "free":
        premium_users.discard(uid); premium_expiry.pop(str(uid), None)
    else:
        premium_users.add(uid)
        if duration == "lifetime" or plan == "lifetime": premium_expiry[str(uid)] = "lifetime"
        else:
            delta = parse_duration(duration)
            if not delta: await update.effective_message.reply_text("Duration example: 30d"); return
            premium_expiry[str(uid)] = (datetime.now()+delta).isoformat(timespec="seconds")
    user_plans[str(uid)] = plan
    save_data(); save_v7_data(); audit(update.effective_user.id, "setplan", str(uid), f"{plan} {duration}")
    await update.effective_message.reply_text(premium_box("✅ ᴘʟᴀɴ ᴜᴘᴅᴀᴛᴇᴅ", [f"User: <code>{uid}</code>", f"Plan: <b>{esc(plan.title())}</b>", f"Duration: <code>{esc(duration)}</code>"]), parse_mode=ParseMode.HTML)


async def createcode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if len(context.args) < 4:
        await update.effective_message.reply_text("Usage: /createcode CODE plan|credits VALUE MAX_USES [expiry:30d]"); return
    code=context.args[0].upper(); kind=context.args[1].lower(); value=context.args[2]
    try: max_uses=int(context.args[3])
    except ValueError: await update.effective_message.reply_text("MAX_USES must be number"); return
    expiry=""
    if len(context.args)>4:
        d=parse_duration(context.args[4]); expiry=(datetime.now()+d).isoformat(timespec="seconds") if d else ""
    redeem_codes[code]={"kind":kind,"value":value,"max_uses":max_uses,"used_by":[],"expiry":expiry,"created_by":update.effective_user.id}
    save_v7_data(); audit(update.effective_user.id,"createcode",code,f"{kind}:{value}")
    await update.effective_message.reply_text(f"✅ Redeem code created: <code>{esc(code)}</code>",parse_mode=ParseMode.HTML)


async def redeem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.effective_message.reply_text("Usage: /redeem CODE"); return
    uid=update.effective_user.id; code=context.args[0].upper(); row=redeem_codes.get(code)
    if row and row.get("disabled"):
        await update.effective_message.reply_text("❌ This redeem code is disabled."); return
    if not row: await update.effective_message.reply_text("❌ Invalid code"); return
    if uid in row.get("used_by",[]): await update.effective_message.reply_text("❌ You already used this code"); return
    if len(row.get("used_by",[])) >= int(row.get("max_uses",0)): await update.effective_message.reply_text("❌ Code usage limit reached"); return
    if row.get("expiry") and datetime.fromisoformat(row["expiry"]) <= datetime.now(): await update.effective_message.reply_text("❌ Code expired"); return
    if row.get("kind") == "credits": set_credits(uid,get_credits(uid)+int(row["value"]))
    elif row.get("kind") == "plan":
        plan=row["value"].lower(); premium_users.add(uid); user_plans[str(uid)]=plan; premium_expiry[str(uid)]=(datetime.now()+timedelta(days=30)).isoformat(timespec="seconds"); save_data()
    else: await update.effective_message.reply_text("❌ Invalid code configuration"); return
    row.setdefault("used_by",[]).append(uid); save_v7_data(); audit(uid,"redeem",code,str(row.get("value")))
    await update.effective_message.reply_text("✅ Code redeemed successfully")


async def setenv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context): return
    f=pipe_fields(update)
    if len(f)>=3: project,key,value=f[0],f[1]," | ".join(f[2:])
    elif len(context.args)>=3: project,key,value=context.args[0],context.args[1]," ".join(context.args[2:])
    else: await update.effective_message.reply_text("Usage: /setenv PROJECT | KEY | VALUE"); return
    found=find_project(update.effective_user.id,project)
    if not found: await update.effective_message.reply_text("Project not found"); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text("🔒 Project is locked by admin."); return
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,80}",key): await update.effective_message.reply_text("Invalid variable name"); return
    project_envs.setdefault(project_key(item),{})[key]=value; project_settings.setdefault(project_key(item),{}).setdefault("env",{})[key]=value
    save_v7_data(); _rewrite_generated_env(item); ready,missing=ensure_project_env_ready(item,Path(item.folder))
    await update.effective_message.reply_text(f"✅ <code>{esc(key)}</code> saved and masked.\n"+("✅ ENV ready." if ready else "⚠️ Missing: "+", ".join(esc(x) for x in missing)),parse_mode=ParseMode.HTML)

async def env_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context): return
    project=command_payload(update)
    if not project: await update.effective_message.reply_text("Usage: /env PROJECT NAME"); return
    found=find_project(update.effective_user.id,project)
    if not found: await update.effective_message.reply_text("Project not found"); return
    _,item=found; envs=_active_project_env(item,Path(item.folder)); _,missing=required_env_summary(item)
    lines=[f"<code>{esc(k)}</code> = ••••••••" for k in sorted(envs)] or ["No variables configured"]
    if missing: lines += ["", "Missing required:"]+[f"• <code>{esc(x)}</code>" for x in missing]
    await update.effective_message.reply_text(premium_box("🔐 ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ",lines),parse_mode=ParseMode.HTML)

async def delenv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /delenv PROJECT | KEY"); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text("Project not found"); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text("🔒 Project is locked by admin."); return
    project_envs.get(project_key(item),{}).pop(f[1],None); project_settings.setdefault(project_key(item),{}).setdefault('env',{}).pop(f[1],None); save_v7_data(); _rewrite_generated_env(item); ensure_project_env_ready(item,Path(item.folder)); await update.effective_message.reply_text("✅ Variable removed. ENV Guard rechecked the project.")

async def autorestart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /autorestart PROJECT | on|off"); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text("Project not found"); return
    _,item=found; item.auto_restart=f[1].lower() in {"on","yes","1"}; item.restarts=0; save_projects(); await update.effective_message.reply_text(f"♻️ Auto restart: {'ON' if item.auto_restart else 'OFF'}")

async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context): return
    project=command_payload(update)
    if not project: await update.effective_message.reply_text("Usage: /health PROJECT NAME"); return
    found=find_project(update.effective_user.id,project)
    if not found: await update.effective_message.reply_text("Project not found"); return
    _,item=found; r=project_resources(item); ram_limit=project_settings.get(project_key(item),{}).get("ram_mb",plan_limits(update.effective_user.id)[2]); _,missing=required_env_summary(item)
    lines=[f"Project: <b>{esc(item.display_name)}</b>",f"Status: {'🟢 Online' if item.running else '🔴 Offline'}",f"PID: <code>{item.pid}</code>",f"CPU: <code>{r['cpu']}</code>",f"RAM: <code>{r['ram']} / {ram_limit} MB</code>",f"Disk: <code>{r['disk']}</code>",f"Uptime: <code>{uptime(item.started_at) if item.running else '—'}</code>",f"Restarts: <code>{item.restarts}</code>",f"ENV Missing: <code>{len(missing)}</code>",f"Lock: <code>{'ON' if project_locked(item) else 'OFF'}</code>"]
    await update.effective_message.reply_text(premium_box("📊 ᴘʀᴏᴊᴇᴄᴛ ʜᴇᴀʟᴛʜ",lines),parse_mode=ParseMode.HTML)


async def auditlog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    rows=audit_log[-30:]; text="\n".join(f"{x['time']} | {x['actor']} | {x['action']} | {x['target']} | {x['detail']}" for x in rows) or "No audit entries"
    await update.effective_message.reply_text(f"<pre>{esc(text[-3800:])}</pre>",parse_mode=ParseMode.HTML)


async def plans_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid=update.effective_user.id; exp=premium_expiry.get(str(uid),"—")
    lines=[f"Current: <b>{esc(plan_name(uid))}</b>",f"Expiry: <code>{esc(exp)}</code>","Free: 1 daily / 1-2 running / 128 MB","Basic: 5 daily / 3 running / 256 MB","Premium: 25 daily / 10 running / 512 MB","Business: 100 daily / 30 running / 1024 MB"]
    await update.effective_message.reply_text(premium_box("💎 ᴘʟᴀɴs",lines),parse_mode=ParseMode.HTML)



class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] not in {"/", "/health"}:
            self.send_response(404); self.end_headers(); return
        body = json.dumps({
            "service": BRAND_NAME,
            "status": "online",
            "runtime": "multi-runtime",
            "uptime": uptime(),
            "projects": sum(len(v) for v in running_scripts.values()),
            "active": sum(i.running for v in running_scripts.values() for i in v),
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def start_health_server() -> None:
    global health_server_started
    try:
        server = ThreadingHTTPServer(("0.0.0.0", HEALTH_PORT), _HealthHandler)
        health_server_started = True
        threading.Thread(target=server.serve_forever, daemon=True, name="QURESHIxOTP-health").start()
        logger.info("Health server listening on 0.0.0.0:%s", HEALTH_PORT)
    except OSError as exc:
        health_server_started = False
        logger.warning("Health server could not start on port %s: %s", HEALTH_PORT, exc)


def _ping_keepalive(url: str) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QURESHIxOTP-Host-KeepAlive/8.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


async def keepalive_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global keepalive_last_status, keepalive_last_at, keepalive_failures, keepalive_last_epoch
    if not keepalive_enabled or not keepalive_url:
        return
    now = time.time()
    if keepalive_last_epoch and now - keepalive_last_epoch < keepalive_interval:
        return
    keepalive_last_epoch = now
    ok, detail = await asyncio.to_thread(_ping_keepalive, keepalive_url)
    keepalive_last_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    keepalive_last_status = detail
    if ok:
        keepalive_failures = 0
    else:
        keepalive_failures += 1
        logger.warning("Keep-alive ping failed (%s): %s", keepalive_failures, detail)
        if keepalive_failures in {3, 10}:
            try:
                await context.bot.send_message(OWNER_ID, premium_box("⚠️ ᴋᴇᴇᴘ-ᴀʟɪᴠᴇ ᴡᴀʀɴɪɴɢ", [f"Failures: <code>{keepalive_failures}</code>", f"Status: <code>{esc(detail)}</code>", f"URL: <code>{esc(keepalive_url)}</code>"]), parse_mode=ParseMode.HTML)
            except TelegramError:
                pass


def keepalive_text() -> str:
    return premium_box("💓 ᴋᴇᴇᴘ ᴀʟɪᴠᴇ", [
        f"Status: <code>{'ON' if keepalive_enabled else 'OFF'}</code>",
        f"Interval: <code>{keepalive_interval}s</code>",
        f"URL: <code>{esc(keepalive_url or 'Not configured')}</code>",
        f"Last Ping: <code>{esc(keepalive_last_at)}</code>",
        f"Last Result: <code>{esc(keepalive_last_status)}</code>",
        f"Failures: <code>{keepalive_failures}</code>",
        f"Health Server: <code>{'ONLINE' if health_server_started else 'UNAVAILABLE'}</code> : <code>{HEALTH_PORT}</code>",
        "Use <code>/setkeepalive https://your-domain/health 40</code>",
    ])


async def keepalive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global keepalive_enabled
    if not owner_only(update): return
    if context.args:
        mode = context.args[0].lower()
        if mode in {"on", "off"}:
            keepalive_enabled = mode == "on"; save_v7_data(); audit(update.effective_user.id, "keepalive", detail=mode)
    await update.effective_message.reply_text(keepalive_text(), parse_mode=ParseMode.HTML)


async def setkeepalive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global keepalive_url, keepalive_interval, keepalive_enabled
    if not owner_only(update): return
    if not context.args:
        await update.effective_message.reply_text("Usage: /setkeepalive URL [30-45] | /setkeepalive off"); return
    if context.args[0].lower() == "off":
        keepalive_enabled = False; save_v7_data(); await update.effective_message.reply_text("💤 Keep-alive disabled."); return
    url = context.args[0].strip()
    if not url.startswith(("http://", "https://")):
        await update.effective_message.reply_text("❌ URL must start with http:// or https://"); return
    interval = keepalive_interval
    if len(context.args) > 1:
        try: interval = max(30, min(45, int(context.args[1])))
        except ValueError: await update.effective_message.reply_text("❌ Interval must be 30-45 seconds."); return
    keepalive_url = url; keepalive_interval = interval; keepalive_enabled = True; save_v7_data()
    audit(update.effective_user.id, "set_keepalive", detail=f"{url} @ {interval}s")
    await update.effective_message.reply_text(keepalive_text(), parse_mode=ParseMode.HTML)


def host_stats_text() -> str:
    all_items=[i for items in running_scripts.values() for i in items]
    active=sum(i.running for i in all_items)
    disk="N/A"; ram="N/A"; cpu="N/A"
    try:
        total, used, free=shutil.disk_usage(BASE_DIR); disk=f"{used/1024**3:.2f}/{total/1024**3:.2f} GB"
    except OSError: pass
    try:
        import psutil
        ram=f"{psutil.virtual_memory().percent:.1f}%"; cpu=f"{psutil.cpu_percent(interval=0.1):.1f}%"
    except Exception: pass
    return premium_box("🖥 ʜᴏsᴛ sᴛᴀᴛᴜs", [
        f"Python: <code>{platform.python_version()}</code>", f"OS: <code>{esc(platform.system())} {esc(platform.release())}</code>",
        f"CPU: <code>{cpu}</code>", f"RAM: <code>{ram}</code>", f"Disk: <code>{disk}</code>",
        f"Projects: <code>{len(all_items)}</code>", f"Running: <code>{active}</code>", f"Users: <code>{len(user_stats)}</code>",
        f"Keep Alive: <code>{'ON' if keepalive_enabled else 'OFF'} / {keepalive_interval}s</code>", f"Uptime: <code>{uptime()}</code>",
    ])


async def hoststats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    await update.effective_message.reply_text(host_stats_text(), parse_mode=ParseMode.HTML)


def security_text() -> str:
    return premium_box("🛡 sᴇᴄᴜʀɪᴛʏ & ʀᴜɴᴛɪᴍᴇ", [
        "Runtime: <code>PYTHON ONLY</code>", f"Security Scan: <code>{'ON' if SECURITY_SCAN_ENABLED else 'OFF'}</code>",
        f"Auto Dependencies: <code>{'ON' if AUTO_INSTALL_DEPENDENCIES else 'OFF'}</code>", f"Docker Mode: <code>{'ON' if DOCKER_MODE else 'OFF'}</code>",
        f"Resource Limits: <code>{'ON' if ENFORCE_RESOURCE_LIMITS else 'OFF'}</code>", f"Process Limit: <code>{PROJECT_PROCESS_LIMIT or 'disabled'}</code>",
        f"Open Files: <code>{PROJECT_OPEN_FILES_LIMIT}</code>", f"Max Upload: <code>{MAX_FILE_MB} MB</code>", f"Max ZIP Expanded: <code>{MAX_ZIP_EXPANDED_MB} MB</code>",
    ])


async def security_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    await update.effective_message.reply_text(security_text(), parse_mode=ParseMode.HTML)


async def finduser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if not context.args: await update.effective_message.reply_text("Usage: /finduser USER_ID|username|name"); return
    q=" ".join(context.args).lstrip("@").casefold(); rows=[]
    for uid, st in user_stats.items():
        hay=f"{uid} {st.get('username','')} {st.get('first_name','')}".casefold()
        if q in hay:
            rows.append(f"• <code>{uid}</code> @{esc(st.get('username') or 'not_set')} — {esc(st.get('first_name') or 'Unknown')} — {esc(plan_name(int(uid)))}")
    await update.effective_message.reply_text(premium_box("🔎 ᴜsᴇʀ sᴇᴀʀᴄʜ", rows[:30] or ["No matching user found."]), parse_mode=ParseMode.HTML)


async def allprojects_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    rows=[]
    for uid, items in sorted(running_scripts.items()):
        for i in items:
            rows.append(f"• <code>{uid}</code> | <b>{esc(i.display_name)}</b> | {'🟢' if i.running else '🔴'} | <code>{Path(i.entry_file).name}</code>")
    await update.effective_message.reply_text(premium_box("📂 ᴀʟʟ ᴘʀᴏᴊᴇᴄᴛs", rows[:70] or ["No projects registered."]), parse_mode=ParseMode.HTML)


async def restartall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    restarted=failed=0
    for items in running_scripts.values():
        for item in items:
            try:
                if item.running: kill_process(item)
                spawn_script(item, Path(item.entry_file), Path(item.folder), Path(item.log_path)); restarted += 1
            except Exception:
                failed += 1; logger.exception("Restart-all failure")
    save_projects(); audit(update.effective_user.id, "restart_all", detail=f"ok={restarted}, failed={failed}")
    await update.effective_message.reply_text(premium_box("♻️ ʀᴇsᴛᴀʀᴛ ᴀʟʟ", [f"Restarted: <code>{restarted}</code>", f"Failed: <code>{failed}</code>"]), parse_mode=ParseMode.HTML)



async def watchdog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global watchdog_enabled
    if not owner_only(update): return
    if context.args:
        v=context.args[0].lower()
        if v in ("on","off"):
            watchdog_enabled = v == "on"; save_v7_data(); audit(update.effective_user.id,"watchdog",detail=v)
    await update.effective_message.reply_text(premium_box("🛡 ᴡᴀᴛᴄʜᴅᴏɢ", [
        f"Status: <code>{'ON' if watchdog_enabled else 'OFF'}</code>",
        f"Interval: <code>{watchdog_interval}s</code>", f"Crash window: <code>{CRASH_WINDOW_SECONDS}s</code>",
        f"Crash limit: <code>{CRASH_LIMIT}</code>", f"Auto restarts: <code>{watchdog_restarts}</code>"
    ]), parse_mode=ParseMode.HTML)

async def setwatchdog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global watchdog_interval
    if not owner_only(update): return
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /setwatchdog SECONDS (minimum 20)"); return
    watchdog_interval=max(20,int(context.args[0])); save_v7_data(); audit(update.effective_user.id,"set_watchdog",detail=str(watchdog_interval))
    await update.effective_message.reply_text(f"✅ Watchdog interval set to {watchdog_interval}s")

async def watchdogstatus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await watchdog_cmd(update, context)

async def schedulerestart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if len(context.args) < 2:
        await update.effective_message.reply_text("Usage: /schedulerestart PROJECT 6h|30m|1d"); return
    found=find_project(update.effective_user.id, " ".join(context.args[:-1]))
    dur=parse_duration(context.args[-1])
    if not found or not dur:
        await update.effective_message.reply_text("❌ Project/duration invalid. Example: /schedulerestart MyBot 6h"); return
    _,item=found; sec=max(300,int(dur.total_seconds())); st=project_setting(item); st["restart_schedule_seconds"]=sec; st["next_restart_at"]=time.time()+sec
    save_v7_data(); audit(update.effective_user.id,"schedule_restart",item.display_name,str(sec))
    await update.effective_message.reply_text(f"✅ {item.display_name} scheduled every {human_duration(sec)}.")

async def scheduleremove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /scheduleremove PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; st=project_setting(item); st.pop("restart_schedule_seconds",None); st.pop("next_restart_at",None); save_v7_data()
    await update.effective_message.reply_text("✅ Scheduled restart removed.")

async def autostart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if len(context.args)<2 or context.args[-1].lower() not in ("on","off"):
        await update.effective_message.reply_text("Usage: /autostart PROJECT on|off"); return
    found=find_project(update.effective_user.id," ".join(context.args[:-1]))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; project_setting(item)["autostart"]=context.args[-1].lower()=="on"; save_v7_data()
    await update.effective_message.reply_text(f"✅ Auto-start {'enabled' if project_setting(item)['autostart'] else 'disabled'} for {item.display_name}.")

async def projectbackup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /projectbackup PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; folder=Path(item.folder); stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    out=PROJECT_BACKUPS_DIR/f"{update.effective_user.id}_{clean_project_name(item.display_name)}_{stamp}.zip"
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for f in folder.rglob("*"):
            if not f.is_file() or ".venv" in f.parts or f.name=="runtime.log": continue
            z.write(f, f.relative_to(folder))
    await send_real_file(context.bot, update.effective_chat.id, out, f"💾 Project backup: {item.display_name}")

async def backups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    rows=sorted(BACKUPS_DIR.glob("QURESHIxOTP_backup_*.zip"),key=lambda x:x.stat().st_mtime,reverse=True)[:10]
    await update.effective_message.reply_text(premium_box("💾 ʙᴀᴄᴋᴜᴘs", [f"• <code>{esc(x.name)}</code>" for x in rows] or ["No backups yet."]),parse_mode=ParseMode.HTML)

async def restorebackup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if len(context.args) != 2 or context.args[1] != "CONFIRM":
        await update.effective_message.reply_text("Usage: /restorebackup FILENAME.zip CONFIRM\nUse /backups to list available backups."); return
    name=Path(context.args[0]).name; src=BACKUPS_DIR/name
    if not src.exists() or not name.startswith("QURESHIxOTP_backup_"):
        await update.effective_message.reply_text("❌ Backup not found."); return
    allowed={DATA_FILE.name,PROJECTS_FILE.name,V7_DATA_FILE.name,V9_DB_FILE.name}
    with zipfile.ZipFile(src) as z:
        for member in z.infolist():
            if Path(member.filename).name in allowed and "/" not in member.filename.strip("/"):
                z.extract(member, BASE_DIR)
    audit(update.effective_user.id,"restore_backup",name)
    await update.effective_message.reply_text("✅ Backup files restored. Restart QURESHIxOTP Host to reload the restored state.")

async def repairenv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /repairenv PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; folder=Path(item.folder); req=next(iter(folder.rglob("requirements.txt")),None)
    if not req: await update.effective_message.reply_text("❌ requirements.txt not found."); return
    msg=await update.effective_message.reply_text("🔧 Rebuilding private Python environment…")
    venv=folder/".venv"
    try:
        if venv.exists(): shutil.rmtree(venv,ignore_errors=True)
        note=await asyncio.to_thread(install_project_dependencies,folder,Path(item.entry_file),Path(item.log_path))
        await msg.edit_text(f"✅ Environment repaired. {note}")
    except Exception as exc:
        await msg.edit_text(f"❌ Repair failed: {exc}")


async def logsize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /logsize PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args));
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; p=Path(item.log_path); size=(p.stat().st_size/(1024*1024)) if p.exists() else 0
    await update.effective_message.reply_text(f"🧾 {item.display_name} log size: {size:.2f} MB")

async def clearlogs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /clearlogs PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args));
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; Path(item.log_path).write_text("",encoding="utf-8"); await update.effective_message.reply_text("✅ Runtime log cleared.")

async def diagnose_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /diagnose PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args));
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; p=Path(item.log_path); text=p.read_text("utf-8",errors="replace")[-12000:] if p.exists() else ""
    await update.effective_message.reply_text(premium_box("🩺 ᴅɪᴀɢɴᴏsᴛɪᴄs", [f"Project: <b>{esc(item.display_name)}</b>"]+[f"• {esc(x)}" for x in diagnose_log_text(text)]),parse_mode=ParseMode.HTML)

async def storage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid=update.effective_user.id; used=user_storage_mb(uid); limit=storage_limit_mb(uid)
    await update.effective_message.reply_text(premium_box("💾 sᴛᴏʀᴀɢᴇ", [f"Used: <code>{used:.1f} MB</code>",f"Quota: <code>{limit} MB</code>",f"Available: <code>{max(0,limit-used):.1f} MB</code>"]),parse_mode=ParseMode.HTML)

async def setstorage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if len(context.args)!=2 or not context.args[0].isdigit() or not context.args[1].isdigit():
        await update.effective_message.reply_text("Usage: /setstorage USER_ID MB"); return
    user_storage_limits[str(int(context.args[0]))]=max(50,int(context.args[1])); save_v7_data(); audit(update.effective_user.id,"set_storage",context.args[0],context.args[1])
    await update.effective_message.reply_text("✅ Storage quota updated.")

async def analytics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_or_owner(update): return
    total_projects=sum(len(x) for x in running_scripts.values()); running=sum(i.running for x in running_scripts.values() for i in x)
    total_storage=sum(user_storage_mb(uid) for uid in running_scripts)
    await update.effective_message.reply_text(premium_box("📈 ᴀɴᴀʟʏᴛɪᴄs", [
        f"Known users: <code>{len(user_stats)}</code>",f"Approved: <code>{len(approved_users)}</code>",f"Premium: <code>{len(premium_users)}</code>",
        f"Projects: <code>{total_projects}</code>",f"Running: <code>{running}</code>",f"Storage: <code>{total_storage:.1f} MB</code>",
        f"Redeem codes: <code>{len(redeem_codes)}</code>",f"Audit events: <code>{len(audit_log)}</code>"
    ]),parse_mode=ParseMode.HTML)

async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if len(context.args)!=2 or not context.args[0].isdigit() or context.args[1].lower() not in ("support","moderator","superadmin"):
        await update.effective_message.reply_text("Usage: /addadmin USER_ID support|moderator|superadmin"); return
    admin_roles[str(int(context.args[0]))]=context.args[1].lower(); save_v7_data(); audit(update.effective_user.id,"add_admin",context.args[0],context.args[1])
    await update.effective_message.reply_text("✅ Admin role added. Delegated roles can access read-only V10 admin views; owner-only destructive commands remain protected.")

async def deladmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if not context.args or not context.args[0].isdigit(): await update.effective_message.reply_text("Usage: /deladmin USER_ID"); return
    admin_roles.pop(str(int(context.args[0])),None); save_v7_data(); await update.effective_message.reply_text("✅ Admin role removed.")

async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_or_owner(update): return
    rows=[f"• <code>{uid}</code> — <b>{esc(role)}</b>" for uid,role in admin_roles.items()]
    await update.effective_message.reply_text(premium_box("👑 ᴀᴅᴍɪɴ ʀᴏʟᴇs", rows or ["No delegated admins."]),parse_mode=ParseMode.HTML)

async def codes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    rows=[]
    for code,row in list(redeem_codes.items())[:50]: rows.append(f"• <code>{esc(code)}</code> — {esc(str(row.get('kind')))}:{esc(str(row.get('value')))} — {'OFF' if row.get('disabled') else 'ON'} — {len(row.get('used_by',[]))}/{row.get('max_uses','∞')}")
    await update.effective_message.reply_text(premium_box("🎟 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇs",rows or ["No codes."]),parse_mode=ParseMode.HTML)

async def disablecode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if not context.args: await update.effective_message.reply_text("Usage: /disablecode CODE"); return
    code=context.args[0].upper(); row=redeem_codes.get(code)
    if not row: await update.effective_message.reply_text("❌ Code not found."); return
    row["disabled"]=not bool(row.get("disabled")); save_v7_data(); await update.effective_message.reply_text(f"✅ {code}: {'disabled' if row['disabled'] else 'enabled'}")

async def deletecode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if not context.args: await update.effective_message.reply_text("Usage: /deletecode CODE"); return
    code=context.args[0].upper(); existed=redeem_codes.pop(code,None); save_v7_data(); await update.effective_message.reply_text("✅ Code deleted." if existed else "❌ Code not found.")

async def codeinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    if not context.args: await update.effective_message.reply_text("Usage: /codeinfo CODE"); return
    code=context.args[0].upper(); row=redeem_codes.get(code)
    if not row: await update.effective_message.reply_text("❌ Code not found."); return
    await update.effective_message.reply_text(premium_box("🎟 ᴄᴏᴅᴇ ɪɴғᴏ",[f"Code: <code>{esc(code)}</code>",f"Kind: <code>{esc(str(row.get('kind')))}</code>",f"Value: <code>{esc(str(row.get('value')))}</code>",f"Used: <code>{len(row.get('used_by',[]))}</code>",f"Max: <code>{row.get('max_uses','∞')}</code>",f"Status: <code>{'Disabled' if row.get('disabled') else 'Active'}</code>"]),parse_mode=ParseMode.HTML)

async def forcejoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global FORCE_JOIN_ENABLED
    if not owner_only(update): return
    if context.args and context.args[0].lower() in ("on","off"):
        FORCE_JOIN_ENABLED=context.args[0].lower()=="on"; project_settings.setdefault("__global__",{})["force_join_enabled"]=FORCE_JOIN_ENABLED; save_v7_data()
    await update.effective_message.reply_text(f"🔐 Force Join: {'ON' if FORCE_JOIN_ENABLED else 'OFF'}")

async def setbrand_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global BRAND_NAME
    if not owner_only(update): return
    if not context.args: await update.effective_message.reply_text("Usage: /setbrand NAME"); return
    BRAND_NAME=" ".join(context.args)[:50]; project_settings.setdefault("__global__",{})["brand_name"]=BRAND_NAME; save_v7_data(); await update.effective_message.reply_text("✅ Brand name updated.")

async def setfooter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global brand_footer
    if not owner_only(update): return
    if not context.args: await update.effective_message.reply_text("Usage: /setfooter TEXT"); return
    brand_footer=" ".join(context.args)[:120]; save_v7_data(); await update.effective_message.reply_text("✅ Footer updated.")

async def panelreminder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global panel_reminder_enabled
    if not owner_only(update): return
    if context.args and context.args[0].lower() in ("on","off"):
        panel_reminder_enabled=context.args[0].lower()=="on"; save_v7_data()
    next_due=panel_last_confirmed_at + PANEL_REMINDER_HOURS*3600
    await update.effective_message.reply_text(premium_box("⏰ ᴘᴀɴᴇʟ ʀᴇᴍɪɴᴅᴇʀ",[f"Status: <code>{'ON' if panel_reminder_enabled else 'OFF'}</code>",f"Cycle: <code>{PANEL_REMINDER_HOURS}h</code>",f"Last confirmed: <code>{datetime.fromtimestamp(panel_last_confirmed_at).strftime('%Y-%m-%d %H:%M')}</code>",f"Next due: <code>{datetime.fromtimestamp(next_due).strftime('%Y-%m-%d %H:%M')}</code>","After visiting your panel, use <code>/panelvisited</code>."]),parse_mode=ParseMode.HTML)

async def panelvisited_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global panel_last_confirmed_at, panel_last_reminder_at
    if not owner_only(update): return
    panel_last_confirmed_at=time.time(); panel_last_reminder_at=0.0; save_v7_data(); audit(update.effective_user.id,"panel_visited")
    await update.effective_message.reply_text("✅ Panel visit marked. Next reminder is due in 3 days.")

async def piplist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /piplist PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args));
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; py=Path(item.folder)/".venv"/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    if not py.exists(): await update.effective_message.reply_text("❌ Private environment not found."); return
    r=await asyncio.to_thread(subprocess.run,[str(py),"-m","pip","list","--format=freeze"],capture_output=True,text=True,timeout=60)
    text=(r.stdout or r.stderr)[-3500:]; await update.effective_message.reply_text(f"<pre>{esc(text)}</pre>",parse_mode=ParseMode.HTML)

async def requirements_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /requirements PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args));
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; req=Path(item.folder)/"requirements.txt"
    if not req.exists(): await update.effective_message.reply_text("No requirements.txt found."); return
    await update.effective_message.reply_text(f"<pre>{esc(req.read_text('utf-8',errors='replace')[:3500])}</pre>",parse_mode=ParseMode.HTML)

async def checkcompat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_access(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /checkcompat PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args));
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; req=Path(item.folder)/"requirements.txt"; notes=[f"Host Python: <code>{sys.version.split()[0]}</code>"]
    if req.exists():
        txt=req.read_text("utf-8",errors="replace"); notes.append("requirements.txt: <code>Detected</code>")
        if sys.version_info >= (3,13) and re.search(r"python-telegram-bot\s*==\s*20\.",txt,re.I): notes.append("⚠️ PTB 20.x is not recommended on Python 3.13; compatibility rewrite will be used.")
    else: notes.append("requirements.txt: <code>Not found</code>")
    await update.effective_message.reply_text(premium_box("🧪 ᴄᴏᴍᴘᴀᴛɪʙɪʟɪᴛʏ",notes),parse_mode=ParseMode.HTML)


async def scheduled_backup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily real ZIP backup delivered as a Telegram document to the backup vault."""
    try:
        archive=await asyncio.to_thread(create_full_source_backup)
        old=sorted(BACKUPS_DIR.glob("QURESHIxOTP_full_source_backup_*.zip"),key=lambda x:x.stat().st_mtime,reverse=True)[7:]
        for f in old:
            f.unlink(missing_ok=True)
        await send_full_backup_to_vault(context,archive,"💾 ᴅᴀɪʟʏ ғᴜʟʟ ʙᴀᴄᴋᴜᴘ")
    except Exception:
        logger.exception("Automatic full backup delivery failed")


# ═════════════════════════════════════════════════════════════════════════════
# JOBS & ERRORS
# ═════════════════════════════════════════════════════════════════════════════

async def auto_restart_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    for uid, items in list(running_scripts.items()):
        async with lock_for(uid):
            for item in items:
                if (
                    not item.running
                    and item.auto_restart
                    and item.restarts < MAX_RESTARTS
                ):
                    try:
                        item.restarts += 1

                        spawn_script(
                            item,
                            Path(item.entry_file),
                            Path(item.folder),
                            Path(item.log_path),
                        )

                        await context.bot.send_message(
                            uid,
                            f"♻️ Auto-restarted "
                            f"{item.display_name}.",
                        )

                    except Exception:
                        logger.exception(
                            "Auto restart failed"
                        )



async def watchdog_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global watchdog_last_epoch, watchdog_restarts
    if not watchdog_enabled or time.time()-watchdog_last_epoch < watchdog_interval: return
    watchdog_last_epoch=time.time(); now=time.time()
    for uid,items in list(running_scripts.items()):
        async with lock_for(uid):
            for item in items:
                st=project_setting(item)
                if project_settings.get(project_key(item),{}).get("env_blocked"):
                    continue
                # scheduled restarts
                sec=int(st.get("restart_schedule_seconds",0) or 0); nxt=float(st.get("next_restart_at",0) or 0)
                if sec and nxt and now>=nxt:
                    try:
                        if item.running: kill_process(item)
                        spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path)); st["next_restart_at"]=now+sec; watchdog_restarts+=1
                    except Exception: logger.exception("Scheduled restart failed")
                if item.running: continue
                if not (item.auto_restart or st.get("autostart") or item.desired_running): continue
                crashes=[float(x) for x in st.get("crash_times",[]) if now-float(x)<=CRASH_WINDOW_SECONDS]
                crashes.append(now); st["crash_times"]=crashes[-20:]
                if len(crashes)>CRASH_LIMIT:
                    if not st.get("crash_alerted"):
                        st["crash_alerted"]=True
                        if project_notifications(uid).get("crash", True):
                            try: await context.bot.send_message(uid,f"🛑 {item.display_name} stopped by crash-loop protection ({len(crashes)} crashes in {human_duration(CRASH_WINDOW_SECONDS)}).")
                            except TelegramError: pass
                    continue
                try:
                    spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path)); watchdog_restarts+=1
                    if project_notifications(uid).get("restart", True):
                        try: await context.bot.send_message(uid, f"♻️ {item.display_name} was automatically restarted by Watchdog.")
                        except TelegramError: pass
                except Exception: logger.exception("Watchdog restart failed")
    save_v7_data(); save_projects()

async def startup_recovery_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    recovered=0
    for uid,items in running_scripts.items():
        async with lock_for(uid):
            for item in items:
                if item.running: continue
                if project_settings.get(project_key(item),{}).get("env_blocked"): continue
                if not (item.desired_running or project_setting(item).get("autostart")): continue
                try: spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path)); recovered+=1
                except Exception: logger.exception("Startup recovery failed")
    if recovered:
        try: await context.bot.send_message(OWNER_ID,f"♻️ V10 startup recovery restored {recovered} Python project(s).")
        except TelegramError: pass

async def log_rotation_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    maxb=LOG_ROTATE_MAX_MB*1024*1024; keep=LOG_ROTATE_KEEP_MB*1024*1024
    for items in running_scripts.values():
        for item in items:
            p=Path(item.log_path)
            try:
                if p.exists() and p.stat().st_size>maxb:
                    with p.open("rb") as f: f.seek(-min(keep,p.stat().st_size),2); tail=f.read()
                    p.write_bytes(b"===== QURESHIxOTP V10 log rotated =====\n"+tail)
            except OSError: pass

async def panel_reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global panel_last_reminder_at
    if not panel_reminder_enabled: return
    now=time.time(); due=panel_last_confirmed_at+PANEL_REMINDER_HOURS*3600
    if now<due or (panel_last_reminder_at and now-panel_last_reminder_at<12*3600): return
    panel_last_reminder_at=now; save_v7_data()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ I Visited Panel",callback_data="admin:panelvisited")]])
    try:
        await context.bot.send_message(OWNER_ID,premium_box("⏰ ᴘᴀɴᴇʟ ʀᴇᴍɪɴᴅᴇʀ",["Your 3-day panel visit reminder is due.","Open your hosting panel manually, then tap the button below or run <code>/panelvisited</code>."]),parse_mode=ParseMode.HTML,reply_markup=kb)
    except TelegramError: logger.exception("Panel reminder failed")


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    logger.exception(
        "Unhandled update error",
        exc_info=context.error,
    )

    if (
        isinstance(update, Update)
        and update.effective_message
    ):
        try:
            await update.effective_message.reply_text(
                "⚠️ An internal error occurred. Try again."
            )
        except TelegramError:
            pass




# ═════════════════════════════════════════════════════════════════════════════
# V10.4 PREMIUM UX / CONTROL FEATURES (no security-review queue)
# ═════════════════════════════════════════════════════════════════════════════

def _meta(item: ScriptProcess) -> dict[str, Any]:
    return project_setting(item)

def _find_any_project(target: str) -> tuple[int,int,ScriptProcess] | None:
    t=target.casefold()
    for uid,items in running_scripts.items():
        for idx,item in enumerate(items):
            if item.display_name.casefold()==t or Path(item.entry_file).name.casefold()==t:
                return uid,idx,item
    return None

async def favorite_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text("Usage: /favorite PROJECT on|off"); return
    val=True
    args=context.args[:]
    if args[-1].lower() in {"on","off"}: val=args.pop().lower()=="on"
    found=find_project(update.effective_user.id," ".join(args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; _meta(item)["favorite"]=val; save_v7_data()
    await update.effective_message.reply_text(f"{'⭐' if val else '☆'} Favorite {'enabled' if val else 'disabled'} for {item.display_name}.")

async def tag_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /tag PROJECT NAME | TAG'); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; project_setting(item)['tag']=f[1][:40]; save_v7_data(); await update.effective_message.reply_text('✅ Project tag saved.')


async def searchproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    q=" ".join(context.args).casefold().strip()
    rows=[]
    for i,item in enumerate(scripts_for(update.effective_user.id)):
        m=_meta(item); hay=f"{item.display_name} {m.get('tag','')}".casefold()
        if not q or q in hay: rows.append(f"{'⭐ ' if m.get('favorite') else ''}<b>{esc(item.display_name)}</b> • {esc(m.get('tag','No tag'))} • <code>{'ONLINE' if item.running else 'OFFLINE'}</code>")
    await update.effective_message.reply_text(premium_box("🔎 ᴘʀᴏᴊᴇᴄᴛ sᴇᴀʀᴄʜ",rows or ["No matching projects."]),parse_mode=ParseMode.HTML)

async def trash_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    uid=update.effective_user.id; now=time.time(); rows=global_cfg().setdefault("trash",{}).setdefault(str(uid),[])
    alive=[x for x in rows if float(x.get("expires_at",0))>now]; global_cfg()["trash"][str(uid)]=alive; save_v7_data()
    lines=[f"• <code>{esc(x['trash_id'])}</code> — {esc(x.get('project',{}).get('display_name','Project'))} — expires in {human_duration(max(0,int(x['expires_at']-now)))}" for x in alive]
    await update.effective_message.reply_text(premium_box("🗑 ᴛʀᴀsʜ",lines+["Restore: <code>/restoretrash TRASH_ID</code>"] if lines else ["Trash is empty."]),parse_mode=ParseMode.HTML)

async def restoretrash_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text("Usage: /restoretrash TRASH_ID"); return
    uid=update.effective_user.id; rows=global_cfg().setdefault("trash",{}).setdefault(str(uid),[]); tid=context.args[0]
    row=next((x for x in rows if x.get("trash_id")==tid and float(x.get("expires_at",0))>time.time()),None)
    if not row: await update.effective_message.reply_text("❌ Trash item not found/expired."); return
    src=Path(row.get("trash_folder","")); pdata=row["project"]
    if not src.exists(): await update.effective_message.reply_text("❌ Trash source files are missing."); return
    dest=user_folder(uid)/(datetime.now().strftime("%Y%m%d_%H%M%S_%f")+"_restored"); shutil.move(str(src),str(dest))
    oldfolder=Path(pdata["folder"]); oldentry=Path(pdata["entry_file"]); rel=oldentry.relative_to(oldfolder) if oldentry.is_relative_to(oldfolder) else Path(oldentry.name); entry=dest/rel
    item=ScriptProcess(display_name=pdata.get("display_name",entry.name),entry_file=str(entry),folder=str(dest),log_path=str(dest/"runtime.log"),started_at=time.time(),restarts=0,auto_restart=bool(pdata.get("auto_restart",False)),desired_running=False,runtime=pdata.get("runtime",runtime_for_entry(entry)),source_type=pdata.get("source_type","upload"),repo_url=pdata.get("repo_url",""),branch=pdata.get("branch","main"),commit_sha=pdata.get("commit_sha",""))
    scripts_for(uid).append(item); project_settings[project_key(item)]=row.get("settings",{}); project_envs[project_key(item)]=row.get("envs",{}); rows.remove(row); save_projects(); save_v7_data(); audit(uid,"restore_trash",item.display_name,tid)
    await update.effective_message.reply_text(f"✅ Restored <b>{esc(item.display_name)}</b>. Use /restart to start it.",parse_mode=ParseMode.HTML)

async def backupschedule_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if len(context.args)<2 or context.args[-1].lower() not in {"off","daily","weekly"}: await update.effective_message.reply_text("Usage: /backupschedule PROJECT daily|weekly|off"); return
    found=find_project(update.effective_user.id," ".join(context.args[:-1])); mode=context.args[-1].lower()
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; _meta(item)["backup_schedule"]=mode; _meta(item)["next_backup_at"]=time.time()+(86400 if mode=="daily" else 604800 if mode=="weekly" else 0); save_v7_data()
    await update.effective_message.reply_text(f"💾 Backup schedule for {item.display_name}: {mode.upper()}")

async def activity_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    uid=update.effective_user.id; rows=[x for x in audit_log if int(x.get("actor",0))==uid][-20:][::-1]
    lines=[f"• <code>{esc(x.get('time',''))}</code> — {esc(x.get('action',''))} {esc(x.get('target',''))}" for x in rows]
    await update.effective_message.reply_text(premium_box("📜 ᴍʏ ᴀᴄᴛɪᴠɪᴛʏ",lines or ["No activity yet."]),parse_mode=ParseMode.HTML)

async def templates_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    names=["telegram-python","telegram-node","flask","fastapi","express","discord","worker"]
    if not context.args:
        await update.effective_message.reply_text(premium_box("🧩 ᴘʀᴏᴊᴇᴄᴛ ᴛᴇᴍᴘʟᴀᴛᴇs",[f"• <code>{x}</code>" for x in names]+["Create: <code>/template NAME PROJECT_NAME</code>"]),parse_mode=ParseMode.HTML); return
    await template_cmd(update,context)

async def template_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if len(context.args)<2: await update.effective_message.reply_text("Usage: /template TYPE PROJECT_NAME"); return
    typ=context.args[0].lower(); name=clean_project_name(" ".join(context.args[1:])); root=user_folder(update.effective_user.id)/(datetime.now().strftime("%Y%m%d_%H%M%S_%f")+"_"+name); root.mkdir(parents=True)
    files={
      "telegram-python":{"main.py":"import os\nfrom telegram import Update\nfrom telegram.ext import Application,CommandHandler,ContextTypes\nasync def start(u:Update,c:ContextTypes.DEFAULT_TYPE): await u.message.reply_text('Hello from QURESHIxOTP')\na=Application.builder().token(os.environ['BOT_TOKEN']).build(); a.add_handler(CommandHandler('start',start)); a.run_polling()\n","requirements.txt":"python-telegram-bot>=21,<23\n"},
      "telegram-node":{"index.js":"console.log('QURESHIxOTP Telegram Node starter'); setInterval(()=>{},60000);\n","package.json":"{\"scripts\":{\"start\":\"node index.js\"}}\n"},
      "flask":{"main.py":"from flask import Flask\napp=Flask(__name__)\n@app.get('/')\ndef home(): return 'QURESHIxOTP Flask Online'\napp.run(host='0.0.0.0',port=8080)\n","requirements.txt":"flask\n"},
      "fastapi":{"main.py":"from fastapi import FastAPI\nimport uvicorn\napp=FastAPI()\n@app.get('/')\ndef home(): return {'status':'online'}\nuvicorn.run(app,host='0.0.0.0',port=8080)\n","requirements.txt":"fastapi\nuvicorn\n"},
      "express":{"index.js":"const express=require('express'); const app=express(); app.get('/',(_,r)=>r.send('QURESHIxOTP Express Online')); app.listen(8080);\n","package.json":"{\"scripts\":{\"start\":\"node index.js\"},\"dependencies\":{\"express\":\"latest\"}}\n"},
      "discord":{"main.py":"import os\nprint('Discord starter: add your client code and DISCORD_TOKEN env')\n","requirements.txt":"discord.py\n"},
      "worker":{"main.py":"import time\nprint('QURESHIxOTP worker online')\nwhile True: time.sleep(60)\n"}}
    if typ not in files: shutil.rmtree(root,ignore_errors=True); await update.effective_message.reply_text("❌ Unknown template. Use /templates"); return
    for fn,content in files[typ].items(): (root/fn).write_text(content,encoding="utf-8")
    entry=detect_entry(root); item=ScriptProcess(display_name=name,entry_file=str(entry),folder=str(root),log_path=str(root/"runtime.log"),started_at=time.time(),runtime=runtime_for_entry(entry),source_type="template"); scripts_for(update.effective_user.id).append(item); save_projects(); audit(update.effective_user.id,"create_template",name,typ)
    await update.effective_message.reply_text(f"✅ Template <b>{esc(typ)}</b> created as <b>{esc(name)}</b>. Add ENV/dependencies then /restart {esc(name)}.",parse_mode=ParseMode.HTML)

async def replyticket_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not admin_or_owner(update) or len(context.args)<2 or not context.args[0].isdigit(): return
    tid=int(context.args[0]); text=" ".join(context.args[1:])[:1500]; tickets=global_cfg().setdefault("tickets",[]); row=next((x for x in tickets if int(x.get('id',0))==tid),None)
    if not row: await update.effective_message.reply_text("❌ Ticket not found."); return
    row.setdefault("replies",[]).append({"by":update.effective_user.id,"text":text,"time":datetime.now().isoformat(timespec="seconds")}); save_v7_data()
    try: await context.bot.send_message(int(row['user_id']),premium_box("💬 sᴜᴘᴘᴏʀᴛ ʀᴇᴘʟʏ",[f"Ticket • <code>#{tid}</code>",esc(text)]),parse_mode=ParseMode.HTML)
    except TelegramError: pass
    await update.effective_message.reply_text("✅ Reply sent.")

async def warn_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not admin_or_owner(update) or len(context.args)<2 or not context.args[0].isdigit(): return
    uid=int(context.args[0]); reason=" ".join(context.args[1:])[:500]; cfg=global_cfg().setdefault("warnings",{}); cfg.setdefault(str(uid),[]).append({"time":datetime.now().isoformat(timespec="seconds"),"reason":reason,"by":update.effective_user.id}); save_v7_data(); audit(update.effective_user.id,"warn_user",str(uid),reason)
    try: await context.bot.send_message(uid,premium_box("⚠️ ᴀᴄᴄᴏᴜɴᴛ ᴡᴀʀɴɪɴɢ",[esc(reason)]),parse_mode=ParseMode.HTML)
    except TelegramError: pass
    await update.effective_message.reply_text("✅ Warning recorded.")

async def usernote_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not admin_or_owner(update) or not context.args or not context.args[0].isdigit(): return
    uid=context.args[0]; notes=global_cfg().setdefault("user_notes",{})
    if len(context.args)>1: notes.setdefault(uid,[]).append({"time":datetime.now().isoformat(timespec="seconds"),"text":" ".join(context.args[1:])[:800],"by":update.effective_user.id}); save_v7_data()
    lines=[f"• <code>{esc(x['time'])}</code> — {esc(x['text'])}" for x in notes.get(uid,[])[-15:]]
    await update.effective_message.reply_text(premium_box("📝 ᴜsᴇʀ ɴᴏᴛᴇs",lines or ["No notes."]),parse_mode=ParseMode.HTML)

async def userprojects_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not admin_or_owner(update) or not context.args or not context.args[0].isdigit(): return
    uid=int(context.args[0]); lines=[f"• <b>{esc(x.display_name)}</b> • <code>{'ONLINE' if x.running else 'OFFLINE'}</code> • {esc(x.source_type)}" for x in scripts_for(uid)]
    await update.effective_message.reply_text(premium_box("🚀 ᴜsᴇʀ ᴘʀᴏᴊᴇᴄᴛs",lines or ["No projects."]),parse_mode=ParseMode.HTML)

async def adminproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not admin_or_owner(update) or len(context.args)<2: await update.effective_message.reply_text("Usage: /adminproject stop|restart|delete PROJECT"); return
    action=context.args[0].lower(); found=_find_any_project(" ".join(context.args[1:]))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    uid,idx,item=found
    if action=="stop": kill_process(item) if item.running else None
    elif action=="restart":
        if item.running: kill_process(item)
        spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
    elif action=="delete" and (is_owner(update.effective_user.id) or admin_role(update.effective_user.id)=="superadmin"):
        if item.running: kill_process(item)
        safe_remove_folder(item.folder); scripts_for(uid).pop(idx); save_projects()
    else: await update.effective_message.reply_text("❌ Action not permitted."); return
    audit(update.effective_user.id,"admin_project_"+action,item.display_name,str(uid)); await update.effective_message.reply_text("✅ Admin project action completed.")

async def extensions_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    cfg=global_cfg(); exts=set(cfg.get("allowed_extensions",[".py",".js",".mjs",".cjs",".php",".sh",".rb",".jar",".zip"]))
    if len(context.args)>=2:
        ext=context.args[1].lower(); ext=ext if ext.startswith('.') else '.'+ext
        if context.args[0].lower()=="add": exts.add(ext)
        elif context.args[0].lower()=="remove": exts.discard(ext)
        cfg["allowed_extensions"]=sorted(exts); save_v7_data()
    await update.effective_message.reply_text(premium_box("📁 ᴀʟʟᴏᴡᴇᴅ ғɪʟᴇ ᴛʏᴘᴇs",[" • ".join(sorted(exts)),"Use: <code>/extensions add .py</code> or <code>/extensions remove .rb</code>"]),parse_mode=ParseMode.HTML)

async def packageblacklist_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    bl=set(global_cfg().get("package_blacklist",[]))
    if len(context.args)>=2:
        pkg=context.args[1].lower()
        if context.args[0].lower()=="add": bl.add(pkg)
        elif context.args[0].lower()=="remove": bl.discard(pkg)
        global_cfg()["package_blacklist"]=sorted(bl); save_v7_data()
    await update.effective_message.reply_text(premium_box("📦 ᴘᴀᴄᴋᴀɢᴇ ʙʟᴀᴄᴋʟɪsᴛ",[f"• <code>{esc(x)}</code>" for x in sorted(bl)] or ["Blacklist empty."]),parse_mode=ParseMode.HTML)

async def broadcastplan_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update) or len(context.args)<2: return
    plan=context.args[0].lower(); text=" ".join(context.args[1:]); targets=[]
    for uid_s in user_stats:
        uid=int(uid_s); p=user_plans.get(uid_s,"premium" if uid in premium_users else "free")
        if plan=="all" or p==plan: targets.append(uid)
    ok=0
    for uid in targets:
        try: await context.bot.send_message(uid,premium_box("📢 ᴇʟᴇᴠᴀᴛᴇx ɴᴏᴛɪᴄᴇ",[esc(text)]),parse_mode=ParseMode.HTML); ok+=1
        except TelegramError: pass
    await update.effective_message.reply_text(f"✅ Broadcast delivered to {ok}/{len(targets)} users.")

async def backup_scheduler_job(context:ContextTypes.DEFAULT_TYPE)->None:
    now=time.time()
    for uid,items in list(running_scripts.items()):
        for item in items:
            st=_meta(item); mode=st.get("backup_schedule","off"); due=float(st.get("next_backup_at",0) or 0)
            if mode not in {"daily","weekly"} or not due or now<due: continue
            folder=Path(item.folder); stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); out=PROJECT_BACKUPS_DIR/f"{uid}_{clean_project_name(item.display_name)}_auto_{stamp}.zip"
            try:
                with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
                    for f in folder.rglob('*'):
                        if f.is_file() and '.venv' not in f.parts and 'node_modules' not in f.parts and f.name!='runtime.log': z.write(f,f.relative_to(folder))
                try: await send_real_file(context.bot,uid,out,f"💾 Scheduled backup: {item.display_name}")
                except TelegramError: pass
                st["next_backup_at"]=now+(86400 if mode=="daily" else 604800); save_v7_data()
            except Exception: logger.exception("Scheduled project backup failed")




# ═════════════════════════════════════════════════════════════════════════════
# V10.7 DATA-SAFE ENV / FILE REPLACEMENT / OWNER GITHUB DATA SYNC
# ═════════════════════════════════════════════════════════════════════════════

V106_DATA_SYNC_BRANCH = "data-backup"
V106_DATA_SYNC_INTERVAL = 300
V106_DATA_EXTS = {".json", ".db", ".sqlite", ".sqlite3", ".yaml", ".yml", ".csv", ".dat", ".pkl", ".pickle"}
V106_DATA_DIR_NAMES = {"data", "database", "db", "storage", "uploads", "state"}
V106_SOURCE_EXTS = {".py", ".js", ".mjs", ".cjs", ".php", ".rb", ".sh", ".jar", ".md"}
V106_SECRET_FILE_NAMES = {".env", ".env.local", ".env.production", ".env.development", "credentials.json", "secrets.json"}
V106_MANAGER_SECRET_PATTERN = re.compile(r"(?:TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|PRIVATE_KEY|ACCESS_KEY|AUTH_KEY|CREDENTIAL)", re.I)



# ═════════════════════════════════════════════════════════════════════════════
# V10.7 — PROJECT MANAGEMENT + RELIABILITY
# ═════════════════════════════════════════════════════════════════════════════
V107_FILE_HISTORY_LIMIT = 12
V107_DATA_VERSION_LIMIT = 20
V107_DEP_TIMEOUT = 300
V107_STARTUP_TEST_SECONDS = 4
V107_NOTIFY_EVENTS = {"crash","restart","github","datasync","backup","env"}

def v107_cfg() -> dict[str, Any]:
    return global_cfg().setdefault("v107", {})

def command_payload(update: Update) -> str:
    text = (getattr(update.effective_message, "text", "") or "").strip()
    return text.split(maxsplit=1)[1].strip() if " " in text else ""

def pipe_fields(update: Update) -> list[str]:
    payload = command_payload(update)
    return [x.strip() for x in payload.split("|")] if payload else []

def project_locked(item: ScriptProcess) -> bool:
    return bool(project_settings.get(project_key(item), {}).get("locked", False))

def parse_project_pipe(update: Update, context: ContextTypes.DEFAULT_TYPE, min_fields: int = 1) -> list[str]:
    fields = pipe_fields(update)
    if len(fields) >= min_fields:
        return fields
    # Backward compatibility: callers can still inspect context.args.
    return []

def file_history_dir(item: ScriptProcess, rel: str) -> Path:
    token = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16]
    d = Path(item.folder) / ".QURESHIxOTP_file_history" / token
    d.mkdir(parents=True, exist_ok=True)
    return d

def save_file_version(item: ScriptProcess, rel: str) -> str | None:
    try:
        target = safe_inside_project(item, rel)
        if not target.is_file() or _secret_project_path(target):
            return None
        d = file_history_dir(item, rel)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        ext = target.suffix or ".file"
        out = d / f"{stamp}{ext}"
        shutil.copy2(target, out)
        meta = d / "meta.json"
        rows = json.loads(meta.read_text()) if meta.exists() else []
        rows.append({"id": stamp, "path": rel, "saved_at": datetime.now().isoformat(timespec="seconds"), "file": out.name})
        rows = rows[-V107_FILE_HISTORY_LIMIT:]
        keep={r['file'] for r in rows}
        for f in d.iterdir():
            if f.is_file() and f.name!='meta.json' and f.name not in keep: f.unlink(missing_ok=True)
        meta.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return stamp
    except Exception:
        logger.exception("Could not save file version")
        return None

def load_file_versions(item: ScriptProcess, rel: str) -> list[dict[str, Any]]:
    d=file_history_dir(item, rel); meta=d/"meta.json"
    try: return json.loads(meta.read_text()) if meta.exists() else []
    except Exception: return []

def required_env_summary(item: ScriptProcess) -> tuple[list[str], list[str]]:
    root=Path(item.folder); required=sorted(detect_required_env_vars(root)); active=_active_project_env(item,root)
    missing=[x for x in required if not active.get(x)]
    present=[x for x in required if active.get(x)]
    return present, missing

def setup_summary(item: ScriptProcess) -> list[str]:
    root=Path(item.folder); present,missing=required_env_summary(item)
    req=next(iter(root.rglob('requirements.txt')),None); pkg=next(iter(root.rglob('package.json')),None)
    return [
        f"Project • <b>{esc(item.display_name)}</b>",
        f"Runtime • <code>{esc(item.runtime)}</code>",
        f"Entry • <code>{esc(str(Path(item.entry_file).relative_to(root)))}</code>",
        f"Dependencies • <code>{'requirements.txt' if req else ('package.json' if pkg else 'None')}</code>",
        f"ENV Ready • <code>{len(present)}</code>",
        f"ENV Missing • <code>{len(missing)}</code>",
        *( ["Missing • "+", ".join(f"<code>{esc(x)}</code>" for x in missing[:12])] if missing else ["✅ Required ENV is ready"] ),
        f"Lock • <code>{'ON' if project_locked(item) else 'OFF'}</code>",
    ]

def env_wizard_keyboard(index:int,item:ScriptProcess)->InlineKeyboardMarkup:
    _,missing=required_env_summary(item)
    cfg=project_settings.setdefault(project_key(item),{})
    rows=[]
    for key in missing[:8]: rows.append([InlineKeyboardButton(f"➕ {key}",callback_data=f"v107:envkey:{index}:{key[:32]}")])
    if missing:
        rows.append([InlineKeyboardButton("⏭ Skip ENV & Start",callback_data=f"v107:envskip:{index}"), InlineKeyboardButton("🔄 Refresh",callback_data=f"v107:setup:{index}")])
        if item.source_type=="github":
            rows.append([InlineKeyboardButton("✅ Skip ENV For Future GitHub Projects",callback_data=f"v1073:envremember:{index}")])
    else:
        rows.append([InlineKeyboardButton("✅ No ENV Required",callback_data=f"v107:envskip:{index}"), InlineKeyboardButton("🚀 Start",callback_data=f"project:start:{index}")])
    rows.append([InlineKeyboardButton("⬅️ Project",callback_data=f"v10:center:{index}")])
    return InlineKeyboardMarkup(rows)

def project_notification_settings(item: ScriptProcess)->dict[str,bool]:
    return project_settings.setdefault(project_key(item),{}).setdefault('notifications_v107',{x:True for x in V107_NOTIFY_EVENTS})

def detailed_diagnosis(text:str)->list[str]:
    patterns=[
        (r"ModuleNotFoundError: No module named ['\"]([^'\"]+)",lambda m:["❌ Type • <b>ModuleNotFoundError</b>",f"📦 Missing • <code>{esc(m.group(1))}</code>",f"💡 Try • <code>/depadd PROJECT | {esc(m.group(1))}</code>"]),
        (r"SyntaxError.*?\n",lambda m:["❌ Type • <b>SyntaxError</b>","💡 Open the referenced file/line and fix Python syntax before restart."]),
        (r"ENV_SETUP_REQUIRED: missing ([^\n]+)",lambda m:["❌ Type • <b>Missing ENV</b>",f"🔐 Missing • <code>{esc(m.group(1)[:300])}</code>","💡 Use the ENV Wizard."]),
        (r"InvalidToken|Unauthorized",lambda m:["❌ Type • <b>Invalid Token</b>","💡 Replace the PROJECT token/secret; QURESHIxOTP manager secrets are never injected."]),
        (r"Conflict:.*terminated by other getUpdates|Conflict",lambda m:["❌ Type • <b>Telegram Polling Conflict</b>","💡 Another instance may be using the same bot token."]),
        (r"EADDRINUSE|Address already in use",lambda m:["❌ Type • <b>Port Conflict</b>","💡 Change the project port or stop the other process using it."]),
        (r"PermissionError|Permission denied",lambda m:["❌ Type • <b>Permission Error</b>","💡 Project attempted an unavailable filesystem/resource operation."]),
        (r"ERESOLVE|dependency conflict|ResolutionImpossible",lambda m:["❌ Type • <b>Dependency Conflict</b>","💡 Review dependency versions or create a dependency snapshot before changing them."]),
    ]
    for pat,builder in patterns:
        m=re.search(pat,text,re.I|re.S)
        if m: return builder(m)
    return ["ℹ️ No known error signature detected.","Use full logs for manual diagnosis."]

def data_remote_base(item:ScriptProcess)->str:
    uid=_project_owner_id(item)
    return f"QURESHIxOTP-data/{uid}/{re.sub(r'[^A-Za-z0-9._-]+','_',item.display_name)}"

def remote_data_object(item:ScriptProcess, token:str, branch:str, path:str)->dict:
    owner,repo=_ensure_private_data_branch(item,token,branch)
    api=f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path,safe='/')}?ref={urllib.parse.quote(branch,safe='')}"
    return _github_request('GET',api,token)

def local_data_digest(item:ScriptProcess)->str:
    h=hashlib.sha256()
    for f in sorted(_runtime_data_files(item),key=lambda x:str(x)):
        try:
            h.update(str(f.relative_to(Path(item.folder))).encode()); h.update(f.read_bytes())
        except OSError: pass
    return h.hexdigest()

def admin_project_lookup(owner_uid:int,name:str)->ScriptProcess|None:
    found=find_project(owner_uid,name)
    return found[1] if found else None

def v106_cfg() -> dict[str, Any]:
    return global_cfg().setdefault("v106", {})


def _project_owner_id(item: ScriptProcess) -> int:
    for uid, items in running_scripts.items():
        if item in items:
            return int(uid)
    return OWNER_ID


def _parse_dotenv_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists() or not path.is_file():
        return out
    try:
        for raw in path.read_text("utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", key):
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            out[key] = value
    except Exception:
        logger.exception("Could not parse project .env: %s", path)
    return out


def _active_project_env(item: ScriptProcess | None, folder: Path) -> dict[str, str]:
    envs: dict[str, str] = {}
    envs.update(_parse_dotenv_file(folder / ".env"))
    key = project_key(item if item is not None else folder)
    envs.update({str(k): str(v) for k, v in project_envs.get(key, {}).items()})
    cfg = project_settings.get(key, {})
    active_profile = str(cfg.get("active_env_profile", ""))
    profiles = cfg.get("env_profiles", {})
    if active_profile and isinstance(profiles, dict) and isinstance(profiles.get(active_profile), dict):
        envs.update({str(k): str(v) for k, v in profiles[active_profile].items()})
    return envs


def detect_required_env_vars(folder: Path) -> set[str]:
    """Best-effort discovery of ENV keys that are actually required.

    Python ``os.getenv('KEY', default)`` and ``os.environ.get('KEY', default)``
    are optional and must not block deployment. Direct lookups and lookups
    without a default remain required. JavaScript/PHP/Ruby direct ENV reads
    are treated as required because static analysis cannot reliably infer a
    fallback across arbitrary expressions.
    """
    found: set[str] = set()
    py_required = [
        re.compile(r"os\.getenv\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)"),
        re.compile(r"os\.environ\.get\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)"),
        re.compile(r"os\.environ\[\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\]"),
    ]
    other_required = [
        re.compile(r"process\.env\.([A-Za-z_][A-Za-z0-9_]*)"),
        re.compile(r"process\.env\[\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\]"),
        re.compile(r"ENV\[\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\]"),
        re.compile(r"\$_ENV\[\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\]"),
    ]
    skip_parts = {".venv", "node_modules", ".git", "__pycache__", ".QURESHIxOTP_history", ".QURESHIxOTP_data_sync"}
    for file in folder.rglob("*"):
        if not file.is_file() or any(part in skip_parts for part in file.relative_to(folder).parts):
            continue
        suffix = file.suffix.lower()
        if suffix not in {".py", ".js", ".mjs", ".cjs", ".php", ".rb", ".sh"}:
            continue
        try:
            if file.stat().st_size > 1024 * 1024:
                continue
            text = file.read_text("utf-8", errors="ignore")
        except Exception:
            continue
        patterns = py_required if suffix == ".py" else other_required
        for pat in patterns:
            found.update(pat.findall(text))
    found.difference_update({"PATH", "HOME", "USER", "LANG", "PWD", "SHELL", "TMPDIR", "TEMP", "TMP", "PORT", "HOSTNAME"})
    return found


def ensure_project_env_ready(item: ScriptProcess | None, folder: Path) -> tuple[bool, list[str]]:
    required = detect_required_env_vars(folder)
    configured = _active_project_env(item, folder)
    missing = sorted(k for k in required if not configured.get(k))
    key = project_key(item if item is not None else folder)
    cfg = project_settings.setdefault(key, {})
    cfg["required_env_vars"] = sorted(required)
    cfg["missing_env_vars"] = missing
    # Owner/user may explicitly skip ENV setup for projects that do not actually need
    # the statically detected variables. Skipping NEVER exposes QURESHIxOTP manager secrets.
    env_skipped = bool(cfg.get("env_setup_skipped", False))
    cfg["env_blocked"] = bool(missing) and not env_skipped
    # If the user configured ENV through QURESHIxOTP and repo has no .env, create a private generated .env.
    env_file = folder / ".env"
    if configured and not env_file.exists():
        try:
            lines = []
            for k, v in sorted(configured.items()):
                escaped = str(v).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
                lines.append(f'{k}="{escaped}"')
            env_file.write_text("\n".join(lines) + "\n", "utf-8")
            try:
                env_file.chmod(0o600)
            except OSError:
                pass
            cfg["QURESHIxOTP_generated_env"] = True
        except Exception:
            logger.exception("Could not materialize generated .env for %s", folder)
    save_v7_data()
    # V10.7.2: an explicit per-project ENV skip is authoritative for every
    # launch path (Start/Restart/Redeploy/Watchdog). Missing keys are still
    # reported for diagnostics, but they no longer block startup. Manager
    # secrets remain excluded by sanitized_host_environment().
    return (not missing) or env_skipped, missing


def sanitized_host_environment() -> dict[str, str]:
    """Never leak manager secrets into hosted projects."""
    safe: dict[str, str] = {}
    for k, v in os.environ.items():
        if V106_MANAGER_SECRET_PATTERN.search(k):
            continue
        safe[k] = v
    # Explicitly protect the manager's BotFather token even if named unusually.
    for key in ("BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"):
        safe.pop(key, None)
    return safe


def _secret_project_path(path: Path) -> bool:
    name = path.name.lower()
    if name in V106_SECRET_FILE_NAMES or name.startswith(".env"):
        return True
    return any(x in name for x in ("secret", "credential", "private_key"))


def _rewrite_generated_env(item: ScriptProcess) -> None:
    cfg = project_settings.setdefault(project_key(item), {})
    if not cfg.get("QURESHIxOTP_generated_env"):
        return
    path = Path(item.folder) / ".env"
    envs = _active_project_env(item, Path(item.folder))
    # _active_project_env includes old generated .env; project_envs/profile override it.
    wanted = dict(project_envs.get(project_key(item), {}))
    profile = cfg.get("active_env_profile", "")
    profiles = cfg.get("env_profiles", {})
    if profile and isinstance(profiles, dict) and isinstance(profiles.get(profile), dict):
        wanted.update(profiles[profile])
    try:
        lines=[]
        for k,v in sorted(wanted.items()):
            escaped=str(v).replace("\\","\\\\").replace("\n","\\n").replace('"','\\"')
            lines.append(f'{k}="{escaped}"')
        path.write_text("\n".join(lines)+("\n" if lines else ""),"utf-8")
        try: path.chmod(0o600)
        except OSError: pass
    except Exception:
        logger.exception("Failed refreshing generated .env")


def _find_global_project(owner_uid: int, project_name: str) -> tuple[int, ScriptProcess] | None:
    return find_project(owner_uid, project_name)


def data_sync_settings(item: ScriptProcess) -> dict[str, Any]:
    return project_settings.setdefault(project_key(item), {}).setdefault("github_data_sync", {
        "enabled": False,
        "mode": "full",
        "branch": V106_DATA_SYNC_BRANCH,
        "last_sync": "—",
        "last_restore": "—",
        "last_status": "Not configured",
    })


def _github_request(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "QURESHIxOTP-Host-V10.7", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"GitHub API {exc.code}: {body or exc.reason}") from exc


def _ensure_private_data_branch(item: ScriptProcess, token: str, branch: str) -> tuple[str, str]:
    owner, repo = github_repo_parts(item.repo_url)
    meta = _github_request("GET", f"https://api.github.com/repos/{owner}/{repo}", token)
    if not meta.get("private", False):
        raise RuntimeError("Data Sync requires a PRIVATE GitHub repository to protect runtime data.")
    default_branch = str(meta.get("default_branch") or item.branch or "main")
    try:
        _github_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{urllib.parse.quote(branch, safe='')}", token)
    except Exception:
        ref = _github_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{urllib.parse.quote(default_branch, safe='')}", token)
        sha = ref.get("object", {}).get("sha")
        if not sha:
            raise RuntimeError("Could not resolve GitHub default branch for Data Sync")
        try:
            _github_request("POST", f"https://api.github.com/repos/{owner}/{repo}/git/refs", token, {"ref": f"refs/heads/{branch}", "sha": sha})
        except RuntimeError as exc:
            if "422" not in str(exc):
                raise
    return owner, repo


def _runtime_data_files(item: ScriptProcess) -> list[Path]:
    root = Path(item.folder)
    out: list[Path] = []
    skip_parts = {".venv", "node_modules", ".git", "__pycache__", ".QURESHIxOTP_history", ".QURESHIxOTP_data_sync"}
    skip_names = {"runtime.log", "package-lock.json", "requirements.txt", "readme.md", "readme", "profile", "start.sh"}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root)
        if any(part in skip_parts for part in rel.parts):
            continue
        if _secret_project_path(f) or f.name.lower() in skip_names:
            continue
        in_data_dir = any(part.lower() in V106_DATA_DIR_NAMES for part in rel.parts[:-1])
        data_name = bool(re.match(r"^(users?|premium|banned?|settings?|state|database|data)[._-]", f.name.lower()))
        if in_data_dir or f.suffix.lower() in V106_DATA_EXTS or data_name:
            out.append(f)
    return out


def create_project_data_archive(item: ScriptProcess) -> Path:
    root = Path(item.folder)
    sync_dir = root / ".QURESHIxOTP_data_sync"
    sync_dir.mkdir(parents=True, exist_ok=True)
    archive = sync_dir / "latest-data.zip"
    files = _runtime_data_files(item)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        manifest = {"project": item.display_name, "created": datetime.now(timezone.utc).isoformat(), "files": [str(f.relative_to(root)) for f in files]}
        z.writestr(".QURESHIxOTP-data-manifest.json", json.dumps(manifest, indent=2))
        for f in files:
            z.write(f, f.relative_to(root))
    return archive


def github_data_sync_push(item: ScriptProcess) -> str:
    settings = data_sync_settings(item)
    if not settings.get("enabled"):
        return "OFF"
    if item.source_type != "github" or not item.repo_url:
        raise RuntimeError("Data Sync only works for GitHub-connected projects")
    uid = _project_owner_id(item)
    token = github_token_for(uid)
    if not token:
        raise RuntimeError("Project owner has no GitHub token configured")
    branch = str(settings.get("branch") or V106_DATA_SYNC_BRANCH)
    owner, repo = _ensure_private_data_branch(item, token, branch)
    archive = create_project_data_archive(item)
    content = base64.b64encode(archive.read_bytes()).decode("ascii")
    remote_path = f"QURESHIxOTP-data/{uid}/{re.sub(r'[^A-Za-z0-9._-]+','_',item.display_name)}/latest-data.zip"
    api = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(remote_path, safe='/')}"
    existing_sha = ""
    try:
        existing = _github_request("GET", api + "?ref=" + urllib.parse.quote(branch, safe=""), token)
        existing_sha = str(existing.get("sha") or "")
    except Exception:
        pass
    payload = {"message": f"QURESHIxOTP auto data backup • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", "content": content, "branch": branch}
    if existing_sha:
        payload["sha"] = existing_sha
    # Conflict protection: if remote changed since our last known SHA, do not blindly overwrite.
    if existing_sha and settings.get("last_remote_sha") and existing_sha != settings.get("last_remote_sha"):
        raise RuntimeError("DATA_SYNC_CONFLICT: remote backup changed independently; use /syncpreview before resolving")
    result=_github_request("PUT", api, token, payload)
    new_sha=str((result.get("content") or {}).get("sha") or existing_sha)
    # Keep timestamped backup versions as well as latest-data.zip.
    version_name=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")+"-data.zip"
    version_path=data_remote_base(item)+"/versions/"+version_name
    version_api=f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(version_path,safe='/')}"
    try: _github_request("PUT",version_api,token,{"message":f"QURESHIxOTP data version • {version_name}","content":content,"branch":branch})
    except Exception: logger.exception("Could not store timestamped data version")
    settings["last_remote_sha"] = new_sha
    settings["last_local_digest"] = local_data_digest(item)
    settings["last_sync"] = datetime.now(timezone.utc).isoformat()
    settings["last_status"] = f"SYNCED • {len(_runtime_data_files(item))} data file(s)"
    save_v7_data()
    return settings["last_status"]


def github_data_sync_restore(item: ScriptProcess) -> str:
    settings = data_sync_settings(item)
    if not settings.get("enabled"):
        return "OFF"
    uid = _project_owner_id(item)
    token = github_token_for(uid)
    if not token:
        raise RuntimeError("Project owner has no GitHub token configured")
    branch = str(settings.get("branch") or V106_DATA_SYNC_BRANCH)
    owner, repo = _ensure_private_data_branch(item, token, branch)
    remote_path = f"QURESHIxOTP-data/{uid}/{re.sub(r'[^A-Za-z0-9._-]+','_',item.display_name)}/latest-data.zip"
    api = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(remote_path, safe='/')}?ref={urllib.parse.quote(branch, safe='')}"
    try:
        obj = _github_request("GET", api, token)
    except Exception as exc:
        if "404" in str(exc):
            return "No remote data backup yet"
        raise
    encoded = str(obj.get("content") or "").replace("\n", "")
    if not encoded:
        return "No remote data backup yet"
    raw = base64.b64decode(encoded)
    tmp_dir = Path(item.folder) / ".QURESHIxOTP_data_sync"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp = tmp_dir / "restore.zip"
    tmp.write_bytes(raw)
    safe_extract_zip_owner(tmp, Path(item.folder))
    tmp.unlink(missing_ok=True)
    settings["last_restore"] = datetime.now(timezone.utc).isoformat()
    settings["last_status"] = "RESTORED"
    save_v7_data()
    return "RESTORED"


async def datasync_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    f=pipe_fields(update)
    if len(f)<3: await update.effective_message.reply_text("Usage: /datasync USER_ID | PROJECT NAME | on|off"); return
    try: uid=int(f[0])
    except ValueError: await update.effective_message.reply_text("❌ Invalid user ID."); return
    found=find_project(uid,f[1]); mode=f[2].lower()
    if not found or mode not in {'on','off'}: await update.effective_message.reply_text('❌ Project/mode invalid.'); return
    _,item=found
    if item.source_type!='github': await update.effective_message.reply_text('❌ Data Sync is only for GitHub-connected projects.'); return
    settings=data_sync_settings(item); settings['enabled']=mode=='on'; settings['branch']=V106_DATA_SYNC_BRANCH; save_v7_data()
    if mode=='on':
        try:
            result=await asyncio.to_thread(github_data_sync_push,item)
            await update.effective_message.reply_text(premium_box('☁️ ᴅᴀᴛᴀ sʏɴᴄ ᴇɴᴀʙʟᴇᴅ',[f'Project • <b>{esc(item.display_name)}</b>',f'Owner • <code>{uid}</code>',f'Branch • <code>{V106_DATA_SYNC_BRANCH}</code>',f'Initial backup • <code>{esc(result)}</code>','🕘 Timestamped backup versions enabled.','🛡 Remote conflict protection enabled.']),parse_mode=ParseMode.HTML)
        except Exception as exc:
            settings['enabled']=False; settings['last_status']='Enable failed: '+str(exc); save_v7_data(); await update.effective_message.reply_text(f'❌ Data Sync failed: {esc(exc)}',parse_mode=ParseMode.HTML)
    else: await update.effective_message.reply_text('✅ Owner GitHub Data Sync disabled for this project.')

async def datasyncstatus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /datasyncstatus USER_ID | PROJECT NAME'); return
    try: uid=int(f[0])
    except ValueError: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    found=find_project(uid,f[1])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; cfg=data_sync_settings(item)
    await update.effective_message.reply_text(premium_box('☁️ ɢɪᴛʜᴜʙ ᴅᴀᴛᴀ sʏɴᴄ',[f'Project • <b>{esc(item.display_name)}</b>',f'Status • <code>{"ON" if cfg.get("enabled") else "OFF"}</code>',f'Branch • <code>{esc(str(cfg.get("branch",V106_DATA_SYNC_BRANCH)))}</code>',f'Last Sync • <code>{esc(str(cfg.get("last_sync","—")))}</code>',f'Last Restore • <code>{esc(str(cfg.get("last_restore","—")))}</code>',f'Result • <code>{esc(str(cfg.get("last_status","—")))}</code>',f'Conflict Guard • <code>ON</code>',f'Versions • <code>ON</code>']),parse_mode=ParseMode.HTML)

async def syncdata_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /syncdata USER_ID | PROJECT NAME'); return
    try: uid=int(f[0])
    except ValueError: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    found=find_project(uid,f[1])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    try: result=await asyncio.to_thread(github_data_sync_push,item); await update.effective_message.reply_text(f'✅ Data synced: {result}')
    except Exception as e: await update.effective_message.reply_text(f'❌ Data sync failed: {e}')

async def restoredata_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not owner_only(update): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /restoredata USER_ID | PROJECT NAME'); return
    try: uid=int(f[0])
    except ValueError: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    found=find_project(uid,f[1])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; was=item.running
    try:
        if was: kill_process(item)
        result=await asyncio.to_thread(github_data_sync_restore,item)
        if was and not project_locked(item): spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
        await update.effective_message.reply_text(f'✅ Data restore result: {result}')
    except Exception as e: await update.effective_message.reply_text(f'❌ Data restore failed: {e}')


async def envcheck_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context): return
    if not context.args: await update.effective_message.reply_text("Usage: /envcheck PROJECT"); return
    found=find_project(update.effective_user.id," ".join(context.args))
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found
    required=sorted(detect_required_env_vars(Path(item.folder)))
    configured=_active_project_env(item,Path(item.folder))
    missing=[k for k in required if not configured.get(k)]
    skipped=bool(project_settings.get(project_key(item),{}).get("env_setup_skipped",False))
    lines=[f"Project • <b>{esc(item.display_name)}</b>", f".env • <code>{'FOUND' if (Path(item.folder)/'.env').exists() else 'NOT FOUND'}</code>", f"ENV Guard • <code>{'SKIPPED' if skipped else 'ACTIVE'}</code>", f"Required • <code>{len(required)}</code>", f"Configured • <code>{len(configured)}</code>"]
    if required: lines.append("Required keys • " + ", ".join(f"<code>{esc(k)}</code>" for k in required[:20]))
    if missing and not skipped: lines += ["", "🚫 <b>START BLOCKED</b>", "Missing • " + ", ".join(f"<code>{esc(k)}</code>" for k in missing[:20]), "Add each with <code>/setenv PROJECT KEY VALUE</code> or use <code>/skipenv PROJECT</code>."]
    elif missing and skipped: lines += ["", "⏭ <b>ENV GUARD SKIPPED</b>", "Skipped • " + ", ".join(f"<code>{esc(k)}</code>" for k in missing[:20]), "Startup is allowed; manager secrets remain isolated."]
    else: lines += ["", "✅ ENV requirements are ready."]
    await update.effective_message.reply_text(premium_box("🔐 ᴇɴᴠ ɢᴜᴀʀᴅ",lines),parse_mode=ParseMode.HTML)


async def replacefile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /replacefile PROJECT NAME | PATH\nExample: /replacefile QURESHIxOTP Store | bot.py"); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; rel=f[1]
    if project_locked(item): await update.effective_message.reply_text("🔒 Project is locked by admin."); return
    try:
        target=safe_inside_project(item,rel)
        if _secret_project_path(target): raise ValueError("Secret/.env files must be managed through ENV commands")
    except Exception as e: await update.effective_message.reply_text(f"❌ {e}"); return
    v106_cfg().setdefault("pending_file_replacements",{})[str(update.effective_user.id)]={"owner_uid":update.effective_user.id,"project":item.display_name,"path":rel}; save_v7_data()
    await update.effective_message.reply_text(premium_box("📤 ʀᴇᴘʟᴀᴄᴇ ᴘʀᴏᴊᴇᴄᴛ ғɪʟᴇ",[f"Project • <b>{esc(item.display_name)}</b>",f"Target • <code>{esc(rel)}</code>",f"📎 Upload your new <b>{esc(Path(rel).name)}</b> file now.","💾 Previous file version is saved automatically.","🧪 Validation runs before restart.","✅ Other project data stays untouched."]),parse_mode=ParseMode.HTML)


async def replaceuserfile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_or_owner(update): return
    if len(context.args)<3: await update.effective_message.reply_text("Usage: /replaceuserfile USER_ID PROJECT PATH"); return
    try: owner_uid=int(context.args[0])
    except ValueError: await update.effective_message.reply_text("❌ Invalid user ID."); return
    found=find_project(owner_uid,context.args[1])
    if not found: await update.effective_message.reply_text("❌ Project not found for that user."); return
    _,item=found; rel=" ".join(context.args[2:])
    try:
        target=safe_inside_project(item,rel)
        if _secret_project_path(target): raise ValueError("Secret/.env files must be managed through ENV commands")
    except Exception as e: await update.effective_message.reply_text(f"❌ {e}"); return
    v106_cfg().setdefault("pending_file_replacements",{})[str(update.effective_user.id)]={"owner_uid":owner_uid,"project":item.display_name,"path":rel}
    save_v7_data()
    await update.effective_message.reply_text(premium_box("👑 ᴀᴅᴍɪɴ ғɪʟᴇ ʀᴇᴘʟᴀᴄᴇ",[f"User • <code>{owner_uid}</code>",f"Project • <b>{esc(item.display_name)}</b>",f"Target • <code>{esc(rel)}</code>",f"Upload the new <b>{esc(Path(rel).name)}</b> now.","Only this file will change; runtime data is preserved."]),parse_mode=ParseMode.HTML)


async def adminfiles_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_or_owner(update): return
    if len(context.args)<2: await update.effective_message.reply_text("Usage: /adminfiles USER_ID PROJECT [FOLDER]"); return
    try: owner_uid=int(context.args[0])
    except ValueError: await update.effective_message.reply_text("❌ Invalid user ID."); return
    found=find_project(owner_uid,context.args[1])
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; rel=" ".join(context.args[2:]) if len(context.args)>2 else "."
    try: folder=safe_inside_project(item,rel)
    except Exception as e: await update.effective_message.reply_text(f"❌ {e}"); return
    if not folder.is_dir(): await update.effective_message.reply_text("❌ Folder not found."); return
    rows=[]
    for x in sorted(folder.iterdir(),key=lambda z:(not z.is_dir(),z.name.lower()))[:60]:
        if x.name in {'.venv','node_modules','.git','__pycache__','.QURESHIxOTP_history','.QURESHIxOTP_data_sync'}: continue
        icon='📁' if x.is_dir() else ('🔐' if _secret_project_path(x) else '📄')
        rows.append(f"{icon} <code>{esc(str(x.relative_to(Path(item.folder))))}</code>")
    await update.effective_message.reply_text(premium_box("👑 ᴘʀᴏᴊᴇᴄᴛ ғɪʟᴇs",[f"User • <code>{owner_uid}</code>",f"Project • <b>{esc(item.display_name)}</b>",*rows] if rows else ["Folder is empty."]),parse_mode=ParseMode.HTML)


async def github_data_sync_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    for uid, items in list(running_scripts.items()):
        for item in list(items):
            cfg=data_sync_settings(item)
            if not cfg.get("enabled"):
                continue
            try:
                await asyncio.to_thread(github_data_sync_push,item)
            except Exception as exc:
                cfg["last_status"]=f"FAILED: {exc}"
                save_v7_data()
                logger.exception("GitHub Data Sync failed for %s",item.display_name)


# ═════════════════════════════════════════════════════════════════════════════
# V10.5 PREMIUM AUTOMATION / UX LAYER
# ═════════════════════════════════════════════════════════════════════════════

V105_EDITABLE_EXTS={'.py','.js','.mjs','.cjs','.json','.txt','.md','.yaml','.yml','.toml','.ini','.cfg','.php','.rb','.sh'}
V105_MAX_EDIT_BYTES=128*1024


def v105_cfg()->dict:
    return global_cfg().setdefault('v105',{})


def safe_inside_project(item:ScriptProcess, rel:str)->Path:
    root=Path(item.folder).resolve()
    candidate=(root/rel).resolve()
    if candidate!=root and root not in candidate.parents:
        raise ValueError('Path escapes project folder')
    if any(part in {'.venv','node_modules','.git','__pycache__','.QURESHIxOTP_history'} for part in candidate.relative_to(root).parts):
        raise ValueError('Protected/generated path is not editable')
    return candidate


def deployment_profile(item:ScriptProcess)->dict:
    cfg=project_settings.setdefault(project_key(item),{})
    return cfg.setdefault('deployment_profile',{
        'runtime': item.runtime,
        'entry': str(Path(item.entry_file).relative_to(Path(item.folder))) if item.entry_file and Path(item.entry_file).exists() else Path(item.entry_file).name,
        'install': 'auto',
        'start': 'auto',
        'branch': item.branch or 'main',
        'env_profile': 'default',
    })


def syntax_test_entry(entry:Path)->tuple[bool,str]:
    runtime=runtime_for_entry(entry)
    import subprocess as _sp
    if runtime=='python': cmd=[sys.executable,'-m','py_compile',str(entry)]
    elif runtime=='node':
        exe=shutil.which('node');
        if not exe: return False,'Node.js runtime is not installed'
        cmd=[exe,'--check',str(entry)]
    elif runtime=='php':
        exe=shutil.which('php');
        if not exe: return False,'PHP runtime is not installed'
        cmd=[exe,'-l',str(entry)]
    elif runtime=='ruby':
        exe=shutil.which('ruby');
        if not exe: return False,'Ruby runtime is not installed'
        cmd=[exe,'-c',str(entry)]
    elif runtime=='bash': cmd=['bash','-n',str(entry)]
    elif runtime=='java': return (entry.exists(), 'JAR detected' if entry.exists() else 'JAR missing')
    else: return False,f'Unsupported runtime: {runtime}'
    r=_sp.run(cmd,capture_output=True,text=True,timeout=25)
    msg=(r.stdout+r.stderr).strip()[-1800:] or ('Syntax OK' if r.returncode==0 else 'Validation failed')
    return r.returncode==0,msg


def mark_last_good(item:ScriptProcess)->str:
    snap=snapshot_project(item,'last_good')
    cfg=project_settings.setdefault(project_key(item),{})
    cfg['last_known_good']=snap
    cfg['last_known_good_at']=datetime.now(timezone.utc).isoformat()
    save_v7_data()
    return snap


def env_profiles(item:ScriptProcess)->dict:
    return project_settings.setdefault(project_key(item),{}).setdefault('env_profiles',{'default':{}})


def scheduled_actions()->list:
    return v105_cfg().setdefault('scheduled_actions',[])


def feature_flags_v105()->dict:
    defaults={'github_center':True,'file_manager':True,'code_editor':True,'env_profiles':True,'scheduled_actions':True,'import_export':True,'templates':True,'tickets':True,'referrals':True,'gift_tools':True}
    flags=v105_cfg().setdefault('features',{})
    for k,v in defaults.items(): flags.setdefault(k,v)
    return flags


async def deployprofile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text('Usage: /deployprofile PROJECT NAME'); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; d=deployment_profile(item); lines=[f'{k} • <code>{esc(str(v))}</code>' for k,v in d.items()]
    await update.effective_message.reply_text(premium_box('⚙️ ᴅᴇᴘʟᴏʏᴍᴇɴᴛ ᴘʀᴏғɪʟᴇ',lines),parse_mode=ParseMode.HTML)


async def predeploy_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text('Usage: /predeploy PROJECT'); return
    found=find_project(update.effective_user.id,' '.join(context.args))
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; entry=Path(item.entry_file)
    ok,msg=await asyncio.to_thread(syntax_test_entry,entry)
    title='✅ ᴘʀᴇ-ᴅᴇᴘʟᴏʏ ᴘᴀssᴇᴅ' if ok else '❌ ᴘʀᴇ-ᴅᴇᴘʟᴏʏ ғᴀɪʟᴇᴅ'
    await update.effective_message.reply_text(premium_box(title,[f'Project • <b>{esc(item.display_name)}</b>',f'Runtime • <code>{esc(item.runtime)}</code>',f'Result • <code>{esc(msg)}</code>']),parse_mode=ParseMode.HTML)


async def markgood_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text('Usage: /markgood PROJECT'); return
    found=find_project(update.effective_user.id,' '.join(context.args))
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; snap=await asyncio.to_thread(mark_last_good,item)
    await update.effective_message.reply_text(premium_box('💙 ʟᴀsᴛ ᴋɴᴏᴡɴ ɢᴏᴏᴅ',[f'Project • <b>{esc(item.display_name)}</b>',f'Snapshot • <code>{esc(snap)}</code>','✅ Marked as recovery deployment.']),parse_mode=ParseMode.HTML)


async def restoregood_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text('Usage: /restoregood PROJECT'); return
    found=find_project(update.effective_user.id,' '.join(context.args))
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; snap=project_settings.get(project_key(item),{}).get('last_known_good','')
    if not snap: await update.effective_message.reply_text('❌ No last-known-good snapshot saved.'); return
    try:
        await asyncio.to_thread(restore_snapshot,item,snap); record_deploy(item,'rollback','Last-known-good restore')
        await update.effective_message.reply_text('✅ Last-known-good deployment restored.')
    except Exception as e: await update.effective_message.reply_text(f'❌ Restore failed: {e}')


async def githubcenter_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    uid=update.effective_user.id; rows=[x for x in scripts_for(uid) if x.source_type=='github']
    token='CONFIGURED' if github_token_for(uid) else 'NOT SET'
    lines=[f'🔐 Token • <code>{token}</code>',f'📦 Connected Repos • <code>{len(rows)}</code>']
    for x in rows[:15]:
        cfg=project_settings.get(project_key(x),{})
        lines.append(f'• <b>{esc(x.display_name)}</b> • <code>{esc(x.branch)}</code> • <code>{esc((x.commit_sha or "")[:8] or "—")}</code> • Auto <code>{"ON" if cfg.get("github_autodeploy") else "OFF"}</code>')
    kb=InlineKeyboardMarkup([[InlineKeyboardButton('🐙 My Repos',callback_data='project:list')],[InlineKeyboardButton('🔐 Token Status',callback_data='v105:token')]])
    await update.effective_message.reply_text(premium_box('🐙 ɢɪᴛʜᴜʙ ᴄᴇɴᴛᴇʀ',lines or ['No connected repositories.']),parse_mode=ParseMode.HTML,reply_markup=kb)


async def deploycommit_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /deploycommit PROJECT NAME | COMMIT_SHA'); return
    found=find_project(update.effective_user.id,f[0]); ref=f[1]
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked.'); return
    if item.source_type!='github': await update.effective_message.reply_text('❌ Not a GitHub project.'); return
    msg=await update.effective_message.reply_text('🐙 Deploying selected commit…'); root=Path(item.folder); staging=root.parent/(root.name+'_commit_stage')
    try:
        token=github_token_for(update.effective_user.id); shutil.rmtree(staging,ignore_errors=True); github_archive_download(item.repo_url,ref,staging,token); entry=detect_entry(staging)
        if not entry: raise RuntimeError('No supported entry')
        ok,why=syntax_test_entry(entry)
        if not ok: raise RuntimeError(why)
        snapshot_project(item,'pre_commit'); was=item.running
        if was: kill_process(item)
        for child in list(root.iterdir()):
            if child.name in {'.venv','node_modules','.git','.QURESHIxOTP_history','.QURESHIxOTP_data_sync','.QURESHIxOTP_file_history','runtime.log'}: continue
            if child.is_dir(): shutil.rmtree(child,ignore_errors=True)
            else: child.unlink(missing_ok=True)
        for child in staging.iterdir(): shutil.move(str(child),root/child.name)
        shutil.rmtree(staging,ignore_errors=True); entry=detect_entry(root); item.entry_file=str(entry); item.runtime=runtime_for_entry(entry); item.commit_sha=ref
        install_project_dependencies(root,entry,Path(item.log_path)) if v10_flags()['dependencies'] else None
        if was: spawn_script(item,entry,root,Path(item.log_path))
        mark_last_good(item); record_deploy(item,'success',f'Commit {ref[:10]}'); save_projects(); await msg.edit_text('✅ Specific commit deployed and marked last-known-good.')
    except Exception as e: shutil.rmtree(staging,ignore_errors=True); await msg.edit_text(f'❌ Commit deploy failed: {e}')


async def filemanager_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update); project=f[0] if f else command_payload(update); rel=f[1] if len(f)>1 else '.'
    if not project: await update.effective_message.reply_text('Usage: /filemanager PROJECT NAME | folder(optional)'); return
    found=find_project(update.effective_user.id,project)
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    try: folder=safe_inside_project(item,rel)
    except Exception as e: await update.effective_message.reply_text(f'❌ {e}'); return
    if not folder.exists() or not folder.is_dir(): await update.effective_message.reply_text('❌ Folder not found.'); return
    rows=[]
    for x in sorted(folder.iterdir(),key=lambda z:(not z.is_dir(),z.name.lower()))[:60]:
        if x.name in {'.venv','node_modules','.git','__pycache__','.QURESHIxOTP_history','.QURESHIxOTP_data_sync','.QURESHIxOTP_file_history'}: continue
        icon='📁' if x.is_dir() else '📄'; size='' if x.is_dir() else f' • {x.stat().st_size/1024:.1f} KB'; rows.append(f'{icon} <code>{esc(str(x.relative_to(Path(item.folder))))}</code>{size}')
    await update.effective_message.reply_text(premium_box('📁 ғɪʟᴇ ᴍᴀɴᴀɢᴇʀ',[f'Project • <b>{esc(item.display_name)}</b>',f'Folder • <code>{esc(rel)}</code>',*rows] if rows else ['Folder is empty.']),parse_mode=ParseMode.HTML)


async def viewfile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /viewfile PROJECT NAME | PATH'); return
    found=find_project(update.effective_user.id,f[0]); rel=f[1]
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    try: x=safe_inside_project(item,rel)
    except Exception as e: await update.effective_message.reply_text(f'❌ {e}'); return
    if not x.is_file(): await update.effective_message.reply_text('❌ File not found.'); return
    if _secret_project_path(x): await update.effective_message.reply_text('🔐 Secret/.env files cannot be previewed.'); return
    if x.stat().st_size>V105_MAX_EDIT_BYTES: await update.effective_message.reply_text('⚠️ File too large. Use /downloadfile.'); return
    await update.effective_message.reply_text(premium_box('📄 ғɪʟᴇ ᴠɪᴇᴡ',[f'Path • <code>{esc(rel)}</code>',f'<pre>{esc(x.read_text(errors="replace")[:3500])}</pre>']),parse_mode=ParseMode.HTML)


async def downloadfile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /downloadfile PROJECT NAME | PATH'); return
    found=find_project(update.effective_user.id,f[0]); rel=f[1]
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    try: x=safe_inside_project(item,rel)
    except Exception as e: await update.effective_message.reply_text(f'❌ {e}'); return
    if not x.is_file() or _secret_project_path(x): await update.effective_message.reply_text('❌ File unavailable/secret.'); return
    await send_real_file(context.bot,update.effective_chat.id,x,f'📄 {item.display_name} • {rel}')


async def renamefile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<3: await update.effective_message.reply_text('Usage: /renamefile PROJECT NAME | OLD_PATH | NEW_PATH'); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked by admin.'); return
    try: old=safe_inside_project(item,f[1]); new=safe_inside_project(item,f[2]); save_file_version(item,f[1]); new.parent.mkdir(parents=True,exist_ok=True); old.rename(new); audit(update.effective_user.id,'rename_file',item.display_name,f'{f[1]} -> {f[2]}')
    except Exception as e: await update.effective_message.reply_text(f'❌ Rename failed: {e}'); return
    await update.effective_message.reply_text('✅ File renamed.')


async def deletefile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<3 or f[2].upper()!='CONFIRM': await update.effective_message.reply_text('Usage: /deletefile PROJECT NAME | PATH | CONFIRM'); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked by admin.'); return
    try: x=safe_inside_project(item,f[1]); save_file_version(item,f[1]); x.unlink(); audit(update.effective_user.id,'delete_file',item.display_name,f[1])
    except Exception as e: await update.effective_message.reply_text(f'❌ Delete failed: {e}'); return
    await update.effective_message.reply_text('✅ File deleted. Previous version remains in file history.')


async def editfile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /editfile PROJECT NAME | PATH'); return
    found=find_project(update.effective_user.id,f[0]); rel=f[1]
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked by admin.'); return
    try: x=safe_inside_project(item,rel)
    except Exception as e: await update.effective_message.reply_text(f'❌ {e}'); return
    if _secret_project_path(x): await update.effective_message.reply_text('🔐 Secret/.env files use ENV Wizard.'); return
    if x.suffix.lower() not in V105_EDITABLE_EXTS: await update.effective_message.reply_text('❌ File type not allowed in Telegram editor.'); return
    v105_cfg().setdefault('pending_edits',{})[str(update.effective_user.id)]={'project':item.display_name,'path':rel}; save_v7_data(); await update.effective_message.reply_text(premium_box('✏️ ᴄᴏᴅᴇ ᴇᴅɪᴛᴏʀ',[f'Project • <b>{esc(item.display_name)}</b>',f'File • <code>{esc(rel)}</code>','Send COMPLETE replacement text next.','💾 Old version is saved automatically.']),parse_mode=ParseMode.HTML)


async def canceledit_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    v105_cfg().setdefault('pending_edits',{}).pop(str(update.effective_user.id),None); save_v7_data(); await update.effective_message.reply_text('✅ Pending edit cancelled.')


async def envprofile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /envprofile PROJECT NAME | list OR use NAME OR set NAME KEY VALUE OR delete NAME'); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; tail=f[1].split(); profiles=env_profiles(item); cfg=project_settings.setdefault(project_key(item),{})
    if not tail: await update.effective_message.reply_text('❌ Missing action.'); return
    action=tail[0].lower()
    if action=='list': lines=[f'• <code>{esc(k)}</code> — {len(v)} secret(s)' for k,v in profiles.items()] or ['No profiles.']
    elif action=='use' and len(tail)>=2:
        name=tail[1]
        if name not in profiles: await update.effective_message.reply_text('❌ Profile not found.'); return
        cfg['active_env_profile']=name; cfg['env']=dict(profiles[name]); save_v7_data(); lines=[f'✅ Active profile • <code>{esc(name)}</code>']
    elif action=='delete' and len(tail)>=2:
        name=tail[1]
        if name=='default': await update.effective_message.reply_text('❌ Default profile cannot be deleted.'); return
        profiles.pop(name,None); save_v7_data(); lines=[f'✅ Deleted profile <code>{esc(name)}</code>.']
    elif action=='set' and len(tail)>=4:
        name,key=tail[1],tail[2]; value=' '.join(tail[3:]); profiles.setdefault(name,{})[key]=value; save_v7_data(); lines=[f'✅ Saved <code>{esc(key)}</code> in <code>{esc(name)}</code>.']
    else: lines=['Invalid ENV profile action.']
    await update.effective_message.reply_text(premium_box('🔐 ᴇɴᴠ ᴘʀᴏғɪʟᴇs',lines),parse_mode=ParseMode.HTML)


async def rotateenv_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<3: await update.effective_message.reply_text('Usage: /rotateenv PROJECT NAME | KEY | NEW_VALUE'); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked.'); return
    key,value=f[1],f[2]; project_envs.setdefault(project_key(item),{})[key]=value; project_settings.setdefault(project_key(item),{}).setdefault('env',{})[key]=value; save_v7_data(); _rewrite_generated_env(item)
    if item.running: kill_process(item); spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
    await update.effective_message.reply_text('✅ Secret rotated and project restarted. Value remains masked.')


async def scheduleaction_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<3: await update.effective_message.reply_text('Usage: /scheduleaction PROJECT NAME | restart|backup|sync | 6h'); return
    found=find_project(update.effective_user.id,f[0]); action=f[1].lower()
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    if action not in {'restart','backup','sync'}: await update.effective_message.reply_text('❌ Actions: restart, backup, sync'); return
    try: interval=parse_interval_seconds(f[2])
    except Exception as e: await update.effective_message.reply_text(f'❌ {e}'); return
    _,item=found; rows=scheduled_actions(); rows[:]=[r for r in rows if not (r.get('uid')==update.effective_user.id and r.get('project')==item.display_name and r.get('action')==action)]; rows.append({'uid':update.effective_user.id,'project':item.display_name,'action':action,'interval':interval,'next':time.time()+interval}); save_v7_data(); await update.effective_message.reply_text(f'✅ Scheduled {action} every {f[2]} for {item.display_name}.')


async def schedules_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    rows=[r for r in scheduled_actions() if r.get('uid')==update.effective_user.id]
    lines=[f'• <b>{esc(r["project"])}</b> • <code>{r["action"]}</code> every <code>{r["interval"]}s</code>' for r in rows]
    await update.effective_message.reply_text(premium_box('⏰ sᴄʜᴇᴅᴜʟᴇᴅ ᴀᴄᴛɪᴏɴs',lines or ['No scheduled actions.']),parse_mode=ParseMode.HTML)


async def unscheduleaction_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if len(context.args)<2: await update.effective_message.reply_text('Usage: /unscheduleaction PROJECT ACTION'); return
    before=len(scheduled_actions()); scheduled_actions()[:]=[r for r in scheduled_actions() if not (r.get('uid')==update.effective_user.id and r.get('project')==context.args[0] and r.get('action')==context.args[1].lower())]; save_v7_data()
    await update.effective_message.reply_text(f'✅ Removed {before-len(scheduled_actions())} schedule(s).')


async def scheduled_actions_job(context:ContextTypes.DEFAULT_TYPE)->None:
    now=time.time(); changed=False
    for r in list(scheduled_actions()):
        if now<float(r.get('next',0)): continue
        found=find_project(int(r.get('uid',0)),str(r.get('project','')))
        if not found: r['next']=now+int(r.get('interval',3600)); changed=True; continue
        _,item=found; action=r.get('action')
        try:
            if action=='restart':
                if item.running: kill_process(item)
                spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
            elif action=='backup':
                out=await asyncio.to_thread(create_project_backup_file,int(r['uid']),item)
                await send_real_file(context.bot,int(r['uid']),Path(out),f'💾 Scheduled backup • {item.display_name}')
            elif action=='sync' and item.source_type=='github': await asyncio.to_thread(sync_github_item,item)
        except Exception: logger.exception('Scheduled action failed: %s',r)
        r['next']=now+int(r.get('interval',3600)); changed=True
    if changed: save_v7_data()


async def depsnapshot_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /depsnapshot PROJECT NAME | SNAPSHOT_NAME'); return
    found=find_project(update.effective_user.id,f[0]); name=clean_project_name(f[1])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; root=Path(item.folder); d=root/'.QURESHIxOTP_dependency_profiles'; d.mkdir(exist_ok=True)
    if item.runtime=='python':
        req=root/'requirements.txt'; (d/f'{name}.requirements.txt').write_text(req.read_text(errors='replace') if req.exists() else '')
    elif item.runtime=='node':
        for fn in ('package.json','package-lock.json'):
            if (root/fn).exists(): shutil.copy2(root/fn,d/f'{name}.{fn}')
    else: await update.effective_message.reply_text('ℹ️ Dependency snapshots support Python/Node.'); return
    await update.effective_message.reply_text('✅ Dependency profile saved.')


async def deprestore_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /deprestore PROJECT NAME | SNAPSHOT_NAME'); return
    found=find_project(update.effective_user.id,f[0]); name=clean_project_name(f[1])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; root=Path(item.folder); d=root/'.QURESHIxOTP_dependency_profiles'
    try:
        if item.runtime=='python': shutil.copy2(d/f'{name}.requirements.txt',root/'requirements.txt')
        elif item.runtime=='node':
            if (d/f'{name}.package.json').exists(): shutil.copy2(d/f'{name}.package.json',root/'package.json')
            if (d/f'{name}.package-lock.json').exists(): shutil.copy2(d/f'{name}.package-lock.json',root/'package-lock.json')
        else: raise RuntimeError('Unsupported runtime')
        await asyncio.to_thread(install_project_dependencies,root,Path(item.entry_file),Path(item.log_path)); await update.effective_message.reply_text('✅ Dependency profile restored and installed.')
    except Exception as e: await update.effective_message.reply_text(f'❌ Restore failed: {e}')


async def exportproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    if not context.args: await update.effective_message.reply_text('Usage: /exportproject PROJECT'); return
    found=find_project(update.effective_user.id,' '.join(context.args))
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found; out=Path(item.folder).parent/f'{clean_project_name(item.display_name)}_QURESHIxOTP_Export.zip'
    root=Path(item.folder)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        export_settings=dict(project_settings.get(project_key(item),{})); export_settings.pop('env',None); export_settings.pop('env_profiles',None); meta={'name':item.display_name,'runtime':item.runtime,'entry':str(Path(item.entry_file).relative_to(root)),'settings':export_settings,'secrets_included':False}
        z.writestr('QURESHIxOTP-project.json',json.dumps(meta,indent=2,default=str))
        for f in root.rglob('*'):
            if f.is_file() and not any(x in f.parts for x in ('.venv','node_modules','.git','__pycache__','.QURESHIxOTP_history')) and f.name!='runtime.log': z.write(f,'source/'+str(f.relative_to(root)))
    await send_real_file(context.bot,update.effective_chat.id,out,f'📦 Portable QURESHIxOTP export • {item.display_name}'); out.unlink(missing_ok=True)


async def importproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    v105_cfg().setdefault('pending_imports',{})[str(update.effective_user.id)]=True; save_v7_data()
    await update.effective_message.reply_text('📥 Send the QURESHIxOTP project export ZIP now. The import will create a new project.')


async def features_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    flags=feature_flags_v105(); lines=[f'{"🟢" if v else "🔴"} {k} • <code>{"ON" if v else "OFF"}</code>' for k,v in flags.items()]
    await update.effective_message.reply_text(premium_box('✨ ᴘʟᴀᴛғᴏʀᴍ ғᴇᴀᴛᴜʀᴇs',lines),parse_mode=ParseMode.HTML)


async def feature_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    if len(context.args)<2: await update.effective_message.reply_text('Usage: /feature NAME on|off'); return
    name=context.args[0].lower(); mode=context.args[1].lower(); flags=feature_flags_v105()
    if name not in flags or mode not in {'on','off'}: await update.effective_message.reply_text('❌ Unknown feature/mode. Use /features.'); return
    flags[name]=(mode=='on'); save_v7_data(); await update.effective_message.reply_text(f'✅ {name} = {mode.upper()}')


async def usercenter_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    if not context.args: await update.effective_message.reply_text('Usage: /usercenter USER_ID'); return
    try: uid=int(context.args[0])
    except: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    st=user_stats.get(str(uid),{}); items=scripts_for(uid); notes=global_cfg().get('user_notes',{}).get(str(uid),[]); warns=global_cfg().get('warnings',{}).get(str(uid),[])
    lines=[f'🆔 ID • <code>{uid}</code>',f'👤 Name • <b>{esc(st.get("name","Unknown"))}</b>',f'💎 Plan • <code>{esc(plan_name(uid))}</code>',f'💳 Credits • <code>{get_credits(uid)}</code>',f'🚀 Projects • <code>{len(items)}</code>',f'⚠️ Warnings • <code>{len(warns)}</code>',f'📝 Notes • <code>{len(notes)}</code>',f'🎫 Tickets • <code>{sum(1 for t in global_cfg().get("tickets",[]) if int(t.get("user_id",0))==uid and t.get("status")!="closed")}</code>']
    kb=InlineKeyboardMarkup([[InlineKeyboardButton('🚀 Projects',callback_data='admin:processes'),InlineKeyboardButton('📊 Analytics',callback_data='admin:analytics')],[InlineKeyboardButton('⬅️ Admin',callback_data='admin:overview')]])
    await update.effective_message.reply_text(premium_box('👤 ᴜsᴇʀ ᴅᴇᴛᴀɪʟ ᴄᴇɴᴛᴇʀ',lines),parse_mode=ParseMode.HTML,reply_markup=kb)


async def transferproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    if len(context.args)<2: await update.effective_message.reply_text('Usage: /transferproject PROJECT NEW_USER_ID'); return
    name=context.args[0]
    try: new_uid=int(context.args[1])
    except: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    found=None; old_uid=None
    for uid,items in running_scripts.items():
        for i,x in enumerate(items):
            if x.display_name.lower()==name.lower(): found=(i,x); old_uid=uid; break
        if found: break
    if not found: await update.effective_message.reply_text('❌ Project not found globally.'); return
    i,item=found; running_scripts[old_uid].pop(i); running_scripts.setdefault(new_uid,[]).append(item); save_projects(); await update.effective_message.reply_text(f'✅ Project transferred from {old_uid} to {new_uid}.')


async def bulkproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    if len(context.args)<2: await update.effective_message.reply_text('Usage: /bulkproject stop|restart USER_ID|all'); return
    action,target=context.args[0].lower(),context.args[1].lower()
    if action not in {'stop','restart'}: await update.effective_message.reply_text('❌ Actions: stop, restart'); return
    targets=[]
    for uid,items in running_scripts.items():
        if target!='all' and str(uid)!=target: continue
        targets.extend(items)
    done=0
    for item in targets:
        try:
            if item.running: kill_process(item)
            if action=='restart': spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
            done+=1
        except Exception: logger.exception('bulkproject failed')
    await update.effective_message.reply_text(f'✅ {action.title()} applied to {done} project(s).')


async def announcement_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    if not context.args:
        cur=v105_cfg().get('announcement',''); await update.effective_message.reply_text(premium_box('📢 ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ',[esc(cur) if cur else 'No announcement set.']),parse_mode=ParseMode.HTML); return
    if context.args[0].lower()=='clear': v105_cfg()['announcement']=''; save_v7_data(); await update.effective_message.reply_text('✅ Announcement cleared.'); return
    text=' '.join(context.args[1:] if context.args[0].lower()=='set' else context.args); v105_cfg()['announcement']=text; save_v7_data(); await update.effective_message.reply_text('✅ Announcement published.')


async def loyalty_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    uid=update.effective_user.id; st=user_stats.get(str(uid),{}); referrals=global_cfg().get('referrals',{}).get(str(uid),[]); projects=len(scripts_for(uid)); score=min(100,projects*5+len(referrals)*10+10)
    await update.effective_message.reply_text(premium_box('🏆 ʟᴏʏᴀʟᴛʏ',[f'Score • <code>{score}/100</code>',f'Projects • <code>{projects}</code>',f'Referrals • <code>{len(referrals)}</code>','Rewards are controlled by admin campaigns/redeem codes.']),parse_mode=ParseMode.HTML)


async def campaign_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    campaigns=v105_cfg().setdefault('campaigns',{})
    if not context.args:
        lines=[f'• <code>{esc(k)}</code> — {esc(v.get("note",""))}' for k,v in campaigns.items()]; await update.effective_message.reply_text(premium_box('🎯 ᴄᴀᴍᴘᴀɪɢɴs',lines or ['No campaigns.']),parse_mode=ParseMode.HTML); return
    action=context.args[0].lower()
    if action=='create' and len(context.args)>=3:
        name=context.args[1]; campaigns[name]={'note':' '.join(context.args[2:]),'created':datetime.now(timezone.utc).isoformat(),'enabled':True}; save_v7_data(); await update.effective_message.reply_text('✅ Campaign created.')
    elif action=='delete' and len(context.args)>=2: campaigns.pop(context.args[1],None); save_v7_data(); await update.effective_message.reply_text('✅ Campaign deleted.')
    else: await update.effective_message.reply_text('Usage: /campaign create NAME NOTE | /campaign delete NAME')


async def setupwizard_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /setup PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    idx,item=found
    await update.effective_message.reply_text(premium_box("🧙 sᴍᴀʀᴛ sᴇᴛᴜᴘ",setup_summary(item)),parse_mode=ParseMode.HTML,reply_markup=env_wizard_keyboard(idx,item))

async def envwizard_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /envwizard PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    idx,item=found; present,missing=required_env_summary(item)
    lines=[f"Project • <b>{esc(item.display_name)}</b>",f"✅ Added • <code>{len(present)}</code>",f"❌ Missing • <code>{len(missing)}</code>"]+[f"• <code>{esc(x)}</code>" for x in missing[:12]]
    await update.effective_message.reply_text(premium_box("🔐 ᴇɴᴠ ᴡɪᴢᴀʀᴅ",lines),parse_mode=ParseMode.HTML,reply_markup=env_wizard_keyboard(idx,item))

async def skipenv_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /skipenv PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; cfg=project_settings.setdefault(project_key(item),{}); _,missing=required_env_summary(item)
    cfg['env_setup_skipped']=True; cfg['env_blocked']=False; save_v7_data()
    lines=[f"Project • <b>{esc(item.display_name)}</b>","⏭ ENV setup skipped.","🚀 Start is now allowed.","🛡 QURESHIxOTP Host BOT_TOKEN/GITHUB_TOKEN/secrets remain isolated."]
    if missing: lines += ["", "⚠️ Skipped detected variables • "+", ".join(f"<code>{esc(x)}</code>" for x in missing[:12]), "Project can still fail if its code truly requires them."]
    await update.effective_message.reply_text(premium_box("⏭ ᴇɴᴠ sᴋɪᴘᴘᴇᴅ",lines),parse_mode=ParseMode.HTML)

async def newfile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /newfile PROJECT NAME | path/to/file.txt"); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text("🔒 Project is locked by admin."); return
    try:
        target=safe_inside_project(item,f[1]);
        if _secret_project_path(target): raise ValueError("Secret/.env files are managed through ENV Wizard")
        if target.exists(): raise ValueError("File already exists")
        target.parent.mkdir(parents=True,exist_ok=True); target.write_text("",encoding="utf-8"); audit(update.effective_user.id,"new_file",item.display_name,f[1])
        await update.effective_message.reply_text(f"✅ Created <code>{esc(f[1])}</code>.",parse_mode=ParseMode.HTML)
    except Exception as e: await update.effective_message.reply_text(f"❌ {e}")

async def newfolder_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /newfolder PROJECT NAME | path/to/folder"); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text("🔒 Project is locked by admin."); return
    try: d=safe_inside_project(item,f[1]); d.mkdir(parents=True,exist_ok=False); await update.effective_message.reply_text("✅ Folder created.")
    except Exception as e: await update.effective_message.reply_text(f"❌ {e}")

async def filehistory_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /filehistory PROJECT NAME | bot.py"); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; rows=load_file_versions(item,f[1]); lines=[f"• <code>{r['id']}</code> • {esc(r['saved_at'])}" for r in rows[-10:]]
    await update.effective_message.reply_text(premium_box("💾 ғɪʟᴇ ᴠᴇʀsɪᴏɴs",[f"File • <code>{esc(f[1])}</code>",*lines] if lines else ["No previous versions saved."]),parse_mode=ParseMode.HTML)

async def undofile_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /undofile PROJECT NAME | bot.py | VERSION(optional)"); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text("🔒 Project is locked by admin."); return
    rows=load_file_versions(item,f[1]); target_row=next((r for r in rows if len(f)>=3 and r['id']==f[2]),None) if len(f)>=3 else (rows[-1] if rows else None)
    if not target_row: await update.effective_message.reply_text("❌ Version not found."); return
    try:
        target=safe_inside_project(item,f[1]); src=file_history_dir(item,f[1])/target_row['file'];
        if target.exists(): save_file_version(item,f[1])
        shutil.copy2(src,target); ok,why=syntax_test_entry(target) if target.suffix.lower() in V105_EDITABLE_EXTS else (True,"Restored")
        if not ok: raise RuntimeError(why)
        await update.effective_message.reply_text("✅ Previous file version restored.")
    except Exception as e: await update.effective_message.reply_text(f"❌ Restore failed: {e}")

async def testproject_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /testproject PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; ok,why=syntax_test_entry(Path(item.entry_file)); ready,missing=ensure_project_env_ready(item,Path(item.folder))
    lines=[f"Project • <b>{esc(item.display_name)}</b>",f"Syntax • <code>{'PASS' if ok else 'FAIL'}</code>",f"ENV • <code>{'READY' if ready else 'MISSING'}</code>",f"Detail • <code>{esc(why)[:500]}</code>"]
    if missing: lines.append("Missing • "+", ".join(f"<code>{esc(x)}</code>" for x in missing))
    await update.effective_message.reply_text(premium_box("🧪 ᴘʀᴇ-ʀᴇsᴛᴀʀᴛ ᴛᴇsᴛ",lines),parse_mode=ParseMode.HTML)

async def timeline_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /timeline PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; rows=[r for r in audit_log if str(r.get('target','')).casefold()==item.display_name.casefold() or item.display_name.casefold() in str(r.get('detail','')).casefold()]
    lines=[f"• <code>{esc(str(r.get('time','')))}</code> • <b>{esc(str(r.get('action','')))}</b>" for r in rows[-15:]]
    await update.effective_message.reply_text(premium_box("📋 ᴘʀᴏᴊᴇᴄᴛ ᴛɪᴍᴇʟɪɴᴇ",lines or ["No timeline events yet."]),parse_mode=ParseMode.HTML)

async def errorcenter_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /errorcenter PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; lp=Path(item.log_path); text=lp.read_text(errors='replace')[-12000:] if lp.exists() else ''
    await update.effective_message.reply_text(premium_box("🔎 sᴍᴀʀᴛ ᴇʀʀᴏʀ ᴄᴇɴᴛᴇʀ",[f"Project • <b>{esc(item.display_name)}</b>",*detailed_diagnosis(text)]),parse_mode=ParseMode.HTML)

async def projectnotify_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<3: await update.effective_message.reply_text("Usage: /projectnotify PROJECT | crash|restart|github|datasync|backup|env | on|off"); return
    found=find_project(update.effective_user.id,f[0]); event=f[1].lower(); val=f[2].lower()
    if not found or event not in V107_NOTIFY_EVENTS or val not in {'on','off'}: await update.effective_message.reply_text("❌ Invalid project/event/value."); return
    _,item=found; project_notification_settings(item)[event]=val=='on'; save_v7_data(); await update.effective_message.reply_text(f"✅ {event} notifications {'enabled' if val=='on' else 'disabled'}.")

async def dependencies_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update)
    if not name: await update.effective_message.reply_text("Usage: /dependencies PROJECT NAME"); return
    found=find_project(update.effective_user.id,name)
    if not found: await update.effective_message.reply_text("❌ Project not found."); return
    _,item=found; root=Path(item.folder); lines=[f"Runtime • <code>{esc(item.runtime)}</code>"]
    if item.runtime=='python':
        req=root/'requirements.txt'; lines += ["<pre>"+esc(req.read_text(errors='replace')[:3500])+"</pre>" if req.exists() else 'No requirements.txt']
    elif item.runtime=='node':
        pkg=root/'package.json'; lines += ["<pre>"+esc(pkg.read_text(errors='replace')[:3500])+"</pre>" if pkg.exists() else 'No package.json']
    else: lines.append('Dependency UI currently supports Python/Node.')
    await update.effective_message.reply_text(premium_box("📦 ᴅᴇᴘᴇɴᴅᴇɴᴄɪᴇs",lines),parse_mode=ParseMode.HTML)

def _safe_pkg(raw:str)->str:
    raw=raw.strip()
    if not re.fullmatch(r"[@A-Za-z0-9_.\-/\[\]<>=!~^:+]+",raw): raise ValueError('Invalid package spec')
    return raw

async def depadd_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text("Usage: /depadd PROJECT NAME | package"); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked.'); return
    try:
        pkg=_safe_pkg(f[1]); root=Path(item.folder)
        if item.runtime=='python':
            py=root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python');
            if not py.exists(): subprocess.run([sys.executable,'-m','venv',str(root/'.venv')],check=True,timeout=60)
            r=await asyncio.to_thread(subprocess.run,[str(py),'-m','pip','install','--disable-pip-version-check','--no-input',pkg],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=V107_DEP_TIMEOUT)
            if r.returncode: raise RuntimeError(r.stdout.decode(errors='replace')[-1200:])
        elif item.runtime=='node':
            npm=shutil.which('npm');
            if not npm: raise RuntimeError('npm is not installed on this host')
            r=await asyncio.to_thread(subprocess.run,[npm,'install',pkg,'--save'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=V107_DEP_TIMEOUT)
            if r.returncode: raise RuntimeError(r.stdout.decode(errors='replace')[-1200:])
        else: raise RuntimeError('Dependency manager supports Python/Node')
        await update.effective_message.reply_text(f"✅ Installed <code>{esc(pkg)}</code>.",parse_mode=ParseMode.HTML)
    except Exception as e: await update.effective_message.reply_text(f"❌ Install failed: {e}")

async def regenrequirements_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    name=command_payload(update); found=find_project(update.effective_user.id,name) if name else None
    if not found: await update.effective_message.reply_text('Usage: /regenrequirements PROJECT NAME'); return
    _,item=found; root=Path(item.folder)
    if item.runtime!='python': await update.effective_message.reply_text('❌ Python projects only.'); return
    py=root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not py.exists(): await update.effective_message.reply_text('❌ Project virtual environment not found.'); return
    r=await asyncio.to_thread(subprocess.run,[str(py),'-m','pip','freeze'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
    if r.returncode: await update.effective_message.reply_text('❌ pip freeze failed.'); return
    req=root/'requirements.txt';
    if req.exists(): save_file_version(item,'requirements.txt')
    req.write_bytes(r.stdout); await update.effective_message.reply_text('✅ requirements.txt regenerated from project venv.')

async def syncpreview_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    f=pipe_fields(update)
    if len(f)<2:
        await update.effective_message.reply_text('Usage: /syncpreview USER_ID | PROJECT NAME'); return
    try: uid=int(f[0])
    except ValueError: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    item=admin_project_lookup(uid,f[1])
    if not item: await update.effective_message.reply_text('❌ Project not found.'); return
    files=_runtime_data_files(item); digest=local_data_digest(item); st=data_sync_settings(item)
    lines=[f"Project • <b>{esc(item.display_name)}</b>",f"Files detected • <code>{len(files)}</code>",f"Local digest • <code>{digest[:16]}</code>",f"Last sync • <code>{esc(str(st.get('last_sync','—')))}</code>"]+[f"{'M' if st.get('last_local_digest') else '+'} <code>{esc(str(x.relative_to(Path(item.folder))))}</code>" for x in files[:20]]
    await update.effective_message.reply_text(premium_box('☁️ ᴅᴀᴛᴀ sʏɴᴄ ᴘʀᴇᴠɪᴇᴡ',lines),parse_mode=ParseMode.HTML)

async def dataversions_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /dataversions USER_ID | PROJECT NAME'); return
    try: uid=int(f[0])
    except: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    item=admin_project_lookup(uid,f[1]);
    if not item: await update.effective_message.reply_text('❌ Project not found.'); return
    token=github_token_for(uid); st=data_sync_settings(item); branch=str(st.get('branch') or V106_DATA_SYNC_BRANCH); owner,repo=_ensure_private_data_branch(item,token,branch); path=data_remote_base(item)+'/versions'
    api=f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path,safe='/')}?ref={urllib.parse.quote(branch,safe='')}"
    try: rows=_github_request('GET',api,token)
    except Exception as e: await update.effective_message.reply_text(f'❌ Could not list versions: {e}'); return
    if not isinstance(rows,list): rows=[]
    lines=[f"• <code>{esc(str(x.get('name','')))}</code>" for x in rows[-V107_DATA_VERSION_LIMIT:]]
    await update.effective_message.reply_text(premium_box('🕘 ᴅᴀᴛᴀ ʙᴀᴄᴋᴜᴘ ᴠᴇʀsɪᴏɴs',lines or ['No versions yet.']),parse_mode=ParseMode.HTML)

async def projectexplorer_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not admin_or_owner(update): await update.effective_message.reply_text('❌ Admin only.'); return
    f=pipe_fields(update)
    if not f:
        await update.effective_message.reply_text('Usage: /projectexplorer USER_ID | PROJECT(optional)'); return
    try: uid=int(f[0])
    except: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    if len(f)==1 or not f[1]:
        lines=[f"• <b>{esc(x.display_name)}</b> • <code>{'ONLINE' if x.running else 'OFFLINE'}</code>" for x in scripts_for(uid)]
        await update.effective_message.reply_text(premium_box('🧭 ᴘʀᴏᴊᴇᴄᴛ ᴇxᴘʟᴏʀᴇʀ',[f'User • <code>{uid}</code>',*lines] if lines else ['No projects.']),parse_mode=ParseMode.HTML); return
    item=admin_project_lookup(uid,f[1])
    if not item: await update.effective_message.reply_text('❌ Project not found.'); return
    present,missing=required_env_summary(item); st=data_sync_settings(item)
    await update.effective_message.reply_text(premium_box('🧭 ᴘʀᴏᴊᴇᴄᴛ ᴇxᴘʟᴏʀᴇʀ',[f'User • <code>{uid}</code>',f'Project • <b>{esc(item.display_name)}</b>',f'Status • <code>{"ONLINE" if item.running else "OFFLINE"}</code>',f'Runtime • <code>{esc(item.runtime)}</code>',f'ENV missing • <code>{len(missing)}</code>',f'GitHub • <code>{"CONNECTED" if item.repo_url else "NO"}</code>',f'Data Sync • <code>{"ON" if st.get("enabled") else "OFF"}</code>',f'Locked • <code>{"YES" if project_locked(item) else "NO"}</code>']),parse_mode=ParseMode.HTML)

async def projectlock_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not admin_or_owner(update): await update.effective_message.reply_text('❌ Admin only.'); return
    f=pipe_fields(update)
    if len(f)<3: await update.effective_message.reply_text('Usage: /projectlock USER_ID | PROJECT NAME | on|off'); return
    try: uid=int(f[0])
    except: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    item=admin_project_lookup(uid,f[1]); val=f[2].lower()
    if not item or val not in {'on','off'}: await update.effective_message.reply_text('❌ Invalid project/value.'); return
    project_settings.setdefault(project_key(item),{})['locked']=val=='on'
    if val=='on' and item.running: kill_process(item); item.desired_running=False
    save_v7_data(); save_projects(); audit(update.effective_user.id,'project_lock',item.display_name,val)
    await update.effective_message.reply_text(f"✅ Project lock {'enabled' if val=='on' else 'disabled'} for {esc(item.display_name)}.",parse_mode=ParseMode.HTML)

async def datasync_center_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    enabled=[]; failed=[]
    for uid,items in running_scripts.items():
        for item in items:
            st=data_sync_settings(item)
            if st.get('enabled'):
                enabled.append((uid,item,st))
                if 'FAIL' in str(st.get('last_status','')).upper(): failed.append((uid,item,st))
    lines=[f"🟢 Enabled • <code>{len(enabled)}</code>",f"❌ Failed • <code>{len(failed)}</code>",""]+[f"• <code>{uid}</code> • <b>{esc(i.display_name)}</b> • {esc(str(st.get('last_status','—')))[:80]}" for uid,i,st in enabled[:30]]
    await update.effective_message.reply_text(premium_box('☁️ ᴅᴀᴛᴀ sʏɴᴄ ᴄᴇɴᴛᴇʀ',lines),parse_mode=ParseMode.HTML)

async def syncall_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    ok=fail=0
    msg=await update.effective_message.reply_text('☁️ Syncing all enabled projects…')
    for _,items in running_scripts.items():
        for item in items:
            if not data_sync_settings(item).get('enabled'): continue
            try: await asyncio.to_thread(github_data_sync_push,item); ok+=1
            except Exception as e: data_sync_settings(item)['last_status']='FAILED • '+str(e)[:200]; fail+=1
    save_v7_data(); await msg.edit_text(premium_box('☁️ sʏɴᴄ ᴀʟʟ',[f'✅ Successful • <code>{ok}</code>',f'❌ Failed • <code>{fail}</code>']),parse_mode=ParseMode.HTML)

async def v1073_callback(update:Update,context:ContextTypes.DEFAULT_TYPE)->bool:
    q=update.callback_query; data=q.data or ""
    if not data.startswith("v1073:"): return False
    parts=data.split(":"); action=parts[1] if len(parts)>1 else ""; uid=q.from_user.id
    try: idx=int(parts[2]); item=scripts_for(uid)[idx]
    except Exception: await q.answer("Project not found",show_alert=True); return True
    if action=="envremember":
        global_cfg().setdefault("github_env_skip_default",{})[str(uid)]=True
        cfg=project_settings.setdefault(project_key(item),{}); cfg["env_setup_skipped"]=True; cfg["env_blocked"]=False; save_v7_data()
        await q.answer("ENV auto-skip remembered for future GitHub projects",show_alert=True)
        try:
            if not item.running: spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
        except Exception: pass
        await edit_message(q,project_center_text(item),project_center_buttons(idx,item)); return True
    if item.source_type!="github": await q.answer("Not a GitHub project",show_alert=True); return True
    try:
        if action in {"github","ghcheck"}:
            token=github_token_for(uid); remote=await asyncio.to_thread(github_remote_sha,item.repo_url,item.branch,token); current=item.commit_sha or project_settings.get(project_key(item),{}).get("github_last_sha","")
            lines=[f"Project • <b>{esc(item.display_name)}</b>",f"Branch • <code>{esc(item.branch)}</code>",f"Current • <code>{esc((current or '—')[:10])}</code>",f"Latest • <code>{esc((remote or '—')[:10])}</code>",f"Update • <code>{'AVAILABLE' if remote!=current else 'UP TO DATE'}</code>",f"Token • <code>{'REMEMBERED' if token else 'NOT SET'}</code>"]
            await edit_message(q,premium_box("🐙 ɢɪᴛʜᴜʙ ᴜᴘᴅᴀᴛᴇs",lines),github_project_buttons(idx,item)); return True
        if action=="ghsync":
            changed=await asyncio.to_thread(sync_github_item,item,False); await q.answer("Updated & redeployed" if changed else "Already up to date",show_alert=True); await edit_message(q,project_center_text(item),project_center_buttons(idx,item)); return True
        if action=="ghforce":
            await asyncio.to_thread(sync_github_item,item,True); await q.answer("Force redeploy complete",show_alert=True); await edit_message(q,project_center_text(item),project_center_buttons(idx,item)); return True
        if action=="ghtoggle":
            cfg=project_settings.setdefault(project_key(item),{}); cfg["github_autodeploy"]=not bool(cfg.get("github_autodeploy",False)); save_v7_data(); await q.answer("Auto Deploy "+("ON" if cfg["github_autodeploy"] else "OFF")); await edit_message(q,premium_box("🐙 ɢɪᴛʜᴜʙ",[f"Project • <b>{esc(item.display_name)}</b>",f"Auto Deploy • <code>{'ON' if cfg['github_autodeploy'] else 'OFF'}</code>"]),github_project_buttons(idx,item)); return True
    except Exception as e:
        await q.answer("GitHub action failed",show_alert=True); await edit_message(q,premium_box("❌ ɢɪᴛʜᴜʙ ᴀᴄᴛɪᴏɴ ғᴀɪʟᴇᴅ",[f"Reason • <code>{esc(e)}</code>",f"Token remembered • <code>{'YES' if github_token_for(uid) else 'NO'}</code>","For private repos, the remembered token must have access to this repository."]),github_project_buttons(idx,item)); return True
    return True

async def v107_callback(update:Update,context:ContextTypes.DEFAULT_TYPE)->bool:
    q=update.callback_query; data=q.data or ''
    if not data.startswith('v107:'): return False
    parts=data.split(':'); action=parts[1] if len(parts)>1 else ''; uid=q.from_user.id
    try: idx=int(parts[2]); item=scripts_for(uid)[idx]
    except Exception: await q.answer('Project not found',show_alert=True); return True
    if action=='setup':
        await edit_message(q,premium_box('🧙 sᴍᴀʀᴛ sᴇᴛᴜᴘ',setup_summary(item)),env_wizard_keyboard(idx,item)); return True
    if action=='envkey':
        key=':'.join(parts[3:]); v107_cfg().setdefault('pending_env_values',{})[str(uid)]={'project':item.display_name,'key':key}; save_v7_data();
        await edit_message(q,premium_box('🔐 ᴀᴅᴅ ᴇɴᴠ',[f'Project • <b>{esc(item.display_name)}</b>',f'Key • <code>{esc(key)}</code>','Send the secret VALUE as your next private text message.','The value will remain masked.']),env_wizard_keyboard(idx,item)); return True
    if action=='envskip':
        cfg=project_settings.setdefault(project_key(item),{})
        _,missing=required_env_summary(item)
        cfg['env_setup_skipped']=True
        cfg['env_blocked']=False
        save_v7_data()
        lines=[f'Project • <b>{esc(item.display_name)}</b>','⏭ ENV setup skipped.','🛡 QURESHIxOTP Host secrets remain isolated and will NOT be injected.']
        if missing: lines += ['', '⚠️ Detected but skipped • '+', '.join(f'<code>{esc(x)}</code>' for x in missing[:12]), 'If the project actually needs these values, it may fail at runtime.']
        try:
            if item.running:
                kill_process(item)
            item.restarts += 1
            spawn_script(item,Path(item.entry_file),Path(item.folder),Path(item.log_path))
            await asyncio.sleep(0.5)
            lines += ['', ('✅ Project started successfully.' if item.running else '⚠️ Project was launched but exited immediately. Check logs.')]
        except Exception as exc:
            lines += ['', f'❌ Runtime start failed • <code>{esc(exc)}</code>']
        await edit_message(q,premium_box('⏭ ᴇɴᴠ sᴋɪᴘ & sᴛᴀʀᴛ',lines),project_center_buttons(idx,item)); return True
    return True



async def depremove_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /depremove PROJECT NAME | package'); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    if project_locked(item): await update.effective_message.reply_text('🔒 Project is locked.'); return
    try:
        pkg=_safe_pkg(f[1]); root=Path(item.folder)
        if item.runtime=='python':
            py=root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python'); cmd=[str(py),'-m','pip','uninstall','-y',pkg]
        elif item.runtime=='node':
            npm=shutil.which('npm');
            if not npm: raise RuntimeError('npm is not installed on this host')
            cmd=[npm,'uninstall',pkg]
        else: raise RuntimeError('Dependency manager supports Python/Node')
        r=await asyncio.to_thread(subprocess.run,cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=V107_DEP_TIMEOUT)
        if r.returncode: raise RuntimeError(r.stdout.decode(errors='replace')[-1200:])
        await update.effective_message.reply_text(f'✅ Removed <code>{esc(pkg)}</code>.',parse_mode=ParseMode.HTML)
    except Exception as e: await update.effective_message.reply_text(f'❌ Remove failed: {e}')

async def depupdate_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    f=pipe_fields(update)
    if len(f)<2: await update.effective_message.reply_text('Usage: /depupdate PROJECT NAME | package'); return
    found=find_project(update.effective_user.id,f[0])
    if not found: await update.effective_message.reply_text('❌ Project not found.'); return
    _,item=found
    try:
        pkg=_safe_pkg(f[1]); root=Path(item.folder)
        if item.runtime=='python':
            py=root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python'); cmd=[str(py),'-m','pip','install','--upgrade',pkg]
        elif item.runtime=='node':
            npm=shutil.which('npm');
            if not npm: raise RuntimeError('npm is not installed on this host')
            cmd=[npm,'update',pkg]
        else: raise RuntimeError('Dependency manager supports Python/Node')
        r=await asyncio.to_thread(subprocess.run,cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=V107_DEP_TIMEOUT)
        if r.returncode: raise RuntimeError(r.stdout.decode(errors='replace')[-1200:])
        await update.effective_message.reply_text(f'✅ Updated <code>{esc(pkg)}</code>.',parse_mode=ParseMode.HTML)
    except Exception as e: await update.effective_message.reply_text(f'❌ Update failed: {e}')

async def restoreversion_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not owner_only(update): return
    f=pipe_fields(update)
    if len(f)<3: await update.effective_message.reply_text('Usage: /restoreversion USER_ID | PROJECT NAME | VERSION_FILE'); return
    try: uid=int(f[0])
    except: await update.effective_message.reply_text('❌ Invalid user ID.'); return
    item=admin_project_lookup(uid,f[1])
    if not item: await update.effective_message.reply_text('❌ Project not found.'); return
    if not re.fullmatch(r'[A-Za-z0-9_.-]+-data\.zip',f[2]): await update.effective_message.reply_text('❌ Invalid version filename.'); return
    token=github_token_for(uid); st=data_sync_settings(item); branch=str(st.get('branch') or V106_DATA_SYNC_BRANCH); owner,repo=_ensure_private_data_branch(item,token,branch); path=data_remote_base(item)+'/versions/'+f[2]
    try:
        obj=remote_data_object(item,token,branch,path); raw=base64.b64decode(str(obj.get('content') or '').replace('\n','')); tmp=Path(item.folder)/'.QURESHIxOTP_data_sync'/'version-restore.zip'; tmp.parent.mkdir(exist_ok=True); tmp.write_bytes(raw); safe_extract_zip_owner(tmp,Path(item.folder)); tmp.unlink(missing_ok=True); st['last_restore']=datetime.now(timezone.utc).isoformat(); save_v7_data(); await update.effective_message.reply_text('✅ Selected GitHub data backup version restored.')
    except Exception as e: await update.effective_message.reply_text(f'❌ Version restore failed: {e}')

async def isolationstatus_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not await guard(update,context): return
    lines=['Manager secrets inheritance • <code>BLOCKED</code>','ZIP path traversal • <code>BLOCKED</code>','ZIP symlinks • <code>BLOCKED</code>',f'Dependency timeout • <code>{DEPENDENCY_TIMEOUT_SECONDS}s</code>',f'Process limits • <code>{"ON" if ENFORCE_RESOURCE_LIMITS else "OFF"}</code>','Container isolation • <code>HOST-DEPENDENT</code>','Note • true per-project container isolation requires Docker/cgroups support from the hosting panel.']
    await update.effective_message.reply_text(premium_box('🛡 ɪsᴏʟᴀᴛɪᴏɴ sᴛᴀᴛᴜs',lines),parse_mode=ParseMode.HTML)


async def setup_user_command_menu(app: Application) -> None:
    """Publish only user-facing commands in Telegram's slash-command menu."""
    commands = [
        BotCommand("start", "Open QURESHIxOTP Host dashboard"),
        BotCommand("help", "User hosting guide"),
        BotCommand("projects", "Open My Projects"),
        BotCommand("logs", "View project logs"),
        BotCommand("credits", "Check credits and plan"),
        BotCommand("plans", "View available plans"),
        BotCommand("usage", "Account usage and limits"),
        BotCommand("storage", "Check storage usage"),
        BotCommand("health", "Project resource health"),
        BotCommand("connectrepo", "Deploy public/private GitHub repo"),
        BotCommand("setgithubtoken", "Connect your private GitHub access token"),
        BotCommand("githubtoken", "Check GitHub token status"),
        BotCommand("delgithubtoken", "Remove saved GitHub token"),
        BotCommand("repos", "View connected GitHub projects"),
        BotCommand("repostatus", "GitHub sync status"),
        BotCommand("redeploy", "Redeploy a project"),
        BotCommand("syncrepo", "Sync GitHub project now"),
        BotCommand("githubcheck", "Check GitHub for new commit"),
        BotCommand("forceredeploy", "Force latest GitHub redeploy"),
        BotCommand("envskipdefault", "Remember GitHub ENV skip default"),
        BotCommand("deployhistory", "View deployment history"),
        BotCommand("rollback", "Rollback a deployment"),
        BotCommand("projectbackup", "Download project backup"),
        BotCommand("notifications", "Project notification settings"),
        BotCommand("ticket", "Open a support ticket"),
        BotCommand("referral", "Referral information"),
        BotCommand("favorite", "Favorite/unfavorite a project"),
        BotCommand("tag", "Add a project tag"),
        BotCommand("searchproject", "Search your projects"),
        BotCommand("trash", "Recently deleted projects"),
        BotCommand("restoretrash", "Restore a deleted project"),
        BotCommand("backupschedule", "Schedule project backups"),
        BotCommand("activity", "View your recent activity"),
        BotCommand("templates", "Browse project templates"),
        BotCommand("githubcenter", "Open GitHub deployment center"),
        BotCommand("predeploy", "Test project before deploy"),
        BotCommand("filemanager", "Browse project files"),
        BotCommand("editfile", "Edit project text file"),
        BotCommand("replacefile", "Upload replacement for one project file"),
        BotCommand("envcheck", "Check missing project ENV variables"),
        BotCommand("skipenv", "Skip ENV setup for a project"),
        BotCommand("envprofile", "Manage ENV profiles"),
        BotCommand("schedules", "View scheduled actions"),
        BotCommand("exportproject", "Export a portable project"),
        BotCommand("importproject", "Import a portable project"),
        BotCommand("features", "View platform features"),
        BotCommand("loyalty", "View loyalty score"),
    ]
    await app.bot.set_my_commands(commands)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    if (
        not TOKEN
        or TOKEN == "PASTE_NEW_BOT_TOKEN_HERE"
    ):
        raise SystemExit(
            "BOT token missing. Paste a NEW BotFather token "
            "in TOKEN at the top of main.py."
        )

    if OWNER_ID <= 0:
        raise SystemExit(
            "Missing or invalid OWNER_ID in main.py."
        )

    load_data()
    load_v7_data()
    init_v9_database()
    sync_v9_database()
    global FORCE_JOIN_ENABLED, BRAND_NAME
    g=project_settings.get("__global__",{})
    FORCE_JOIN_ENABLED=bool(g.get("force_join_enabled",FORCE_JOIN_ENABLED))
    BRAND_NAME=str(g.get("brand_name",BRAND_NAME))
    expire_plans()
    start_health_server()

    app: Application = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .concurrent_updates(32)
        .post_init(setup_user_command_menu)
        .build()
    )

    # V10 is intentionally silent in groups/supergroups.
    app.add_handler(MessageHandler(~filters.ChatType.PRIVATE, group_silent_handler), group=-1)

    app.add_handler(CommandHandler("setgithubtoken", setgithubtoken_cmd))
    app.add_handler(CommandHandler("githubtoken", githubtoken_cmd))
    app.add_handler(CommandHandler("delgithubtoken", delgithubtoken_cmd))
    app.add_handler(CommandHandler("connectrepo", connectrepo_cmd))
    app.add_handler(CommandHandler("repos", repos_cmd))
    app.add_handler(CommandHandler("repostatus", repostatus_cmd))
    app.add_handler(CommandHandler("disconnectrepo", disconnectrepo_cmd))
    app.add_handler(CommandHandler("setbranch", setbranch_cmd))
    app.add_handler(CommandHandler("redeploy", redeploy_cmd))
    app.add_handler(CommandHandler("replaceproject", replaceproject_cmd))
    app.add_handler(CommandHandler("setentry", setentry_cmd))
    app.add_handler(CommandHandler("autodeploy", autodeploy_cmd))
    app.add_handler(CommandHandler("syncrepo", syncrepo_cmd))
    app.add_handler(CommandHandler("githubcheck", githubcheck_cmd))
    app.add_handler(CommandHandler("forceredeploy", forceredeploy_cmd))
    app.add_handler(CommandHandler("envskipdefault", envskipdefault_cmd))
    app.add_handler(CommandHandler("deployhistory", deployhistory_cmd))
    app.add_handler(CommandHandler("rollback", rollback_cmd))
    app.add_handler(CommandHandler("cloneproject", cloneproject_cmd))
    app.add_handler(CommandHandler("notifications", notifications_cmd))
    app.add_handler(CommandHandler("usage", usage_cmd))
    app.add_handler(CommandHandler("myaccount", usage_cmd))
    app.add_handler(CommandHandler("compareplans", compareplans_cmd))
    app.add_handler(CommandHandler("upgrade", compareplans_cmd))
    app.add_handler(CommandHandler("expiry", expiry_cmd))
    app.add_handler(CommandHandler("planbuilder", planbuilder_cmd))
    app.add_handler(CommandHandler("ticket", ticket_cmd))
    app.add_handler(CommandHandler("tickets", tickets_cmd))
    app.add_handler(CommandHandler("closeticket", closeticket_cmd))
    app.add_handler(CommandHandler("emergency", emergency_cmd))
    app.add_handler(CommandHandler("restartcrashed", restartcrashed_cmd))
    app.add_handler(CommandHandler("referral", referral_cmd))
    app.add_handler(CommandHandler("refstats", referral_cmd))

    app.add_handler(CommandHandler("favorite", favorite_cmd))
    app.add_handler(CommandHandler("tag", tag_cmd))
    app.add_handler(CommandHandler("searchproject", searchproject_cmd))
    app.add_handler(CommandHandler("trash", trash_cmd))
    app.add_handler(CommandHandler("restoretrash", restoretrash_cmd))
    app.add_handler(CommandHandler("backupschedule", backupschedule_cmd))
    app.add_handler(CommandHandler("activity", activity_cmd))
    app.add_handler(CommandHandler("templates", templates_cmd))
    app.add_handler(CommandHandler("template", template_cmd))
    app.add_handler(CommandHandler("replyticket", replyticket_cmd))
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("usernote", usernote_cmd))
    app.add_handler(CommandHandler("userprojects", userprojects_cmd))
    app.add_handler(CommandHandler("adminproject", adminproject_cmd))
    app.add_handler(CommandHandler("extensions", extensions_cmd))
    app.add_handler(CommandHandler("packageblacklist", packageblacklist_cmd))
    app.add_handler(CommandHandler("broadcastplan", broadcastplan_cmd))
    app.add_handler(CommandHandler("deployprofile", deployprofile_cmd))
    app.add_handler(CommandHandler("predeploy", predeploy_cmd))
    app.add_handler(CommandHandler("markgood", markgood_cmd))
    app.add_handler(CommandHandler("restoregood", restoregood_cmd))
    app.add_handler(CommandHandler("githubcenter", githubcenter_cmd))
    app.add_handler(CommandHandler("deploycommit", deploycommit_cmd))
    app.add_handler(CommandHandler("filemanager", filemanager_cmd))
    app.add_handler(CommandHandler("viewfile", viewfile_cmd))
    app.add_handler(CommandHandler("downloadfile", downloadfile_cmd))
    app.add_handler(CommandHandler("renamefile", renamefile_cmd))
    app.add_handler(CommandHandler("deletefile", deletefile_cmd))
    app.add_handler(CommandHandler("editfile", editfile_cmd))
    app.add_handler(CommandHandler("canceledit", canceledit_cmd))
    app.add_handler(CommandHandler("envprofile", envprofile_cmd))
    app.add_handler(CommandHandler("rotateenv", rotateenv_cmd))
    app.add_handler(CommandHandler("scheduleaction", scheduleaction_cmd))
    app.add_handler(CommandHandler("schedules", schedules_cmd))
    app.add_handler(CommandHandler("unscheduleaction", unscheduleaction_cmd))
    app.add_handler(CommandHandler("depsnapshot", depsnapshot_cmd))
    app.add_handler(CommandHandler("deprestore", deprestore_cmd))
    app.add_handler(CommandHandler("exportproject", exportproject_cmd))
    app.add_handler(CommandHandler("importproject", importproject_cmd))
    app.add_handler(CommandHandler("features", features_cmd))
    app.add_handler(CommandHandler("feature", feature_cmd))
    app.add_handler(CommandHandler("usercenter", usercenter_cmd))
    app.add_handler(CommandHandler("transferproject", transferproject_cmd))
    app.add_handler(CommandHandler("bulkproject", bulkproject_cmd))
    app.add_handler(CommandHandler("announcement", announcement_cmd))
    app.add_handler(CommandHandler("loyalty", loyalty_cmd))
    app.add_handler(CommandHandler("campaign", campaign_cmd))
    # V10.7 project management + reliability
    app.add_handler(CommandHandler("setup", setupwizard_cmd))
    app.add_handler(CommandHandler("envwizard", envwizard_cmd))
    app.add_handler(CommandHandler("skipenv", skipenv_cmd))
    app.add_handler(CommandHandler("newfile", newfile_cmd))
    app.add_handler(CommandHandler("newfolder", newfolder_cmd))
    app.add_handler(CommandHandler("filehistory", filehistory_cmd))
    app.add_handler(CommandHandler("undofile", undofile_cmd))
    app.add_handler(CommandHandler("testproject", testproject_cmd))
    app.add_handler(CommandHandler("timeline", timeline_cmd))
    app.add_handler(CommandHandler("errorcenter", errorcenter_cmd))
    app.add_handler(CommandHandler("projectnotify", projectnotify_cmd))
    app.add_handler(CommandHandler("dependencies", dependencies_cmd))
    app.add_handler(CommandHandler("depadd", depadd_cmd))
    app.add_handler(CommandHandler("depremove", depremove_cmd))
    app.add_handler(CommandHandler("depupdate", depupdate_cmd))
    app.add_handler(CommandHandler("regenrequirements", regenrequirements_cmd))
    app.add_handler(CommandHandler("restoreversion", restoreversion_cmd))
    app.add_handler(CommandHandler("isolationstatus", isolationstatus_cmd))
    app.add_handler(CommandHandler("syncpreview", syncpreview_cmd))
    app.add_handler(CommandHandler("dataversions", dataversions_cmd))
    app.add_handler(CommandHandler("projectexplorer", projectexplorer_cmd))
    app.add_handler(CommandHandler("projectlock", projectlock_cmd))
    app.add_handler(CommandHandler("datasynccenter", datasync_center_cmd))
    app.add_handler(CommandHandler("syncall", syncall_cmd))
    # V10.7 data-safe project controls
    app.add_handler(CommandHandler("envcheck", envcheck_cmd))
    app.add_handler(CommandHandler("replacefile", replacefile_cmd))
    app.add_handler(CommandHandler("replaceuserfile", replaceuserfile_cmd))
    app.add_handler(CommandHandler("adminfiles", adminfiles_cmd))
    app.add_handler(CommandHandler("datasync", datasync_cmd))
    app.add_handler(CommandHandler("datasyncstatus", datasyncstatus_cmd))
    app.add_handler(CommandHandler("syncdata", syncdata_cmd))
    app.add_handler(CommandHandler("restoredata", restoredata_cmd))
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("projects", projects_cmd))
    app.add_handler(CommandHandler("status", projects_cmd))
    app.add_handler(CommandHandler("logs", logs_cmd))
    app.add_handler(CommandHandler("credits", credits_cmd))
    app.add_handler(CommandHandler("skip", skip_cmd))
    app.add_handler(CommandHandler("rename", rename_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("delete", delete_cmd))

    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("premium", premium_cmd))
    app.add_handler(CommandHandler("unpremium", unpremium_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("userinfo", userinfo_cmd))
    app.add_handler(CommandHandler("addcredits", addcredits_cmd))
    app.add_handler(CommandHandler("setcredits", setcredits_cmd))
    app.add_handler(CommandHandler("takecredits", takecredits_cmd))
    app.add_handler(CommandHandler("setdaily", setdaily_cmd))
    app.add_handler(CommandHandler("setrunning", setrunning_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("maintenance", maintenance_cmd))
    app.add_handler(CommandHandler("startall", startall_cmd))
    app.add_handler(CommandHandler("stopalladmin", stopalladmin_cmd))
    app.add_handler(CommandHandler("cleanup", cleanup_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("backupnow", backup_cmd))
    app.add_handler(CommandHandler("install", install_cmd))
    app.add_handler(CommandHandler("installed", installed_cmd))
    app.add_handler(CommandHandler("setplan", setplan_cmd))
    app.add_handler(CommandHandler("plans", plans_cmd))
    app.add_handler(CommandHandler("createcode", createcode_cmd))
    app.add_handler(CommandHandler("redeem", redeem_cmd))
    app.add_handler(CommandHandler("setenv", setenv_cmd))
    app.add_handler(CommandHandler("env", env_cmd))
    app.add_handler(CommandHandler("delenv", delenv_cmd))
    app.add_handler(CommandHandler("autorestart", autorestart_cmd))
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(CommandHandler("auditlog", auditlog_cmd))
    app.add_handler(CommandHandler("keepalive", keepalive_cmd))
    app.add_handler(CommandHandler("setkeepalive", setkeepalive_cmd))
    app.add_handler(CommandHandler("hoststats", hoststats_cmd))
    app.add_handler(CommandHandler("security", security_cmd))
    app.add_handler(CommandHandler("finduser", finduser_cmd))
    app.add_handler(CommandHandler("allprojects", allprojects_cmd))
    app.add_handler(CommandHandler("restartall", restartall_cmd))
    app.add_handler(CommandHandler("watchdog", watchdog_cmd))
    app.add_handler(CommandHandler("setwatchdog", setwatchdog_cmd))
    app.add_handler(CommandHandler("watchdogstatus", watchdogstatus_cmd))
    app.add_handler(CommandHandler("schedulerestart", schedulerestart_cmd))
    app.add_handler(CommandHandler("scheduleremove", scheduleremove_cmd))
    app.add_handler(CommandHandler("autostart", autostart_cmd))
    app.add_handler(CommandHandler("projectbackup", projectbackup_cmd))
    app.add_handler(CommandHandler("backups", backups_cmd))
    app.add_handler(CommandHandler("restorebackup", restorebackup_cmd))
    app.add_handler(CommandHandler("logsize", logsize_cmd))
    app.add_handler(CommandHandler("clearlogs", clearlogs_cmd))
    app.add_handler(CommandHandler("diagnose", diagnose_cmd))
    app.add_handler(CommandHandler("storage", storage_cmd))
    app.add_handler(CommandHandler("setstorage", setstorage_cmd))
    app.add_handler(CommandHandler("analytics", analytics_cmd))
    app.add_handler(CommandHandler("addadmin", addadmin_cmd))
    app.add_handler(CommandHandler("deladmin", deladmin_cmd))
    app.add_handler(CommandHandler("admins", admins_cmd))
    app.add_handler(CommandHandler("codes", codes_cmd))
    app.add_handler(CommandHandler("disablecode", disablecode_cmd))
    app.add_handler(CommandHandler("deletecode", deletecode_cmd))
    app.add_handler(CommandHandler("codeinfo", codeinfo_cmd))
    app.add_handler(CommandHandler("forcejoin", forcejoin_cmd))
    app.add_handler(CommandHandler("setbrand", setbrand_cmd))
    app.add_handler(CommandHandler("setfooter", setfooter_cmd))
    app.add_handler(CommandHandler("piplist", piplist_cmd))
    app.add_handler(CommandHandler("requirements", requirements_cmd))
    app.add_handler(CommandHandler("checkcompat", checkcompat_cmd))
    app.add_handler(CommandHandler("repairenv", repairenv_cmd))

    app.add_handler(
        CallbackQueryHandler(callback_handler)
    )
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            handle_document,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler,
        )
    )

    app.add_error_handler(error_handler)

    if app.job_queue:
        app.job_queue.run_once(startup_recovery_job, when=8)
        app.job_queue.run_repeating(watchdog_job, interval=10, first=20)
        app.job_queue.run_repeating(github_autodeploy_job, interval=GITHUB_POLL_SECONDS, first=45)
        app.job_queue.run_repeating(server_alert_job, interval=300, first=120)
        app.job_queue.run_repeating(log_rotation_job, interval=300, first=180)
        app.job_queue.run_repeating(backup_scheduler_job, interval=1800, first=300)
        app.job_queue.run_repeating(scheduled_actions_job, interval=30, first=60)
        app.job_queue.run_repeating(github_data_sync_job, interval=V106_DATA_SYNC_INTERVAL, first=150, name="QURESHIxOTP_github_data_sync")
        app.job_queue.run_repeating(keepalive_job, interval=5, first=10, name="QURESHIxOTP_keepalive")
        app.job_queue.run_repeating(
            scheduled_backup_job,
            interval=24 * 3600,
            first=120,
        )

    logger.info(
        "%s V10.7 Project Management + Reliability Edition started | Owner: %s",
        BRAND_NAME,
        OWNER_ID,
    )

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
