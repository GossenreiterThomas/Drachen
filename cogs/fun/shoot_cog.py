from discord.ext import commands
import discord
import asyncio
import random
import os
from main import leave_voice, play_audio

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

    if vc.is_connected():
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
    else:
        print("Not connected to a voice channel.")
        return None

class ShootCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="shoot", description="Shoot someone in VC")
    async def shoot(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel!")
            return

        channel = ctx.author.voice.channel

        # Connect or reuse
        try:
            vc = await channel.connect()
        except discord.ClientException:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        await ctx.send("💥 Bang!")

        # Call the utility function
        target = await shoot_someone(
            interaction=ctx.interaction,   # works because Context inherits from Interaction in hybrid commands
            channel=channel,
            vc=vc,
            sound_path="gunshot.mp3",
            delay=0.8,
            exclude_invoker=True
        )

        await asyncio.sleep(1)
        await leave_voice(vc)

    @commands.hybrid_command(name="shootout", description="Shoot everyone in the channel, one by one")
    async def shootout(self, ctx: commands.Context):
        # 1. Check if user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel first!", ephemeral=True)
            return

        channel = ctx.author.voice.channel

        # 2. Connect to the channel
        try:
            vc = await channel.connect()
        except discord.ClientException:
            # already connected
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.interaction.guild)


        last_target = None

        while True:
            # Check if there are still humans to shoot
            humans = [m for m in channel.members if not m.bot]
            if not humans:
                # No one left → report the last person shot
                await ctx.interaction.followup.send(
                    f"Shootout finished. Last person shot was {last_target.display_name if last_target else 'nobody'}."
                )
                break

            # Play standoff sound
            play_audio(vc, "standoff.mp3")
            await asyncio.sleep(random.randrange(5, 20))

            # Shoot someone
            last_target = await shoot_someone(
                interaction=ctx.interaction,
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


async def setup(bot: commands.Bot):
    await bot.add_cog(ShootCog(bot))