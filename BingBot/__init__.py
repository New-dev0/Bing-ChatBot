# Copyright New-dev0 2022
# https://github.com/New-dev0/BING-CHATBOT

import logging
from .configs import Var
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("BingBot")

if not Var.BOT_TOKEN:
    LOG.error("'BOT_TOKEN' not found!\nExiting...")
    exit()

client = TelegramClient(None, api_id=Var.API_ID, api_hash=Var.API_HASH)
client.start(bot_token=Var.BOT_TOKEN)

from .db import JSONDB, save_json

sched = AsyncIOScheduler()
sched.add_job(save_json, "interval", hours=Var.DB_UPDATE_DELAY)
sched.start()
LOG.info(f"Enabled DB Auto Saving after every {Var.DB_UPDATE_DELAY} MINUTES.")
