# cogs/blackjack_cog.py
import random
import discord
from discord import app_commands
from discord.ext import commands
from main import generate_speech, play_audio, leave_voice
import asyncio

suits = ["♠", "♥", "♦", "♣"]
ranks = {
    "A": 11,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10
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

class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="blackjack", description="Play a game of blackjack against the dealer")
    async def blackjack(self, interaction: discord.Interaction):
        await interaction.response.defer()  # defer in case game takes time

        player_hand = [draw_card(), draw_card()]
        dealer_hand = [draw_card(), draw_card()]

        def format_hand(hand, hide_second=False):
            if hide_second:
                return f"{hand[0][0]}{hand[0][1]} [??]"
            return " ".join([f"{r}{s}" for r, s, _ in hand])

        # Send initial hands
        msg = await interaction.followup.send(
            f"🃏 **Blackjack!** 🃏\n\n"
            f"**Your hand:** {format_hand(player_hand)} (value: {hand_value(player_hand)})\n"
            f"**Dealer's hand:** {format_hand(dealer_hand, hide_second=True)}"
        )

        # Player's turn
        while hand_value(player_hand) < 21:
            await interaction.followup.send("Type `hit` to draw another card or `stand` to hold.")

            def check(m):
                return m.author == interaction.user and m.content.lower() in ["hit", "stand"]

            try:
                reply = await self.bot.wait_for("message", check=check, timeout=30.0)
            except:
                await interaction.followup.send("⏰ Timed out! Game over.")
                return

            if reply.content.lower() == "hit":
                player_hand.append(draw_card())
                await interaction.followup.send(
                    f"**Your hand:** {format_hand(player_hand)} (value: {hand_value(player_hand)})"
                )
            else:
                break

        player_value = hand_value(player_hand)
        if player_value > 21:
            await interaction.followup.send("You busted! Dealer wins.")
            await self.say_loss(interaction)
            return

        # Dealer's turn
        while hand_value(dealer_hand) < 17:
            dealer_hand.append(draw_card())

        dealer_value = hand_value(dealer_hand)

        # Final results
        await interaction.followup.send(
            f"**Dealer's hand:** {format_hand(dealer_hand)} (value: {dealer_value})"
        )

        if dealer_value > 21 or player_value > dealer_value:
            await interaction.followup.send("You win!")
        elif player_value == dealer_value:
            await interaction.followup.send("🤝 It's a tie!")
        else:
            await interaction.followup.send("LOL - Dealer wins!")
            await self.say_loss(interaction)

    async def say_loss(self, interaction: discord.Interaction):
        """If the player loses, join their voice channel and say a random line."""
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
