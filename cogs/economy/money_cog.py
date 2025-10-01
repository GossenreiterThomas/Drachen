""""
import random
import asyncio
import time
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

COOLDOWN_SECONDS = 300  # 5 min cooldown
DAILY_COOLDOWN = 86400  # 24h in seconds

class MoneyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("economy.db")
        self.c = self.conn.cursor()

        self.conn.commit()

    def _get_user(self, user_id):
        self.c.execute("SELECT wallet, bank, last_work, last_daily FROM economy WHERE user_id = ?", (user_id,))
        row = self.c.fetchone()
        if not row:
            self.c.execute("INSERT INTO economy (user_id, wallet, bank, last_work, last_daily) VALUES (?, 0, 0, 0, 0)", (user_id,))
            self.conn.commit()
            return (0, 0, 0, 0)
        return row

    def _update_balance(self, user_id, wallet=None, bank=None, last_work=None, last_daily=None):
        fields, params = [], []
        if wallet is not None:
            fields.append("wallet = ?")
            params.append(wallet)
        if bank is not None:
            fields.append("bank = ?")
            params.append(bank)
        if last_work is not None:
            fields.append("last_work = ?")
            params.append(last_work)
        if last_daily is not None:
            fields.append("last_daily = ?")
            params.append(last_daily)

        params.append(user_id)
        set_clause = ", ".join(fields)
        self.c.execute(f"UPDATE economy SET {set_clause} WHERE user_id = ?", tuple(params))
        self.conn.commit()

    # BALANCE
    @app_commands.command(name="balance", description="Check your wallet and bank balance (private).")
    async def balance(self, interaction: discord.Interaction):
        wallet, bank, _, _ = self._get_user(interaction.user.id)
        embed = discord.Embed(title=f"{interaction.user.name}'s Balance", color=discord.Color.gold())
        embed.add_field(name="💰 Wallet", value=f"{wallet} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{bank} coins", inline=True)
        total = wallet + bank
        embed.add_field(name="📊 Total", value=f"{total} coins", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # WORK
    @app_commands.command(name="work", description="Play a mini-game to earn coins (cooldown 5 minutes).")
    async def work(self, interaction: discord.Interaction):
        wallet, bank, last_work, _ = self._get_user(interaction.user.id)

        now = time.time()
        if now - last_work < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_work))
            await interaction.response.send_message(f"⏳ You must wait {remaining} seconds before working again.", ephemeral=True)
            return

        game = random.choice(["typing", "math"])
        reward = 0

        if game == "typing":
            phrase = random.choice([
                "discord is awesome",
                "money makes the bot go brr",
                "blackjack or bust",
                "vosk speech rocks",
                "gamba responsibly"
            ])
            await interaction.response.send_message(
                f"⌨️ **Typing Challenge!**\nType this exactly within **20 seconds**:\n\n`{phrase}`"
            )

            def check(m):
                return m.author.id == interaction.user.id and m.content.lower() == phrase.lower()

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=20.0)
                reward = random.randint(150, 300)
                await msg.reply(f"✅ Perfect! You earned **{reward} coins**.")
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Too slow! No money for you.", ephemeral=True)
                return

        elif game == "math":
            a, b = random.randint(5, 20), random.randint(5, 20)
            correct = a + b
            await interaction.response.send_message(
                f"🧮 **Math Challenge!**\nWhat is **{a} + {b}**? You have **15 seconds**."
            )

            def check(m):
                return m.author.id == interaction.user.id and m.content.isdigit()

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=15.0)
                if int(msg.content) == correct:
                    reward = random.randint(200, 400)
                    await msg.reply(f"✅ Correct! You earned **{reward} coins**.")
                else:
                    await msg.reply(f"❌ Wrong! The answer was **{correct}**. No coins for you.", delete_after=10)
                    return
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Time's up! No coins for you.", ephemeral=True)
                return

        if reward > 0:
            self._update_balance(interaction.user.id, wallet=wallet + reward, last_work=now)

    # DAILY
    @app_commands.command(name="daily", description="Claim your daily coins (once every 24h).")
    async def daily(self, interaction: discord.Interaction):
        wallet, _, _, last_daily = self._get_user(interaction.user.id)
        now = time.time()

        if now - last_daily < DAILY_COOLDOWN:
            remaining = int((DAILY_COOLDOWN - (now - last_daily)) // 3600)
            await interaction.response.send_message(f"⏳ You already claimed your daily. Come back in **{remaining}h**.", ephemeral=True)
            return

        reward = random.randint(500, 1000)
        self._update_balance(interaction.user.id, wallet=wallet + reward, last_daily=now)
        await interaction.response.send_message(f"🎉 You claimed your daily **{reward} coins**!")

    # DEPOSIT
    @app_commands.command(name="deposit", description="Deposit coins into the bank")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        wallet, bank, _, _ = self._get_user(interaction.user.id)
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        if wallet < amount:
            await interaction.response.send_message("❌ You don’t have that much in your wallet.", ephemeral=True)
            return

        self._update_balance(interaction.user.id, wallet=wallet - amount, bank=bank + amount)
        await interaction.response.send_message(f"🏦 Deposited **{amount} coins** into your bank!")

    # WITHDRAW
    @app_commands.command(name="withdraw", description="Withdraw coins from the bank")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        wallet, bank, _, _ = self._get_user(interaction.user.id)
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return
        if bank < amount:
            await interaction.response.send_message("❌ You don’t have that much in the bank.", ephemeral=True)
            return

        self._update_balance(interaction.user.id, wallet=wallet + amount, bank=bank - amount)
        await interaction.response.send_message(f"💸 Withdrew **{amount} coins** into your wallet!")

async def setup(bot: commands.Bot):
    await bot.add_cog(MoneyCog(bot))
"""