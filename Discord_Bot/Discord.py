"""
ASU Class Searcher Discord Bot - Refactored Version
Monitors ASU class availability and notifies users when spots open up.
"""

import discord
from discord.ext import commands, tasks
import asyncio
import pandas as pd
import json
import requests
import re
import logging
from datetime import datetime
from typing import Optional

# Selenium imports for web scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Local imports
from token_disc import TOKEN
from config import (
    CHECK_INTERVAL_MINUTES,
    COMMAND_PREFIX,
    ASU_API_URL,
    ASU_SEARCH_URL,
    CHECK_DELAY_SECONDS,
    MAX_REQUESTS_PER_USER,
)
import persistence

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ASU_Bot")

# Initialize Discord bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Track bot start time for uptime calculation
bot_start_time = None


def scrape_course_availability(course_id: str, term: str) -> tuple:
    """
    Scrape course availability from ASU Class Search website.

    Args:
        course_id: The course ID to check
        term: Academic term (e.g., '2261')

    Returns:
        Tuple of (is_available: bool, text: str)
    """
    link = f"{ASU_SEARCH_URL}?campusOrOnlineSelection=A&honors=F&keywords={course_id}&promod=F&searchType=all&term={term}"

    chrome_options = Options()
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(link)

        wait = WebDriverWait(driver, 20)
        element = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[@id='class-results']"))
        )
        text = element.text

        driver.close()

        # parse availability from text
        pattern = r"(\d+) of (\d+)"
        match = re.search(pattern, text)

        if match:
            n_avail = int(match.group(1))
            is_available = n_avail > 0
            logger.info(f"Course {course_id}: Available = {is_available}")
            return is_available, text
        else:
            logger.warning(f"Could not parse availability for course {course_id}")
            return False, text

    except Exception as e:
        logger.error(f"Error scraping course {course_id}: {e}")
        return False, f"Error: {e}"


def check_class_via_api(class_num: str, class_subject: str, term: str) -> pd.DataFrame:
    """
    Check class availability using ASU API.

    Args:
        class_num: Class catalog number (e.g., '205')
        class_subject: Class subject code (e.g., 'CSE')
        term: Academic term (e.g., '2261')

    Returns:
        DataFrame with class information and availability
    """
    headers = {"Authorization": "Bearer null"}
    params = {
        "refine": "Y",
        "campusOrOnlineSelection": "A",
        "catalogNbr": class_num,
        "honors": "F",
        "promod": "F",
        "searchType": "all",
        "subject": class_subject,
        "term": term,
    }

    try:
        response = requests.get(ASU_API_URL, headers=headers, params=params)
        data = json.loads(response.text)

        # Extract and format data
        formatted_data = []
        class_name = f"{class_subject} {class_num}"

        for item in data.get("classes", []):
            class_info = item.get("CLAS", {})
            row = {
                "Class": class_name,
                "Class Name": class_info.get("TITLE", ""),
                "Class ID": class_info.get("CLASSNBR", ""),
                "Instructor": ", ".join(class_info.get("INSTRUCTORSLIST", [])),
                "Location": class_info.get("LOCATION", ""),
                "Occupancy": f"{class_info.get('ENRLTOT', '')} of {class_info.get('ENRLCAP', '')}",
            }
            formatted_data.append(row)

        df = pd.DataFrame(formatted_data)

        # Add 'Available' column
        if not df.empty:
            df["Available"] = False
            for idx, occupancy in enumerate(df["Occupancy"]):
                numbers = occupancy.split(" of ")
                if len(numbers) == 2 and numbers[0].isdigit() and numbers[1].isdigit():
                    if int(numbers[0]) < int(numbers[1]):
                        df.at[idx, "Available"] = True

        return df

    except Exception as e:
        logger.error(f"Error checking class {class_subject} {class_num}: {e}")
        return pd.DataFrame()


