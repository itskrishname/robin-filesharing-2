# +++ Made By King [telegram username: @Shidoteshika1] +++

from aiohttp import web
from plugins import web_server

import asyncio
import pyromod.listen
from pyrogram.types.pyromod.identifier import Identifier
from typing import Union, List, Optional
from pyrogram import Client
from pyrogram.enums import ParseMode

# Monkeypatch Identifier to fix pyromod 1.5 crash on Python 3.14+
# RecursionError and AttributeError: 'Identifier' object has no attribute '__annotations__'
def patched_matches(self, update: "Identifier") -> bool:
    # Explicitly list fields instead of relying on __annotations__
    fields = ['inline_message_id', 'chat_id', 'message_id', 'from_user_id']
    for field in fields:
        pattern_value = getattr(self, field, None)
        update_value = getattr(update, field, None)

        if pattern_value is not None:
            if isinstance(update_value, list):
                if isinstance(pattern_value, list):
                    if not set(update_value).intersection(set(pattern_value)):
                        return False
                elif pattern_value not in update_value:
                    return False
            elif isinstance(pattern_value, list):
                if update_value not in pattern_value:
                    return False
            elif update_value != pattern_value:
                return False
    return True

def patched_count_populated(self):
    non_null_count = 0
    fields = ['inline_message_id', 'chat_id', 'message_id', 'from_user_id']
    for attr in fields:
        if getattr(self, attr, None) is not None:
            non_null_count += 1
    return non_null_count

