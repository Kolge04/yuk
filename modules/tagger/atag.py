from asyncio import sleep

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from Config import admins  # noqa
from Config import calisan  # noqa
from Config import reasons  # noqa
from modules.helpers import admincount, reload, command, admin
from languages import lan, get_str
from ..databases.mongo.database import get_duration, get_count



@Client.on_message(command(commands="atag"))
@admin
async def atag(client: Client, message: Message):
    global reasons
    global calisan
    global admins
    user_id = message.from_user.id
    
    chat_id = message.chat.id
    lang = await get_str(chat_id)
    LAN = lan(lang)


    await reload(client, message)
    if message.chat.type == "private":
        return

    if message.from_user.id not in admins[message.chat.id]:
        not_admin = await message.reply_text(LAN.U_NOT_ADMIN.format(message.from_user.mention))
        await sleep(3)  # 3 seconds
        await not_admin.delete()  # delete message
        return

    if chat_id in calisan:
        c = await message.reply_text(LAN.ZATEN_CALISIYORUM.format(message.from_user.mention))
        await sleep(3)
        await message.delete()
        await c.delete()
        return

    else:
        if message.reply_to_message:
            if message.reply_to_message.text:
                reason = message.reply_to_message.text
                tip = "1"
            else:
                reason = ""
                tip = "0"
        else:
            if len(message.command) <= 1:
                reason = ""
                tip = "0"
            else:
                reason = message.text.split(None, 1)[1]
                tip = "1"
        COUNT = await get_count(chat_id)
        reasons[chat_id] = reason
        m = await client.send_message(
            chat_id,
            LAN.ASK_ADMINS_TAG,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            LAN.TEKLI, callback_data=f"atag 1|{user_id}|{tip}"
                        ),
                        InlineKeyboardButton(
                            LAN.COKLU.format(COUNT), callback_data=f"atag {COUNT}|{user_id}|{tip}"
                        ),
                    ],
                    [
                        InlineKeyboardButton("❌", callback_data=f"atag 0|{user_id}|{tip}"),
                    ],
                ],
            ),
        )
        await sleep(15)
        if chat_id not in calisan:
            try:
                await m.edit(LAN.ASK_ADMINS_TAG_TIMEOUT.format(message.from_user.mention, "`/atag`"))
            except Exception as e:
                return
            await sleep(3)
            await m.delete()
            return
        else:
            return

@Client.on_callback_query(filters.regex(pattern=r"atag"))
async def acommands(bot: Client, query: CallbackQuery):
    global admins
    global reasons
    global calisan
    chat = query.message.chat.id
    DURATION = await get_duration(chat)
    lang = await get_str(chat)
    LAN = lan(lang)
    
    q = str(query.data)
    typed_ = q.split()[1]
    sayi = int(typed_.split("|")[0])
    useer_id = typed_.split("|")[1]
    tip = typed_.split("|")[2]

    if sayi == 0:
        del reasons[chat]
        await query.message.edit_text(LAN.CALISMA_DURDUR.format(query.from_user.mention))
        await sleep(int(DURATION))
        await query.message.delete()
        return

    if chat in calisan:
        await query.message.edit(LAN.ZATEN_CALISIYORUM.format(query.message.from_user.mention))
        await sleep(3)  # 3 seconds
        await query.message.delete()
        return

    if tip == "1":
        reason = reasons.get(chat)
    elif tip == "0":
        reason = ""

    name = await bot.get_users(int(useer_id))
    if int(useer_id) == int(query.from_user.id):
        if chat not in calisan:
            calisan.append(chat)
        await query.message.delete()
        bots, deleted, toplam = await admincount(bot, chat)
        etiketlenecek = toplam
        started = await bot.send_message(
            chat,
            LAN.TAG_START.format(
                query.from_user.mention, LAN.ADMIN_TAG, etiketlenecek, int(DURATION)
            ),
        )
        usrnum = 0
        usrtxt = ""
        etiketlenen = 0
        async for usr in bot.iter_chat_members(chat, filter="administrators"):
            if usr["user"]["is_bot"]:
                pass
            elif usr["user"]["is_deleted"]:
                pass
            else:
                usrnum += 1
                usrtxt += f"[{usr.user.first_name}](tg://user?id={usr.user.id}) ,"
                etiketlenen += 1
                
                if usrnum == int(sayi):
                    if sayi == 1:
                        text = f"📢 **{reason}** {usrtxt}"
                    else:
                        text = f"📢 **{reason}**\n\n{usrtxt}"
                    await bot.send_message(chat, text=text)
                    await sleep(int(DURATION))
                    usrnum = 0
                    usrtxt = ""

                if etiketlenen == etiketlenecek:
                    calisan.remove(chat)
                    del reasons[chat]
                    stoped = await bot.send_message(
                        chat,
                        LAN.TAG_STOPED.format(
                            LAN.ADMIN_TAG,
                            etiketlenen,
                            int(DURATION),
                            query.from_user.mention,
                        ),
                    )
                    await sleep(int(DURATION))
                    await stoped.delete()
                    await started.delete()
                    return

                if chat not in calisan:
                    del reasons[chat]
                    stopped = await bot.send_message(
                        chat,
                        LAN.TAG_STOPED.format(
                            LAN.ADMIN_TAG,
                            etiketlenen,
                            int(DURATION),
                            query.from_user.mention,
                        ),
                    )
                    await sleep(int(DURATION))
                    await stopped.delete()
                    await started.delete()
                    return


    else:
        return await bot.answer_callback_query(
            callback_query_id=query.id,
            text=LAN.ETAG_DONT_U.format(name.first_name),
            show_alert=True,
      )
                  
