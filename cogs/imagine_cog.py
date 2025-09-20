from discord import app_commands, Interaction
from discord.ext import commands
import discord
import random

DRAGON_GIFS = [
    "https://media.tenor.com/fCu2RwI0fFYAAAAi/dragon.gif",
]
class ImagineCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash command inside the cog
    @app_commands.command(name="imagine", description="stell dir einfach vor")
    async def hello(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"{interaction.user.name}, du bist dabei extreme Aufstellungskraft aufzubringen...!",
            color=discord.Color.green()
        )
        embed.set_image(url=random.choice(DRAGON_GIFS))
        await interaction.response.send_message(embed=embed)

# Cog setup function
async def setup(bot: commands.Bot):
    await bot.add_cog(ImagineCog(bot))