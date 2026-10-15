"""
TheOracleEyes OSINT Bot - Polling Mode (No Webhook Needed)
Bas chalao: python bot.py
"""

import os
import re
import json
import time
import html
import errno
import logging
from urllib.parse import quote

import requests

# =========================================================
# ====================  CONFIG  ===========================
# =========================================================
BOT_TOKEN   = "8804034333:AAEfVuvfil8LGul3MzGX3A_TKfLaXOY4faQ"
LOG_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bot.log")
STATE_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bot_state.json")
LOCK_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bot.lock")
MAX_RETRIES = 3
TIMEOUT     = 180
RETRY_DELAY = 2
_INSTANCE_LOCK_HANDLE = None

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}/"

DEFAULT_APIS = {
    "number":     "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=number&number={number}",
    "instagram":  "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=instagram&username={username}",
    "vehicle":    "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=vehicle&vehicle_number={vehicle_number}",
    "challan":    "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=challan&vehicle_number={vehicle_number}",
    "family":     "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=family&aadhaar={aadhaar}",
    "telegram":   "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=telegram&userid={userid}",
    "pak_number": "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=pak_number&number={number}",
    "pan":        "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=pan&pan={pan}",
    "ifsc":       "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=ifsc&ifsc={ifsc}",
    "imei":       "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=imei&imei={imei}",
    "github":     "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=github&username={username}",
    "jwt":        "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=jwt&jwt_token={jwt_token}",
    "mail":       "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=mail&email={email}",
    "ip":         "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=ip&ip_address={ip_address}",
    "cnic":       "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=cnic&cnic={cnic}",
    "truecaller": "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=truecaller&number={number}",
    "upi":        "https://getofferpro.xyz/apis/api.php?access_key=1month27800&endpoint=upi&upi={upi}",
}

