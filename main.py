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

# Add your channel ID where the bot will pull materials from
FILE_CHANNEL_ID = -1002400431486  # Replace with your file channel ID

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
        if len(query.query) < 1:
            bot.answer_inline_query(query.id, [])
            return
        
        results = []
        search_text = query.query.lower()

        # Search MongoDB for files matching the search term
        matched_files = collection.find({"tags": {"$regex": re.escape(search_text), "$options": "i"}})
        
        # Add each matched file to the results
        for file in matched_files:
            results.append(
                InlineQueryResultCachedDocument(
                    id=str(file["_id"]),
                    title=file["title"],
                    document_file_id=file["file_id"],
                    description=file["description"]
                )
            )

        # If no results are found, send a placeholder message
        if not results:
            bot.answer_inline_query(query.id, [InlineQueryResultCachedDocument(
                id="no_result",
                title="No files found",
                document_file_id="placeholder_file_id",
                description="Try a different search term or check your spelling."
            )], cache_time=0)
        else:
            bot.answer_inline_query(query.id, results)
            
    except Exception as e:
        print(f"Error in inline search: {e}")

# Message handler for receiving files from anyone in the file channel
@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        print(f"Received a document in chat ID: {message.chat.id}")  # Debug: Print chat ID
        
        # Only process if the message is from the specified file channel
        if message.chat.id == FILE_CHANNEL_ID:
            print("File is from the correct channel")  # Debug: Confirm it's from the correct channel
            
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
            
            print(f"Inserted document ID: {result.inserted_id}")  # Debug: Confirm insertion

            # Send confirmation message
            bot.send_message(
                message.chat.id, 
                f"✅ File '{title}' has been successfully added to the database with tags: {', '.join(tags)}."
            )
        else:
            print("Message not from file channel")  # Debug: Print if it's from another chat
            
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
