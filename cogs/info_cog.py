from discord import app_commands, Interaction
from discord.ext import commands
import discord

class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash command inside the cog
    @app_commands.command(name="help", description="Show some info")
    async def help_command(self, interaction: Interaction):
        embed = discord.Embed(
            title="STELL DIR DRACHEN VOR!!",
            description="Alle Befehle, die es so gibt und bissl Info.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="imagine", value="Bissl Vorstellungskraft", inline=True)
        embed.add_field(name="shoot", value="Irgendwer in deinem channel wird in einen gun 'incident' verwickelt.", inline=True)
        embed.add_field(name="music", value="Spiel zufällige ultra umschwärmte Stell Dir drachen Vor Hits.", inline=True)
        embed.add_field(name="say", value="Thorsten sagt genau das, was du willst.", inline=True)
        embed.set_footer(text="Requested by " + interaction.user.name)

        await interaction.response.send_message(embed=embed)

# Cog setup function
async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))