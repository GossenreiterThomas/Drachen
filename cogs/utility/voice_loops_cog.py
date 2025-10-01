# cogs/voice_loops_cog.py
import random
import asyncio
from discord.ext import commands, tasks
from main import leave_voice, generate_speech, replace_speech_placeholders, play_audio

greetings = [
    "Hallo Leute!",
    "Ich bins mal 1wieder, euer Drachen.",
    "Ich bin Batman.",
    "Halli Hallo meine Gesellen.",
    "GuMo meine Besties.",
    "Hällo meine bitches.",
    "Hallo, wäre jemand daun für i sex?",
    "{name}, wie gehts Frau und Kindern?"
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

class VoiceLoopsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.conversation_started = False
        self.conversation_count = 0

        self.auto_voice_manager.start()
        self.random_speaker.start()

    @tasks.loop(minutes=1)
    async def auto_voice_manager(self):
        if not self.conversation_started:
            for guild in self.bot.guilds:
                vc = self.get_voice_client(guild)

                # Already connected
                if vc and vc.channel:
                    if len([m for m in vc.channel.members if not m.bot]) == 0:
                        await leave_voice(vc)
                        print(f"❌ Disconnected from empty channel {vc.channel.name} in {guild.name}")
                    else:
                        continue

                if random.randrange(1, 1000) == 1:
                    for channel in guild.voice_channels:
                        members = [m for m in channel.members if not m.bot]
                        if members:
                            try:
                                await channel.connect()
                                self.conversation_started = True
                                print(f"🔊 Joined {channel.name} in {guild.name}")
                            except Exception:
                                pass
                            break

    @tasks.loop(seconds=5)
    async def random_speaker(self):
        if self.conversation_started:
            for guild in self.bot.guilds:
                vc = self.get_voice_client(guild)

                if vc and vc.is_connected() and not vc.is_playing():
                    if any(not m.bot for m in vc.channel.members):
                        if random.choice([True, False]):
                            if self.conversation_count == 0:
                                text = random.choice(greetings)
                            elif self.conversation_count == 4:
                                text = random.choice(conversationEnds)
                            else:
                                text = random.choice(conversationTexts)

                            text = await replace_speech_placeholders(text, vc.channel)
                            audio_path = await generate_speech(text, "random_tts.wav")
                            print(f"🗣️ Saying: {text}")

                            play_audio(vc, audio_path)
                            while vc.is_playing():
                                await asyncio.sleep(0.5)

                            if self.conversation_count == 4:
                                await leave_voice(vc)
                                self.conversation_count = 0
                                self.conversation_started = False
                            else:
                                self.conversation_count += 1

    def get_voice_client(self, guild):
        return next((vc for vc in self.bot.voice_clients if vc.guild == guild), None)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceLoopsCog(bot))
