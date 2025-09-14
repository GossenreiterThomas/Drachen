# main.py
import asyncio
import random
import wave

import discord
from discord.ext import commands, tasks
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
greetings = [
    "Hallo Leute!",
    "Ich bins mal wieder, euer Drachen.",
    "Ich bin Batman.",
    "Halli Hallo meine Gesellen.",
    "GuMo meine Besties.",
    "Hällo meine bitches.",
    "Hallo, wäre jemand daun für i sex?",
]
conversationTexts = [
    "Stellt euch Drachen vor!",
    "Bin ich ein großer Fan von.",
    "Findet ihr auch das Winn ein Opfer ist?",
    "Bin ich voll dafür.",
    "Gute idee!",
    "Mann, ich hasse Kinder.",
    "Was ist eigendlich so eure Meinung zu Transgschender Drachen?",
    "Se Bluetschufdeveize is connektet.",
    "Ja.",
    "Nein.",
    "Gesundheit.",
    "Leck ei.",
    "Fresse.",
    "Habt ihr schon mal über Würmer nachgedacht?",
    "Kennt ihr eigendlich schon meine Lieblingsband: Knorkator?",
    "Ich bin horny.",
    "Manchmal denke ich, dass ich doch nicht die Schule abbrechen hätte sollen.",
    "Mmmm?",
    "Mmmm",
]
conversationEnds = [
    "Ich muss jetzt hart kacken. Dafür müsst ihr mich jetzt einfach mal entschuldigen, sonst könnte das hier eine knappe Geschichte werden.",
    "Ihr Arschlöcher!",
    "Es tut mir sehr leid, aber ich muss mich jetzt verziehen und mit meiner Frau über interdimensionale Quantenregeln reden.",
    "Ich werde nun von dannen ziehn, einen schönen Tag noch.",
    "Ich geh jetzt frustpissen, auf wiedersehen.",
    "Ich werde jetzt meinen Drachen-Olaf scholtzen, also bis später.",
    "Ach du scheiße, ich habe gerade Wasser über meinen Laptop geschüttet!",
    "Scheiße! die Bullen kommen!",
]
conversationCount = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "de_DE-thorsten-medium.onnx")
voice_model = PiperVoice.load(model_path)

async def generate_speech(text: str, filename: str = "tts_output.wav") -> str:
    """
    Generate TTS audio file from given text.
    Returns the path to the generated audio.
    """
    audio_path = os.path.join("tts", filename)

    with wave.open(audio_path, "wb") as wav_file:
        wav_file.setnchannels(1)      # mono
        wav_file.setsampwidth(2)      # 16-bit
        wav_file.setframerate(22050)  # sample rate
        voice_model.synthesize_wav(text, wav_file)

    return audio_path

async def play_in_channel(interaction: discord.Interaction, audio_path: str):
    """
    Plays an audio file in the user's current voice channel.
    Disconnects after playback finishes.
    """
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("⚠️ You must be in a voice channel!", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    try:
        vc = await channel.connect()
    except discord.ClientException:
        vc = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)

    play_audio(vc, audio_path)

    while vc.is_playing():
        await asyncio.sleep(0.5)

    await leave_voice(vc)

async def shoot_someone(
    *,
    interaction: discord.Interaction,
    channel: discord.VoiceChannel,
    vc: discord.VoiceClient,
    sound_path: str = "gunshot.mp3",
    delay: float = 0.8,
    exclude_invoker: bool = True,
) -> discord.Member | None:
    """
    Play the given sound in `vc`, then pick a random eligible member from `channel`
    and disconnect them from voice. Replies are sent via the provided interaction.
    Returns the Member that was disconnected, or None if no eligible member existed.
    """

    # Validate sound file exists
    if not os.path.exists(sound_path):
        # Use followup because the interaction should be responded to by caller
        await interaction.followup.send("Gunshot sound file not found!", ephemeral=True)
        return None

    # Play the sound
    play_audio(vc, sound_path)

    # optional short delay to simulate timing (0.8s in your original)
    if delay and delay > 0:
        await asyncio.sleep(delay)

    bot_member = interaction.guild.me
    # Build eligible list: exclude the bot itself; optionally exclude the invoker
    eligible = [
        m for m in channel.members
        if (not m.bot) and (m != bot_member)
    ]

    if not eligible:
        await interaction.followup.send("Nobody else was in the channel... you got lucky 😏")
        return None

    target = random.choice(eligible)

    try:
        # disconnect target from voice (move to None)
        await target.edit(voice_channel=None, reason=f"Shot by {interaction.user} via /shoot")
        # announce publicly in channel (not ephemeral)
        await interaction.followup.send(f"💥 **{target.display_name}** was brutally killed in a gun 'incident'")
        return target
    except discord.Forbidden:
        await interaction.followup.send("I don’t have permission to move members!", ephemeral=True)
        return None
    except discord.HTTPException as e:
        await interaction.followup.send(f"Failed to disconnect: {e}", ephemeral=True)
        return None

