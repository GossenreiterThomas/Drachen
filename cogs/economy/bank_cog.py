# cogs/economy/bank_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from .database import EconomyDB
from .utils import format_currency

class BankCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = EconomyDB()

    @app_commands.command(name="deposit", description="Deposit coins into your bank")
    @app_commands.describe(amount="Amount of coins to deposit")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        wallet, bank, _, _ = self.db.get_user(interaction.user.id)

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        if wallet < amount:
            await interaction.response.send_message("❌ You don’t have that much in your wallet.", ephemeral=True)
            return

        self.db.update_balance(interaction.user.id, wallet=wallet - amount, bank=bank + amount)
        await interaction.response.send_message(
            f"🏦 Deposited **{format_currency(amount)} coins** into your bank!",
            ephemeral=True
        )

    @app_commands.command(name="withdraw", description="Withdraw coins from your bank")
    @app_commands.describe(amount="Amount of coins to withdraw")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        wallet, bank, _, _ = self.db.get_user(interaction.user.id)

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        if bank < amount:
            await interaction.response.send_message("❌ You don’t have that much in the bank.", ephemeral=True)
            return

        self.db.update_balance(interaction.user.id, wallet=wallet + amount, bank=bank - amount)
        await interaction.response.send_message(
            f"💸 Withdrew **{format_currency(amount)} coins** into your wallet!",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(BankCog(bot))
