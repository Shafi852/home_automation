from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import requests

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I can control your home automation system. Try commands like:\n"
                                    "- Turn on lights in living room\n"
                                    "- Turn off fan in bedroom")

async def process_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()

    # Devices and rooms
    devices = ['light', 'fan', 'ac', 'tv']
    rooms = ['living room', 'bedroom', 'kitchen', 'bathroom', 'entrance']
    actions = ['turn on', 'turn off']

    # Find the matching device, room, and action
    matched_device = next((dev for dev in devices if dev in user_message), None)
    matched_room = next((room for room in rooms if room in user_message), 'living room')  # Default to living room
    matched_action = next((act for act in actions if act in user_message), None)

    if not matched_device or not matched_action:
        await update.message.reply_text("I didn't understand your command. Please use 'turn on' or 'turn off' with a device like lights, fan, AC, or TV, and specify a room.")
        return

    # Determine action
    action = 'on' if 'turn on' in user_message else 'off'

    # Construct the URL with room
    url = f"http://127.0.0.1:5000/{matched_room.replace(' ', '')}/{matched_device}/{action}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            await update.message.reply_text(f"Successfully turned {action} the {matched_device} in the {matched_room}.")
        else:
            await update.message.reply_text(f"Failed to control the {matched_device}. Please check the server.")
    except requests.RequestException as e:
        await update.message.reply_text(f"Error communicating with the home automation server: {e}")

def main():
    # Your Telegram bot token
    API_TOKEN = 'Your bot token here'

    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_command))

    application.run_polling()

if __name__ == "__main__":
    main()