@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def background_checker():
    """
    Background task that continuously checks all tracked classes/courses.
    """
    logger.info("Running background availability check...")

    requests = persistence.load_requests()

    if not requests:
        logger.info("No active tracking requests")
        return

    logger.info(f"Checking {len(requests)} tracking requests")

    for request in requests:
        request_id = request["id"]
        request_type = request["type"]
        user_id = request["user_id"]
        username = request["username"]
        channel_id = request["channel_id"]
        term = request["term"]

        # Update last checked timestamp
        persistence.update_request_timestamps(request_id, last_checked=True)

        try:
            if request_type == "class":
                # Check class via API
                class_num = request["class_num"]
                class_subject = request["class_subject"]

                df = check_class_via_api(class_num, class_subject, term)
                available_classes = (
                    df[df["Available"]] if not df.empty else pd.DataFrame()
                )

                if not available_classes.empty:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        user_mention = f"<@{user_id}>"
                        table_message = (
                            f"```{available_classes.to_string(index=False)}```"
                        )
                        await channel.send(
                            f"{user_mention} 🎉 **Class spots available!**\n"
                            f"**{class_subject} {class_num}** - Term {term}\n"
                            f"{table_message}"
                        )
                        # Update last notified timestamp
                        persistence.update_request_timestamps(
                            request_id, last_notified=True
                        )
                        logger.info(
                            f"Notified user {username} about {class_subject} {class_num}"
                        )

            elif request_type == "course":
                # Check course via web scraping
                course_id = request["course_id"]

                is_available, text = scrape_course_availability(course_id, term)

                if is_available:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        user_mention = f"<@{user_id}>"
                        await channel.send(
                            f"{user_mention} 🎉 **Course available!**\n"
                            f"**Course ID: {course_id}** - Term {term}\n"
                            f"Register now!\n```{text[:500]}```"
                        )
                        # Update last notified timestamp
                        persistence.update_request_timestamps(
                            request_id, last_notified=True
                        )
                        logger.info(
                            f"Notified user {username} about course {course_id}"
                        )

        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")

        # Small delay between checks to avoid rate limiting
        await asyncio.sleep(CHECK_DELAY_SECONDS)

    logger.info("Background check completed")


@bot.event
async def on_ready():
    """Called when the bot successfully connects to Discord."""
    global bot_start_time
    bot_start_time = datetime.utcnow()

    logger.info(f"Bot logged in as {bot.user}")
    logger.info(f"Connected to {len(bot.guilds)} server(s)")

    # Start the background checker
    if not background_checker.is_running():
        background_checker.start()
        logger.info(
            f"Background checker started (interval: {CHECK_INTERVAL_MINUTES} minutes)"
        )


@bot.event
async def on_command_error(ctx, error):
    """
    Global error handler for all bot commands.
    Sends helpful error messages to Discord.
    """
    # original exception
    if hasattr(ctx, "command") and ctx.command is None:
        return

    error = getattr(error, "original", error)

    # missing arguments
    if isinstance(error, commands.MissingRequiredArgument):
        await send_command_error(
            ctx,
            f"❌ Missing argument: `{error.param.name}`",
            get_command_help(ctx.command.name if ctx.command else "unknown"),
        )

    # too many arguments
    elif isinstance(error, commands.TooManyArguments):
        await send_command_error(
            ctx,
            "❌ Too many arguments provided",
            get_command_help(ctx.command.name if ctx.command else "unknown"),
        )

    # bad argument type
    elif isinstance(error, commands.BadArgument):
        await send_command_error(
            ctx,
            f"❌ Invalid argument: {str(error)}",
            get_command_help(ctx.command.name if ctx.command else "unknown"),
        )

    # command not found
    elif isinstance(error, commands.CommandNotFound):
        cmd = ctx.message.content.split()[0]
        await ctx.send(
            f"❌ Command `{cmd}` not found.\n"
            f"Use `!helpBot` to see available commands."
        )

    # other errors
    else:
        logger.error(f"Unhandled error in command {ctx.command}: {error}")
        await send_command_error(
            ctx,
            f"❌ An error occurred: {str(error)}",
            "Please check the command format or try again.",
        )


async def send_command_error(ctx, error_msg: str, help_text: str):
    """
    Send a formatted error embed to Discord.

    Args:
        ctx: Command context
        error_msg: Error message to display
        help_text: Help text or command usage
    """
    embed = discord.Embed(
        title="⚠️ Command Error", description=error_msg, color=0xFF0000  # Red
    )
    embed.add_field(name="How to use:", value=help_text, inline=False)
    embed.set_footer(text="Use !helpBot for more information")
    await ctx.send(embed=embed)


