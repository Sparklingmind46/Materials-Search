import logging
import os
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from pymongo import MongoClient, errors as PyMongoError
from aiogram.filters import Command  # Import the Command filter for v3

# Configuration
API_TOKEN = os.getenv("API_TOKEN")  # Use environment variable for token security
WELCOME_IMAGE_URL = 'https://envs.sh/wVy.jpg'
WELCOME_IMAGE_CAPTION = "Welcome to the Study Material Bot! 📚\nChoose an option below to get started.\nPowered by- @Team_SAT_25"
ADMIN_IDS = [2031106491]  # Replace with actual Telegram user IDs of bot admins

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up Bot, Dispatcher, and Router
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()  # Router instance to manage handlers
dp.include_router(router)  # Include router in dispatcher

# MongoDB setup
mongo_client = MongoClient("mongodb+srv://uramit0001:EZ1u5bfKYZ52XeGT@cluster0.qnbzn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client['study_bot_db']
materials_collection = db['materials']

# Helper function to create the main menu keyboard
def get_main_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📂 Browse Materials", callback_data="browse_materials"))
    keyboard.add(InlineKeyboardButton("❓ Help", callback_data="help"))
    keyboard.add(InlineKeyboardButton("🌐 Updates channel", url="https://t.me/team_sat_25"))
    return keyboard

# Handler to send welcome image with main menu buttons
@router.message(Command("start"))  # Use Command filter for v3 compatibility
async def send_welcome_image(message: types.Message):
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=WELCOME_IMAGE_URL,
        caption=WELCOME_IMAGE_CAPTION,
        reply_markup=get_main_menu()
    )

# Handler for button clicks in main menu
@router.callback_query(lambda c: c.data in ['browse_materials', 'help'])
async def process_main_menu(callback_query: types.CallbackQuery):
    action = callback_query.data

    if action == "browse_materials":
        # Show categories (e.g., subjects or grade levels)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📖 Mathematics", callback_data="category_math"))
        keyboard.add(InlineKeyboardButton("🔬 Science", callback_data="category_science"))
        keyboard.add(InlineKeyboardButton("🔤 Language Arts", callback_data="category_language"))
        keyboard.add(InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main"))
        await bot.send_message(callback_query.from_user.id, "Select a category:", reply_markup=keyboard)

    elif action == "help":
        help_text = ("Welcome to the Study Material Bot!\n\n"
                     "Here's how to use this bot:\n"
                     "- Use inline mode to search materials quickly.\n"
                     "- Click 'Browse Materials' to see available categories.\n"
                     "- For further questions, reach out to the admin.\n")
        await bot.send_message(callback_query.from_user.id, help_text, reply_markup=get_main_menu())

# Handler for category selection
@router.callback_query(lambda c: c.data.startswith("category_"))
async def show_category(callback_query: types.CallbackQuery):
    category = callback_query.data.split("_")[1]

    # MongoDB search for materials in the selected category
    search_filter = {"subject": category.capitalize()}
    materials = materials_collection.find(search_filter)

    if materials.count() == 0:
        await bot.send_message(callback_query.from_user.id, f"No materials found for {category}.", reply_markup=get_main_menu())
        return

    for material in materials:
        await bot.send_document(
            callback_query.from_user.id,
            material['file_id'],
            caption=f"{material['title']}\n{material.get('description', '')}"
        )
    
    await bot.send_message(callback_query.from_user.id, "⬅️ Back to Main Menu", reply_markup=get_main_menu())

# Handler for returning to the main menu
@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Main Menu:", reply_markup=get_main_menu())

# Command to add a new file with advanced attributes (subject, grade level, tags)
@router.message(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    # Check if the message is from an authorized admin
    if message.from_user.id not in ADMIN_IDS:
        return

    # Document details
    document = message.document
    file_id = document.file_id
    title = document.file_name

    # Extract additional details from command arguments
    args = message.caption.split('|') if message.caption else []
    tags = args[0].strip() if len(args) > 0 else ""
    subject = args[1].strip() if len(args) > 1 else "General"
    grade_level = args[2].strip() if len(args) > 2 else "All Levels"

    try:
        # Insert document data into MongoDB
        materials_collection.insert_one({
            "file_id": file_id,
            "title": title,
            "tags": tags.lower(),
            "subject": subject,
            "grade_level": grade_level,
            "description": f"Study material for {subject}, suitable for {grade_level}."
        })
        await message.reply(f"File '{title}' added successfully with subject '{subject}' and grade level '{grade_level}'.")
    
    except PyMongoError as e:
        await message.reply("Failed to add the file to the database.")
        print(f"Error inserting into MongoDB: {e}")

# Start the bot
if __name__ == '__main__':
    dp.start_polling(bot)
