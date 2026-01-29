import persistence
from config import CHECK_INTERVAL_MINUTES


def display_menu():
    """Display the main menu options."""
    print("\n" + "=" * 60)
    print("    ASU Class Searcher Bot - Startup Menu")
    print("=" * 60)
    print("\n1. View all tracked classes")
    print("2. Clear all tracking requests")
    print("3. Start the bot")
    print("0. Exit")
    print("\n" + "=" * 60)


def display_tracked_classes():
    requests = persistence.load_requests()

    if not requests:
        print("\nNo tracking requests found.")
        return

    print(f"\n📋 Active Tracking Requests ({len(requests)}):")
    print("-" * 80)
    print(f"{'#':<4} {'Type':<8} {'Details':<30} {'User':<20} {'Term':<6}")
    print("-" * 80)

    for idx, req in enumerate(requests):
        req_type = req["type"].capitalize()

        if req["type"] == "class":
            details = f"{req['class_subject']} {req['class_num']}"
        else:
            details = f"Course ID: {req['course_id']}"

        username = (
            req["username"][:18] + ".."
            if len(req["username"]) > 20
            else req["username"]
        )
        term = req["term"]

        print(f"{idx:<4} {req_type:<8} {details:<30} {username:<20} {term:<6}")

    print("-" * 80)
    print(f"\n✓ Bot will check these every {CHECK_INTERVAL_MINUTES} minutes")
    print("\n💡 Tip: Use Discord commands to add/remove tracking requests:")
    print("   • !checkClass <number> <subject> [term]")
    print("   • !checkCourse <courseID> [term]")
    print("   • !removeRequest <index>")
    print("   • !stopChecking")


def clear_all_requests():
    requests = persistence.load_requests()

    if not requests:
        print("\n📭 No tracking requests to clear.")
        return

    print(f"\n⚠️  WARNING: This will remove ALL {len(requests)} tracking requests!")
    confirm = input("Type 'yes' to confirm: ").strip().lower()

    if confirm == "yes":
        persistence.save_requests([])
        print(f"✅ Cleared all {len(requests)} tracking requests")
    else:
        print("Cancelled.")


def run_startup_menu():
    print("\n🎓 Welcome to ASU Class Searcher Bot!")

    while True:
        display_menu()
        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            display_tracked_classes()
        elif choice == "2":
            clear_all_requests()
        elif choice == "3":
            print("\n🚀 Starting bot...")
            return True
        elif choice == "0":
            print("\n👋 Exiting without starting bot.")
            return False
        else:
            print("\n❌ Invalid option. Please try again.")


if __name__ == "__main__":
    run_startup_menu()
