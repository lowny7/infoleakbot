from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
from json import loads

# Carrega configuração
with open("./config.json", "r") as f:
    cfg = loads(f.read())
with open("./strings.json", "r") as f:
    strings = loads(f.read())

# Espera-se que config.json contenha: bot_token, api_id, api_hash, dbLink
bot_token = cfg.get("bot_token")
api_id = cfg.get("api_id")
api_hash = cfg.get("api_hash")
dbLink = cfg.get("dbLink")

# Cliente do Telegram (modo bot)
app = Client(
    "main_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token
)

# Banco de dados (SQLAlchemy sync)
engine = create_engine(dbLink)
base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class EntryTG40M(base):
    __tablename__ = 'tg40m'
    index = Column(Integer, primary_key=True)
    name = Column(String)
    fname = Column(String)
    phone = Column(String)
    uid = Column(String)
    nik = Column(String)
    wo = Column(String)

    def __init__(self, name, fname, phone, uid, nik, wo):
        self.name = name
        self.fname = fname
        self.phone = phone
        self.uid = uid
        self.nik = nik
        self.wo = wo

class EntryEYE(base):
    __tablename__ = 'eye'
    id = Column(String, primary_key=True)
    phone = Column(String)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)

    def __init__(self, id, phone, username, first_name, last_name):
        self.id = id
        self.phone = phone
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

base.metadata.create_all(engine)

### CLEANER ###

def cleaner(dirty):
    clean = dirty

    if getattr(dirty, 'phone', None):
        clean.phone = dirty.phone
    else:
        clean.phone = " "

    if getattr(dirty, 'username', None):
        clean.username = dirty.username
    else:
        clean.username = " "

    if getattr(dirty, 'first_name', None):
        clean.first_name = dirty.first_name
    else:
        clean.first_name = " "

    if getattr(dirty, 'last_name', None):
        clean.last_name = dirty.last_name
    else:
        clean.last_name = " "

    return clean

### METHODS ###

@app.on_message(filters.new_chat_members)
def leaveUnauthChat(client, message):
    try:
        if message.new_chat_members[0].id == client.me.id:
            app.send_message(chat_id=message.chat.id, text=strings["dm"])
            app.leave_chat(message.chat.id)
    except Exception:
        return

@app.on_message(filters.command("start"))
def start(client, message):
    app.send_message(
        chat_id=message.chat.id,
        text=strings["start"],
        reply_markup=ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton(text="/tg40m"),
                    KeyboardButton(text="/eyeofgod")
                ]
            ]
        ),
        reply_to_message_id=message["message_id"]
    )

@app.on_message(filters.command("privacy"))
def privacy(client, message):
    app.send_message(chat_id=message.chat.id, text=strings["privacy"], reply_to_message_id=message["message_id"])

@app.on_message(filters.command("eyeofgod"))
def eyeofgod(client, message):
    if message.chat.type == "private":
        looking = app.send_message(chat_id=message.chat.id, text="Ищем в базе...", reply_to_message_id=message["message_id"])
        obj = session.query(EntryEYE).filter(EntryEYE.id == str(message.from_user.id)).all()
        if len(obj) == 0:
            app.edit_message_text(chat_id=message.chat.id, message_id=looking.message_id, text=strings["congrats_eye"], parse_mode="markdown")
        else:
            n = len(obj)
            raz = 'раз'
            if n % 10 in (2, 3, 4):
                raz = 'раза'
            if n % 100 in (12, 13, 14):
                raz = 'раз'
            toUser = f"Увы, вы найдены в базе {n} {raz}! Вот ваши данные..."
            for occurance in obj:
                mention = cleaner(occurance)
                toUser += f"\n\nУникальный ID в Telegram: `{mention.id}`\nТелефон: `{mention.phone}`\nИмя пользователя: `{mention.username}`\nИмя: `{mention.first_name}`\nФамилия: `{mention.last_name}`"
            toUser += strings["safe_eye"]
            app.edit_message_text(chat_id=message.chat.id, message_id=looking.message_id, text=toUser, parse_mode="markdown")

@app.on_message(filters.command("tg40m"))
def tg40m(client, message):
    if message.chat.type == "private":
        looking = app.send_message(chat_id=message.chat.id, text="Ищем в базе...", reply_to_message_id=message["message_id"])
        obj = session.query(EntryTG40M).filter(EntryTG40M.uid == str(message.from_user.id)).all()
        if len(obj) == 0:
            app.edit_message_text(chat_id=message.chat.id, message_id=looking.message_id, text=strings["congrats_tg40m"], parse_mode="markdown")
        else:
            n = len(obj)
            raz = 'раз'
            if n % 10 in (2, 3, 4):
                raz = 'раза'
            if n % 100 in (12, 13, 14):
                raz = 'раз'
            toUser = f"Увы, вы найдены в базе {n} {raz}! Вот ваши данные..."
            for mention in obj:
                if mention.wo.strip() == "":
                    date = ""
                else:
                    date = datetime.fromtimestamp(int(mention.wo.strip("0")))
                toUser += f"\n\nИмя: `{mention.name}`\nФамилия: `{mention.fname}`\nТелефонный номер: `{mention.phone}`\nУникальный ID в Telegram: `{mention.uid}`\nИмя пользователя: `{mention.nik}`\nВремя последней сетевой активности: `{date}`"
            toUser += strings["safe_tg40m"]
            app.edit_message_text(chat_id=message.chat.id, message_id=looking.message_id, text=toUser, parse_mode="markdown")

@app.on_message()
def checkState(client, message):
    app.send_message(message["chat"]["id"], strings["invalid"], reply_to_message_id=message["message_id"])

if __name__ == "__main__":
    app.run()
