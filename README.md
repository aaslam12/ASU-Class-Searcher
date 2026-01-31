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
1. **Startup Menu** (`startup_menu.py`): Simple CLI to view tracked classes before bot starts
2. **Persistence Layer** (`persistence.py`): JSON-based storage for tracking requests
3. **Bot Core** (`Discord_new.py`): Discord bot with commands and background checker
4. **Configuration** (`config.py`): Centralized settings

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
- Python 3.7 or higher
- Google Chrome browser
- ChromeDriver (matching your Chrome version)
- Internet connection

### Python Dependencies
All dependencies are listed in `requirements.txt`:
- discord.py >= 2.0
- pandas
- selenium
- requests

## Installation & Setup

### 1. Clone the Repository
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
```bash
# Selenium 4.6+ can automatically manage ChromeDriver
# Just ensure Chrome browser is installed
```

**Option B: Manual Installation**
1. Check your Chrome version: `chrome://version` in Chrome
2. Download matching ChromeDriver from [ChromeDriver Downloads](https://developer.chrome.com/docs/chromedriver/downloads)
3. Extract and add to your system PATH

**Verify Installation:**
```bash
chromedriver --version
```

### 5. Configure Discord Bot Token
1. Create a Discord bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create `Discord_Bot/token_disc.py`:
```python
TOKEN = 'your-bot-token-here'
```

⚠️ **Important:** Never commit `token_disc.py` to version control!

3. In the OAuth page, generate an invite link with these permissions:

**Scopes:**
- `bot`
- `applications.commands` (REQUIRED for slash commands)

**Bot Permissions:**
- Send Messages
- Embed Links
- View Channels

## Running the Bot

### Start with Interactive Menu
```bash
./run_bot.sh # or run_bot.bat for Windows
```

This launches the startup menu where you can:
1. View all tracked classes
2. Clear all tracking requests
3. Start the bot

All tracking management is done through Discord slash commands once the bot is running.

### Direct Start (Skip Menu)
```bash
python Discord.py
```

## Bot Commands

All commands are **slash commands** (type `/` in Discord to see them).

### Core Commands

**`/helpbot`**
Display comprehensive help with all available commands and examples.

**`/checkclass <number> <subject> [term]`**
Track a class by catalog number and subject.
- Example: `/checkclass 205 CSE` (uses default term 2261)
- Example: `/checkclass 205 CSE 2241` (Spring 2024)
- Term is optional and defaults to 2261 if not provided

**`/checkcourse <courseID> [term]`**
Track a course by its unique ID number.
- Example: `/checkcourse 12345` (uses default term 2261)
- Example: `/checkcourse 12345 2241` (Spring 2024)
- Term is optional and defaults to 2261 if not provided

**`/searchclass <subject> [term] [limit]`**
Search for available classes by subject code.
- Example: `/searchclass CSE` (searches CSE classes for term 2261)
- Example: `/searchclass MAT 2261` (searches MAT classes for Spring 2026)
- Example: `/searchclass ENG 2261 15` (show up to 15 results)
- Shows class numbers, titles, and seat availability
- Helps you find classes before tracking them

**`/myrequests`**
View all your active tracking requests with details.

**`/removerequest <index>`**
Remove a specific tracking request by index.
- Use `/myrequests` to see indices
- Example: `/removerequest 0`

**`/stopchecking`**
Remove ALL your tracking requests at once.

### Information Commands

**`/status`**
Show bot status including:
- Uptime
- Active tracking requests
- Check interval
- Background task status

**`/listall`**
View all tracking requests from all users

## Configuration

- `CHECK_INTERVAL_MINUTES`: Fixed interval to check class openings (default: 5)
- `MAX_REQUESTS_PER_USER`: Maximum tracking requests per user (default: 10)
- `PERSISTENCE_FILE`: Location of tracking data JSON file

## ASU Term Codes

**Default Term: 2261 (Spring 2026)**

If you don't specify a term, the bot automatically uses **2261**. You can override this by providing a term number.

Common term codes for reference:
- **2261**: Spring 2026 (DEFAULT)
- **2264**: Summer 2026
- **2267**: Fall 2026

Format: The last number is the Semester `1` (Spring) / `4` (Summer) / `7` (Fall) and the three numbers before it is the year. For example the number `2174` would be Fall 2017 because:
```
21: 2017
    ^ ^
7:  2017
       ^
4: Summer

and Spring 2022 would be 2221. You get the idea.
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- **Original project**: [Kunj V Patel](https://github.com/KunjVPatel/ASU-Class-Searcher)
- This version has been extensively refactored and enhanced with persistent storage, automated background checking, improved documentation, error handling, and additional Discord commands.
- ASU Class Search API
- Discord.py library
- Selenium WebDriver
