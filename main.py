# main.py
import asyncio
import logging
import os
import random
import wave

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from piper import PiperVoice

# from ollama import AsyncClient


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TEST_GUILD_ID = 1229147943668289546

# better to use default intents unless you need more
intents = discord.Intents.all()

# enable debug logging to see what discord.py is doing
logging.basicConfig(level=logging.INFO)


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.voice_buffers = {}  # user_id -> list of PCM chunks

    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs")

        # Register commands into ONE test guild for instant availability (dev)
        guild = discord.Object(id=TEST_GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f"Logged in as {self.user} — connected to {len(self.guilds)} guild(s)")
        for g in self.guilds:
            print(f"- {g.id} {g.name}")


bot = MyBot()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "de_DE-thorsten-medium.onnx")
voice_model = PiperVoice.load(model_path)

"""
school server fix?
"""
from discord import VoiceClient

VoiceClient.supported_modes = ["udp"]
"""
UTILITY CLASSES
"""


async def generate_speech(text: str, filename: str = "tts_output.wav") -> str:
    """
    Generate TTS audio file from given text.
    Returns the path to the generated audio.
    """
    audio_path = os.path.join("tts", filename)

    with wave.open(audio_path, "wb") as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(22050)  # sample rate
        voice_model.synthesize_wav(text, wav_file)

    return audio_path


async def replace_speech_placeholders(
    text: str,
    channel: discord.VoiceChannel,
) -> str:
    if "{name}" in text:
        humans = [m for m in channel.members if not m.bot]
        if humans:
            text = text.replace("{name}", f"**{random.choice(humans).display_name}**")

    return text


def play_audio(vc, audio_path):
    if vc.is_connected():
        if vc.is_playing() or vc.is_paused():
            vc.stop()  # stop current playback immediately
        vc.play(discord.FFmpegPCMAudio(audio_path))
    else:
        print("Not connected to a voice channel.")


async def leave_voice(vc):
    if vc.is_playing() or vc.is_paused():
        vc.stop()
    global conversationCount
    conversationCount = 0
    global conversationStarted
    conversationStarted = False
    await vc.disconnect(force=True)


@tasks.loop(minutes=5)
async def keep_alive_ping():
    """
    Periodically prints a message to prevent idle disconnects.
    Can also be used to log that the bot is still running.
    """
    for guild in bot.guilds:
        # ping each guild to ensure the bot is considered active
        print(f"💓 Keep-alive ping for guild: {guild.name} ({guild.id})")


@bot.event
async def on_disconnect():
    print("⚠️ Bot disconnected from Discord!")


@bot.event
async def on_resumed():
    print("✅ Bot reconnected to Discord!")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("Opus loaded:", discord.opus.is_loaded())

    # start the loops
    if not keep_alive_ping.is_running():
        keep_alive_ping.start()


if __name__ == "__main__":
    print("discord.py version:", discord.__version__)
    bot.run(DISCORD_TOKEN)