def get_command_help(command_name: str) -> str:
    """Get help text for a specific command."""
    help_dict = {
        "checkclass": "`!checkClass <classNumber> <subject> [term]`\n"
        "Example: `!checkClass 205 CSE` or `!checkClass 205 CSE 2261`\n"
        "• classNumber: Catalog number (e.g., 205)\n"
        "• subject: Subject code (e.g., CSE, MAT, ENG)\n"
        "• term: Academic term (optional, defaults to 2261)\n"
        "  Examples: 2261 (Spring 2025), 2264 (Summer 2026), 2267 (Fall 2026)",
        "checkcourse": "`!checkCourse <courseID> [term]`\n"
        "Example: `!checkCourse 12345` or `!checkCourse 12345 2261`\n"
        "• courseID: Course ID number\n"
        "• term: Academic term (optional, defaults to 2261)",
        "myrequests": "`!myRequests`\n" "Shows all your active tracking requests.",
        "removerequest": "`!removeRequest <index>`\n"
        "Example: `!removeRequest 0`\n"
        "• index: Request index from !myRequests\n"
        "Use `!myRequests` to see available indices.",
        "stopchecking": "`!stopChecking`\n" "Removes ALL your tracking requests.",
        "status": "`!status`\n" "Shows bot statistics and status.",
        "listall": "`!listAll`\n" "Shows all active requests from all users.",
        "helpbot": "`!helpBot`\n" "Displays all available commands and usage.",
    }
    return help_dict.get(command_name.lower(), "Use `!helpBot` for command list.")


@bot.command()
async def helpBot(ctx):
    """Display comprehensive help information about bot commands."""
    embed = discord.Embed(
        title="🎓 ASU Class Searcher Bot - Help",
        description="Track ASU class availability and get notified when spots open up!",
        color=0x8C1D40,  # ASU Maroon
    )

    embed.add_field(
        name="📚 !checkClass <num> <subject> [term]",
        value="Track a class by number and subject.\n"
        "Examples:\n"
        "  `!checkClass 205 CSE` (uses default term 2261)\n"
        "  `!checkClass 205 CSE 2261` (Spring 2026)\n"
        "Term defaults to 2261 if not provided",
        inline=False,
    )

    embed.add_field(
        name="🔍 !checkCourse <courseID> [term]",
        value="Track a course by ID number.\n"
        "Examples:\n"
        "  `!checkCourse 12345` (uses default term 2261)\n"
        "  `!checkCourse 12345 2261` (Spring 2026)\n"
        "Term defaults to 2261 if not provided",
        inline=False,
    )

    embed.add_field(
        name="📋 !myRequests",
        value="View all your active tracking requests",
        inline=False,
    )

    embed.add_field(
        name="🗑️ !removeRequest <index>",
        value="Remove one of your tracking requests by index.\n"
        "Use `!myRequests` to see indices",
        inline=False,
    )

    embed.add_field(
        name="🛑 !stopChecking", value="Remove ALL your tracking requests", inline=False
    )

    embed.add_field(
        name="📊 !status", value="Show bot status and statistics", inline=False
    )

    embed.add_field(
        name="📖 !listAll",
        value="View all active tracking requests (all users)",
        inline=False,
    )

    embed.set_footer(
        text=f"Bot checks every {CHECK_INTERVAL_MINUTES} minutes • Max {MAX_REQUESTS_PER_USER} requests per user"
    )

    await ctx.send(embed=embed)