COMMAND_META = {
    "num": {
        "api_key": "number", "placeholder": "{number}",
        "title": "📱 ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ",
        "pattern": r"^\d{10}$", "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ 10-ᴅɪɢɪᴛ ɴᴜᴍʙᴇʀ.",
        "prompt": "📱 <b>ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>10-ᴅɪɢɪᴛ</b> ᴍᴏʙɪʟᴇ ɴᴜᴍʙᴇʀ.\n\nᴇxᴀᴍᴘʟᴇ: <code>9876543210</code>",
    },
    "truecaller": {
        "api_key": "truecaller", "placeholder": "{number}",
        "title": "📞 ᴛʀᴜᴇᴄᴀʟʟᴇʀ",
        "pattern": r"^\d{10}$", "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ 10-ᴅɪɢɪᴛ ɴᴜᴍʙᴇʀ.",
        "prompt": "📞 <b>ᴛʀᴜᴇᴄᴀʟʟᴇʀ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>10-ᴅɪɢɪᴛ</b> ᴍᴏʙɪʟᴇ ɴᴜᴍʙᴇʀ.\n\nᴇxᴀᴍᴘʟᴇ: <code>9876543210</code>",
    },
    "instagram": {
        "api_key": "instagram", "placeholder": "{username}",
        "title": "📷 ɪɴsᴛᴀɢʀᴀᴍ",
        "pattern": None, "error": None,
        "prompt": "📷 <b>ɪɴsᴛᴀɢʀᴀᴍ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ɪɴsᴛᴀɢʀᴀᴍ ᴜsᴇʀɴᴀᴍᴇ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>username</code>",
    },
    "vehicle": {
        "api_key": "vehicle", "placeholder": "{vehicle_number}",
        "title": "🚗 ᴠᴇʜɪᴄʟᴇ",
        "pattern": None, "error": None,
        "prompt": "🚗 <b>ᴠᴇʜɪᴄʟᴇ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ᴠᴇʜɪᴄʟᴇ ɴᴜᴍʙᴇʀ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>WB12BR8935</code>",
    },
    "challan": {
        "api_key": "challan", "placeholder": "{vehicle_number}",
        "title": "🚨 ᴄʜᴀʟʟᴀɴ",
        "pattern": None, "error": None,
        "prompt": "🚨 <b>ᴄʜᴀʟʟᴀɴ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ᴠᴇʜɪᴄʟᴇ ɴᴜᴍʙᴇʀ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>WB12BR8935</code>",
    },
    "family": {
        "api_key": "family", "placeholder": "{aadhaar}",
        "title": "👥 ғᴀᴍɪʟʏ",
        "pattern": r"^\d{12}$", "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ 12-ᴅɪɢɪᴛ ᴀᴀᴅʜᴀᴀʀ ɴᴜᴍʙᴇʀ.",
        "prompt": "👥 <b>ғᴀᴍɪʟʏ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>12-ᴅɪɢɪᴛ ᴀᴀᴅʜᴀᴀʀ ɴᴜᴍʙᴇʀ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>123456789012</code>",
    },
    "telegram": {
        "api_key": "telegram", "placeholder": "{userid}",
        "title": "👤 ᴛᴇʟᴇɢʀᴀᴍ",
        "pattern": None, "error": None,
        "prompt": "👤 <b>ᴛᴇʟᴇɢʀᴀᴍ ᴜsᴇʀ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ᴛᴇʟᴇɢʀᴀᴍ ᴜsᴇʀ ɪᴅ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>123456789</code>",
    },
    "pak_number": {
        "api_key": "pak_number", "placeholder": "{number}",
        "title": "📱 ᴘᴀᴋɪsᴛᴀɴ ɴᴜᴍʙᴇʀ",
        "pattern": None, "error": None,
        "prompt": "📱 <b>ᴘᴀᴋɪsᴛᴀɴ ɴᴜᴍʙᴇʀ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ᴘᴀᴋɪsᴛᴀɴɪ ɴᴜᴍʙᴇʀ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>923456789012</code>",
    },
    "cnic": {
        "api_key": "cnic", "placeholder": "{cnic}",
        "title": "🆔 ᴘᴀᴋɪsᴛᴀɴ ᴄɴɪᴄ",
        "pattern": r"^\d{13}$", "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ 13-ᴅɪɢɪᴛ ᴄɴɪᴄ ɴᴜᴍʙᴇʀ.",
        "prompt": "🆔 <b>ᴄɴɪᴄ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>13-ᴅɪɢɪᴛ ᴄɴɪᴄ ɴᴜᴍʙᴇʀ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>3520195597831</code>",
    },
    "pan": {
        "api_key": "pan", "placeholder": "{pan}",
        "title": "🆔 ᴘᴀɴ ᴄᴀʀᴅ",
        "pattern": r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴘᴀɴ ɴᴜᴍʙᴇʀ (ᴇ.ɢ. ABCDE1234F).",
        "prompt": "🆔 <b>ᴘᴀɴ ᴄᴀʀᴅ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ᴘᴀɴ ɴᴜᴍʙᴇʀ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>ABCDE1234F</code>",
    },
    "ifsc": {
        "api_key": "ifsc", "placeholder": "{ifsc}",
        "title": "🏦 ɪғsᴄ ᴄᴏᴅᴇ",
        "pattern": r"^[A-Z]{4}0[A-Z0-9]{6}$", "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɪғsᴄ ᴄᴏᴅᴇ.",
        "prompt": "🏦 <b>ɪғsᴄ ᴄᴏᴅᴇ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ɪғsᴄ ᴄᴏᴅᴇ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>SBIN0000123</code>",
    },
    "imei": {
        "api_key": "imei", "placeholder": "{imei}",
        "title": "📱 ɪᴍᴇɪ ɴᴜᴍʙᴇʀ",
        "pattern": r"^\d{15}$", "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ 15-ᴅɪɢɪᴛ ɪᴍᴇɪ ɴᴜᴍʙᴇʀ.",
        "prompt": "📱 <b>ɪᴍᴇɪ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>15-ᴅɪɢɪᴛ ɪᴍᴇɪ ɴᴜᴍʙᴇʀ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>123456789012345</code>",
    },
    "github": {
        "api_key": "github", "placeholder": "{username}",
        "title": "🐙 ɢɪᴛʜᴜʙ",
        "pattern": None, "error": None,
        "prompt": "🐙 <b>ɢɪᴛʜᴜʙ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ɢɪᴛʜᴜʙ ᴜsᴇʀɴᴀᴍᴇ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>username</code>",
    },
    "jwt": {
        "api_key": "jwt", "placeholder": "{jwt_token}",
        "title": "🔐 ᴊᴡᴛ ᴛᴏᴋᴇɴ",
        "pattern": None, "error": None,
        "prompt": "🔐 <b>ᴊᴡᴛ ᴅᴇᴄᴏᴅᴇ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ᴊᴡᴛ ᴛᴏᴋᴇɴ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>eyJhbGciOiJIUzI1NiIs...</code>",
    },
    "mail": {
        "api_key": "mail", "placeholder": "{email}",
        "title": "📧 ᴇᴍᴀɪʟ",
        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴇᴍᴀɪʟ ᴀᴅᴅʀᴇss.",
        "prompt": "📧 <b>ᴇᴍᴀɪʟ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ᴇᴍᴀɪʟ ᴀᴅᴅʀᴇss</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>example@gmail.com</code>",
    },
    "ip": {
        "api_key": "ip", "placeholder": "{ip_address}",
        "title": "🌐 ɪᴘ ᴀᴅᴅʀᴇss",
        "pattern": r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɪᴘᴠ4 ᴀᴅᴅʀᴇss.",
        "prompt": "🌐 <b>ɪᴘ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ɪᴘ ᴀᴅᴅʀᴇss</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>8.8.8.8</code>",
    },
    "upi": {
        "api_key": "upi", "placeholder": "{upi}",
        "title": "💳 ᴜᴘɪ ɪɴғᴏ",
        "pattern": r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$",
        "error": "ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴜᴘɪ ɪᴅ (ᴇ.ɢ. example@ybl).",
        "prompt": "💳 <b>ᴜᴘɪ ɪɴғᴏ ʟᴏᴏᴋᴜᴘ</b>\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ <b>ᴜᴘɪ ɪᴅ</b>.\n\nᴇxᴀᴍᴘʟᴇ: <code>example@ybl</code>",
    },
}

