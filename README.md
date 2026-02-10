# ASU Class Availability Discord Bot

## About
This Discord bot monitors ASU course and class availability in real-time. It automatically checks the ASU Class Search website and catalog API every 5 minutes, notifying you immediately when spots open up in the classes you're tracking until you tell it to stop.

**Key Features:**
- 🔄 Automatic background checking every 5 minutes
- 📱 User-specific notifications with Discord pings
- 💾 Persistent tracking across bot restarts
- 🖥️ Interactive startup menu for managing tracked classes
- 👥 Multi-user support - each user tracks their own classes
- 📊 Real-time availability monitoring
- 🛡️ Helpful error messages when commands are used incorrectly

## How It Works

### Architecture Overview
1. **Entry Point** (`main.py`): Handles startup menu and bot initialization.
2. **Bot Core** (`bot.py`): Discord bot logic, event handling, and background tasks.
3. **API Layer** (`asu_api.py`): Handles all interactions with ASU services:
   - **Catalog API**: Primary method for checking class details and availability (fast, reliable).
   - **Selenium/Headless Chrome**: Secondary method for specific course checks that require DOM parsing.
4. **Persistence** (`persistence.py`): JSON-based storage for tracking requests.
5. **Commands** (`commands.py`): Definition and logic for all Discord slash commands.
6. **Configuration** (`config.py`): Centralized settings.

### Background Checking Process
1. Bot starts and loads all tracking requests from `class_requests.json`
2. Background task runs every 5 minutes (configurable)
3. For each request:
   - **Classes**: Queries ASU Catalog API for availability
   - **Courses**: Scrapes ASU Class Search website
4. When spots are found, pings the specific user who requested tracking
5. Updates timestamps in persistence file

## Requirements

### System Requirements
- Python 3.8 or higher
- Google Chrome browser
- ChromeDriver (matching your Chrome version)
- Internet connection

### Python Dependencies
All dependencies are listed in `requirements.txt`:
- discord.py
- pandas
- selenium
- requests

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/aaslam12/ASU-Class-Searcher.git
cd ASU-Class-Searcher
```

### 2. Set Up Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install ChromeDriver
**Option A: Automatic (Recommended)**
Selenium 4.6+ can automatically manage ChromeDriver. Just ensure the Google Chrome browser is installed on your system.

**Option B: Manual Installation**
1. Check your Chrome version: `chrome://version` in Chrome.
2. Download matching ChromeDriver from [ChromeDriver Downloads](https://developer.chrome.com/docs/chromedriver/downloads).
3. Extract and add to your system PATH.

**Verify Installation:**
```bash
chromedriver --version
```

### 5. Configure Discord Bot Token
1. Create a Discord bot at [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a file named `token_disc.py` inside the `Discord_Bot/` directory:
```python
TOKEN = 'your-bot-token-here'
```
⚠️ **Important:** Never commit `token_disc.py` to version control!

3. In the OAuth page, generate an invite link with these permissions:
   - **Scopes:** `bot`, `applications.commands`
   - **Bot Permissions:** Send Messages, Embed Links, View Channels

## Running the Bot

### Easy Start (Recommended)
```bash
./run_bot.sh
```
(On Windows, use `run_bot.bat`)

This script handles virtual environment activation and launches the interactive startup menu.

### Manual Start
```bash
source venv/bin/activate
cd Discord_Bot
python main.py
```

## Bot Commands

All commands are **slash commands** (type `/` in Discord to see them).

### Core Tracking Commands

**`/checkclass <class_num> <class_subject> [term]`**
Track a specific class section by its catalog number and subject. Uses the fast API.
- Example: `/checkclass 205 CSE` (uses default term 2261)
- Example: `/checkclass 205 CSE 2267` (Fall 2026)
- **Parameters:**
  - `class_num`: The catalog number (e.g., 205, 110).
  - `class_subject`: The subject code (e.g., CSE, MAT).
  - `term`: (Optional) The 4-digit term code. Defaults to 2261 (Spring 2026).

**`/checkcourse <course_id> [term]`**
Track a course by its unique 5-digit Course ID number. Uses Selenium/Headless Chrome.
- Example: `/checkcourse 12345`
- Example: `/checkcourse 85492 2264`
- **Parameters:**
  - `course_id`: The 5-digit unique ID.
  - `term`: (Optional) The 4-digit term code. Defaults to 2261.

### Search & Management Commands

**`/searchclass <subject> [course_num] [term]`**
Search for available classes/sections.
- Example: `/searchclass CSE` (lists all CSE courses for default term)
- Example: `/searchclass MAT 205` (lists sections for MAT 205)
- Example: `/searchclass ENG 101 2267` (lists sections for ENG 101 in Fall 2026)
- **Parameters:**
  - `subject`: The subject code (e.g., CSE).
  - `course_num`: (Optional) Filter by specific course number.
  - `term`: (Optional) Defaults to 2261.

**`/myrequests`**
View all your active tracking requests with details and their indices.

**`/removerequest <index>`**
Remove a specific tracking request by its index (found via `/myrequests`).
- Example: `/removerequest 0`

**`/stopchecking`**
Remove ALL your tracking requests at once.

**`/listall`**
View all tracking requests from all users (useful for admins).

**`/status`**
Show bot uptime, active request count, and check interval.

## Configuration

Settings are located in `Discord_Bot/config.py`:
- `CHECK_INTERVAL_MINUTES`: Time between availability checks (default: 5).
- `MAX_REQUESTS_PER_USER`: Limit on requests per user (default: 10).
- `PERSISTENCE_FILE`: Name of the JSON file for saving requests.

## ASU Term Codes

**Default Term: 2261 (Spring 2026)**

If you don't specify a term, the bot automatically uses **2261**. You can override this by providing a term number.

Common term codes for reference:
- **2261**: Spring 2026 (DEFAULT)
- **2264**: Summer 2026
- **2267**: Fall 2026
- **2257**: Fall 2025

Format: The last number is the Semester `1` (Spring) / `4` (Summer) / `7` (Fall) and the three numbers before it is the year. For example the number `2174` would be Fall 2017 because:
```
21: 2017
    ^ ^
7:  2017
       ^
4: Summer

and Spring 2022 would be 2221. You get the idea.
```

- **Selenium:** Used only for `/checkcourse` to parse dynamic content on the public search page.
- **User Favorites:** The API endpoint `.../user/favorites/get/class/<term>` exists but is not currently used by this bot.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- **Original project**: [Kunj V Patel](https://github.com/KunjVPatel/ASU-Class-Searcher)
- This version has been extensively refactored and enhanced with persistent storage, automated background checking, improved documentation, error handling, and additional Discord commands.
