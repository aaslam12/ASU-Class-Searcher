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
2. Enable all **Privileged Gateway Intents** (Presence, Server Members, Message Content)
3. Create `Discord_Bot/token_disc.py`:
```python
TOKEN = 'your-bot-token-here'
```

⚠️ **Important:** Never commit `token_disc.py` to version control!

### 6. Invite Bot to Your Server
In the OAuth page, generate an invite link with these permissions:
Scopes:
- bot

Permissions:
- Send Messages
- Read Message History
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

All tracking management is done through Discord commands once the bot is running.

### Direct Start (Skip Menu)
```bash
python Discord_new.py
```

## Bot Commands

### Core Commands

**`!helpBot`**
Display comprehensive help with all available commands and examples.

**`!checkClass <number> <subject> [term]`**
Track a class by catalog number and subject.
- Example: `!checkClass 205 CSE` (uses default term 2261)
- Example: `!checkClass 205 CSE 2241` (Spring 2024)
- Term is optional and defaults to 2261 if not provided

**`!checkCourse <courseID> [term]`**
Track a course by its unique ID number.
- Example: `!checkCourse 12345` (uses default term 2261)
- Example: `!checkCourse 12345 2241` (Spring 2024)
- Term is optional and defaults to 2261 if not provided

**`!myRequests`**
View all your active tracking requests with details.

**`!removeRequest <index>`**
Remove a specific tracking request by index.
- Use `!myRequests` to see indices
- Example: `!removeRequest 0`

**`!stopChecking`**
Remove ALL your tracking requests at once.

### Information Commands

**`!status`**
Show bot status including:
- Uptime
- Active tracking requests
- Check interval
- Background task status

## Configuration

### Modify Check Interval
Edit `Discord_Bot/config.py`:
```python
# Change from 5 minutes to any value you prefer
CHECK_INTERVAL_MINUTES = 5
```

### Other Configurable Settings
- `COMMAND_PREFIX`: Bot command prefix (default: `!`)
- `MAX_REQUESTS_PER_USER`: Maximum tracking requests per user (default: 10)
- `PERSISTENCE_FILE`: Location of tracking data JSON file

## ASU Term Codes

**Default Term: 2261 (Spring 2026)**

If you don't specify a term, the bot automatically uses **2261**. You can override this by providing a term number.

Common term codes for reference:
- **2261**: Spring 2026 (DEFAULT)
- **2264**: Summer 2026
- **2267**: Fall 2026

Format: The leading number is the Semester `1` (Spring) / `4` (Summer) / `7` (Fall) and the two number before it is the year. For example the number `2174` would be Fall 2017 because:
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
