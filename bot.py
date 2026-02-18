import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN
from ai_engine import extract_receipt_data
from google_services import upload_receipt_image, add_transaction_to_sheet, get_monthly_spend

from datetime import datetime

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("receipt_bot.log"),
        logging.StreamHandler()  # Keep console output for now, or remove if user wants silence
    ]
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I am your Receipt Agent. Send me a photo of a receipt!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.effective_chat.id
    
    await context.bot.send_message(chat_id=chat_id, text="Looking at your receipt... 🧐")

    photo_file = await update.message.photo[-1].get_file()
    # Save file locally temporarily
    temp_path = f"temp_{user.id}_{int(datetime.now().timestamp())}.jpg"
    await photo_file.download_to_drive(temp_path)

    try:
        # 1. AI Analysis
        extracted_items = extract_receipt_data(temp_path)
        if not extracted_items:
            await context.bot.send_message(chat_id=chat_id, text="Could not extract data from this receipt/screenshot.")
            os.remove(temp_path)
            return

        # 2. Upload to Drive (Once per file)
        # We use the date of the FIRST item to determine the folder, or today's date
        first_date = extracted_items[0].get('date') or datetime.now().strftime("%Y-%m-%d")
        drive_link = upload_receipt_image(temp_path, first_date)

        if not drive_link:
             await context.bot.send_message(chat_id=chat_id, text="Error saving image to Google Drive.")
             return

        # 3. Process each transaction
        for data in extracted_items:
            date_str = data.get('date')
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            try:
                receipt_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                receipt_date = datetime.now()
                date_str = receipt_date.strftime("%Y-%m-%d")

            year = receipt_date.year
            month = receipt_date.month
            month_name = receipt_date.strftime("%B")

            total = data.get('total')
            vendor = data.get('vendor')
            
            # Add to Sheet
            add_transaction_to_sheet(data, drive_link)
            
            # Reply with summary
            month_total = get_monthly_spend(year, month)
            
            reply_text = (
                f"🧾 *Transaction Saved!*\n"
                f"📅 Date: {date_str}\n"
                f"🏪 Vendor: {vendor}\n"
                f"💰 Total: {data.get('currency', '€')}{total}\n"
                f"📂 Image: [View in Drive]({drive_link})\n"
                f"📊 *Total for {month_name} {year}:* €{month_total:.2f}"
            )
            await context.bot.send_message(chat_id=chat_id, text=reply_text, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error handling photo: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Something went wrong processing your receipt.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text messages (Greetings, Queries)."""
    text = update.message.text.lower().strip()
    chat_id = update.effective_chat.id

    # 1. Greetings
    if text in ['hi', 'hello', 'hey', 'start', 'help']:
        await context.bot.send_message(chat_id=chat_id, text="👋 Hi! I'm your Receipt Bot.\n\n📸 **Send me a photo** to scan a receipt.\n💬 **Ask me:** 'Total for February' or 'How much did I spend in Jan?'")
        return

    # 2. Monthly Spend Queries
    # Keywords: total, spend, bill, cost, much
    if any(word in text for word in ['total', 'spend', 'bill', 'cost', 'much']):
        import re
        
        # Map month names to integers
        MONTHS = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        # Find which month user is asking about
        target_month = None
        target_year = datetime.now().year # Assume current year for now
        
        # Check for month names
        for m_name, m_num in MONTHS.items():
            if m_name in text:
                target_month = m_num
                break
        
        # If no specific month mentioned, assume current month? 
        # Or maybe "this month"
        if not target_month and 'this month' in text:
            target_month = datetime.now().month
            
        if target_month:
            # Check for year (e.g., "total for jan 2025")
            year_match = re.search(r'\b20\d{2}\b', text)
            if year_match:
                target_year = int(year_match.group())

            # Get data
            amount = get_monthly_spend(target_year, target_month)
            month_name = datetime(target_year, target_month, 1).strftime("%B")
            
            await context.bot.send_message(chat_id=chat_id, text=f"📊 Total spend for **{month_name} {target_year}**: €{amount:.2f}", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=chat_id, text="📅 Which month? Try saying 'Total for January'.")
        return

    # 3. Unknown text
    await context.bot.send_message(chat_id=chat_id, text="I didn't understand that. Try sending a receipt photo! 📸")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    image_handler = MessageHandler(filters.PHOTO, handle_photo)
    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(image_handler)
    application.add_handler(text_handler)
    
    print("Bot is running...")
    application.run_polling()
