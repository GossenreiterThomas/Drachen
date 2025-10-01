# cogs/say_cog.py
import discord
from discord.ext import commands
import asyncio
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

        channel = interaction.user.voice.channel
        try:
            vc = await channel.connect()
        except discord.ClientException:
            vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        text = await replace_speech_placeholders(text, channel)
        audio_path = await generate_speech(text)
        play_audio(vc, audio_path)

        # Send confirmation
        await interaction.response.send_message(f"🗣️ Generated speech for: *{text}*", ephemeral=True)

        while vc.is_playing():
            await asyncio.sleep(0.5)

        await leave_voice(vc)


async def setup(bot: commands.Bot):
    await bot.add_cog(SayCog(bot))
