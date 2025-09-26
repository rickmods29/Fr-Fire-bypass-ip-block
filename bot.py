import telebot, sqlite3, re, time, threading
from telebot import types
from flask import Flask
from datetime import datetime, timedelta

# ---------------- CONFIG -----------------
TOKEN = "8229638335:AAE0LVoNeFyUd5Px11EJE0ViFHMbplNlWFQ"
OWNER_ID = 8211257334
DEFAULT_MUTE_SECONDS = 2*60*60  # default auto-mute for links
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cur = conn.cursor()

# Tables
cur.execute("""CREATE TABLE IF NOT EXISTS blacklist(word TEXT PRIMARY KEY)""")
cur.execute("""CREATE TABLE IF NOT EXISTS chat_settings(
    chat_id INTEGER PRIMARY KEY,
    antilink INTEGER DEFAULT 1,
    automute_seconds INTEGER DEFAULT ?,
    welcome_text TEXT DEFAULT 'WELCOME @USERNAME TO RICK MODS X CHAT',
    welcome_media_id TEXT DEFAULT NULL,
    welcome_media_type TEXT DEFAULT NULL
)""",(DEFAULT_MUTE_SECONDS,))
cur.execute("""CREATE TABLE IF NOT EXISTS forward_map(
    owner_msg_id INTEGER PRIMARY KEY,
    user_chat_id INTEGER,
    user_msg_id INTEGER,
    timestamp INTEGER
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS filters(
    chat_id INTEGER,
    keyword TEXT,
    reply TEXT,
    PRIMARY KEY(chat_id, keyword)
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS notes(
    chat_id INTEGER,
    name TEXT,
    content TEXT,
    PRIMARY KEY(chat_id, name)
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS dynamic_cmds(
    cmd TEXT PRIMARY KEY,
    content TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS warnings(
    chat_id INTEGER,
    user_id INTEGER,
    count INTEGER,
    PRIMARY KEY(chat_id, user_id)
)""")
conn.commit()

# ---------------- PATTERNS ----------------
link_pattern = re.compile(r"(t.me|telegram.me|https?://|.com|.ir|.net|.gg|.xyz|www\.)", re.IGNORECASE)
lang_pattern = re.compile(r'[\u0600-\u06FF\u4E00-\u9FFF\u0400-\u04FF]')

# ---------------- UTILITIES ----------------
def is_owner(user_id): return user_id == OWNER_ID
def is_admin(chat_id, user_id):
    try: return bot.get_chat_member(chat_id, user_id).status in ("administrator","creator")
    except: return False

def add_black(word): cur.execute("INSERT OR IGNORE INTO blacklist(word) VALUES(?)",(word.lower(),)); conn.commit()
def remove_black(word): cur.execute("DELETE FROM blacklist WHERE word=?",(word.lower(),)); conn.commit()
def list_black(): cur.execute("SELECT word FROM blacklist"); return [r[0] for r in cur.fetchall()]

def get_setting(chat_id, field):
    cur.execute(f"SELECT {field} FROM chat_settings WHERE chat_id=?",(chat_id,))
    r = cur.fetchone()
    return r[0] if r else None

def set_setting(chat_id, field, value):
    cur.execute(f"INSERT OR REPLACE INTO chat_settings(chat_id,{field}) VALUES(?,?)",(chat_id,value))
    conn.commit()

def map_forward(owner_msg_id, user_chat_id, user_msg_id):
    cur.execute("INSERT OR REPLACE INTO forward_map(owner_msg_id,user_chat_id,user_msg_id,timestamp) VALUES(?,?,?,?)",
                (owner_msg_id,user_chat_id,user_msg_id,int(time.time())))
    conn.commit()

def lookup_forward(owner_msg_id):
    cur.execute("SELECT user_chat_id,user_msg_id FROM forward_map WHERE owner_msg_id=?",(owner_msg_id,))
    return cur.fetchone()

def parse_time(text):
    seconds=0
    for value,unit in re.findall(r'(\d+)([smhd])', text):
        value=int(value)
        if unit=='s': seconds+=value
        elif unit=='m': seconds+=value*60
        elif unit=='h': seconds+=value*3600
        elif unit=='d': seconds+=value*86400
    return seconds

def owner_only(func):
    def wrapper(m):
        if not is_owner(m.from_user.id): return bot.reply_to(m,"Only owner can use this command.")
        return func(m)
    return wrapper

def admin_only(func):
    def wrapper(m):
        if not (is_owner(m.from_user.id) or is_admin(m.chat.id,m.from_user.id)):
            return bot.reply_to(m,"Only admins can use this command.")
        return func(m)
    return wrapper

