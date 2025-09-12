# main.py
import asyncio
import random

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

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

    async def setup_hook(self):
        # Register commands into ONE test guild for instant availability (dev)
        guild = discord.Object(id=TEST_GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        # Register globally (may take up to an hour to appear)
        await self.tree.sync()
        print("Synced global commands")

    async def on_ready(self):
        print(f"Logged in as {self.user} — connected to {len(self.guilds)} guild(s)")
        for g in self.guilds:
            print(f"- {g.id} {g.name}")

bot = MyBot()


# variables used in different commands
DRAGON_GIFS = [
    "https://media.tenor.com/fCu2RwI0fFYAAAAi/dragon.gif",
]
MUSIC_DIR = "stelldirdrachenvor"

@bot.tree.command(name="imagine", description="stell dir einfach vor")
async def hello(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"{interaction.user.name}, du bist daran extreme Aufstellungskraft aufzubringen...!",
        color=discord.Color.green()
    )
    embed.set_image(url=random.choice(DRAGON_GIFS))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help", description="Show some info")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="STELL DIR DRACHEN VOR!!",
        description="Alle Befehle, die es so gibt und bissl Info.",
        color=discord.Color.blurple()
    )
    embed.add_field(name="imagine", value="Bissl Vorstellungskraft", inline=True)
    embed.add_field(name="shoot", value="Irgendwer in deinem channel wird in einen gun 'incident' verwickelt.", inline=True)
    embed.set_footer(text="Requested by " + interaction.user.name)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="shoot", description="Shoot someone")
async def shoot(interaction: discord.Interaction):
    # 1. Check if user is in a voice channel
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You need to be in a voice channel first!", ephemeral=True)
        return

    channel = interaction.user.voice.channel

    # 2. Connect to the channel
    try:
        vc = await channel.connect()
    except discord.ClientException:
        # already connected
        vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    # 3. Play gunshot sound
    sound_path = "gunshot.mp3"
    if not os.path.exists(sound_path):
        await interaction.response.send_message("Gunshot sound file not found!", ephemeral=True)
        return

    if not interaction.response.is_done():
        await interaction.response.send_message("💥 Bang!", ephemeral=True)
    else:
        await interaction.followup.send("💥 Bang!", ephemeral=True)

    vc.play(discord.FFmpegPCMAudio(sound_path))

    # 4. kill someone
    await asyncio.sleep(0.8)

    bot_member = interaction.guild.me
    eligible = [m for m in channel.members if m != bot_member]

    if not eligible:
        await interaction.followup.send("Nobody else was in the channel... you got lucky")

    target = random.choice(eligible)

    try:
        await target.edit(voice_channel=None, reason=f"Brutally shot to death.")
        await interaction.followup.send(f"💥 **{target.display_name}** was brutally killed in a gun 'incident'")
    except discord.Forbidden:
        await interaction.followup.send("I don’t have permission to move members!", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"Failed to disconnect: {e}", ephemeral=True)

    # 4. Wait until audio finishes, then disconnect
    while vc.is_playing():
        await asyncio.sleep(1)

    await vc.disconnect(force=True)


@bot.tree.command(name="musik", description="Play the iconic stell dir drachen vor music")
async def shoot(interaction: discord.Interaction):
    # 1. Check if user is in a voice channel
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You need to be in a voice channel first!", ephemeral=True)
        return

    channel = interaction.user.voice.channel

    # 2. Connect to the channel
    try:
        vc = await channel.connect()
    except discord.ClientException:
        # already connected
        vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    # 3. play music
    files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
    if not files:
        await interaction.response.send_message("No sound files found!", ephemeral=True)
        return

    sound_path = os.path.join(MUSIC_DIR, random.choice(files))

    # Notify user
    if not interaction.response.is_done():
        await interaction.response.send_message(f"🔊 Playing: `{os.path.basename(sound_path)}`")
    else:
        await interaction.followup.send(f"🔊 Playing: `{os.path.basename(sound_path)}`")


    vc.play(discord.FFmpegPCMAudio(sound_path))

    # 4. Wait until audio finishes, then disconnect
    while vc.is_playing():
        await asyncio.sleep(1)

    await vc.disconnect(force=True)


if __name__ == "__main__":
    print("discord.py version:", discord.__version__)
    bot.run(DISCORD_TOKEN)
