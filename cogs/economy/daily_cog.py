# cogs/economy/daily_cog.py
import time
import random
import discord
from discord import app_commands
from discord.ext import commands
from .database import EconomyDB
from .utils import format_currency

DAILY_COINS_RANGE = (500, 1000)  # min and max daily reward
DAILY_COOLDOWN = 24 * 60 * 60  # 24 hours in seconds

class DailyCog(commands.Cog):
    """Daily reward command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = EconomyDB()

    @app_commands.command(name="daily", description="Claim your daily coins (24h cooldown)")
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        wallet, bank, last_work, last_daily = self.db.get_user(user_id)

        now = time.time()
        if now - last_daily < DAILY_COOLDOWN:
            remaining = int(DAILY_COOLDOWN - (now - last_daily))
            hours, rem = divmod(remaining, 3600)
            minutes, seconds = divmod(rem, 60)
            await interaction.response.send_message(
                f"⏳ You already claimed your daily reward. "
                f"Come back in {hours}h {minutes}m {seconds}s.",
                ephemeral=True
            )
            return

        reward = random.randint(*DAILY_COINS_RANGE)
        self.db.update_balance(user_id, wallet=wallet + reward, last_daily=now)

        await interaction.response.send_message(
            f"🎉 You claimed your daily reward of **{format_currency(reward)} coins**! 💰",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(DailyCog(bot))
