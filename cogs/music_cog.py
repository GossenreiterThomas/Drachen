# cogs/music_cog.py
import discord
from discord.ext import commands
import os
import random
import asyncio
from main import play_audio, leave_voice  # import helpers from your main.py

MUSIC_DIR = "stelldirdrachenvor"
class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="music", description="Play a radio containing iconic stell dir drachen vor hits")
    async def music(self, interaction: discord.Interaction):
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
            vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

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
            # Autoplay next song if finished
            if not vc.is_playing() and not vc.is_paused():
                sound_path = get_random_file()
                if not sound_path:
                    break
                play_file(sound_path)
                await msg.edit(content=f"🔊 Now playing: `{os.path.basename(sound_path)}`")

            try:
                reaction, reactor = await self.bot.wait_for(
                    "reaction_add",
                    timeout=300.0,
                    check=lambda r, u: r.message.id == msg.id and u != self.bot.user and str(r.emoji) in reactions,
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


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
