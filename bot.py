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
import time
from datetime import datetime, timedelta
from database.database import kingdb
from pyrogram.types import InlineKeyboardButton, BotCommand
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
        self.FOLDER_LIST = []
        self.EXTRALINK_LIST = []

    async def update_folders(self):
        self.FOLDER_LIST = await kingdb.get_all_folders()

    async def update_extralinks(self):
        self.EXTRALINK_LIST = await kingdb.get_all_extralinks()

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
        await self.update_folders()
        await self.update_extralinks()

        await self.set_bot_commands([
            BotCommand("start", "Start Bot"),
            BotCommand("help", "Get Help"),
            BotCommand("addfolder", "Add Folder Link"),
            BotCommand("myfolders", "Manage Folders"),
            BotCommand("extralink", "Add Extra Link"),
            BotCommand("myextralink", "Manage Extra Links"),
            BotCommand("users", "User Settings"),
            BotCommand("forcesub", "Force Sub Settings"),
            BotCommand("broadcast", "Broadcast Message"),
            BotCommand("cancel", "Cancel Broadcast"),
            BotCommand("status", "Bot Status"),
            BotCommand("cmd", "Admin Commands"),
            BotCommand("restart", "Restart Bot"),
        ])
                
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

                temp_butn = InlineKeyboardButton(text=channel_name, url=channel_link)

                if not data.username:
                    await kingdb.add_reqChannel(chat_id)
                    req_chnl_buttons[chat_id] = channel_name
                    # For private channels, store details in global_buttons for dynamic generation
                    global_buttons.append({'chat_id': chat_id, 'name': channel_name, 'username': None})

                else:
                    chnl_buttons.append(temp_butn)
                    # For public channels, store pre-made button in global_buttons
                    global_buttons.append({'chat_id': chat_id, 'name': channel_name, 'username': data.username, 'url': channel_link})

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

    async def get_valid_invite_link(self, chat_id: int, req_mode: bool = True):
        # Always generate a new link for each user request to ensure uniqueness and 1-user limit
        self.LOGGER(__name__).info(f"Generating new 1-use link for {chat_id} (req_mode={req_mode})")

        expire_ts = int(time.time()) + 600
        expire_dt = datetime.fromtimestamp(expire_ts)
        link_name = f"One-Time Link {expire_ts}"

        if req_mode:
            # Generate link with creates_join_request=True so "Request Force-Sub" flow works.
            # Note: If creates_join_request=True, member_limit must be None.
            link = (await self.create_chat_invite_link(
                chat_id=chat_id,
                creates_join_request=True,
                expire_date=expire_dt,
                name=link_name
            )).invite_link
        else:
            # Normal Force-Sub mode: generate a standard invite link.
            # Use member_limit=1 to effectively make it a one-time use link for security/uniqueness.
            link = (await self.create_chat_invite_link(
                chat_id=chat_id,
                member_limit=1,
                creates_join_request=False,
                expire_date=expire_dt,
                name=link_name
            )).invite_link

        # We do not store this link in the database as it is one-time use and cannot be reused
        return link
