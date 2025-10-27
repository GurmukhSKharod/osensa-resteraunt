"""
Centralized defaults / constants for the backend service.
"""

# MQTT topic prefixes
ORDER_TOPIC_PREFIX = "restaurant/orders/"
FOOD_TOPIC_PREFIX  = "restaurant/foods/"

# Default prep time range (milliseconds)
MIN_PREP_MS = 800
MAX_PREP_MS = 4000