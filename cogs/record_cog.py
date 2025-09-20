# cogs/record_cog.py
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, voice_recv
from main import leave_voice
import logging

logging.getLogger("discord.ext.voice_recv.opus").setLevel(logging.CRITICAL)
logger = logging.getLogger("discord.ext.voice_recv.opus")
logger.addHandler(logging.NullHandler())

class RecordCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="record_sink", description="Record audio using WaveSink")
    async def record_sink(self, interaction: discord.Interaction):
        # Ensure user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("⚠️ Join a VC first", ephemeral=True)
            return

        channel = interaction.user.voice.channel

        # Connect using VoiceRecvClient
        vc = await channel.connect(cls=voice_recv.VoiceRecvClient)

        # Import sinks locally
        from discord.ext.voice_recv import sinks
        sink = sinks.WaveSink("recordings/test.wav")
        vc.listen(sink)

        await interaction.response.send_message(f"🎙️ Recording in {channel.name} for 15 seconds...")

        # Wait for recording
        await asyncio.sleep(15)

        # Stop and disconnect
        vc.stop_listening()
        await leave_voice(vc)

        await interaction.followup.send("✅ Finished recording and saved files")


async def setup(bot: commands.Bot):
    await bot.add_cog(RecordCog(bot))
