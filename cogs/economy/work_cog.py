import asyncio
import random
import time
import discord
from discord import app_commands
from discord.ext import commands
from .database import EconomyDB
from .utils import WORK_PHRASES, WORK_REWARDS, get_random_reward

COOLDOWN_SECONDS = 300  # 5 minutes

class WorkCog(commands.Cog):
    """Handles the /work command with mini-games and cooldowns."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = EconomyDB()
        # Mini-games mapped to functions
        self.minigames = {
            "typing": self.typing_game,
            "math": self.math_game
        }

    @app_commands.command(name="work", description="Play a mini-game to earn coins (5 min cooldown).")
    async def work(self, interaction: discord.Interaction):
        wallet, bank, last_work, _ = self.db.get_user(interaction.user.id)

        # Check cooldown
        now = time.time()
        if now - last_work < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_work))
            await interaction.response.send_message(f"⏳ You must wait {remaining}s before working again.", ephemeral=True)
            return

        # Pick a mini-game
        game_func = random.choice(list(self.minigames.values()))
        reward = await game_func(interaction)

        if reward > 0:
            self.db.update_balance(interaction.user.id, wallet=wallet + reward, last_work=now)

    # --- Mini-games ---
    async def typing_game(self, interaction: discord.Interaction):
        phrase = random.choice(WORK_PHRASES)
        await interaction.response.send_message(
            f"⌨️ **Typing Challenge!**\nType this exactly within 20s:\n`{phrase}`"
        )

        def check(msg):
            return msg.author.id == interaction.user.id and msg.content.lower() == phrase.lower()

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=20.0)
            reward = get_random_reward(*WORK_REWARDS["typing"])
            await msg.reply(f"✅ Perfect! You earned **{reward} coins**.")
            return reward
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Too slow! No coins earned.")
            return 0

    async def math_game(self, interaction: discord.Interaction):
        a, b = random.randint(5, 20), random.randint(5, 20)
        correct = a + b
        await interaction.response.send_message(
            f"🧮 **Math Challenge!**\nWhat is {a} + {b}? You have 15s."
        )

        def check(msg):
            return msg.author.id == interaction.user.id and msg.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=15.0)
            if int(msg.content) == correct:
                reward = get_random_reward(*WORK_REWARDS["math"])
                await msg.reply(f"✅ Correct! You earned **{reward} coins**.")
                return reward
            else:
                await msg.reply(f"❌ Wrong! The answer was {correct}. No coins earned.")
                return 0
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Time's up! No coins earned.")
            return 0

async def setup(bot: commands.Bot):
    await bot.add_cog(WorkCog(bot))