Identifier.matches = patched_matches
Identifier.count_populated = patched_count_populated
import sys
from datetime import datetime, timedelta
from database.database import kingdb
from pyrogram.types import InlineKeyboardButton
from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, CHANNEL_ID, PORT, OWNER_ID

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        bot_info = await self.get_me()
        self.name = bot_info.first_name
        self.username = bot_info.username
        self.uptime = datetime.now()

        self.REQFSUB = await kingdb.get_request_forcesub()
        self.CHANNEL_LIST, self.FSUB_BUTTONS = [], []
        self.REQ_FSUB_BUTTONS = {'normal': [], 'request': {}}
        await self.update_chat_ids()
                
        try:
            db_channel = await self.get_chat(CHANNEL_ID)

            if not db_channel.invite_link:
                db_channel.invite_link = await self.export_chat_invite_link(CHANNEL_ID)

            self.db_channel = db_channel
            
            test = await self.send_message(chat_id = db_channel.id, text = "Testing")
            await test.delete()

        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"Make Sure bot is Admin in DB Channel and have proper Permissions, So Double check the CHANNEL_ID Value, Current Value {CHANNEL_ID}")
            self.LOGGER(__name__).info('Bot Stopped..')
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Aᴅᴠᴀɴᴄᴇ Fɪʟᴇ-Sʜᴀʀɪɴɢ ʙᴏᴛV3 Mᴀᴅᴇ Bʏ ➪ @Shidoteshika1 [Tᴇʟᴇɢʀᴀᴍ Usᴇʀɴᴀᴍᴇ]")
        self.LOGGER(__name__).info(f"{self.name} Bot Running..!")
        self.LOGGER(__name__).info(f"OPERATION SUCCESSFULL ✅")
        #web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

        try: await self.send_message(OWNER_ID, text = f"<b><blockquote>🤖 Bᴏᴛ Rᴇsᴛᴀʀᴛᴇᴅ ♻️</blockquote></b>")
        except: pass


    async def update_chat_ids(self):
        chat_ids = await kingdb.get_all_channels()

        if not chat_ids:
            self.CHANNEL_LIST.clear()
            self.FSUB_BUTTONS.clear()
            self.REQ_FSUB_BUTTONS['normal'].clear()
            self.REQ_FSUB_BUTTONS['request'].clear()
            
            return f"<b><blockquote>❌ Nᴏ Fᴏʀᴄᴇ Sᴜʙ Cʜᴀɴɴᴇʟ Fᴏᴜɴᴅ !</b></blockquote>"

        valid_chat_ids, global_buttons, chnl_buttons, req_chnl_buttons = [], [], [], {}
        channel_infos = []

        for chat_id in chat_ids:
            try:
                data = await self.get_chat(chat_id)
                channel_link = data.invite_link 
                channel_name = data.title

                if not channel_link:
                    channel_link = await self.export_chat_invite_link(chat_id)

                temp_butn = [InlineKeyboardButton(text=channel_name, url=channel_link)]

                if not data.username:
                    await kingdb.add_reqChannel(chat_id)
                    req_chnl_buttons[chat_id] = channel_name

                else:
                    chnl_buttons.append(temp_butn)

                global_buttons.append(temp_butn)

                channel_infos.append(f"<b><blockquote>NAME: <a href = {channel_link}>{channel_name}</a>\n(ID: <code>{chat_id}</code>)</blockquote></b>\n\n")

                valid_chat_ids.append(chat_id)
                    
            except Exception as e:
                print(f"Unable to update the {chat_id}, Reason: {e}")
                channel_infos.append(f"<blockquote expandable><b>ID: <code>{chat_id}</code>\n<i>! Eʀʀᴏʀ ᴏᴄᴄᴜʀᴇᴅ ᴡʜɪʟᴇ ᴜᴘᴅᴀᴛɪɴɢ...</i>\n\nRᴇᴀsᴏɴ:</b> {e}</blockquote>\n\n")
                
                continue
        
        invalid_ids = len(chat_ids) - len(valid_chat_ids)

        if invalid_ids:
            channel_infos.append(f"<blockquote expandable><b>⚠️ WARNING:</b> {invalid_ids} ᴄʜᴀɴɴᴇʟ IDs ᴍᴀʏ ᴀᴘᴘᴇᴀʀ ɪɴᴠᴀʟɪᴅ, ᴏʀ ᴛʜᴇ ʙᴏᴛ ᴍᴀʏ ɴᴏᴛ ʜᴀᴠᴇ ᴛʜᴇ ɴᴇᴄᴇssᴀʀʏ ᴘᴇʀᴍɪssɪᴏɴs. {invalid_ids} Cʜᴀɴɴᴇʟs cᴀɴ ɴᴏᴛ ғᴜɴᴄᴛɪᴏɴ ᴀs 'FᴏʀᴄᴇSᴜʙ' ʙᴜᴛᴛᴏɴ. Tᴏ ᴇɴᴀʙʟᴇ ᴛʜᴇ 'FᴏʀᴄᴇSᴜʙ' ғᴜɴᴄᴛɪᴏɴᴀʟɪᴛʏ ғᴏʀ {invalid_ids} ᴄʜᴀɴɴᴇʟs, ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴠᴀʟɪᴅ IDs ᴏʀ ᴇɴsᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ʜᴀs ᴛʜᴇ ᴀᴘᴘʀᴏᴘʀɪᴀᴛᴇ ᴘᴇʀᴍɪssɪᴏɴs.</blockquote>")

        self.CHANNEL_LIST = valid_chat_ids
        self.FSUB_BUTTONS = global_buttons
        self.REQ_FSUB_BUTTONS['normal'] = chnl_buttons
        self.REQ_FSUB_BUTTONS['request'] = req_chnl_buttons

        return ''.join(channel_infos)
    
              
    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info(f"{self.name} Bot stopped.")

    async def get_valid_invite_link(self, chat_id: int):
        link, expire_date = await kingdb.get_stored_reqLink(chat_id)

        # Check if the link exists and has at least 5 minutes remaining validity
        # This prevents serving a link that is about to expire immediately
        if link and expire_date and datetime.now().timestamp() < (expire_date - 300):
            self.LOGGER(__name__).info(f"Serving cached link for {chat_id} (Expires in {int(expire_date - datetime.now().timestamp())}s)")
            return link

        self.LOGGER(__name__).info(f"Generating new link for {chat_id}")
        new_expire_date = datetime.now() + timedelta(minutes=10)
        link = (await self.create_chat_invite_link(chat_id=chat_id, creates_join_request=True, expire_date=new_expire_date)).invite_link

        await kingdb.store_reqLink(chat_id, link, new_expire_date.timestamp())
        return link
