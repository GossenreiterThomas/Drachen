import time
import random

# Example phrases for the typing mini-game
WORK_PHRASES = [
    "discord is awesome",
    "money makes the bot go brr",
    "blackjack or bust",
    "vosk speech rocks",
    "gamba responsibly",
]

# Typing or math reward ranges
WORK_REWARDS = {
    "typing": (150, 300),
    "math": (200, 400)
}

DAILY_REWARD_RANGE = (300, 600)

# Cooldown helper
def is_on_cooldown(last_timestamp: float, cooldown: int) -> (bool, int):
    """
    Checks if a timestamp is on cooldown.
    Returns (on_cooldown, remaining_seconds)
    """
    now = time.time()
    elapsed = now - last_timestamp
    if elapsed >= cooldown:
        return False, 0
    return True, int(cooldown - elapsed)

# Random reward helper
def get_random_reward(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)

# Format large numbers with commas
def format_coins(amount: int) -> str:
    return f"{amount:,} coins"

# Convert seconds to h:m:s format
def format_seconds(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}h {minutes}m {secs}s"

# format currency into a clean string
def format_currency(amount: int) -> str:
    """Formats an integer with commas for readability."""
    return f"{amount:,}"