from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import requests

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I can control your home automation system. Try commands like:\n"
                                    "- Turn on master bedroom lights\n"
                                    "- Turn off kitchen fan")

# Function to process home automation commands
async def process_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()

    # Parse the command
    if "turn on" in user_message:
        action = "on"
    elif "turn off" in user_message:
        action = "off"
    else:
        await update.message.reply_text("I didn't understand your command. Please use 'turn on' or 'turn off'.")
        return

    # Extract room and device (basic parsing)
    words = user_message.split()
    try:
        room = words[words.index("in") + 1]  # Get the room after "in"
        device = words[words.index("turn") + 2]  # Get the device after "turn on/off"
    except (ValueError, IndexError):
        await update.message.reply_text("Please specify the room and device in your command, e.g., 'Turn on the lights in the bedroom'.")
        return

    # Construct the HTTP request
    url = f"http://127.0.0.1:5000/{room}/{device}/{action}"

    try:
        # Send the HTTP request
        response = requests.get(url)

        if response.status_code == 200:
            await update.message.reply_text(f"Successfully turned {action} the {device} in the {room}.")
        else:
            await update.message.reply_text(f"Failed to control the {device} in the {room}. Please check the server.")
    except requests.RequestException as e:
        await update.message.reply_text(f"Error communicating with the home automation server: {e}")

# Main function to run the bot
def main():
    # Replace 'YOUR_API_TOKEN' with the token from BotFather
    API_TOKEN = '7982507594:AAEiFot9G4AdzIsJJ8ZAPEi9nXYvQxLIVRA'

    # Create the bot application
    application = Application.builder().token(API_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_command))

    # Start polling updates from Telegram
    application.run_polling()

if __name__ == "__main__":
    main()