@bot.command()
async def checkClass(ctx, class_num: str, class_subject: str, term: str = "2261"):
    """
    Start tracking a class for availability.

    Args:
        class_num: Class catalog number (e.g., '205')
        class_subject: Class subject code (e.g., 'CSE')
        term: Academic term (e.g., '2261') - defaults to 2261 if not provided
    """
    user_id = ctx.author.id
    username = str(ctx.author)
    channel_id = ctx.channel.id

    # Validate inputs
    if not class_num or not class_num.replace(".", "", 1).isdigit():
        await send_command_error(
            ctx,
            "❌ Class number must be numeric (e.g., 205 or 112.5)",
            get_command_help("checkclass"),
        )
        return

    if not class_subject or len(class_subject) > 6:
        await send_command_error(
            ctx,
            "❌ Subject must be a valid code (e.g., CSE, MAT, ENG)",
            get_command_help("checkclass"),
        )
        return

    if not term or len(term) != 4 or not term.isdigit():
        await send_command_error(
            ctx,
            "❌ Term must be 4 digits (e.g., 2261 for Spring 2026)",
            get_command_help("checkclass"),
        )
        return

    # Check if user has reached request limit
    current_count = persistence.count_user_requests(user_id)
    if current_count >= MAX_REQUESTS_PER_USER:
        await ctx.send(
            f"❌ You've reached the limit of {MAX_REQUESTS_PER_USER} tracking requests. "
            f"Remove some with `!removeRequest` or `!stopChecking`."
        )
        return

    # Add the request
    request_id = persistence.add_request(
        request_type="class",
        user_id=user_id,
        username=username,
        channel_id=channel_id,
        class_num=class_num,
        class_subject=class_subject.upper(),
        term=term,
    )

    if request_id:
        await ctx.send(
            f"✅ Now tracking **{class_subject.upper()} {class_num}** (Term: {term})\n"
            f"You'll be notified here when spots become available.\n"
            f"_Checking every {CHECK_INTERVAL_MINUTES} minutes_"
        )
        logger.info(
            f"User {username} added class tracking: {class_subject} {class_num}"
        )
    else:
        await ctx.send("❌ Failed to add tracking request. Please try again.")


@bot.command()
async def checkCourse(ctx, course_id: str, term: str = "2261"):
    """
    Start tracking a course by ID for availability.

    Args:
        course_id: Course ID number
        term: Academic term (e.g., '2261') - defaults to 2261 if not provided
    """
    user_id = ctx.author.id
    username = str(ctx.author)
    channel_id = ctx.channel.id

    # Validate inputs
    if not course_id or not course_id.isdigit():
        await send_command_error(
            ctx,
            "❌ Course ID must be numeric (e.g., 12345)",
            get_command_help("checkcourse"),
        )
        return

    if not term or len(term) != 4 or not term.isdigit():
        await send_command_error(
            ctx,
            "❌ Term must be 4 digits (e.g., 2261 for Spring 2026)",
            get_command_help("checkcourse"),
        )
        return

    # Check if user has reached request limit
    current_count = persistence.count_user_requests(user_id)
    if current_count >= MAX_REQUESTS_PER_USER:
        await ctx.send(
            f"❌ You've reached the limit of {MAX_REQUESTS_PER_USER} tracking requests. "
            f"Remove some with `!removeRequest` or `!stopChecking`."
        )
        return

    # Add the request
    request_id = persistence.add_request(
        request_type="course",
        user_id=user_id,
        username=username,
        channel_id=channel_id,
        course_id=course_id,
        term=term,
    )

    if request_id:
        await ctx.send(
            f"✅ Now tracking **Course ID: {course_id}** (Term: {term})\n"
            f"You'll be notified here when it becomes available.\n"
            f"_Checking every {CHECK_INTERVAL_MINUTES} minutes_"
        )
        logger.info(f"User {username} added course tracking: {course_id}")
    else:
        await ctx.send("❌ Failed to add tracking request. Please try again.")


@bot.command()
async def myRequests(ctx):
    """Show all tracking requests for the current user."""
    user_id = ctx.author.id
    requests = persistence.get_user_requests(user_id)

    if not requests:
        await ctx.send(
            "📭 You have no active tracking requests.\n"
            "Use `!checkClass` or `!checkCourse` to add some!"
        )
        return

    embed = discord.Embed(
        title=f"📋 Your Tracking Requests ({len(requests)})", color=0x8C1D40
    )

    for idx, req in enumerate(requests):
        if req["type"] == "class":
            name = f"{idx}. {req['class_subject']} {req['class_num']}"
            value = f"Term: {req['term']}"
        else:
            name = f"{idx}. Course ID: {req['course_id']}"
            value = f"Term: {req['term']}"

        if req["last_notified"]:
            value += f"\n✅ Last notified: {req['last_notified'][:16]}"
        elif req["last_checked"]:
            value += f"\n🔍 Last checked: {req['last_checked'][:16]}"

        embed.add_field(name=name, value=value, inline=False)

    embed.set_footer(text=f"Use !removeRequest <index> to remove a request")

    await ctx.send(embed=embed)


