# cogs/blackjack_cog.py
import random
import discord
from discord import app_commands
from discord.ext import commands
from main import generate_speech, play_audio, leave_voice
import asyncio

suits = ["♠", "♥", "♦", "♣"]
ranks = {
    "A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10
}

LOSS_PHRASES = [
    "Haha, du Loser! Sogar eine Schildkröte hätte besser gespielt, du Hurensohn!",
    "💥 Boom! Du bist so schlecht, dass ich fast lachen muss, Opfer!",
    "Leck mich am Arsch, du kleiner Wicht, der Dealer hat dich fertiggemacht!",
    "Haha, wie peinlich! Du bist voll der Vollidiot. Nächstes Mal vielleicht überlegen, Hurensohn.",
    "Fresse halten, du Nichts! Ich hab dich auseinandergerissen wie ein kleines Kind.",
    "Du dachtest, du kannst gewinnen? Lächerlich, du Elendsopfer!",
    "Verdammt nochmal, bist du immer so dumm oder nur heute?",
]

def draw_card():
    rank = random.choice(list(ranks.keys()))
    suit = random.choice(suits)
    return (rank, suit, ranks[rank])

def hand_value(hand):
    value = sum(card[2] for card in hand)
    aces = sum(1 for card in hand if card[0] == "A")
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

def format_hand(hand, hide_second=False):
    if hide_second:
        return f"{hand[0][0]}{hand[0][1]} [??]"
    return " ".join([f"{r}{s}" for r, s, _ in hand])

class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="blackjack", description="Play a round of blackjack")
    async def blackjack(self, interaction: discord.Interaction):
        """Slash command for blackjack using reactions"""
        await interaction.response.defer()
        player_hand = [draw_card(), draw_card()]
        dealer_hand = [draw_card(), draw_card()]

        embed = discord.Embed(title="🃏 Blackjack!", color=discord.Color.green())
        embed.description = (
            f"**Your hand:** {format_hand(player_hand)} (value: {hand_value(player_hand)})\n"
            f"**Dealer's hand:** {format_hand(dealer_hand, hide_second=True)}\n\n"
            f"React ✅ to hit or ❌ to stand."
        )

        msg = await interaction.followup.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return (
                user == interaction.user
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == msg.id
            )

        # Player turn
        while hand_value(player_hand) < 21:
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Timed out! Game over.")
                return

            if str(reaction.emoji) == "✅":
                player_hand.append(draw_card())
            elif str(reaction.emoji) == "❌":
                break

            embed.description = (
                f"**Your hand:** {format_hand(player_hand)} (value: {hand_value(player_hand)})\n"
                f"**Dealer's hand:** {format_hand(dealer_hand, hide_second=True)}\n\n"
                f"React ✅ to hit or ❌ to stand."
            )
            await msg.edit(embed=embed)
            await msg.remove_reaction(reaction, interaction.user)

        player_value = hand_value(player_hand)
        if player_value > 21:
            embed.description = f"**Your hand:** {format_hand(player_hand)} (value: {player_value})\nYou busted! Dealer wins."
            await msg.edit(embed=embed)
            await self.say_loss(interaction)
            return

        # Dealer turn
        while hand_value(dealer_hand) < 17:
            dealer_hand.append(draw_card())

        dealer_value = hand_value(dealer_hand)

        # Show final hands
        result_text = ""
        if dealer_value > 21 or player_value > dealer_value:
            result_text = "You win!"
        elif player_value == dealer_value:
            result_text = "🤝 It's a tie!"
        else:
            result_text = "LOL - Dealer wins!"
            await self.say_loss(interaction)

        embed.description = (
            f"**Your hand:** {format_hand(player_hand)} (value: {player_value})\n"
            f"**Dealer's hand:** {format_hand(dealer_hand)} (value: {dealer_value})\n\n"
            f"{result_text}"
        )
        await msg.edit(embed=embed)

    async def say_loss(self, interaction: discord.Interaction):
        """Say a random losing phrase in user's voice channel"""
        if interaction.user.voice and interaction.user.voice.channel:
            channel = interaction.user.voice.channel
            try:
                vc = await channel.connect()
            except discord.ClientException:
                vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

            text = random.choice(LOSS_PHRASES)
            audio_path = await generate_speech(text)
            play_audio(vc, audio_path)

            while vc.is_playing():
                await asyncio.sleep(0.5)

            await leave_voice(vc)

async def setup(bot: commands.Bot):
    await bot.add_cog(BlackjackCog(bot))
