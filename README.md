# ASU Class Availability Discord Bot

## About
This Discord bot monitors ASU course and class availability in real-time. It automatically checks the ASU Class Search website and catalog API every 5 minutes, notifying you immediately when spots open up in the classes you're tracking.

**Key Features:**
- 🔄 Automatic background checking every 5 minutes
- 📱 User-specific notifications with Discord pings
- 💾 Persistent tracking across bot restarts
- 🖥️ Interactive startup menu for managing tracked classes
- 👥 Multi-user support - each user tracks their own classes
- 📊 Real-time availability monitoring
- 🛡️ Helpful error messages when commands are used incorrectly

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

**Important:** Never commit `token_disc.py` to version control!

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

## Helpful Error Messages

Made a mistake with a command? Don't worry! The bot provides clear error messages with examples:

- **Missing arguments?** → Shows which argument is missing
- **Wrong format?** → Displays correct command format with examples
- **Invalid input?** → Explains what went wrong and how to fix it
- **Invalid index?** → Shows valid options

All error messages include the correct command usage so you can fix it immediately!

**Examples:**
- `!checkClass 205` → "❌ Missing argument: class_subject" + shows correct format
- `!checkClass abc CSE 2241` → "❌ Class number must be numeric"
- `!removeRequest notanumber` → "❌ Invalid argument" + shows correct format

**`!listAll`**
View all active tracking requests from all users (useful for transparency).

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

### Data Persistence
All tracking requests are saved in `class_requests.json`:
```json
{
  "requests": [
    {
      "id": "unique-uuid",
      "type": "class",
      "user_id": 123456789,
      "username": "User#1234",
      "channel_id": 987654321,
      "class_num": "205",
      "class_subject": "CSE",
      "term": "2241",
      "added_at": "2026-01-31T01:00:00Z",
      "last_checked": "2026-01-31T01:45:00Z",
      "last_notified": null
    }
  ]
}
```

## ASU Term Codes

**Default Term: 2261 (Spring 2025)**

If you don't specify a term, the bot automatically uses **2261**. You can override this by providing a term number.

Common term codes for reference:
- **2261**: Spring 2025 (DEFAULT)
- **2264**: Summer 2026
- **2267**: Fall 2026

Format: `YY` (year) + `41` (Spring) / `44` (Summer) / `47` (Fall)

## Troubleshooting

### ChromeDriver Issues
**Error: "chromedriver not found"**
- Ensure ChromeDriver is in system PATH
- Try running: `which chromedriver` (Linux/Mac) or `where chromedriver` (Windows)
- For Selenium 4.6+, ensure Chrome browser is installed

**Error: "session not created: This version of ChromeDriver only supports Chrome version X"**
- Update ChromeDriver to match your Chrome version
- Or update Chrome browser to match ChromeDriver

### Discord Bot Issues
**Bot doesn't respond to commands**
- Verify bot token in `token_disc.py` is correct
- Check bot has "Message Content Intent" enabled in Discord Developer Portal
- Ensure bot has proper permissions in your server

**Bot can't send messages**
- Check bot has "Send Messages" and "Embed Links" permissions
- Verify bot role is above any role restrictions

### API/Scraping Issues
**No classes found**
- Verify term code is correct (e.g., 2241 for Spring 2024)
- Check class subject and number are valid
- ASU website may be temporarily down

**Rate limiting errors**
- Reduce `CHECK_INTERVAL_MINUTES` to avoid frequent checks
- Add delays between checks in `config.py`

## Extending the Bot

### Adding New Commands
1. Edit `Discord_Bot/Discord_new.py`
2. Add new command using `@bot.command()` decorator:
```python
@bot.command()
async def myCommand(ctx, arg1, arg2):
    # Your logic here
    await ctx.send("Response")
```

### Modifying Check Logic
Edit the `background_checker()` function in `Discord_new.py` to customize:
- Check frequency
- Notification format
- API parameters

### Adding New Data Fields
1. Update JSON schema in `persistence.py`
2. Modify `add_request()` function to include new fields
3. Update display functions to show new data

## Security & Privacy

- ⚠️ **Never share your bot token** - it's like a password
- Bot tokens are in `.gitignore` to prevent accidental commits
- Consider running the bot on a private server or your local machine
- Be mindful of Discord's rate limits when checking many classes

## Contributing

Contributions welcome! Areas for improvement:
- Additional notification methods (email, SMS)
- Web dashboard for managing tracked classes
- Support for other universities
- Database backend (PostgreSQL, MongoDB)
- Docker containerization

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- **Original project**: [Kunj V Patel](https://github.com/KunjVPatel/ASU-Class-Searcher)
- This version has been extensively refactored and enhanced with persistent storage, automated background checking, improved documentation, error handling, and additional Discord commands.

- ASU Class Search API
- Discord.py library
- Selenium WebDriver
