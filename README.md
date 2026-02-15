# Receipt Bot 🧾🤖

A Telegram Bot that uses AI (Llama 3.2 Vision via Groq) to extract data from receipt images and automatically logs them into Google Drive and Google Sheets.

## Key Features

### 1. 📷 Smart Receipt Scanning
- **AI-Powered:** Uses `llama-3.2-90b-vision-preview` via Groq API.
- **Data Extraction:** Extracts *Date*, *Vendor*, *Total*, *Currency*, and *Items*.
- **Robust:** Handles different date formats (YYYY-MM-DD, DD.MM.YYYY) and currency symbols (e.g., €, $).

### 2. 📂 Organized Storage (Google Drive)
- **Automatic Folders:** Creates a folder structure `Year > Month` (e.g., `2026/02`).
- **File Naming:** Uploads original images for safe-keeping.

### 3. 📊 Automated Bookkeeping (Google Sheets)
- **Multi-Sheet Support:** Automatically creates a new tab for each month (e.g., `February 2026`).
- **Auto-Headers:** Adds headers (`Date | Vendor | Total | ...`) immediately if a new sheet is created.
- **Data Logging:** Appends extracted data row-by-row.

### 4. 💬 Chat Assistant
- **Greetings:** Responds to "Hi", "Hello".
- **Spend Queries:** Answers questions like "Total for January" or "How much did I spend in Feb 2026?".
- **Immediate Feedback:** Replies with a summary after every upload.

---

## Setup Instructions

### Prerequisites
1.  **Python 3.10+**
2.  **Google Cloud Account** (for Drive/Sheets API)
3.  **Groq API Key**
4.  **Telegram Bot Token**

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Ammar-2510809836/Receipt-bot.git
    cd Receipt-bot
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the root directory:
    ```ini
    TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
    GROQ_API_KEY="your_groq_api_key"
    GOOGLE_SERVICE_ACCOUNT_JSON="credentials.json"
    GOOGLE_DRIVE_PARENT_FOLDER_ID="your_folder_id"
    GOOGLE_SHEET_ID="your_sheet_id"
    ```

4.  **Google OAuth Setup:**
    - Place your `credentials.json` (OAuth Client ID) in the project folder.
    - Run the bot once to generate `token.json`.

### Running the Bot
```bash
python bot.py
```

---

## Project Structure
- `bot.py`: Main Telegram bot logic.
- `ai_engine.py`: Handles image processing and Groq API calls.
- `google_services.py`: Manages Google Drive uploads and Sheets updates.
- `config.py`: Loads environment variables.
- `SETUP_GUIDE.md`: Detailed setup instructions.

---
*Created by Receipt Bot Assistant*
