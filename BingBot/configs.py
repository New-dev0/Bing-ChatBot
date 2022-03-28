# Copyright New-dev0 2022
# https://github.com/New-dev0/BING-CHATBOT


from decouple import config


class Var:
    API_ID = config("API_ID", default=6, cast=int)
    API_HASH = config("API_HASH", default="eb06d4abfb49dc3eeb1aeb98ae0f581e")
    BOT_TOKEN = config("BOT_TOKEN", default=None)
    OWNER_ID = config("OWNER_ID", default=0, cast=int)
    CH_DB = config("CH_DB_ID", cast=int, default=0)
    CH_MSG_ID = config("CH_MSG_ID", cast=int, default=0)

    LOG_CHAT_ID = config("LOG_CHAT_ID", cast=int, default=0)

    DB_UPDATE_DELAY = config("DB_UPD_DELAY", cast=int, default=60 * 3)
