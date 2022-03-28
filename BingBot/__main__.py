# Copyright New-dev0 2022
# https://github.com/New-dev0/BING-CHATBOT

import re
import aiohttp
from telethon.tl.types import Message
from telethon.tl.custom import Button
from telethon.events import NewMessage, CallbackQuery
import asyncio
from telethon.errors.rpcerrorlist import (
    FloodWaitError,
    UserBlockedError,
    ChatWriteForbiddenError,
)
from random import choice

from google_trans_new.constant import LANGUAGES
from google_trans_new import google_translator
from . import client, JSONDB, save_json, LOG, Var


API_URL = "https://services.bingapis.com/sydney/chat"
HI_STRINGS = ["hi", "hello", "hey"]
IGNORE_CMDS = ("/setlanguage", "/broadcast", "/stats", "/savedb", "/source")
CONVERSATION_HANDLER = {}
SELF = client.loop.run_until_complete(client.get_me())
translator = google_translator()


def split_list(lis, index):
    new_ = []
    while lis:
        new_.append(lis[:index])
        lis = lis[index:]
    return new_


Buttons = [Button.inline(LANGUAGES[lang].upper(), f"st-{lang}") for lang in LANGUAGES]
# 2 Rows
Buttons = split_list(Buttons, 2)
# 5 Columns
Buttons = split_list(Buttons, 5)


def translate(text, sender=None, to_bing=False):
    if to_bing:
        return translator.translate(text, lang_tgt="en")
    get_ = JSONDB["language"].get(str(sender))
    if get_:
        try:
            return translator.translate(text, lang_tgt=get_)
        except Exception as er:
            LOG.exception(er)
    return text


@client.on(NewMessage(func=lambda x: x.text or x.sticker, incoming=True))
async def message_handler(event: Message):
    if event.chat_id not in JSONDB["users"]:
        JSONDB["users"].append(event.chat_id)
    if event.text.lower().startswith(IGNORE_CMDS):
        return
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
    json = {"userMessageText": translate(msg, to_bing=True)}
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
            LOG.error(f"KeyError: {output}")
        return
    for message in msgs:
        if message["author"] == "bot":
            text = message["text"]
            buttons = []
            if message.get("hiddenText"):
                text += "\n\n__" + message["hiddenText"] + "__"
            if message.get("sourceName"):
                buttons.append(
                    [Button.url(message["sourceName"], message["sourceUrl"])]
                )
            if message.get("linkUrl"):
                buttons.append([Button.url("View on Bing", message["linkUrl"])])
            await event.reply(translate(message["text"], chat), buttons=buttons or None)
    CONVERSATION_HANDLER.update({chat: output["conversationId"]})


@client.on(
    NewMessage(
        pattern=f"/setlanguage($|@{SELF.username})",
        forwards=False,
        func=lambda E: E.is_private,
    )
)
async def set_language(event):
    bts = Buttons[0].copy()
    bts.append([Button.inline("Next ▶", "btsh"), Button.inline("Cancel ❌", "cncl")])
    await event.reply("Choose your desired language..", buttons=bts)


@client.on(CallbackQuery(data=re.compile("btsh(.*)")))
async def click_next(event):
    data = event.data_match.group(1).decode("utf-8")
    if not data:
        val = 1
    else:
        prev_or_next = data[0]
        val = int(data[1:])
        if prev_or_next == "p":
            val -= 1
        else:
            val += 1
    try:
        bt = Buttons[val].copy()
    except IndexError:
        val = 0
        bt = Buttons[0].copy()
    if val == 0:
        bt.append([Button.inline("Next ▶", "btsh"), Button.inline("Cancel ❌", "cncl")])
    else:
        bt.extend(
            [
                [
                    Button.inline("◀ Prev", f"btshp{val}"),
                    Button.inline("Next ▶", f"btshn{val}"),
                ],
                [Button.inline("Cancel ❌", "cncl")],
            ]
        )
    await event.edit(buttons=bt)


@client.on(CallbackQuery(pattern="cncl"))
async def maggie(event):
    await event.delete()


@client.on(CallbackQuery(data=re.compile("st-(.*)")))
async def set_lang(event):
    match = event.data_match.group(1).decode("utf-8")
    if match == "en":
        if JSONDB["language"].get(str(event.sender_id)):
            del JSONDB["language"][str(event.sender_id)]
    else:
        JSONDB["language"][str(event.sender_id)] = match
    code_lang = {code: name for code, name in LANGUAGES.items()}
    name = code_lang[match]
    name = name[0].upper() + name[1:]
    await event.edit(f"Language successfully changed to {name} !")


@client.on(NewMessage(pattern="^/source$"))
async def source_cmd(event):
    await event.reply("Here is my Source!\nhttps://github.com/New-dev0/Bing-Chatbot")


if Var.OWNER_ID:

    @client.on(
        NewMessage(pattern=f"^/savedb($|@{SELF.username})", from_users=Var.OWNER_ID)
    )
    async def save_db(event):
        msg = await save_json()
        if msg:
            if not msg.chat.username:
                msglink = f"https://t.me/c/{msg.chat.id}/{msg.id}"
            else:
                msglink = f"https://t.me/{msg.chat.username}/{msg.id}"
            return await event.respond(f"Saved Successfully [here]({msglink})!")
        await event.respond("Something Went Wrong!")

    @client.on(NewMessage(pattern="^/broadcast", from_users=Var.OWNER_ID))
    async def broadcast(event):
        try:
            msg = event.text.split(maxsplit=1)[1]
        except IndexError:
            if event.is_reply:
                msg = await event.get_reply_message()
            else:
                return await event.respond(
                    "Reply to Message or Provide some text to broadcast..."
                )
        users = JSONDB["users"]
        total = len(users)
        success = 0
        for user in users:
            try:
                await event.client.send_message(user, msg)
                success += 1
                continue
            except FloodWaitError as er:
                LOG.error(er)
                await asyncio.sleep(er.seconds)
            except (ChatWriteForbiddenError, UserBlockedError) as er:
                LOG.info(f"Broadcast: {user} | {er}")
                users.remove(user)
            except Exception as er:
                LOG.error(er)
        await event.reply(
            f"**Broadcast Completed!**\n**Success:** {success}\n"
            + f"**Failed:** {total - success}"
        )

    @client.on(NewMessage(pattern="^/stats$", from_users=Var.OWNER_ID))
    async def stats_message(event):
        await event.reply(f"**Total Users:** {len(JSONDB['users'])}")


with client:
    LOG.info(f"Done! Send /start to @{SELF.username}...")
    client.run_until_disconnected()
    # Start TelegramClient...
