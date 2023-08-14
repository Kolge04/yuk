from logging import getLogger
LOGS = getLogger(__name__)




from . import CallTone_AZ, CallTone_EN, CallTone_TR, CallTone_RU
from modules.databases.mongo.database import get_lang

async def get_str(chat_id: int):
    if await get_lang((chat_id)) == "TR":
        return "TR"
    elif await get_lang((chat_id)) == "EN":
        return "EN"
    elif await get_lang((chat_id)) == "AZ":
        return "AZ"
    elif await get_lang((chat_id)) == "RU":
        return "RU"
    else:
        return "TR"

def lan(lang: str = None):
    if lang.upper() == "TR":
        LAN = CallTone_TR
    elif lang.upper() == "AZ":
        LAN = CallTone_AZ
    elif lang.upper() == "EN":
        LAN = CallTone_EN
    elif lang.upper() == "RU":
        LAN = CallTone_RU
    else:
        LAN = CallTone_TR
    return LAN
  