def play_audio(vc, audio_path):
    if vc.is_playing() or vc.is_paused():
        vc.stop()  # stop current playback immediately
    vc.play(discord.FFmpegPCMAudio(audio_path))

async def leave_voice(vc):
    if vc.is_playing() or vc.is_paused():
        vc.stop()
    global conversationCount
    conversationCount = 0
    await vc.disconnect(force=True)

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

    if not interaction.response.is_done():
        await interaction.response.send_message("💥 Bang!", ephemeral=False)

    # 3. shoot someone
    await shoot_someone(
        interaction=interaction,
        channel=channel,
        vc=vc,
        sound_path="gunshot.mp3",
        delay=0.8,
        exclude_invoker=True,
    )

    # 4. Wait until audio finishes, then disconnect
    while vc.is_playing():
        await asyncio.sleep(1)

    await leave_voice(vc)


@bot.tree.command(name="shootout", description="Shoot everyone in the channel, one by one")
async def shootout(interaction: discord.Interaction):
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

    if not interaction.response.is_done():
        await interaction.response.send_message("💥 Shootout starting...", ephemeral=False)

    last_target = None

    while True:
        # Check if there are still humans to shoot
        humans = [m for m in channel.members if not m.bot]
        if not humans:
            # No one left → report the last person shot
            await interaction.followup.send(
                f"Shootout finished. Last person shot was {last_target.display_name if last_target else 'nobody'}."
            )
            break

        # Play standoff sound
        play_audio(vc, "standoff.mp3")
        await asyncio.sleep(random.randrange(5, 20))

        # Shoot someone
        last_target = await shoot_someone(
            interaction=interaction,
            channel=channel,
            vc=vc,
            sound_path="gunshot.mp3",
            delay=0.8,
            exclude_invoker=True,
        )

        # Wait until shooting audio finishes
        while vc.is_playing():
            await asyncio.sleep(1)

    await leave_voice(vc)


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
        play_audio(vc, path)

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
        await leave_voice(vc)


@bot.tree.command(name="say", description="Convert text to speech")
async def say(interaction: discord.Interaction, text: str):
    if not text:
        await interaction.response.send_message("❌ You must provide text!", ephemeral=True)
        return

    if len(text) >= 2000:
        await interaction.response.send_message("⚠️ Text too long (max 2000 chars)!", ephemeral=True)
        return

    await interaction.response.defer()

    # Generate speech
    audio_path = await generate_speech(text)

    # Send confirmation
    await interaction.followup.send(f"🗣️ Generated speech for: `{text}`")

    # Play in VC
    await play_in_channel(interaction, audio_path)


@tasks.loop(minutes=1)
async def auto_voice_manager():
    for guild in bot.guilds:
        vc = discord.utils.get(bot.voice_clients, guild=guild)

        # Case 1: Already connected
        if vc and vc.channel:
            if len([m for m in vc.channel.members if not m.bot]) == 0:
                # No humans left in channel
                await leave_voice(vc)
                print(f"❌ Disconnected from empty channel {vc.channel.name} in {guild.name}")
            else:
                # Still users there, stay
                continue

        if random.randrange(1, 10) == 1:
            # Case 2: Not connected → try to find a channel with people
            for channel in guild.voice_channels:
                members = [m for m in channel.members if not m.bot]
                if members:  # found humans
                    try:
                        await channel.connect()
                        print(f"🔊 Joined {channel.name} in {guild.name}")
                    except discord.ClientException:
                        pass
                    break  # only join one channel per guild


@tasks.loop(seconds=5)
async def random_speaker():
    for guild in bot.guilds:
        vc = discord.utils.get(bot.voice_clients, guild=guild)

        if vc and vc.is_connected() and not vc.is_playing():
            # Only speak if there's at least 1 human in the channel
            if any(not m.bot for m in vc.channel.members):
                if random.choice([True, False]):
                    global conversationCount
                    if conversationCount == 0:
                        text = random.choice(greetings)
                    elif conversationCount == 4:
                        text = random.choice(conversationEnds)
                    else:
                        text = random.choice(conversationTexts)

                    audio_path = await generate_speech(text, "random_tts.wav")
                    print(f"🗣️ Saying: {text}")

                    # Play inside the connected VC
                    play_audio(vc, audio_path)
                    while vc.is_playing():
                        await asyncio.sleep(0.5)

                    if conversationCount == 4:
                        await leave_voice(vc)
                    else:
                        conversationCount += 1

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
    # start the loops
    if not auto_voice_manager.is_running():
        auto_voice_manager.start()
    if not random_speaker.is_running():
        random_speaker.start()
    if not keep_alive_ping.is_running():
        keep_alive_ping.start()


if __name__ == "__main__":
    print("discord.py version:", discord.__version__)
    bot.run(DISCORD_TOKEN)