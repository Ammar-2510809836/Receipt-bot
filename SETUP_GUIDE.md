# Google Cloud & Telegram Setup Guide 🛠️

To get your Receipt Agent working, you need three main things:
1.  **Telegram Bot Token** (Your bot's ID).
2.  **Google Service Account JSON** (Your "key" to access Google).
3.  **Folder ID & Sheet ID** (Where to save images/data).

---

## ⭐️ 1. Telegram Bot Token 🤖

1.  Open **Telegram App**.
2.  Search for **`@BotFather`** (The official bot with a blue checkmark).
3.  Click **Start** (or type `/start`).
4.  Send the command: `/newbot`.
5.  **Name your bot:** (e.g., "My Receipt Agent").
6.  **Create a username:** Must end in `bot` (e.g., `my_receipt_agent_bot`).
7.  **BotFather will give you a token.** It looks like this:
    `123456789:ABCdefGHIjklMNOpqrsTUVwxYZ`
8.  **Copy the token.**
9.  In your `.env` file, paste it here:
    ```ini
    TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxYZ"
    ```

---

## 2. The Service Account JSON (The Most Important Part)

The `google_service_account.json` is a file that acts like a username/password for your bot.

### **How to get it:**
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a **New Project** (e.g., named "Receipt Bot").
3.  **Enable APIs:**
    *   Search for "Google Drive API" -> Click **Enable**.
    *   Search for "Google Sheets API" -> Click **Enable**.
4.  **Create Service Account:**
    *   Go to **IAM & Admin** > **Service Accounts**.
    *   Click **+ CREATE SERVICE ACCOUNT**.
    *   Name it (e.g., "receipt-bot"). Click **Create and Continue**.
    *   **Grant Access:** Select **Editor** role (found under "Basic"). Click **Done**.
5.  **Download Key:**
    *   Click on the email address of the service account you just created.
    *   Go to the **KEYS** tab (top bar).
    *   Click **ADD KEY** > **Create new key**.
    *   Select **JSON** and click **Create**.
    *   A file will download to your computer.

### **What to do with it:**
1.  **Rename** that downloaded file to `credentials.json`.
2.  **Move** it into your project folder: `d:\MASTER SPAI.2025\receipt Agent\`.
3.  In your `.env` file, set:
    ```ini
    GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
    ```

---

## 2. Google Drive Folder ID

You don't paste the whole link. You only need the **ID**.

1.  Open your folder in Google Drive.
2.  Look at the URL in your browser address bar. It looks like this:
    `drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J`
3.  **Copy only the last part** (`1A2B3C4D5E6F7G8H9I0J`).
4.  In your `.env` file:
    ```ini
    GOOGLE_DRIVE_PARENT_FOLDER_ID=1A2B3C4D5E6F7G8H9I0J
    ```
5.  **IMPORTANT:** Right-click the folder in Drive > **Share** > Paste the **Service Account Email** (from step 1.4) and make it an **Editor**.

---

## 🚨 IMPORTANT: "App not verified" / 403 Error Fix

If you see **"Access blocked: App has not completed the Google verification process"**, do this:

1.  Go to **[Google Cloud Console > OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)**.
2.  Your "User Type" is likely **External** and status is **Testing**.
3.  Scroll down to **"Test users"**.
4.  Click **+ ADD UNERS**.
5.  Enter your email address (`khalidammar103@gmail.com`).
6.  Click **Save**.

Now try logging in again!

1.  Create a new Google Sheet.
2.  Look at the URL. It looks like this:
    `docs.google.com/spreadsheets/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit#gid=0`
3.  **Copy the long string** in the middle (`1aBcDeFgHiJkLmNoPqRsTuVwXyZ`).
4.  In your `.env` file:
    ```ini
    GOOGLE_SHEET_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ
    ```
5.  **IMPORTANT:** Click **Share** (top right) > Paste the **Service Account Email** and make it an **Editor**.
