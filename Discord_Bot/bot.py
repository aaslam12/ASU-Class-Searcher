"""ASU Class Searcher Discord Bot - Main bot setup and background tasks."""

import asyncio
import logging
from datetime import datetime

import discord
from discord.ext import commands, tasks

import persistence
from asu_api import check_class_via_api, scrape_course_availability
from commands import setup_commands
from config import CHECK_DELAY_SECONDS, CHECK_INTERVAL_MINUTES
from token_disc import TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ASU_Bot")

# Bot setup
intents = discord.Intents.default()
intents.message_content = False
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
bot.remove_command("help")

# Track start time (using list for mutability in nested function)
bot_start_time = [None]


@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def background_checker():
    """Background task that checks all tracked classes for availability."""
    logger.info("Running background availability check...")
    requests = persistence.load_requests()

    if not requests:
        logger.info("No active tracking requests")
        return

    logger.info(f"Checking {len(requests)} tracking request(s)")

    for req in requests:
        try:
            await check_single_request(req)
        except Exception as e:
            logger.error(f"Error checking request {req['id']}: {e}")

        await asyncio.sleep(CHECK_DELAY_SECONDS)

    logger.info("Background check completed")


async def check_single_request(req: dict):
    """Check a single tracking request and notify if available."""
    is_available = False
    message = ""

    if req["type"] == "class":
        df = check_class_via_api(req["class_num"], req["class_subject"], req["term"])

        if not df.empty and "Open Seats" in df.columns:
            open_seats = df["Open Seats"].iloc[0]
            if open_seats > 0:
                is_available = True
                class_name = df["Class Name"].iloc[0] if "Class Name" in df.columns else "Unknown"
                instructor = df["Instructor"].iloc[0] if "Instructor" in df.columns else "TBA"
                message = (
                    f"🎉 **SPOT AVAILABLE!**\n\n"
                    f"**{req['class_subject']} {req['class_num']}** - {class_name}\n"
                    f"👨‍🏫 {instructor}\n"
                    f"🪑 **{open_seats} seat(s) available!**\n\n"
                    f"⚡ Enroll now before it fills up!"
                )

    elif req["type"] == "course":
        enrolled, capacity, title = scrape_course_availability(req["course_id"], req["term"])

        if enrolled is not None and capacity is not None:
            available = capacity - enrolled
            if available > 0:
                is_available = True
                message = (
                    f"🎉 **SPOT AVAILABLE!**\n\n"
                    f"**Course {req['course_id']}** - {title}\n"
                    f"🪑 **{available} seat(s) available!**\n\n"
                    f"⚡ Enroll now before it fills up!"
                )

    # Update last checked
    persistence.update_request(req["id"], {"last_checked": datetime.utcnow().isoformat() + "Z"})

    # Send notification if available
    if is_available:
        try:
            channel = bot.get_channel(req["channel_id"])
            if channel:
                await channel.send(f"<@{req['user_id']}>\n{message}")
                persistence.update_request(req["id"], {"last_notified": datetime.utcnow().isoformat() + "Z"})
                logger.info(f"Notified user {req['username']} about availability")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


@bot.event
async def on_ready():
    """Called when the bot successfully connects to Discord."""
    bot_start_time[0] = datetime.utcnow()

    logger.info(f"Bot logged in as {bot.user}")
    logger.info(f"Connected to {len(bot.guilds)} server(s)")

    # Clear guild commands and sync globally
    try:
        for guild in bot.guilds:
            bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
            logger.info(f"Cleared guild commands from: {guild.name}")

        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} commands globally")
    except Exception as e:
        logger.error(f"Failed to sync app commands: {e}")

    # Start background checker
    if not background_checker.is_running():
        background_checker.start()
        logger.info(f"Background checker started (interval: {CHECK_INTERVAL_MINUTES} minutes)")


# Register commands
setup_commands(bot, bot_start_time, background_checker)

# Export for main.py
__all__ = ["bot", "TOKEN", "logger"]
