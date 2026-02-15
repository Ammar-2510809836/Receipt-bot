To get your Receipt Agent working, you need three main things:
1.  **Telegram Bot Token** (Your bot's ID).
2.  **Google OAuth 2.0 Client ID** (Your "key" to access Google as yourself).
3.  **Folder ID & Sheet ID** (Where to save images/data).

---

## ⭐️ 1. Telegram Bot Token 🤖

1.  Open **Telegram App**.
2.  Search for **`@BotFather`**.
3.  Send the command: `/newbot`.
4.  **Name your bot:** (e.g., "My Receipt Agent").
5.  **Create a username:** Must end in `bot` (e.g., `my_receipt_agent_bot`).
6.  **Copy the token** and paste it in your `.env` file:
    ```ini
    TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxYZ"
    ```

---

## 2. Google OAuth 2.0 Setup (User Account)

This allows the bot to access **your** Google Drive and Sheets storage directly.

### **Step A: Create Credentials**
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a **New Project** (e.g., "Receipt Bot").
3.  **Enable APIs:**
    *   Search/Enable "Google Drive API".
    *   Search/Enable "Google Sheets API".
4.  **Configure OAuth Consent Screen:**
    *   Go to **APIs & Services** > **OAuth consent screen**.
    *   Select **External** -> **Create**.
    *   Fill in App Name ("Receipt Bot") and User Support Email (your email).
    *   **IMPORTANT:** Under **"Test users"**, click **+ ADD USERS** and enter your email address (`khalidammar103@gmail.com`). This fixes the 403 error!
    *   Save and Continue.
5.  **Create Credentials:**
    *   Go to **Credentials** > **+ CREATE CREDENTIALS** > **OAuth client ID**.
    *   Application type: **Desktop app**.
    *   Name: "Desktop client 1".
    *   Click **Create**.
6.  **Download JSON:**
    *   Click **DOWNLOAD JSON** on the pop-up.
    *   **Rename** the file to `credentials.json`.
    *   **Move** it into your project folder.

### **Step B: Configuration**
In your `.env` file, point to this file (though the code looks for `credentials.json` by default):
```ini
GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
```
*(Note: We kept the variable name same for compatibility, but it now points to the OAuth file)*

---

## 3. Google Drive Folder & Sheet IDs

### **Drive Folder**
1.  Open your folder in Google Drive.
2.  Copy the ID from the URL: `drive.google.com/drive/folders/1A2B3C...` -> `1A2B3C...`
3.  In `.env`:
    ```ini
    GOOGLE_DRIVE_PARENT_FOLDER_ID=1A2B3C...
    ```

### **Google Sheet**
1.  Create a new Google Sheet.
2.  Copy the ID from the URL: `docs.google.com/spreadsheets/d/1aBcDe.../edit` -> `1aBcDe...`
3.  In `.env`:
    ```ini
    GOOGLE_SHEET_ID=1aBcDe...
    ```