@bot.command()
async def removeRequest(ctx, index: int = None):
    """
    Remove a specific tracking request by index.

    Args:
        index: The index of the request (from !myRequests)
    """
    user_id = ctx.author.id
    requests = persistence.get_user_requests(user_id)

    # Validate input
    if index is None:
        await send_command_error(
            ctx,
            "❌ You must provide an index number",
            get_command_help("removerequest"),
        )
        return

    if not requests:
        await ctx.send("📭 You have no active tracking requests to remove.")
        return

    if index < 0 or index >= len(requests):
        await ctx.send(
            f"❌ Invalid index. Use `!myRequests` to see valid indices (0-{len(requests)-1})."
        )
        return

    request_to_remove = requests[index]
    request_id = request_to_remove["id"]

    if persistence.remove_request(request_id):
        if request_to_remove["type"] == "class":
            desc = (
                f"{request_to_remove['class_subject']} {request_to_remove['class_num']}"
            )
        else:
            desc = f"Course ID: {request_to_remove['course_id']}"

        await ctx.send(f"✅ Removed tracking request: **{desc}**")
        logger.info(f"User {ctx.author} removed request: {desc}")
    else:
        await ctx.send("❌ Failed to remove request. Please try again.")


@bot.command()
async def stopChecking(ctx):
    """Remove ALL tracking requests for the current user."""
    user_id = ctx.author.id
    count = persistence.remove_user_requests(user_id)

    if count > 0:
        await ctx.send(f"✅ Removed all **{count}** tracking request(s).")
        logger.info(f"User {ctx.author} removed all {count} requests")
    else:
        await ctx.send("📭 You have no active tracking requests.")


@bot.command()
async def listAll(ctx):
    """Show all active tracking requests from all users."""
    requests = persistence.load_requests()

    if not requests:
        await ctx.send("📭 No active tracking requests.")
        return

    embed = discord.Embed(
        title=f"📊 All Active Tracking Requests ({len(requests)})",
        description=f"Checking every {CHECK_INTERVAL_MINUTES} minutes",
        color=0xFFC627,  # ASU Gold
    )

    # Group by user
    user_requests = {}
    for req in requests:
        username = req["username"]
        if username not in user_requests:
            user_requests[username] = []
        user_requests[username].append(req)

    for username, user_reqs in user_requests.items():
        value = ""
        for req in user_reqs[:5]:  # Limit to 5 per user for display
            if req["type"] == "class":
                value += f"• {req['class_subject']} {req['class_num']} (Term {req['term']})\n"
            else:
                value += f"• Course {req['course_id']} (Term {req['term']})\n"

        if len(user_reqs) > 5:
            value += f"_...and {len(user_reqs) - 5} more_\n"

        embed.add_field(
            name=f"{username} ({len(user_reqs)})", value=value, inline=False
        )

    await ctx.send(embed=embed)


@bot.command()
async def status(ctx):
    """Show bot status and statistics."""
    requests = persistence.load_requests()

    # Calculate uptime
    if bot_start_time:
        uptime = datetime.utcnow() - bot_start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
    else:
        uptime_str = "Unknown"

    embed = discord.Embed(title="🤖 Bot Status", color=0x8C1D40)

    embed.add_field(name="Uptime", value=uptime_str, inline=True)
    embed.add_field(name="Active Requests", value=str(len(requests)), inline=True)
    embed.add_field(
        name="Check Interval", value=f"{CHECK_INTERVAL_MINUTES} min", inline=True
    )
    embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    embed.add_field(
        name="Background Task",
        value="✅ Running" if background_checker.is_running() else "❌ Stopped",
        inline=True,
    )

    await ctx.send(embed=embed)


# Run the bot
if __name__ == "__main__":
    logger.info("Starting ASU Class Searcher Bot...")
    bot.run(TOKEN)
