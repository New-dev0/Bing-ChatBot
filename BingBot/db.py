# Copyright New-dev0 2022
# https://github.com/New-dev0/BING-CHATBOT

import json
import os
from io import BytesIO
from . import client, Var, LOG

JSONDB = None

if Var.CH_DB and Var.CH_MSG_ID:
    MSG = client.loop.run_until_complete(
        client.get_messages(Var.CH_DB, ids=Var.CH_MSG_ID)
    )
    if MSG:
        LOG.info("Downloading last DB file...")
        JSONDB_ = client.loop.run_until_complete(MSG.download_media())
        if JSONDB_:
            JSONDB = json.load(open(JSONDB_, "r"))
            os.remove(JSONDB_)

if not JSONDB:
    JSONDB = {"users": [], "language": {}}


async def save_json():
    if Var.CH_DB:
        file = BytesIO(json.dumps(JSONDB, indent=1).encode())
        file.name = "Bing-DB.json"
        if Var.CH_MSG_ID:
            try:
                return await client.edit_message(Var.CH_DB, Var.CH_MSG_ID, file=file)
            except Exception as er:
                LOG.exception(er)
                # Todo: Some errors need to be specifically Handled
                # MessageIDInvalidError, ChatWriteAdminForb
        else:
            text = "Add `{}` to Your Env Var `CH_MSG_ID`."
            try:
                msg = await client.send_message(Var.CH_DB, file=file)
                Var.CH_MSG_ID = msg.id
            except Exception as er:
                LOG.exception(er)
                msg = None
            if msg:
                text = text.format(msg.id)
                LOG.info(text)
                return await msg.edit(text)
