# study_material_bot.py
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Dispatcher
from aiogram import Bot
from aiogram.types import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os

API_TOKEN = '7475415260:AAFtcB-4MXtYNqR_y7miGURL-Xb35CCzd7A'
WELCOME_IMAGE_URL = 'https://envs.sh/wVy.jpg'  # URL for the welcome image
WELCOME_IMAGE_CAPTION = "Welcome to the Study Material Bot! 📚\nChoose an option below to get started.\nPowered by- @Team_SAT_25"

ADMIN_IDS = [2031106491]  # Replace with actual Telegram user IDs of bot admins

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# MongoDB setup
mongo_client = MongoClient("mongodb+srv://uramit0001:EZ1u5bfKYZ52XeGT@cluster0.qnbzn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client['study_bot_db']
materials_collection = db['materials']

# Helper function to create the main menu keyboard
def get_main_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📂 Browse Materials", callback_data="browse_materials"))
    keyboard.add(InlineKeyboardButton("❓ Help", callback_data="help"))
    keyboard.add(InlineKeyboardButton("📞 Updates channel", url="https://t.me/team_sat_25"))  # Replace with actual admin link
    return keyboard

# Send a welcome image with the main menu buttons when the user starts the bot
@dp.message_handler(commands=['start'])
async def send_welcome_image(message: types.Message):
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=WELCOME_IMAGE_URL,
        caption=WELCOME_IMAGE_CAPTION,
        reply_markup=get_main_menu()
    )

# Handle button clicks in the main menu
@dp.callback_query_handler(lambda c: c.data in ['browse_materials', 'help'])
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
        # Send help message
        help_text = ("Welcome to the Study Material Bot!\n\n"
                     "Here's how to use this bot:\n"
                     "- Use inline mode to search materials quickly.\n"
                     "- Click 'Browse Materials' to see available categories.\n"
                     "- For further questions, reach out to the admin.\n")
        await bot.send_message(callback_query.from_user.id, help_text, reply_markup=get_main_menu())

# Handle category selection
@dp.callback_query_handler(lambda c: c.data.startswith("category_"))
async def show_category(callback_query: types.CallbackQuery):
    category = callback_query.data.split("_")[1]

    # Perform MongoDB search for materials in the selected category
    search_filter = {"subject": category.capitalize()}
    materials = materials_collection.find(search_filter)

    if materials.count() == 0:
        await bot.send_message(callback_query.from_user.id, f"No materials found for {category}.", reply_markup=get_main_menu())
        return

    # Display materials as messages with file links
    for material in materials:
        await bot.send_document(callback_query.from_user.id, material['file_id'], caption=f"{material['title']}\n{material.get('description', '')}")
    
    await bot.send_message(callback_query.from_user.id, "⬅️ Back to Main Menu", reply_markup=get_main_menu())

# Handle returning to the main menu
@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Main Menu:", reply_markup=get_main_menu())

# Command to add a new file with advanced attributes (subject, grade level)
@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    # Check if the message is from the authorized admin
    if message.from_user.id not in ADMIN_IDS:
        return  # If not authorized, do nothing

    # Get the document
    document = message.document
    file_id = document.file_id
    title = document.file_name

    # You can add additional logic here to get subject, grade level, etc.
    subject = "General"  # Default to "General" for now
    grade_level = "All Levels"  # Default to "All Levels"

    try:
        # Insert the document data into MongoDB
        materials_collection.insert_one({
            "file_id": file_id,
            "title": title,
            "subject": subject,
            "grade_level": grade_level,
            "description": f"Study material for {subject}, suitable for {grade_level}."
        })
        await message.reply(f"File '{title}' added successfully to the database.")
    
    except PyMongoError as e:
        await message.reply("Failed to add the file to the database.")
        print(f"Error inserting into MongoDB: {e}")

    # Extract document and details
    document = message.reply_to_message.document
    file_id = document.file_id
    title = document.file_name
    args = message.get_args().split('|')
    tags = args[0].strip() if len(args) > 0 else ""
    subject = args[1].strip() if len(args) > 1 else "General"
    grade_level = args[2].strip() if len(args) > 2 else "All Levels"

    try:
        # Insert the document data into MongoDB
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
    # Start polling
    dp.run_polling()

