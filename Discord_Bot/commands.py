"""Discord slash commands for ASU Class Searcher Bot."""

from datetime import datetime

import discord
import persistence
from asu_api import (
    check_class_via_api,
    get_class_details,
    scrape_course_availability,
    search_classes_by_subject,
)
from config import CHECK_INTERVAL_MINUTES, MAX_REQUESTS_PER_USER
from discord import app_commands


async def send_error(interaction: discord.Interaction, message: str):
    """Send error message, handling both deferred and non-deferred states."""
    try:
        await interaction.followup.send(message, ephemeral=True)
    except discord.errors.InteractionResponded:
        await interaction.followup.send(message, ephemeral=True)


def setup_commands(bot, bot_start_time_ref, background_checker):
    """Register all slash commands with the bot."""

    @bot.tree.command(
        name="helpbot", description="Display help information about bot commands"
    )
    async def help_bot(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎓 ASU Class Searcher Bot - Help",
            description="Track ASU class availability and get notified when spots open up!",
            color=0x8C1D40,
        )

        commands_info = [
            (
                "/checkclass <num> <subject> [term]",
                "Track a class by number and subject\n"
                "  `/checkclass 205 CSE` (defaults to term 2261)\n"
                "  `/checkclass 205 CSE 2267` (specific term)",
            ),
            (
                "/checkcourse <course_id> [term]",
                "Track a course by its ID number\n" "  `/checkcourse 12345`",
            ),
            (
                "/searchclass <subject> [course_num] [term]",
                "Search for classes\n"
                "  `/searchclass CSE` (list all CSE courses)\n"
                "  `/searchclass CSE 205` (show CSE 205 sections)",
            ),
            ("/myrequests", "Show all your active tracking requests"),
            (
                "/removerequest <index>",
                "Remove a specific request by index\n"
                "Use `/myrequests` to see indices",
            ),
            ("/stopchecking", "Remove ALL your tracking requests"),
            ("/listall", "Show all active tracking requests from all users"),
            ("/status", "Show bot status and statistics"),
        ]

        for name, value in commands_info:
            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text="Bot checks for availability every 5 minutes")
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="checkclass", description="Track a class by number and subject"
    )
    @app_commands.describe(
        class_num="Class catalog number (e.g., 205)",
        class_subject="Class subject code (e.g., CSE, MAT, ENG)",
        term="Academic term (default: 2261)",
    )
    async def check_class(
        interaction: discord.Interaction,
        class_num: str,
        class_subject: str,
        term: str = "2261",
    ):
        await interaction.response.defer(thinking=True)

        user_id = interaction.user.id
        username = str(interaction.user)
        channel_id = interaction.channel.id

        # validation
        if not class_num or not class_num.replace(".", "", 1).isdigit():
            await send_error(
                interaction, "❌ Class number must be numeric (e.g., 205 or 112.5)"
            )
            return

        if not class_subject or len(class_subject) > 6:
            await send_error(
                interaction, "❌ Subject must be a valid code (e.g., CSE, MAT, ENG)"
            )
            return

        if not term or len(term) != 4 or not term.isdigit():
            await send_error(
                interaction, "❌ Term must be 4 digits (e.g., 2261 for Spring 2026)"
            )
            return

        # check duplicate
        if persistence.is_duplicate_request(
            user_id=user_id,
            request_type="class",
            class_num=class_num,
            class_subject=class_subject.upper(),
            term=term,
        ):
            await interaction.followup.send(
                f"⚠️ You're already tracking **{class_subject.upper()} {class_num}** (Term: {term})\n"
                f"Use `/myrequests` to see all your tracked classes."
            )
            return

        # check limit
        if persistence.count_user_requests(user_id) >= MAX_REQUESTS_PER_USER:
            await interaction.followup.send(
                f"❌ You've reached the limit of {MAX_REQUESTS_PER_USER} tracking requests. "
                f"Remove some with `/removerequest` or `/stopchecking`."
            )
            return

        # get details and check availability
        class_details = get_class_details(class_num, class_subject.upper(), term)
        class_title = class_details.get("title", "Unknown")

        df = check_class_via_api(class_num, class_subject.upper(), term)
        is_open = False
        seats_available = 0
        if not df.empty and "Open Seats" in df.columns:
            try:
                seats_available = int(df["Open Seats"].iloc[0])
                is_open = seats_available > 0
            except (ValueError, TypeError):
                pass

        # add request
        request_id = persistence.add_request(
            request_type="class",
            user_id=user_id,
            username=username,
            channel_id=channel_id,
            class_num=class_num,
            class_subject=class_subject.upper(),
            term=term,
            class_title=class_title,
            class_details=class_details,
        )

        if not request_id:
            await interaction.followup.send(
                "❌ Failed to add tracking request. Please try again."
            )
            return

        # response
        details_str = ""
        if class_details:
            details_str = f"\n📚 **{class_title}**"
            if class_details.get("instructor", "TBA") != "TBA":
                details_str += f"\n👨‍🏫 {class_details['instructor']}"
            if class_details.get("days", "TBA") != "TBA":
                details_str += (
                    f"\n🗓️ {class_details['days']} {class_details.get('time', '')}"
                )
            if class_details.get("location", "TBA") != "TBA":
                details_str += f"\n📍 {class_details['location']}"

        if is_open:
            await interaction.followup.send(
                f"🎉 **GOOD NEWS!** {class_subject.upper()} {class_num} is **ALREADY OPEN!**{details_str}\n"
                f"🪑 **{seats_available} seat(s) available** - Enroll now!\n"
                f"_I'll keep tracking and notify you if it closes and reopens._"
            )
        else:
            await interaction.followup.send(
                f"✅ Now tracking **{class_subject.upper()} {class_num}** (Term: {term}){details_str}\n"
                f"📭 Currently full - You'll be notified here when spots open.\n"
                f"_Checking every {CHECK_INTERVAL_MINUTES} minutes_"
            )

    @bot.tree.command(
        name="checkcourse", description="Track a course by ID for availability"
    )
    @app_commands.describe(
        course_id="Course ID number (e.g., 12345)", term="Academic term (default: 2261)"
    )
    async def check_course(
        interaction: discord.Interaction, course_id: str, term: str = "2261"
    ):
        await interaction.response.defer(thinking=True)

        user_id = interaction.user.id
        username = str(interaction.user)
        channel_id = interaction.channel.id

        # validation
        if not course_id or not course_id.isdigit():
            await send_error(interaction, "❌ Course ID must be numeric (e.g., 12345)")
            return

        if not term or len(term) != 4 or not term.isdigit():
            await send_error(
                interaction, "❌ Term must be 4 digits (e.g., 2261 for Spring 2026)"
            )
            return

        # check duplicate
        if persistence.is_duplicate_request(
            user_id=user_id,
            request_type="course",
            course_id=course_id,
            term=term,
        ):
            await interaction.followup.send(
                f"⚠️ You're already tracking **Course ID: {course_id}** (Term: {term})\n"
                f"Use `/myrequests` to see all your tracked courses."
            )
            return

        # check limit
        if persistence.count_user_requests(user_id) >= MAX_REQUESTS_PER_USER:
            await interaction.followup.send(
                f"❌ You've reached the limit of {MAX_REQUESTS_PER_USER} tracking requests. "
                f"Remove some with `/removerequest` or `/stopchecking`."
            )
            return

        # get info and check availability
        course_title = "Course"
        is_open = False
        seats_available = 0
        try:
            enrolled, capacity, course_title = scrape_course_availability(
                course_id, term
            )
            if enrolled is not None and capacity is not None:
                seats_available = capacity - enrolled
                is_open = seats_available > 0
        except:
            course_title = f"Course {course_id}"

        # add request
        request_id = persistence.add_request(
            request_type="course",
            user_id=user_id,
            username=username,
            channel_id=channel_id,
            course_id=course_id,
            term=term,
            class_title=course_title,
        )

        if not request_id:
            await interaction.followup.send(
                "❌ Failed to add tracking request. Please try again."
            )
            return

        if is_open:
            await interaction.followup.send(
                f"🎉 **GOOD NEWS!** Course {course_id} is **ALREADY OPEN!**\n"
                f"📚 **{course_title}**\n"
                f"🪑 **{seats_available} seat(s) available** - Enroll now!\n"
                f"_I'll keep tracking and notify you if it closes and reopens._"
            )
        else:
            await interaction.followup.send(
                f"✅ Now tracking **Course ID: {course_id}** (Term: {term})\n"
                f"📚 **{course_title}**\n"
                f"📭 Currently full - You'll be notified here when spots open.\n"
                f"_Checking every {CHECK_INTERVAL_MINUTES} minutes_"
            )

    @bot.tree.command(
        name="myrequests", description="Show all tracking requests for the current user"
    )
    async def my_requests(interaction: discord.Interaction):
        user_id = interaction.user.id
        requests = persistence.get_user_requests(user_id)

        if not requests:
            await interaction.response.send_message(
                "📭 You have no active tracking requests.\n"
                "Use `/checkclass` or `/checkcourse` to add some!"
            )
            return

        embed = discord.Embed(
            title=f"📋 Your Tracking Requests ({len(requests)})", color=0x8C1D40
        )

        for idx, req in enumerate(requests):
            if req["type"] == "class":
                name = f"{idx}. {req['class_subject']} {req['class_num']}"
                value = f"**{req.get('class_title', 'Unknown')}**\nTerm: {req['term']}"
            else:
                course_id = req["course_id"]
                name = f"{idx}. Course ID: {course_id}"
                value = f"**{req.get('course_title', f'Course {course_id}')}**\nTerm: {req['term']}"

            # add details if available
            if req.get("instructor") and req["instructor"] != "TBA":
                value += f"\n👨‍🏫 {req['instructor']}"
            if req.get("days") and req["days"] != "TBA":
                value += f"\n🗓️ {req['days']} {req.get('time', '')}"
            if req.get("location") and req["location"] != "TBA":
                value += f"\n📍 {req['location']}"

            if req.get("last_notified"):
                value += f"\n✅ Last notified: {req['last_notified'][:16]}"
            elif req.get("last_checked"):
                value += f"\n🔍 Last checked: {req['last_checked'][:16]}"

            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text="Use /removerequest <index> to remove a request")
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="removerequest", description="Remove a specific tracking request by index"
    )
    @app_commands.describe(index="The index of the request (from /myrequests)")
    async def remove_request(interaction: discord.Interaction, index: int):
        user_id = interaction.user.id
        requests = persistence.get_user_requests(user_id)

        if not requests:
            await interaction.response.send_message(
                "📭 You have no active tracking requests."
            )
            return

        if index < 0 or index >= len(requests):
            await interaction.response.send_message(
                f"❌ Invalid index. Use `/myrequests` to see valid indices (0-{len(requests)-1})."
            )
            return

        request = requests[index]
        if persistence.remove_request(request["id"]):
            if request["type"] == "class":
                desc = f"{request['class_subject']} {request['class_num']}"
            else:
                desc = f"Course {request['course_id']}"
            await interaction.response.send_message(
                f"✅ Removed tracking request for **{desc}**"
            )
        else:
            await interaction.response.send_message(
                "❌ Failed to remove request. Please try again."
            )

    @bot.tree.command(
        name="stopchecking",
        description="Remove ALL tracking requests for the current user",
    )
    async def stop_checking(interaction: discord.Interaction):
        user_id = interaction.user.id
        count = persistence.remove_user_requests(user_id)

        if count > 0:
            await interaction.response.send_message(
                f"✅ Removed all **{count}** tracking request(s)."
            )
        else:
            await interaction.response.send_message(
                "📭 You have no active tracking requests."
            )

    @bot.tree.command(
        name="listall", description="Show all active tracking requests from all users"
    )
    async def list_all(interaction: discord.Interaction):
        requests = persistence.load_requests()

        if not requests:
            await interaction.response.send_message("📭 No active tracking requests.")
            return

        embed = discord.Embed(
            title=f"📊 All Active Tracking Requests ({len(requests)})",
            description=f"Checking every {CHECK_INTERVAL_MINUTES} minutes",
            color=0xFFC627,
        )

        # group by user
        user_requests = {}
        for req in requests:
            username = req["username"]
            if username not in user_requests:
                user_requests[username] = []
            user_requests[username].append(req)

        for username, user_reqs in user_requests.items():
            value = ""
            for req in user_reqs[:5]:
                if req["type"] == "class":
                    title = req.get("class_title", "Unknown")
                    if len(title) > 35:
                        title = title[:32] + "..."
                    instructor = req.get("instructor", "TBA")
                    days = req.get("days", "")
                    value += (
                        f"• **{req['class_subject']} {req['class_num']}** - {title}\n"
                    )
                    if instructor != "TBA" or days:
                        value += f"  └ {instructor} | {days}\n"
                else:
                    title = req.get("course_title", f"Course {req['course_id']}")
                    if len(title) > 35:
                        title = title[:32] + "..."
                    value += f"• **Course {req['course_id']}** - {title}\n"

            if len(user_reqs) > 5:
                value += f"_...and {len(user_reqs) - 5} more_\n"

            embed.add_field(
                name=f"{username} ({len(user_reqs)})", value=value, inline=False
            )

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="status", description="Show bot status and statistics")
    async def status(interaction: discord.Interaction):
        requests = persistence.load_requests()

        if bot_start_time_ref[0]:
            uptime = datetime.utcnow() - bot_start_time_ref[0]
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

        unique_users = len(set(r["user_id"] for r in requests))
        embed.add_field(name="Users Tracking", value=str(unique_users), inline=True)
        embed.add_field(
            name="Servers", value=str(len(interaction.client.guilds)), inline=True
        )
        embed.add_field(
            name="Background Task",
            value="✅ Running" if background_checker.is_running() else "❌ Stopped",
            inline=True,
        )

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="searchclass",
        description="Search for classes by subject code and optionally course number",
    )
    @app_commands.describe(
        subject="Subject code (e.g., CSE, MAT, ENG)",
        course_num="Course number (e.g., 205) - leave empty to list all courses",
        term="Academic term (default: 2261)",
    )
    async def search_class(
        interaction: discord.Interaction,
        subject: str,
        course_num: str = None,
        term: str = "2261",
    ):
        await interaction.response.defer(thinking=True)

        # validation
        if not subject or len(subject) > 6:
            await send_error(
                interaction, "❌ Subject must be a valid code (e.g., CSE, MAT, ENG)"
            )
            return

        if not term or len(term) != 4 or not term.isdigit():
            await send_error(
                interaction, "❌ Term must be 4 digits (e.g., 2261 for Spring 2026)"
            )
            return

        if course_num:
            # search specific course
            results = search_classes_by_subject(subject.upper(), term, course_num)

            if not results:
                await interaction.followup.send(
                    f"📭 No sections found for **{subject.upper()} {course_num}** in term {term}"
                )
                return

            embed = discord.Embed(
                title=f"🔍 {subject.upper()} {course_num} Sections (Term: {term})",
                description=f"Found {len(results)} section(s)",
                color=0x8C1D40,
            )

            for info in results[:20]:
                available = info["available"]
                capacity = info["capacity"]
                enrolled = info["enrolled"]

                if available > 0:
                    status = f"✅ {available} seats ({enrolled}/{capacity})"
                else:
                    status = f"❌ Full ({enrolled}/{capacity})"

                value = (
                    f"👨‍🏫 {info['instructor']}\n"
                    f"📍 {info['location']} | 🕐 {info['days']} {info['time']}\n"
                    f"{status}"
                )
                embed.add_field(
                    name=f"Class #{info['class_nbr']}", value=value, inline=True
                )

            if len(results) > 20:
                embed.set_footer(
                    text=f"Showing 20 of {len(results)} sections | Use /checkclass to track"
                )
            else:
                embed.set_footer(
                    text=f"Use /checkclass {subject.upper()} {course_num} to track a section"
                )

        else:
            # list all courses in subject
            results = search_classes_by_subject(subject.upper(), term)

            if not results:
                await interaction.followup.send(
                    f"📭 No classes found for **{subject.upper()}** in term {term}"
                )
                return

            # group by course number
            courses = {}
            for r in results:
                cat_num = r["catalog_num"]
                if cat_num not in courses:
                    courses[cat_num] = {
                        "title": r["title"],
                        "sections": 0,
                        "total_seats": 0,
                        "available_seats": 0,
                    }
                courses[cat_num]["sections"] += 1
                courses[cat_num]["total_seats"] += r["capacity"]
                courses[cat_num]["available_seats"] += max(0, r["available"])

            sorted_courses = sorted(courses.items(), key=lambda x: x[0])

            embed = discord.Embed(
                title=f"🔍 {subject.upper()} Courses (Term: {term})",
                description=f"Found {len(courses)} unique course(s)\nUse `/searchclass {subject.upper()} <number>` to see sections",
                color=0x8C1D40,
            )

            for cat_num, info in sorted_courses[:25]:
                title = info["title"]
                if len(title) > 40:
                    title = title[:37] + "..."

                avail = info["available_seats"]
                total = info["total_seats"]
                sections = info["sections"]

                status = f"✅ {avail}/{total} seats" if avail > 0 else "❌ Full"
                embed.add_field(
                    name=f"{subject.upper()} {cat_num}",
                    value=f"{title}\n{sections} section(s) | {status}",
                    inline=True,
                )

            if len(courses) > 25:
                embed.set_footer(text=f"Showing 25 of {len(courses)} courses")
            else:
                embed.set_footer(
                    text=f"Use /searchclass {subject.upper()} <number> to see sections"
                )

        await interaction.followup.send(embed=embed)

    @bot.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ You don't have permission to use this command."
        elif isinstance(error, app_commands.CommandOnCooldown):
            message = f"⏳ Command on cooldown. Try again in {error.retry_after:.1f}s"
        else:
            message = f"❌ An error occurred: {str(error)}"

        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except:
            pass
