# cogs/say_cog.py
import discord
from discord.ext import commands
import asyncio

from brain import brain

from main import generate_speech, replace_speech_placeholders, play_audio, leave_voice  # import helpers

class SayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="say", description="Convert text to speech")
    async def say(self, interaction: discord.Interaction, text: str):
        if not text:
            await interaction.response.send_message("❌ You must provide text!", ephemeral=True)
            return

        if len(text) >= 2000:
            await interaction.response.send_message("⚠️ Text too long (max 2000 chars)!", ephemeral=True)
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("⚠️ You must be in a voice channel!", ephemeral=True)
            return

        brain.add_text_to_queue(text, interaction)

        # Send confirmation
        await interaction.response.send_message(f"🗣️ Generated speech for: *{text}*", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SayCog(bot))
