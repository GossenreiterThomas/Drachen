import discord


class SpeachPhrase:
    def __init__(self, phrase, interaction: discord.interactions.Interaction):
        self.phrase = phrase
        self.interaction = interaction