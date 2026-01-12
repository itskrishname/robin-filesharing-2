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
    folders = client.FOLDER_LIST

    if not folders:
        return await message.reply("<b>❌ No Folders Found!</b>")

    text = "<b>📂 Your Folders:</b>\n\n"
    buttons = []

    for i, link in enumerate(folders, 1):
        text += f"{i}. {link}\n"
        # Extract slug for safer deletion (https://t.me/addlist/SLUG)
        try:
            slug = link.split("https://t.me/addlist/")[1]
            buttons.append([InlineKeyboardButton(f"🗑 Delete Folder {i}", callback_data=f"delfolder_{slug}")])
        except IndexError:
            pass # Should not happen if addfolder validation works

    buttons.append([InlineKeyboardButton("✖️ Close", callback_data="close")])

    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Bot.on_callback_query(filters.regex(r"^delfolder_"))
async def delete_folder_callback(client: Bot, query: CallbackQuery):
    user_id = query.from_user.id
    # Manually check admin status since we can't await the is_admin filter
    is_admin_user = (user_id == OWNER_ID) or (await kingdb.admin_exist(user_id))

    if not is_admin_user:
        return await query.answer("❌ You are not Admin!", show_alert=True)

    try:
        slug = query.data.split("_", 1)[1]
        link_to_delete = f"https://t.me/addlist/{slug}"

        await kingdb.del_folder(link_to_delete)
        await client.update_folders()

        await query.answer("✅ Folder Deleted!", show_alert=True)
        await query.message.delete()

    except Exception as e:
        await query.answer(f"❌ Error: {e}", show_alert=True)
