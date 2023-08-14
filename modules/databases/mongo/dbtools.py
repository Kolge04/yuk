import asyncio
import datetime
import os
import random
import string
import time
import traceback
from pyrogram import Client
import aiofiles
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    PeerIdInvalid,
    UserIsBlocked,
)

from Config import BROADCAST_AS_COPY, GROUP_SUPPORT, LOG_CHANNEL

from .database import db, mongo_handlers
from pyrogram.types import Message

async def handle_user_status(bot: Client, cmd: Message):
    chat_id = cmd.chat.id
    if not await db.is_user_exist(chat_id):
        if cmd.chat.type == "private":
            await db.add_user(chat_id)
            await bot.send_message(
                LOG_CHANNEL,
                f"```📣 Yeni Bildirim``` \n\n#YENI_KULLANICI **botu başlattı!** \n\n🏷 isim: `{cmd.from_user.first_name}` \n📮 kullanıcı id: `{cmd.from_user.id}` \n🧝🏻‍♂️ profil linki: [{cmd.from_user.first_name}](tg://user?id={cmd.from_user.id})",
            )
        else:
            await db.add_user(chat_id)
            chat = await bot.get_chat(chat_id)
            await bot.send_message(
                LOG_CHANNEL,
                f"```📣 Yeni Bildirim``` \n\n#YENI_GRUP **botu başlattı!** \n\n🏷 Gruba Alan İsim: `{cmd.from_user.first_name}` \n📮 Gruba Alan kullanıcı id: `{cmd.from_user.id}` \n🧝🏻‍♂️ profil linki: [{cmd.from_user.first_name}](tg://user?id={cmd.from_user.id})\n Grubun Adı: {chat.title}\n Grubun ID: {cmd.chat.id}\n Grubun Mesaj Linki( sadece açık gruplar): [Buraya Tıkla](https://t.me/c/{cmd.chat.id}/1)",
            )

    ban_status = await db.get_ban_status(chat_id)
    if ban_status["is_banned"]:
        if int(
            (
                datetime.date.today()
                - datetime.date.fromisoformat(ban_status["banned_on"])
            ).days
        ) > int(ban_status["ban_duration"]):
            await db.remove_ban(chat_id)
        else:
            if cmd.chat.type == "private":
                await bot.send_message(cmd.chat.id,
                    f"Üzgünüm, yasaklandınız! Çözüm için @{GROUP_SUPPORT}'a bekleriz."
                )
            else:
                await bot.send_message(cmd.chat.id,
                    f"Üzgünüm, grubunuz karalisteye alındı! Burada daha fazla kalamam. Destek için @{GROUP_SUPPORT}'e gelin.",
                )
                await bot.leave_chat(cmd.chat.id)

            return
    await cmd.continue_propagation()


# Broadcast Tools

broadcast_ids = {}


async def send_msg(user_id, message):
    try:
        if BROADCAST_AS_COPY is False:
            await message.forward(chat_id=user_id)
        elif BROADCAST_AS_COPY is True:
            await message.copy(chat_id=user_id)
        return 200, None
    except FloodWait as e:
        await asyncio.sleep(int(e.x))
        return send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : aktif değil\n"
    except UserIsBlocked:
        return 400, f"{user_id} : botu engellemiş\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : kullanıcı kimliği yanlış\n"
    except Exception:
        return 500, f"{user_id} : {traceback.format_exc()}\n"


async def main_broadcast_handler(m, db):
    all_users = await db.get_all_users()
    broadcast_msg = m.reply_to_message
    while True:
        broadcast_id = "".join(random.choice(string.ascii_letters) for i in range(3))
        if not broadcast_ids.get(broadcast_id):
            break
    out = await m.reply_text(
        text="```📤 BroadCast başlatıldı! Bittiği zaman mesaj alacaksınız!"
    )

    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0
    broadcast_ids[broadcast_id] = dict(
        total=total_users, current=done, failed=failed, success=success
    )
    async with aiofiles.open("broadcast-logs.txt", "w") as broadcast_log_file:
        async for user in all_users:
            sts, msg = await send_msg(user_id=int(user["id"]), message=broadcast_msg)
            if msg is not None:
                await broadcast_log_file.write(msg)
            if sts == 200:
                success += 1
            else:
                failed += 1
            if sts == 400:
                await db.delete_user(user["id"])
            done += 1
            if broadcast_ids.get(broadcast_id) is None:
                break
            else:
                broadcast_ids[broadcast_id].update(
                    dict(current=done, failed=failed, success=success)
                )
    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(3)
    await out.delete()
    if failed == 0:
        await m.reply_text(
            text=f"✅ ```Broadcast başarıyla tamamlandı``` \n\n**Tamamlanan:** `{completed_in}` \n\n**Toplam:** `{total_users}` \n\n**Total done:** `{done}` \n\n**Toplam tamamlanan:** `{success}` \n\n**Toplam hata:** `{failed}`",
            quote=True,
        )
    else:
        await m.reply_document(
            document="broadcast-logs.txt",
            caption=f"✅ ```Broadcast başarıyla tamamlandı``` \n\n**Tamamlanan:** `{completed_in}` \n\n**Toplam:** `{total_users}` \n\n**Total done:** `{done}` \n\n**Toplam tamamlanan:** `{success}` \n\n**Toplam hata:** `{failed}`",
            quote=True,
        )
    os.remove("broadcast-logs.txt")







delcmdmdb = mongo_handlers.admins



async def delcmd_is_on(chat_id: int) -> bool:
    chat = await delcmdmdb.find_one({"chat_id": chat_id})
    return not chat


async def delcmd_on(chat_id: int):
    already_del = await delcmd_is_on(chat_id)
    if already_del:
        return
    return await delcmdmdb.delete_one({"chat_id": chat_id})


async def delcmd_off(chat_id: int):
    already_del = await delcmd_is_on(chat_id)
    if not already_del:
        return
    return await delcmdmdb.insert_one({"chat_id": chat_id})
                                      
