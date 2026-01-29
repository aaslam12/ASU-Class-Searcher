#!/usr/bin/env python3

import sys
import logging
from startup_menu import run_startup_menu

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Main")


def main():
    try:
        should_start = run_startup_menu()

        if not should_start:
            logger.info("Bot startup cancelled by user")
            sys.exit(0)

        logger.info("Importing Discord bot...")
        from Discord import bot, TOKEN, logger as bot_logger

        bot_logger.info("Starting ASU Class Searcher Bot...")
        bot.run(TOKEN)

    except KeyboardInterrupt:
        logger.info("\nBot stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
