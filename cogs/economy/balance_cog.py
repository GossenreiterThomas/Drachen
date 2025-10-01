import discord
from discord import app_commands
from discord.ext import commands
from .database import EconomyDB

db = EconomyDB()

class BalanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your wallet and bank balance (private).")
    async def balance(self, interaction: discord.Interaction):
        wallet, bank, _, _ = db.get_user(interaction.user.id)
        embed = discord.Embed(title=f"{interaction.user.name}'s Balance", color=discord.Color.gold())
        embed.add_field(name="💰 Wallet", value=f"{wallet} coins")
        embed.add_field(name="🏦 Bank", value=f"{bank} coins")
        embed.add_field(name="📊 Total", value=f"{wallet + bank} coins")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BalanceCog(bot))
