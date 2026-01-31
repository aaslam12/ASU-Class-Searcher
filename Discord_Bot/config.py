"""Bot configuration constants."""

# How often to check for class availability (minutes)
CHECK_INTERVAL_MINUTES = 5

# Delay between checks to avoid rate limiting (seconds)
CHECK_DELAY_SECONDS = 0.5

# Maximum tracking requests per user
MAX_REQUESTS_PER_USER = 10

# Data persistence
PERSISTENCE_FILE = "class_requests.json"

# ASU API endpoints
ASU_API_URL = "https://eadvs-cscc-catalog-api.apps.asu.edu/catalog-microservices/api/v1/search/classes"
ASU_SEARCH_URL = "https://catalog.apps.asu.edu/catalog/classes/classlist"
