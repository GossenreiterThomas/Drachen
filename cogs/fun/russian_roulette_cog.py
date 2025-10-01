# cogs/russian_roulette_cog.py
import random
import discord
from discord import app_commands
from discord.ext import commands
from main import generate_speech, play_audio, leave_voice
import asyncio

class RussianRouletteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="roulette", description="Play Russian Roulette!")
    async def roulette(self, interaction: discord.Interaction):
        """Slash command for Russian Roulette using buttons"""
        await interaction.response.defer()
        bullet_chamber = random.randint(1, 6)
        current_chamber = 1

        # Create a button
        class RouletteView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60.0)
                self.result = None

            @discord.ui.button(label="Pull the Trigger", style=discord.ButtonStyle.danger)
            async def pull(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_chamber
                if current_chamber == bullet_chamber:
                    self.result = "💥 Bang! You're dead!"
                    sound_file = "gunshot.mp3"
                    button.disabled = True
                else:
                    self.result = "🔫 Click… safe."
                    sound_file = "click.mp3"
                    current_chamber += 1
                    if current_chamber > 6:
                        button.disabled = True

                embed = discord.Embed(title="Russian Roulette", description=self.result, color=discord.Color.red())
                await interaction.response.edit_message(embed=embed, view=self)

                # Play audio in VC
                if interaction.user.voice and interaction.user.voice.channel:
                    try:
                        vc = await interaction.user.voice.channel.connect()
                    except discord.ClientException:
                        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

                    if vc.is_connected():
                        if vc.is_playing() or vc.is_paused():
                            vc.stop()
                        vc.play(discord.FFmpegPCMAudio(sound_file))
                        while vc.is_playing():
                            await asyncio.sleep(0.3)
                        await leave_voice(vc)

                if button.disabled:
                    self.stop()

        embed = discord.Embed(title="Russian Roulette", description="Press the button to pull the trigger!", color=discord.Color.red())
        await interaction.followup.send(embed=embed, view=RouletteView())

async def setup(bot: commands.Bot):
    await bot.add_cog(RussianRouletteCog(bot))
