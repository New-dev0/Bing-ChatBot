# Copyright New-dev0 2022
# https://github.com/New-dev0/BING-CHATBOT


import logging
import aiohttp
from decouple import config

from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.tl.custom import Button
from telethon.events import NewMessage
from random import choice

API_ID = config("API_ID", default=6, cast=int)
API_HASH = config("API_HASH", default="eb06d4abfb49dc3eeb1aeb98ae0f581e")
BOT_TOKEN = config("BOT_TOKEN", default=None)

if not BOT_TOKEN:
    print("'BOT_TOKEN' not found!\nExiting...")
    exit()

logging.basicConfig(level=logging.INFO)

client = TelegramClient(None, api_id=API_ID, api_hash=API_HASH)
client.start(bot_token=BOT_TOKEN)

API_URL = "https://services.bingapis.com/sydney/chat"

HI_STRINGS = ["hi", "hello", "hey"]

CONVERSATION_HANDLER = {}
SELF = client.loop.run_until_complete(client.get_me())


@client.on(NewMessage(func= lambda x: x.text or x.sticker))
async def message_handler(event : Message):
    if not event.is_private:
        reply = None
        if event.is_reply:
            reply = await event.get_reply_message()
        if not (event.mentioned or (reply and reply.sender_id == SELF.id)):
            return
    chat = event.chat_id
    if event.text.lower() == "/start":
        msg = choice(HI_STRINGS)

        # Refresh Conversation on /start
        if CONVERSATION_HANDLER.get(chat):
            del CONVERSATION_HANDLER[chat]
    elif event.sticker and event.file.emoji:
        msg = event.file.emoji
    else:
        msg = event.text
    json = {"userMessageText":msg}
    c_id = CONVERSATION_HANDLER.get(chat)
    if c_id:
        json.update({"conversationId": c_id})

    async with aiohttp.ClientSession() as ses:
        async with ses.post(API_URL, json=json) as res:
            output = await res.json()
    try:
        msgs = output["messages"]
    except KeyError:
        if "has expired." in output["result"]["message"]:
            del CONVERSATION_HANDLER[chat]
            await message_handler(event)
        else:
            print(output)
        return
    for message in msgs:
        if message["author"] == "bot":
            text = message["text"]
            buttons = []
            if message.get("hiddenText"):
                text += "\n\n__" + message["hiddenText"] + "__"
            if message.get("sourceName"):
                buttons.append([Button.url(message["sourceName"], message["sourceUrl"])])
            if message.get("linkUrl"):
                buttons.append([Button.url("View on Bing", message["linkUrl"])])
            await event.reply(message["text"], buttons=buttons or None)
    CONVERSATION_HANDLER.update({chat:output["conversationId"]})


with client:
    print(f"Done! Send /start to @{SELF.username}...")
    client.run_until_disconnected()