BUTTON_TO_COMMAND = {
    "📱 ɴᴜᴍʙᴇʀ":     "num",
    "📞 ᴛʀᴜᴇᴄᴀʟʟᴇʀ": "truecaller",
    "📷 ɪɴsᴛᴀɢʀᴀᴍ":   "instagram",
    "🚗 ᴠᴇʜɪᴄʟᴇ":     "vehicle",
    "🚨 ᴄʜᴀʟʟᴀɴ":    "challan",
    "👥 ғᴀᴍɪʟʏ":      "family",
    "👤 ᴛᴇʟᴇɢʀᴀᴍ":    "telegram",
    "📱 ᴘᴀᴋ ɴᴜᴍ":    "pak_number",
    "🆔 ᴄɴɪᴄ":       "cnic",
    "🆔 ᴘᴀɴ":        "pan",
    "🏦 ɪғsᴄ":        "ifsc",
    "📱 ɪᴍᴇɪ":        "imei",
    "🐙 ɢɪᴛʜᴜʙ":     "github",
    "🔐 ᴊᴡᴛ":         "jwt",
    "📧 ᴍᴀɪʟ":        "mail",
    "🌐 ɪᴘ":          "ip",
    "💳 ᴜᴘɪ ɪɴғᴏ":    "upi",
}

# =========================================================
# ======================  LOGGER  =========================
# =========================================================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def log_msg(msg):
    try:
        logging.info(msg)
    except Exception:
        pass
    # Console pe bhi dikhao
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def escape_html(text):
    return html.escape(str(text), quote=True)