# ---------------- MODERATION ----------------
def handle_link_blacklist(message):
    text = message.text or message.caption or ""
    if not text: return
    if message.from_user and (is_owner(message.from_user.id) or (message.chat.type!="private" and is_admin(message.chat.id,message.from_user.id))):
        return
    for w in list_black():
        if w.lower() in text.lower():
            try: bot.delete_message(message.chat.id,message.message_id)
            except: pass
            return "black"
    if get_setting(message.chat.id,"antilink") and link_pattern.search(text):
        try:
            bot.delete_message(message.chat.id,message.message_id)
            seconds = get_setting(message.chat.id,"automute_seconds") or DEFAULT_MUTE_SECONDS
            bot.restrict_chat_member(message.chat.id,message.from_user.id,can_send_messages=False,until_date=int(time.time()+seconds))
        except: pass
        return "link"
    if lang_pattern.search(text):
        try: bot.delete_message(message.chat.id,message.message_id)
        except: pass
        return "lang"
    return None

# ---------------- PRIVATE FORWARD ----------------
def forward_to_owner(message):
    user=message.from_user
    header=f"<b>Message from</b> {user.first_name}"
    if user.username: header+=f" (@{user.username})"
    header+=f"\n<b>id:</b> <code>{user.id}</code>\n\n"
    try:
        if message.content_type=="text": sent=bot.send_message(OWNER_ID,header+message.text)
        elif message.content_type=="photo": sent=bot.send_photo(OWNER_ID,message.photo[-1].file_id,caption=header)
        elif message.content_type=="video": sent=bot.send_video(OWNER_ID,message.video.file_id,caption=header)
        elif message.content_type=="document": sent=bot.send_document(OWNER_ID,message.document.file_id,caption=header)
        elif message.content_type=="voice": sent=bot.send_voice(OWNER_ID,message.voice.file_id,caption=header)
        elif message.content_type=="sticker": sent=bot.send_sticker(OWNER_ID,message.sticker.file_id)
        if message.content_type=="text": map_forward(sent.message_id,message.chat.id,message.message_id)
    except Exception as e: print("Forward failed:",e)

# ---------------- MESSAGE HANDLER ----------------
@bot.message_handler(content_types=['text','photo','video','document','sticker','voice','video_note'])
def on_message(m):
    # Private messages
    if m.chat.type=="private" and not is_owner(m.from_user.id):
        forward_to_owner(m); return
    # Group messages
    if m.chat.type in ("group","supergroup"):
        handle_link_blacklist(m)
        # Dynamic commands
        cur.execute("SELECT cmd,content FROM dynamic_cmds")
        for cmd,content in cur.fetchall():
            if (m.text or "").strip().lower()==f"/{cmd.lower()}": bot.send_message(m.chat.id,content)
        # Filters
        cur.execute("SELECT keyword,reply FROM filters WHERE chat_id=?",(m.chat.id,))
        for k,r in cur.fetchall():
            if k.lower() in (m.text or "").lower(): bot.reply_to(m,r)
        # Notes
        cur.execute("SELECT content FROM notes WHERE chat_id=? AND name=?",(m.chat.id,(m.text or "").strip()))
        r=cur.fetchone()
        if r: bot.reply_to(m,r[0])

# ---------------- WELCOME ----------------
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new(m):
    text=get_setting(m.chat.id,"welcome_text") or "WELCOME @USERNAME TO RICK MODS X CHAT"
    media_id=get_setting(m.chat.id,"welcome_media_id")
    media_type=get_setting(m.chat.id,"welcome_media_type")
    for user in m.new_chat_members:
        msg=text.replace("@USERNAME",f"@{user.username}" if user.username else user.first_name)\
                .replace("{first}",user.first_name)\
                .replace("{last}",user.last_name or "")\
                .replace("{chatname}",m.chat.title)
        try:
            if media_id and media_type:
                if media_type=="photo": bot.send_photo(m.chat.id,media_id,caption=msg)
                elif media_type=="video": bot.send_video(m.chat.id,media_id,caption=msg)
            else: bot.send_message(m.chat.id,msg)
        except: pass

# ---------------- OWNER PRIVATE HANDLER ----------------
@bot.message_handler(func=lambda m:m.chat.type=="private" and is_owner(m.from_user.id))
def owner_private(m):
    # Reply to user
    if m.reply_to_message:
        mapping=lookup_forward(m.reply_to_message.message_id)
        if mapping:
            user_chat_id,_=mapping
            try: bot.send_message(user_chat_id,m.text)
            except: bot.send_message(OWNER_ID,"Failed to send message")
    # Dynamic command add
    if m.text and m.text.startswith("/add "):
        parts=m.text.split(maxsplit=2)
        if len(parts)<3: return bot.send_message(OWNER_ID,"Usage: /add <cmd> <text>")
        cur.execute("INSERT OR REPLACE INTO dynamic_cmds(cmd,content) VALUES(?,?)",(parts[1],parts[2]))
        conn.commit()
        bot.send_message(OWNER_ID,f"Command /{parts[1]} added.")

# ---------------- KEEPALIVE ----------------
app = Flask('')
@app.route('/')
def home(): return "Bot is alive"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# ---------------- RUN ----------------
if __name__=="__main__":
    threading.Thread(target=run_flask).start()
    print("Bot started...")
    bot.infinity_polling(timeout=60,long_polling_timeout=60)