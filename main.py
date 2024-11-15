import telebot
from telebot.types import InlineQueryResultCachedDocument
from pymongo import MongoClient
import re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Connect to MongoDB
client = MongoClient("mongodb+srv://uramit0001:EZ1u5bfKYZ52XeGT@cluster0.qnbzn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["materials"]
collection = db["study_materials"]

# Set up your bot
bot = telebot.TeleBot("7475415260:AAFtcB-4MXtYNqR_y7miGURL-Xb35CCzd7A")

# Handler for the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        # Prepare the inline keyboard with buttons
        keyboard = InlineKeyboardMarkup()
        button1 = InlineKeyboardButton(text="Updates Channel", url="https://t.me/team_sat_25")  # Replace with your channel link
        button2 = InlineKeyboardButton(text="Developer", url="https://t.me/ur_amit_01")  # Replace with your Telegram ID
        keyboard.add(button1, button2)

        # Send an image with a caption and the inline buttons
        image_url = "https://envs.sh/wVy.jpg"  # URL or local path of the image
        caption = "Welcome to the Study Material search Bot! Powered by - @Team_SAT_25"
        
        # Send the image with caption and buttons
        bot.send_photo(message.chat.id, image_url, caption=caption, reply_markup=keyboard)
    
    except Exception as e:
        print(f"Error sending start message: {e}")

# Inline query handler for searching files
@bot.inline_handler(lambda query: len(query.query) > 0)
def inline_search(query):
    try:
        search_text = query.query.lower()
        print(f"Inline search triggered with query: {search_text}")  # Add a print statement for debugging

        # Search MongoDB for files matching the search term in title or tags
        matched_files = list(collection.find({
            "$or": [
                {"title": {"$regex": re.escape(search_text), "$options": "i"}},
                {"tags": {"$regex": re.escape(search_text), "$options": "i"}}
            ]
        }))
        
        print(f"Matched files: {matched_files}")  # Print the matched files for debugging

        results = []
        for file in matched_files:
            results.append(
                InlineQueryResultCachedDocument(
                    id=str(file["_id"]),
                    title=file["title"],
                    document_file_id=file["file_id"],
                    description=file.get("description", "No description available.")
                )
            )

        if not results:
            print("No files matched.")  # Log no results case
            results.append(
                InlineQueryResultCachedDocument(
                    id="no_result",  # Ensure unique ID
                    title="No files found",
                    document_file_id="your_placeholder_file_id",  # Placeholder file ID
                    description="Try a different search term or check your spelling."
                )
            )
            
        bot.answer_inline_query(query.id, results, cache_time=0)
        print("Inline query answered successfully.")
        
    except Exception as e:
        print(f"Error in inline search: {e}")


@bot.message_handler(commands=['list_data'])
def list_data(message):
    try:
        documents = list(collection.find({}))
        if documents:
            for doc in documents:
                bot.send_message(message.chat.id, f"Title: {doc.get('title')}, Tags: {doc.get('tags')}")
        else:
            bot.send_message(message.chat.id, "No documents in the database.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error fetching data: {e}")


# Define a list of admin user IDs who are allowed to send files to the bot
ADMIN_IDS = [2031106491]  # Replace with actual admin user IDs

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        # Check if the sender's user ID is in the list of admins
        if message.from_user.id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "❌ You do not have permission to upload files.")
            return

        # Process the document if the sender is an admin
        file_id = message.document.file_id
        title = message.document.file_name
        description = message.caption if message.caption else "No description provided."
        
        # Extract tags from the filename
        tags = extract_tags_from_filename(title)

        # Insert file data into MongoDB with extracted tags
        result = collection.insert_one({
            "file_id": file_id,
            "title": title,
            "description": description,
            "tags": tags
        })
        
        # Send confirmation message
        bot.send_message(
            message.chat.id, 
            f"✅ File '{title}' has been successfully added to the database with tags: {', '.join(tags)}."
        )
    
    except Exception as e:
        print(f"Error handling document: {e}")

# Function to extract tags from the filename
def extract_tags_from_filename(filename):
    # Example: Split the filename by spaces, underscores, or dashes and filter out common words
    tags = re.findall(r'\b\w+\b', filename.lower())
    # Optional: Exclude common stop words (you can customize this list)
    stop_words = {"the", "and", "or", "for", "with", "a", "an", "by", "on"}
    tags = [tag for tag in tags if tag not in stop_words]
    return tags

# Polling to keep the bot running
bot.polling()