def build_api_url(api_template, placeholder, value):
    clean_value = str(value).strip()
    if not clean_value:
        return api_template.replace(placeholder, "")
    return api_template.replace(placeholder, quote(clean_value, safe=""))

# =========================================================
# ===================  TELEGRAM HELPERS  ==================
# =========================================================
def tg_request(method, params=None):
    if params is None:
        params = {}
    try:
        r = requests.post(API_BASE + method, data=params, timeout=60)
        return r.json()
    except Exception as e:
        log_msg(f"tg_request error [{method}]: {e}")
        return None

def tg_send(chat_id, text, extra=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if extra:
        payload.update(extra)
    return tg_request("sendMessage", payload)

# =========================================================
# ==================  STATE (file-based)  =================
# =========================================================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception as e:
        log_msg(f"save_state error: {e}")

# =========================================================
# ==============  ERROR MESSAGE BUILDER  ==================
# =========================================================
ERROR_MAP = {
    "TIMEOUT":        "⚠️ ᴛɪᴍᴇᴏᴜᴛ ᴇʀʀᴏʀ\n\nᴛʜᴇ sᴇʀᴠᴇʀ ᴛᴏᴏᴋ ᴛᴏᴏ ʟᴏɴɢ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
    "CONNECTION":     "🌐 ᴄᴏɴɴᴇᴄᴛɪᴏɴ ᴇʀʀᴏʀ\n\nᴄᴏᴜʟᴅ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
    "FORBIDDEN":      "🚫 ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ (403)\n\nᴛʜᴇ sᴇʀᴠᴇʀ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʀᴇǫᴜᴇsᴛ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
    "NOT_FOUND":      "🔍 ᴅᴀᴛᴀ ɴᴏᴛ ғᴏᴜɴᴅ (404)\n\nɴᴏ ᴅᴀᴛᴀ ᴡᴀs ғᴏᴜɴᴅ ғᴏʀ ᴛʜɪs ɪɴᴘᴜᴛ.",
    "RATE_LIMIT":     "⏱️ ʀᴀᴛᴇ ʟɪᴍɪᴛ (429)\n\nᴛᴏᴏ ᴍᴀɴʏ ʀᴇǫᴜᴇsᴛs. ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴀ ᴡʜɪʟᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.",
    "SERVER_ERROR":   "🔧 sᴇʀᴠᴇʀ ᴇʀʀᴏʀ (5xx)\n\nᴛʜᴇʀᴇ ɪs ᴀ ᴘʀᴏʙʟᴇᴍ ᴡɪᴛʜ ᴛʜᴇ sᴇʀᴠᴇʀ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
    "BAD_REQUEST":    "❌ ɪɴᴠᴀʟɪᴅ ʀᴇǫᴜᴇsᴛ (400)\n\nᴛʜᴇ ɪɴᴘᴜᴛ ɪs ɴᴏᴛ ᴠᴀʟɪᴅ. ᴘʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴀɴᴅ sᴇɴᴅ ᴀɢᴀɪɴ.",
    "EMPTY_RESPONSE": "📭 ᴇᴍᴘᴛʏ ʀᴇsᴘᴏɴsᴇ\n\nᴛʜᴇ sᴇʀᴠᴇʀ ᴅɪᴅ ɴᴏᴛ ʀᴇᴛᴜʀɴ ᴀɴʏ ᴅᴀᴛᴀ.",
    "INVALID_JSON":   "⚠️ ɪɴᴠᴀʟɪᴅ ʀᴇsᴘᴏɴsᴇ\n\nᴛʜᴇ sᴇʀᴠᴇʀ ʀᴇᴛᴜʀɴᴇᴅ ᴅᴀᴛᴀ ɪɴ ᴀ ᴡʀᴏɴɢ ғᴏʀᴍᴀᴛ.",
    "CLOUDFLARE":     "🛡️ ᴄʟᴏᴜᴅғʟᴀʀᴇ ʙʟᴏᴄᴋ\n\nᴛʜᴇ sᴇᴄᴜʀɪᴛʏ sʏsᴛᴇᴍ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʀᴇǫᴜᴇsᴛ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
    "UNKNOWN":        "⚠️ ᴜɴᴋɴᴏᴡɴ ᴇʀʀᴏʀ\n\nsᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
}

def build_error_message(error_code, detail=""):
    message = ERROR_MAP.get(error_code, ERROR_MAP["UNKNOWN"])
    if detail:
        message += f"\n\n<i>ᴅᴇᴛᴀɪʟ: {escape_html(detail)}</i>"
    return json.dumps(
        {"status": "ᴇʀʀᴏʀ", "message": message},
        ensure_ascii=False, indent=2,
    )

# =========================================================
# =====================  API FETCH  =======================
# =========================================================
def fetch_api(api_url, command_name):
    last_code, last_detail = "UNKNOWN", ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        log_msg(f"API call attempt {attempt}/{MAX_RETRIES} for {command_name}")
        try:
            r = requests.get(
                api_url,
                headers=headers,
                timeout=(30, TIMEOUT),
                allow_redirects=True,
            )
        except requests.exceptions.Timeout:
            last_code, last_detail = "TIMEOUT", f"{TIMEOUT}s"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return build_error_message(last_code, last_detail)
        except requests.exceptions.ConnectionError:
            last_code, last_detail = "CONNECTION", "conn error"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return build_error_message(last_code, last_detail)
        except Exception as e:
            last_code, last_detail = "UNKNOWN", str(e)[:80]
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return build_error_message(last_code, last_detail)

        status = r.status_code
        body = (r.text or "").strip()
        preview = body[:200].lower()

        if status == 403:
            last_code = "CLOUDFLARE" if ("cloudflare" in preview or "cf-" in preview) else "FORBIDDEN"
            last_detail = f"HTTP {status}"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return build_error_message(last_code, last_detail)
        if status == 404:
            return build_error_message("NOT_FOUND", f"HTTP {status}")
        if status == 429:
            return build_error_message("RATE_LIMIT", f"HTTP {status}")
        if status == 406:
            last_code, last_detail = "BAD_REQUEST", f"HTTP {status}"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return build_error_message(last_code, last_detail)
        if 400 <= status < 500:
            return build_error_message("BAD_REQUEST", f"HTTP {status}")
        if status >= 500:
            last_code, last_detail = "SERVER_ERROR", f"HTTP {status}"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return build_error_message(last_code, last_detail)

        if not body:
            last_code = "EMPTY_RESPONSE"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return build_error_message("EMPTY_RESPONSE")

        try:
            json_data = json.loads(body)
        except json.JSONDecodeError:
            if ("cloudflare" in preview or "cf-" in preview or "just a moment" in preview):
                last_code = "CLOUDFLARE"
            else:
                last_code = "INVALID_JSON"
            last_detail = f"HTTP {status}"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return build_error_message(last_code, last_detail)

        if isinstance(json_data, dict):
            if json_data.get("success") is False:
                err = json_data.get("message") or json_data.get("error") or "Request failed"
                return json.dumps(
                    {"status": "ᴇʀʀᴏʀ", "message": f"❌ {escape_html(str(err))}"},
                    ensure_ascii=False,
                    indent=2,
                )
            if "error" in json_data and not json_data.get("success", False):
                err = json_data.get("error") or json_data.get("message") or "Unknown error"
                return json.dumps(
                    {"status": "ᴇʀʀᴏʀ", "message": f"❌ {escape_html(str(err))}"},
                    ensure_ascii=False,
                    indent=2,
                )
            if "status" in json_data and str(json_data.get("status")).lower() == "error":
                err = json_data.get("message") or json_data.get("error") or "Request failed"
                return json.dumps(
                    {"status": "ᴇʀʀᴏʀ", "message": f"❌ {escape_html(str(err))}"},
                    ensure_ascii=False,
                    indent=2,
                )

        try:
            return json.dumps(json_data, ensure_ascii=False, indent=2)
        except TypeError:
            return str(json_data)

    return build_error_message(last_code, last_detail)

# =========================================================
# =======================  MENUS  =========================
# =========================================================
def main_menu_keyboard():
    keyboard = [
        [{"text": "📱 ɴᴜᴍʙᴇʀ"},     {"text": "📞 ᴛʀᴜᴇᴄᴀʟʟᴇʀ"}],
        [{"text": "📷 ɪɴsᴛᴀɢʀᴀᴍ"}, {"text": "🚗 ᴠᴇʜɪᴄʟᴇ"}],
        [{"text": "🚨 ᴄʜᴀʟʟᴀɴ"},   {"text": "👥 ғᴀᴍɪʟʏ"}],
        [{"text": "👤 ᴛᴇʟᴇɢʀᴀᴍ"},   {"text": "📱 ᴘᴀᴋ ɴᴜᴍ"}],
        [{"text": "🆔 ᴄɴɪᴄ"},      {"text": "🆔 ᴘᴀɴ"}],
        [{"text": "🏦 ɪғsᴄ"},      {"text": "📱 ɪᴍᴇɪ"}],
        [{"text": "🐙 ɢɪᴛʜᴜʙ"},    {"text": "🔐 ᴊᴡᴛ"}],
        [{"text": "📧 ᴍᴀɪʟ"},      {"text": "🌐 ɪᴘ"}],
        [{"text": "💳 ᴜᴘɪ ɪɴғᴏ"}],
    ]
    return json.dumps(
        {"keyboard": keyboard, "resize_keyboard": True},
        ensure_ascii=False,
    )

def show_main_menu(chat_id):
    text = (
        "👁‍🗨 𝐓ʜᴇ𝐎ʀᴀᴄʟᴇ𝐄ʏᴇs 𝐎sɪɴᴛ 𝐁ᴏᴛ - ᴠᴇʀsɪᴏɴ 2.0\n\n"
        "✅ ᴘʀɪᴠᴀᴄʏ ᴘʀᴏᴛᴇᴄᴛᴇᴅ\n\n"
        "👑 ᴏᴡɴᴇʀ - KAVY X\n\n"
        "✨ ғʀᴇᴇ & ᴜɴʟɪᴍɪᴛᴇᴅ ᴜsᴀɢᴇ!\n\n"
        "📌 ᴄʟɪᴄᴋ ᴀɴʏ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ sᴛᴀʀᴛ ᴀ ʟᴏᴏᴋᴜᴘ.\n"
        "✨ ʙᴏᴛ ᴡɪʟʟ ᴀsᴋ ʏᴏᴜ ғᴏʀ ᴛʜᴇ ᴠᴀʟᴜᴇ."
    )
    tg_send(chat_id, text, {"reply_markup": main_menu_keyboard()})

# =========================================================
# =====================  OSINT RUN  =======================
# =========================================================
def run_osint(chat_id, command_key, user_input, message_id):
    meta = COMMAND_META[command_key]
    api_template = DEFAULT_APIS.get(meta["api_key"])
    if not api_template:
        tg_send(chat_id, escape_html(f"ᴀᴘɪ ᴛᴇᴍᴘʟᴀᴛᴇ ғᴏʀ '{meta['api_key']}' ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ."))
        return

    api_url = build_api_url(api_template, meta["placeholder"], user_input)

    loading = tg_send(
        chat_id,
        f"⏳ ᴘʀᴏᴄᴇssɪɴɢ {meta['title']} ғᴏʀ <b>{escape_html(user_input)}</b>...\n",
    )

    result = fetch_api(api_url, command_key)

    if loading and loading.get("result"):
        try:
            tg_request("deleteMessage", {
                "chat_id": chat_id,
                "message_id": loading["result"]["message_id"],
            })
        except Exception:
            pass

    if not isinstance(result, str):
        result = str(result)

    safe_title = escape_html(meta["title"])
    safe_input = escape_html(user_input)

    prefix = f"<b>{safe_title} ʀᴇsᴜʟᴛs ғᴏʀ {safe_input}:</b>\n\n<pre><code>"
    suffix = "</code></pre>"
    output = prefix + escape_html(result) + suffix

    if len(output) > 4000:
        content = escape_html(result)
        max_chunk = 3800
        chunks = []
        while len(content) > max_chunk:
            cut = content.rfind("\n", 0, max_chunk)
            if cut == -1:
                cut = max_chunk
            chunks.append(content[:cut])
            content = content[cut:]
        if content:
            chunks.append(content)

        for i, chunk in enumerate(chunks):
            part = (prefix if i == 0 else "<pre><code>") + chunk + suffix
            tg_send(chat_id, part)
    else:
        tg_send(chat_id, output)

# =========================================================
# ==================  UPDATE HANDLER  =====================
# =========================================================
def handle_update(update):
    if "message" not in update:
        return
    msg = update["message"]
    if "chat" not in msg or "id" not in msg["chat"] or "text" not in msg:
        return

    chat_id = msg["chat"]["id"]
    chat_type = msg["chat"].get("type", "private")
    user_id = msg.get("from", {}).get("id", 0)
    text = msg["text"].strip()
    message_id = msg.get("message_id", 0)

    if chat_type != "private":
        tg_send(
            chat_id,
            "❌ ᴛʜɪs ʙᴏᴛ ᴏɴʟʏ ᴡᴏʀᴋs ɪɴ <b>ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ</b>.\n\nᴘʟᴇᴀsᴇ ᴅᴍ ᴍᴇ ᴛᴏ ᴜsᴇ ɪᴛ.",
            {"reply_to_message_id": message_id},
        )
        return

    if text.startswith("/"):
        cmd = text.split(" ")[0].lower()
        if cmd in ("/start", "/menu"):
            show_main_menu(chat_id)
            return
        if cmd == "/help":
            help_text = (
                "𝐓ʜᴇ𝐎ʀᴀᴄʟᴇ𝐄ʏᴇs 𝐎sɪɴᴛ 𝐁ᴏᴛ - 𝐇ᴇʟᴘ\n\n"
                "✨ ғʀᴇᴇ & ᴜɴʟɪᴍɪᴛᴇᴅ ᴜsᴀɢᴇ!\n\n"
                "<b>ʜᴏᴡ ᴛᴏ ᴜsᴇ:</b>\n"
                "1️⃣ sᴇɴᴅ /start ᴛᴏ ᴏᴘᴇɴ ᴛʜᴇ ᴍᴇɴᴜ\n"
                "2️⃣ ᴄʟɪᴄᴋ ᴀ ʟᴏᴏᴋᴜᴘ ᴛʏᴘᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ\n"
                "3️⃣ sᴇɴᴅ ᴛʜᴇ ᴠᴀʟᴜᴇ ᴡʜᴇɴ ᴀsᴋᴇᴅ\n\n"
                "<b>ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
                "/start - ᴏᴘᴇɴ ᴍᴀɪɴ ᴍᴇɴᴜ\n"
                "/menu - ᴏᴘᴇɴ ᴍᴀɪɴ ᴍᴇɴᴜ\n"
                "/help - sʜᴏᴡ ᴛʜɪs ʜᴇʟᴘ"
            )
            tg_send(chat_id, help_text)
            return
        return

    state = load_state()
    key = str(user_id)

    if text in BUTTON_TO_COMMAND:
        command_key = BUTTON_TO_COMMAND[text]
        meta = COMMAND_META[command_key]
        state[key] = {"command": command_key}
        save_state(state)
        tg_send(chat_id, meta["prompt"])
        return

    if key not in state or "command" not in state[key]:
        return
    command_key = state[key]["command"]
    if command_key not in COMMAND_META:
        state.pop(key, None)
        save_state(state)
        return
    meta = COMMAND_META[command_key]

    user_input = text
    if command_key in ("num", "imei", "family", "pak_number", "cnic", "truecaller"):
        user_input = re.sub(r"\D+", "", user_input)
    elif command_key in ("pan", "ifsc", "vehicle", "challan"):
        user_input = user_input.replace(" ", "").upper()
    elif command_key in ("instagram", "github"):
        user_input = user_input.replace("@", "").strip()

    if meta["pattern"]:
        if not re.match(meta["pattern"], user_input):
            tg_send(
                chat_id,
                f"❌ {meta['error']}\n\nᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴏʀ ᴄʟɪᴄᴋ /menu.",
                {"reply_to_message_id": message_id},
            )
            return

    state.pop(key, None)
    save_state(state)

    run_osint(chat_id, command_key, user_input, message_id)

# =========================================================
# =====================  POLLING  =========================
# =========================================================
def acquire_instance_lock():
    """Prevent multiple copies of this script polling from the same machine."""
    global _INSTANCE_LOCK_HANDLE

    lock_handle = open(LOCK_FILE, "a+b")
    try:
        lock_handle.seek(0)
        if not lock_handle.read(1):
            lock_handle.write(b"\0")
            lock_handle.flush()
        lock_handle.seek(0)

        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
        lock_handle.close()
        if e.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
            return False
        raise

    _INSTANCE_LOCK_HANDLE = lock_handle
    return True

def delete_webhook_if_any():
    """Delete any existing webhook so polling works."""
    try:
        res = tg_request("deleteWebhook", {"drop_pending_updates": "true"})
        if res and res.get("ok"):
            print("✔ Old webhook removed (if any).")
        else:
            print("ℹ Webhook delete response:", res)
    except Exception as e:
        print("⚠ Could not delete webhook:", e)

def get_me():
    try:
        res = tg_request("getMe", {})
        if res and res.get("ok"):
            u = res["result"]
            print(f"✔ Bot connected: @{u.get('username')} ({u.get('first_name')})")
            return True
        print("✘ getMe failed:", res)
        return False
    except Exception as e:
        print("✘ getMe error:", e)
        return False

def polling_loop():
    offset = 0
    print("🚀 Bot started in POLLING mode. Press Ctrl+C to stop.\n")
    while True:
        try:
            res = tg_request("getUpdates", {
                "offset": offset,
                "timeout": 30,
                "allowed_updates": json.dumps(["message"]),
            })

            if not res or not res.get("ok"):
                if isinstance(res, dict) and res.get("error_code") == 409:
                    message = (
                        "Telegram rejected getUpdates because another bot instance is "
                        "already polling. Stop the other instance (including on any "
                        "other machine or hosting service) before restarting this one."
                    )
                    log_msg(message)
                    print(f"✘ {message}")
                    break
                log_msg(f"getUpdates bad response: {res}")
                time.sleep(3)
                continue

            for update in res.get("result", []):
                update_id = update.get("update_id", 0)
                offset = update_id + 1
                try:
                    handle_update(update)
                except Exception as e:
                    log_msg(f"handle_update error: {e}")

        except KeyboardInterrupt:
            print("\n👋 Bot stopped.")
            break
        except Exception as e:
            log_msg(f"polling_loop error: {e}")
            time.sleep(3)

# =========================================================
# ======================  MAIN  ===========================
# =========================================================
if __name__ == "__main__":
    print("=" * 50)
    print("OSINT Bot Started- Polling Mode")
    print("=" * 50)

    if not acquire_instance_lock():
        print("✘ Another copy of this bot is already running on this machine.")
        exit(1)

    if not get_me():
        print("✘ Bot token invalid. Exiting.")
        exit(1)

    delete_webhook_if_any()
    time.sleep(1)
    polling_loop()