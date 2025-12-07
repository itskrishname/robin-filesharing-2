from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID, LOG_FILE_NAME
import os

@Client.on_message(filters.command("logs") & filters.user(OWNER_ID))
async def get_logs(client: Client, message: Message):
    if os.path.exists(LOG_FILE_NAME):
        try:
            await message.reply_document(document=LOG_FILE_NAME, caption="<b>Here is your log file.</b>")
        except Exception as e:
            await message.reply_text(f"Failed to send log file: {e}")
    else:
        await message.reply_text("Log file not found.")
