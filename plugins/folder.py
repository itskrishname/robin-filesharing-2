from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_func import is_admin
from database.database import kingdb
from bot import Bot
from config import OWNER_ID
import logging

logger = logging.getLogger(__name__)

# Allow Owner explicitly in case is_admin check fails for some reason
@Bot.on_message(filters.command("addfolder") & filters.private & (is_admin | filters.user(OWNER_ID)))
async def add_folder(client: Bot, message: Message):
    logger.info(f"Command /addfolder triggered by {message.from_user.id}")
    if len(message.command) < 2:
        return await message.reply("<b>⚠️ Usage:</b> `/addfolder https://t.me/addlist/...`")

    link = message.command[1]

    if not link.startswith("https://t.me/addlist/"):
        return await message.reply("<b>⚠️ Invalid Link!</b> Link must start with `https://t.me/addlist/`")

    await kingdb.add_folder(link)
    await client.update_folders()

    await message.reply(f"<b>✅ Folder Added Successfully!</b>\n\nLink: {link}")

@Bot.on_message(filters.command("myfolders") & filters.private & (is_admin | filters.user(OWNER_ID)))
async def my_folders(client: Bot, message: Message):
    logger.info(f"Command /myfolders triggered by {message.from_user.id}")
    # Refresh folders to ensure indices match current state
    await client.update_folders()
    folders = client.FOLDER_LIST

    if not folders:
        return await message.reply("<b>❌ No Folders Found!</b>")

    text = "<b>📂 Your Folders:</b>\n\n"
    buttons = []

    for i, link in enumerate(folders):
        # Display 1-based index to user, but use 0-based index for logic if preferred,
        # or just use the index `i` (0 to N-1).
        text += f"{i+1}. {link}\n"
        # Use index in callback data to avoid length limits and slug parsing issues
        buttons.append([InlineKeyboardButton(f"🗑 Delete Folder {i+1}", callback_data=f"delfolder_{i}")])

    buttons.append([InlineKeyboardButton("✖️ Close", callback_data="close")])

    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Bot.on_callback_query(filters.regex(r"^delfolder_"), group=-1)
async def delete_folder_callback(client: Bot, query: CallbackQuery):
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

        # Access the cached folder list
        current_folders = client.FOLDER_LIST

        if 0 <= index < len(current_folders):
            link_to_delete = current_folders[index]

            await kingdb.del_folder(link_to_delete)
            await client.update_folders()

            await query.answer("✅ Folder Deleted!", show_alert=True)
            await query.message.delete()
        else:
             await query.answer("❌ Folder not found (List may have changed). Try /myfolders again.", show_alert=True)
             await query.message.delete()

    except ValueError:
         await query.answer("❌ Invalid Data!", show_alert=True)
    except Exception as e:
        logger.error(f"Error in delete_folder_callback: {e}", exc_info=True)
        await query.answer(f"❌ Error: {e}", show_alert=True)
