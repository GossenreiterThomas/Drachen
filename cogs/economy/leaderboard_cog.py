# cogs/economy/leaderboard_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from .database import EconomyDB
from .utils import format_currency

class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = EconomyDB()

    @app_commands.command(name="leaderboard", description="Show the richest users in the server")
    @app_commands.describe(limit="Number of top users to show (default 10)")
    async def leaderboard(self, interaction: discord.Interaction, limit: int = 10):
        # Fetch all users and their total balance
        self.db.c.execute("SELECT user_id, wallet + bank as total FROM economy ORDER BY total DESC LIMIT ?", (limit,))
        rows = self.db.c.fetchall()

        if not rows:
            await interaction.response.send_message("No users found on the leaderboard.", ephemeral=True)
            return

        embed = discord.Embed(title="💰 Economy Leaderboard", color=discord.Color.gold())
        for idx, (user_id, total) in enumerate(rows, start=1):
            user = self.bot.get_user(user_id)
            name = user.display_name if user else f"<User {user_id}>"
            embed.add_field(name=f"{idx}. {name}", value=f"Total: {format_currency(total)} coins", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
