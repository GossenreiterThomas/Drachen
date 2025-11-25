# cogs/ask_cog.py
import asyncio
import datetime
import threading
from collections import deque

import discord
from discord.ext import commands

from main import (
    generate_speech,
    leave_voice,
    logging,
    play_audio,
    replace_speech_placeholders,
)

# Ollama-Konfiguration
OLLAMA_MODEL = "thorsten"
ai_queue = deque()
conversation_history: list[dict] = []

response_queue = []
currently_speaking = False


async def build_ai_context(channel: discord.VoiceChannel) -> str:
    """Erstellt den Kontext für das Ollama-Model basierend auf dem Voice Channel."""
    guild = channel.guild

    humans = [m.display_name for m in channel.members if not m.bot]
    human_list = ", ".join(humans) if humans else "keine Menschen"

    context = (
        f"Dieser ist der Sprachkanal '{channel.name}' im Server '{guild.name}'. "
        f"Anwesende Mitglieder: {human_list}. "
        f"Es ist {datetime.datetime.now().strftime('%H:%M:%S')}. "
        "Du kannst {name} in deiner Antwort verwenden, das einen zufälligen Teilnehmer im Sprachkanal auswählt."
        "Du solltst an deiner Antwort nicht anfügen, von wem sie kommt. Deine Antwort kommt von Thorsten, und das musst du selbst nicht definieren!"
    )
    return context


async def ask_ollama(interaction, prompt: str, max_history: int = 50) -> str:
    """Sendet eine Anfrage an das lokale Ollama-Model und gibt die Antwort zurück."""
    import ollama

    try:
        print("Ai wird gefragt:")
        # Initialisiere den Ollama-Client
        #client = ollama.Client(host="http://host.docker.internal:11434")
        client = ollama.AsyncClient(host="http://localhost:11434")

        # Erstelle die vollständige Prompt-Nachricht
        full_prompt = f"Kontext: {prompt}\n"
        if conversation_history:
            full_prompt += "\nGesprächsverlauf:\n"
            for msg in conversation_history[-max_history:]:
                # Füge Discord-Namen statt 'Benutzer' oder 'Thorsten' hinzu
                user_name = msg.get("user_name", "Thorsten")
                full_prompt += f"{user_name}: {msg['content']}\n"

        # Antwort
        buffer = ""
        sentence = ""

        stream = await client.generate(
            model=OLLAMA_MODEL, prompt=full_prompt, stream=True
        )

        channel = interaction.user.voice.channel
        vc = await channel.connect()

        async for chunk in stream:
            try:
                print(chunk.response)
                text = chunk.response
                sentence += text
                if (
                    sentence.count(".") >= 1
                    or sentence.count("!") >= 1
                    or sentence.count("?") >= 1
                ):
                    print("new sentence")
                    print(sentence)
                    await add_sentence_to_queue(sentence, interaction)
                    await interaction.followup.send(sentence, ephemeral=True)

                    await ai_response_queue_tts(vc)

                    sentence = ""
                    buffer += text
            except Exception as e:
                print(f"Error: {e}")
                continue
        full_response = buffer
        print("full res:", full_response)
        ##full response isnt used anymore

        # Aktualisiere die Konversationshistorie
        conversation_history.append({"role": "assistant", "content": full_response})
        if len(conversation_history) > max_history:
            conversation_history[:] = conversation_history[-max_history:]

        return vc

    except Exception as e:
        logging.exception(e)
        return "Verdammt nochmal, jetzt funktioniert's wieder nicht! Gib mir mal 'ne Minute Zeit..."

async def add_sentence_to_queue(sentence: str, interaction):
    fixed_str = await replace_speech_placeholders(sentence, interaction.user.voice.channel)
    response_queue.append(fixed_str)


async def ai_worker():
    print("--------what even is this?.........")
    while True:
        if not ai_queue:
            await asyncio.sleep(0.5)
            continue

        job = ai_queue.popleft()
        prompt = job["prompt"]
        #result = await ask_ollama(prompt)

        # when only sending full message
        # await send_user_message(job, result)

async def send_user_message(job, result):
    return
    try:
        if job.get("respond_channel"):
            await job["respond_channel"].send(result)
        elif job.get("respond_interaction"):
            await job["respond_interaction"].followup.send(result)
        elif job.get("respond_user"):
            await job["respond_user"].send(result)
    except Exception as e:
        print(f"Fehler beim Senden der KI-Antwort: {e}")


async def ai_response_queue_tts(vc):
    global currently_speaking
    if not currently_speaking:
        currently_speaking = True
        #vc = await channel.connect()

        while len(response_queue) > 0:
            #if not vc.is_connected():
            #    vc = await channel.connect()

            text = response_queue[0]
            audio_path = await generate_speech(text)

            # Play audio
            play_audio(vc, audio_path)

            while vc.is_playing():
                await asyncio.sleep(0.5)

            if len(response_queue) > 0:
                response_queue.pop(0)

        currently_speaking = False
        #await leave_voice(vc) moved to ask ai function


class AiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(
        name="askchat", description="Frage Thorsten etwas im Chat."
    )
    async def askchat(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(ephemeral=True)

        # Hole Kontextinformationen
        # context_str = await build_ai_context(interaction.user.voice.channel)

        # Erstelle vollständige Prompt mit Kontext und Benutzernamen
        full_prompt = f"Kontext: User wrote in a text channel.\n\n{interaction.user.display_name} fragte: {prompt}"

        resp = await ask_ollama(interaction, full_prompt)
        await interaction.followup.send(resp)

    @discord.app_commands.command(name="ask", description="Frage Thorsten etwas.")
    async def askai(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send(
                "⚠️ Du musst in einem Sprachkanal sein!", ephemeral=True
            )
            return

        channel = interaction.user.voice.channel

        # Baue Kontext für KI
        context_str = await build_ai_context(channel)
        full_prompt = f"Kontext: {context_str}\n\n Prompt: {prompt}"
        await self.save_message(interaction.user, prompt)

        # Frage KI-Model
        vc = await ask_ollama(interaction, full_prompt)

        # Ersetze Platzhalter und füge zur Warteschlange hinzu
        #text = await replace_speech_placeholders(resp, channel)

        await interaction.followup.send(
            "Antwort generiert und zur Wiedergabeliste hinzugefügt", ephemeral=True
        )

        # Verarbeite die TTS-Warteschlange
        #await ai_response_queue_tts(channel)

        #await interaction.followup.send(text)

        while vc.is_playing():
            await asyncio.sleep(0.5)

        await leave_voice(vc)


    # Neue Methode zum Speichern der Nachrichten mit Benutzernamen
    async def save_message(self, user: discord.Member, content: str):
        """Speichert eine Nachricht mit dem Benutzernamen in der Konversationshistorie."""
        conversation_history.append(
            {"role": "user", "content": content, "user_name": user.display_name}
        )

    @discord.app_commands.command(
        name="print-context", description="Die History mit der Thorsten arbeitet."
    )
    async def printContext(self, interaction: discord.Interaction):
        full_prompt = ""

        if conversation_history:
            full_prompt += "\nGesprächsverlauf:\n"
            for msg in conversation_history:
                user_name = msg.get("user_name", "Thorsten")
                full_prompt += f"{user_name}: {msg['content']}\n"

        await interaction.response.send_message(full_prompt)


async def setup(bot: commands.Bot):
    await bot.add_cog(AiCog(bot))
