from discord import app_commands, Interaction
from discord.ext import commands
import discord
import asyncio

from kba.kba import ask as ask_kba
from main import replace_speech_placeholders, generate_speech, play_audio, leave_voice

class KbaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="askkba", description="Convert text to speech")
    async def askkba(self, interaction: discord.Interaction, text: str):
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
            
        resp = ask_kba(text)

        resp = await replace_speech_placeholders(resp, channel)
        audio_path = await generate_speech(resp)
        play_audio(vc, audio_path)

        # Send confirmation
        await interaction.response.send_message(f"🗣️ Asked Thorsten something", ephemeral=True)

        while vc.is_playing():
            await asyncio.sleep(0.5)

        await leave_voice(vc)


async def setup(bot: commands.Bot):
    await bot.add_cog(KbaCog(bot))
