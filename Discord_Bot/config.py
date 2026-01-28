# Fixed interval (in minutes) for checking class availability
# Modify this constant to change how often the bot checks for open classes
CHECK_INTERVAL_MINUTES = 5

# Command prefix for bot commands
COMMAND_PREFIX = "!"

# Path to the JSON file that stores class tracking requests
PERSISTENCE_FILE = "class_requests.json"

# ASU Class Catalog API endpoint
ASU_API_URL = "https://eadvs-cscc-catalog-api.apps.asu.edu/catalog-microservices/api/v1/search/classes"

# ASU Class Search website URL template
ASU_SEARCH_URL = "https://catalog.apps.asu.edu/catalog/classes/classlist"

# Maximum number of requests per user (to prevent abuse)
MAX_REQUESTS_PER_USER = 10

# Delay between individual class checks to avoid rate limiting
CHECK_DELAY_SECONDS = 0.5
