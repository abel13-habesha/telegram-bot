import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8025808006:AAEba18fOGKkMBENeka7buuQ9Ml53-GUpoo"
ADMIN_IDS = [5042921652]
ADMINS_FILE = "admins.json"
DATA_DIR = "data"

if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w") as f:
        json.dump(ADMIN_IDS, f)
else:
    with open(ADMINS_FILE, "r") as f:
        ADMIN_IDS = json.load(f)

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

user_buttons = ReplyKeyboardMarkup([
    ["ጥያቄ ይላኩ", "አስተያየት ይላኩ"],
    ["ጥቆማ ይላኩ", "ፈቃድ ይጠይቁ"],
    ["ፋይል ይላኩ"]
], resize_keyboard=True)

admin_buttons = ReplyKeyboardMarkup([
    ["View Messages", "Add Admin"],
    ["Remove Admin", "List Admins"]
], resize_keyboard=True)

def save_to_file(filename, text):
    with open(os.path.join(DATA_DIR, filename), "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

def is_admin(user_id):
    return user_id in ADMIN_IDS

def add_admin(user_id):
    if user_id not in ADMIN_IDS:
        ADMIN_IDS.append(user_id)
        with open(ADMINS_FILE, "w") as f:
            json.dump(ADMIN_IDS, f)

def remove_admin(user_id):
    if user_id in ADMIN_IDS:
        ADMIN_IDS.remove(user_id)
        with open(ADMINS_FILE, "w") as f:
            json.dump(ADMIN_IDS, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        await update.message.reply_text("Welcome, Admin!", reply_markup=admin_buttons)
    else:
        await update.message.reply_text("እንኳን ደህና መጡ! እባኮትን አንዱን ይምረጡ።", reply_markup=user_buttons)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if is_admin(user.id):
        if text == "Add Admin":
            await update.message.reply_text("Send the user ID to add:")
            context.user_data["admin_action"] = "add"
        elif text == "Remove Admin":
            await update.message.reply_text("Send the user ID to remove:")
            context.user_data["admin_action"] = "remove"
        elif text == "List Admins":
            await update.message.reply_text(f"Admin IDs: {ADMIN_IDS}")
        elif text == "View Messages":
            files = os.listdir(DATA_DIR)
            message = "\n".join(files) if files else "No messages yet."
            await update.message.reply_text("Saved files:\n" + message)
        elif context.user_data.get("admin_action"):
            action = context.user_data["admin_action"]
            try:
                new_id = int(text)
                if action == "add":
                    add_admin(new_id)
                    await update.message.reply_text(f"Added admin: {new_id}")
                elif action == "remove":
                    remove_admin(new_id)
                    await update.message.reply_text(f"Removed admin: {new_id}")
                context.user_data["admin_action"] = None
            except ValueError:
                await update.message.reply_text("Invalid ID.")
        else:
            await update.message.reply_text("Unknown command.")
    else:
        filename = ""
        if text == "ጥያቄ ይላኩ":
            context.user_data["mode"] = "question"
            await update.message.reply_text("እባኮትን ጥያቄዎን ይላኩ።")
        elif text == "አስተያየት ይላኩ":
            context.user_data["mode"] = "comment"
            await update.message.reply_text("እባኮትን አስተያየትዎን ይላኩ።")
        elif text == "ጥቆማ ይላኩ":
            context.user_data["mode"] = "suggestion"
            await update.message.reply_text("እባኮትን ጥቆማዎን ይላኩ።")
        elif text == "ፈቃድ ይጠይቁ":
            context.user_data["mode"] = "permission"
            await update.message.reply_text("እባኮትን ፈቃድ ይጠይቁ።")
        elif text == "ፋይል ይላኩ":
            await update.message.reply_text("እባኮትን PDF ወይም Word ፋይል ያጭኑ።")
        else:
            mode = context.user_data.get("mode", "unknown")
            filename = f"{mode}_{user.id}.txt"
            save_to_file(filename, f"From: {user.first_name} ({user.id})\n{text}")
            await update.message.reply_text("ለመላክዎ እናመሰግናለን!")
            context.user_data["mode"] = None

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    user = update.effective_user
    file = await doc.get_file()
    filename = f"{user.id}_{doc.file_name}"
    await file.download_to_drive(os.path.join(DATA_DIR, filename))
    await update.message.reply_text("ፋይሉ ተቀባይነት አግኝቷል። እናመሰግናለን!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()