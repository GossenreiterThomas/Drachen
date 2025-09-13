# main.py
import asyncio
import random
import wave

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from piper import PiperVoice

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


@bot.tree.command(name="help", description="Show some info")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="STELL DIR DRACHEN VOR!!",
        description="Alle Befehle, die es so gibt und bissl Info.",
        color=discord.Color.blurple()
    )
    embed.add_field(name="imagine", value="Bissl Vorstellungskraft", inline=True)
    embed.add_field(name="shoot", value="Irgendwer in deinem channel wird in einen gun 'incident' verwickelt.", inline=True)
    embed.add_field(name="music", value="Spiel zufällige ultra umschwärmte Stell Dir drachen Vor Hits.", inline=True)
    embed.add_field(name="say", value="Thorsten sagt genau das, was du willst.", inline=True)
    embed.set_footer(text="Requested by " + interaction.user.name)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="imagine", description="stell dir einfach vor")
async def hello(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"{interaction.user.name}, du bist daran extreme Aufstellungskraft aufzubringen...!",
        color=discord.Color.green()
    )
    embed.set_image(url=random.choice(DRAGON_GIFS))
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


@bot.tree.command(name="music", description="Play a radio containing iconic stell dir drachen vor hits")
async def music(interaction: discord.Interaction):
    user = interaction.user

    # 1. Check if user is in a voice channel
    if not user.voice or not user.voice.channel:
        await interaction.response.send_message(
            "You need to be in a voice channel first!", ephemeral=True
        )
        return

    channel = user.voice.channel

    # 2. Connect or reuse
    try:
        vc = await channel.connect()
    except discord.ClientException:
        vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    # 3. Send the initial message and get the Message object
    await interaction.response.send_message("🔊 Starting playback...")
    msg = await interaction.original_response()

    # 4. Add reactions (pause, resume, stop, skip)
    reactions = ["⏸️", "▶️", "⏹️", "⏭️"]
    for r in reactions:
        await msg.add_reaction(r)

    # 5. Helper to pick a random file
    def get_random_file():
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
        return os.path.join(MUSIC_DIR, random.choice(files)) if files else None

    # 6. Helper to play a file
    def play_file(path):
        vc.play(discord.FFmpegPCMAudio(path))

    # 7. Start the first song
    sound_path = get_random_file()
    if not sound_path:
        await interaction.followup.send("No sound files found!", ephemeral=True)
        return
    play_file(sound_path)
    await msg.edit(content=f"🔊 Now playing: `{os.path.basename(sound_path)}`")

    # 8. Reaction loop
    while True:
        # Auto-play next song if finished
        if not vc.is_playing() and not vc.is_paused():
            sound_path = get_random_file()
            if not sound_path:
                break
            play_file(sound_path)
            await msg.edit(content=f"🔊 Now playing: `{os.path.basename(sound_path)}`")

        try:
            reaction, reactor = await bot.wait_for(
                "reaction_add",
                timeout=300.0,
                check=lambda r, u: r.message.id == msg.id and u != bot.user and str(r.emoji) in reactions,
            )
        except asyncio.TimeoutError:
            break

        emoji = str(reaction.emoji)

        if emoji == "⏸️" and vc.is_playing():
            vc.pause()
        elif emoji == "▶️" and vc.is_paused():
            vc.resume()
        elif emoji == "⏹️":
            vc.stop()
            break
        elif emoji == "⏭️":
            vc.stop()
            # next loop iteration automatically picks a new random song

        # Remove user reaction so it can be pressed again
        await msg.remove_reaction(reaction.emoji, reactor)

        await asyncio.sleep(0.5)

    # 9. Disconnect
    if vc.is_connected():
        await msg.delete()
        await vc.disconnect(force=True)


@bot.tree.command(name="say", description="Convert text to speech")
async def say(interaction: discord.Interaction, text: str):
    if not text:
        await interaction.response.send_message("You need to provide some text!", ephemeral=True)
        return

    if text.__len__() >= 2000:
        await interaction.response.send_message("The text cannot be longer than 2000 characters!", ephemeral=True)
        return

    # 1. Defer the response to allow long processing
    await interaction.response.defer(ephemeral=False)

    # 2. Load voice model
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(BASE_DIR, "de_DE-thorsten-medium.onnx")
    voice_model = PiperVoice.load(model_path)

    # 3. Generate TTS
    audio_path = os.path.join("tts", "tts_output.wav")
    os.makedirs("tts", exist_ok=True)


    # Open the output file for writing
    with wave.open(audio_path, "wb") as wav_file:
        # Set the required parameters
        wav_file.setnchannels(1)  # Mono audio
        wav_file.setsampwidth(2)  # 16-bit samples
        wav_file.setframerate(22050)  # Sample rate (must match the model's expected rate)

        voice_model.synthesize_wav(text, wav_file)

    # 4. Send confirmation
    msg = await interaction.followup.send(f"Generated speech for: `{text}`")

    # 5. Join voice channel and play
    if interaction.user.voice and interaction.user.voice.channel:
        channel = interaction.user.voice.channel
        try:
            vc = await channel.connect()
        except discord.ClientException:
            vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)

        # Play audio
        vc.play(discord.FFmpegPCMAudio(audio_path))

        # Wait until finished
        while vc.is_playing():
            await asyncio.sleep(0.5)

        await msg.delete()

        await vc.disconnect(force=True)


if __name__ == "__main__":
    print("discord.py version:", discord.__version__)
    bot.run(DISCORD_TOKEN)
