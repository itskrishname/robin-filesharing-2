from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_func import is_admin
from database.database import kingdb
from bot import Bot
from config import OWNER_ID
import logging
import re

logger = logging.getLogger(__name__)

# Pattern for basic URL validation
URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')

# Allow Owner explicitly in case is_admin check fails for some reason
@Bot.on_message(filters.command("extralink") & filters.private & (is_admin | filters.user(OWNER_ID)))
async def add_extralink(client: Bot, message: Message):
    logger.info(f"Command /extralink triggered by {message.from_user.id}")
    if len(message.command) < 2:
        return await message.reply("<b>⚠️ Usage:</b> `/extralink https://example.com`")

    link = message.command[1]

    # Basic validation
    if not URL_PATTERN.match(link):
        return await message.reply("<b>⚠️ Invalid Link!</b> Please provide a valid HTTP/HTTPS URL.")

    await kingdb.add_extralink(link)
    await client.update_extralinks()

    await message.reply(f"<b>✅ Extra Link Added Successfully!</b>\n\nLink: {link}")

@Bot.on_message(filters.command("myextralink") & filters.private & (is_admin | filters.user(OWNER_ID)))
async def my_extralinks(client: Bot, message: Message):
    logger.info(f"Command /myextralink triggered by {message.from_user.id}")
    # Refresh to ensure state
    await client.update_extralinks()
    links = client.EXTRALINK_LIST

    if not links:
        return await message.reply("<b>❌ No Extra Links Found!</b>")

    text = "<b>🔗 Your Extra Links:</b>\n\n"
    buttons = []

    for i, link in enumerate(links):
        text += f"{i+1}. {link}\n"
        # Use index in callback data to avoid length limits and slug parsing issues
        buttons.append([InlineKeyboardButton(f"🗑 Delete Link {i+1}", callback_data=f"delextra_{i}")])

    buttons.append([InlineKeyboardButton("✖️ Close", callback_data="close")])

    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Bot.on_callback_query(filters.regex(r"^delextra_"), group=-1)
async def delete_extralink_callback(client: Bot, query: CallbackQuery):
    user_id = query.from_user.id

    # Simple check: Owner or Admin.
    # If admin_exist raises error, at least Owner can still operate.
    is_authorized = (user_id == OWNER_ID)
    if not is_authorized:
        try:
            is_authorized = await kingdb.admin_exist(user_id)
        except Exception as e:
            logger.error(f"Error checking admin status for {user_id}: {e}")

    if not is_authorized:
        return await query.answer("❌ You are not Admin!", show_alert=True)

    try:
        # Parse index
        index = int(query.data.split("_")[1])

        # Access the cached list
        current_links = client.EXTRALINK_LIST

        if 0 <= index < len(current_links):
            link_to_delete = current_links[index]

            await kingdb.del_extralink(link_to_delete)
            await client.update_extralinks()

            await query.answer("✅ Link Deleted!", show_alert=True)
            await query.message.delete()
        else:
             await query.answer("❌ Link not found. Try /myextralink again.", show_alert=True)
             await query.message.delete()

    except ValueError:
         await query.answer("❌ Invalid Data!", show_alert=True)
    except Exception as e:
        logger.error(f"Error in delete_extralink_callback: {e}", exc_info=True)
        await query.answer(f"❌ Error: {e}", show_alert=True)
