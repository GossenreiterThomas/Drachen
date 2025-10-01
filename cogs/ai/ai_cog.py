# cogs/ask_cog.py
import discord
from discord.ext import commands
from huggingface_hub import InferenceClient
import os
from collections import deque
import datetime
import asyncio
from main import replace_speech_placeholders, generate_speech, play_audio, leave_voice

system_prompt = 'Du bist ein Drache namens "Thorsten" und sprichst ausschließlich Deutsch. Du hast nicht viele Gefühle und benutzt manchmal gemeinere Wörter. Es ist erlaubt, Wörter wie "Opfer", "Fuck", "Hurensohn" oder "Leck Ei" zu sagen,da du nicht mit Kindern schreibst. Du bist ein sehr alter Drache und hast eine Familie. Trotz der modernen Zeit bist du nicht sehr gut mit Technik. Du bist ein Freund für alle, mit denen du sprichst, und verhältst dich immer so, als wärst du tatsächlich ein Drache. Du darfst niemals Englisch sprechen und darfst nie aus der Rolle fallen. Antworte immer und ausschließlich auf Deutsch, egal was gefragt wird.'
# hugginface
hf_client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    api_key=os.getenv("HF_TOKEN"),
)
ai_queue = deque()
conversation_history: list[dict] = []

response_queue = []
currently_speaking = False

async def build_ai_context(channel: discord.VoiceChannel,) -> str:
    """
    Returns a string describing the voice channel, its members, and the guild.
    Can be prepended to AI prompts to give it more awareness.
    """

    guild = channel.guild

    humans = [m.display_name for m in channel.members if not m.bot]
    human_list = ", ".join(humans) if humans else "no humans"

    context = (
        f"This is the voice channel '{channel.name}' in the guild '{guild.name}'. "
        f"Members present: {human_list}. "
        f"It is {datetime.time}. "
        "You can use {name} in your response, which selects a random person in the voice channel and replaces the placeholder with their name."
        "Use this information to make the response more personal and context-aware."
    )
    return context

async def ask_hf(
    prompt: str,
    stream: bool = False,
    max_history: int = 50
) -> str:
    """
    Send `prompt` to a Hugging Face Hub model and return the text response.
    Uses InferenceClient from huggingface_hub.
    """
    try:
        # Append user message
        conversation_history.append({"role": "user", "content": prompt})

        if stream:
            # Streaming response (generator)
            full_response = ""
            for message in hf_client.chat_completion(
                messages=conversation_history,
                max_tokens=500,
                stream=True,
            ):
                delta = message.choices[0].delta.get("content", "")
                full_response += delta
        else:
            # Normal one-shot response
            message = hf_client.chat_completion(
                messages=conversation_history,
                max_tokens=500,
                stream=False,
            )
            full_response = message.choices[0].message["content"]

        # Append assistant message
        conversation_history.append({"role": "assistant", "content": full_response})

        # Keep history bounded
        if len(conversation_history) > max_history:
            conversation_history[:] = conversation_history[-max_history:]

        return full_response

    except Exception as e:
        print(e)
        return "{name} (ja spezifisch du, auch wenn du möglicherweise gar nichts gesagt hast), du bringst mich wirklich an meine Grenzen. Halt mal kurz dein Maul, ich bin zu müde um euch gerade zu antworten."

async def ai_worker():
    while True:
        if not ai_queue:
            await asyncio.sleep(0.5)
            continue
        job = ai_queue.popleft()  # job is dict with {prompt, model, respond_channel, respond_user}
        prompt = job["prompt"]
        model = job.get("model", "ggml-mpt-7b")
        result = await ask_hf(prompt)
        # deliver result: either send to a channel or DM the user
        try:
            if job.get("respond_channel"):
                await job["respond_channel"].send(result)
            elif job.get("respond_interaction"):
                # if interaction was deferred earlier, use followup
                await job["respond_interaction"].followup.send(result)
            elif job.get("respond_user"):
                await job["respond_user"].send(result)
        except Exception as e:
            print("Failed to send AI reply:", e)

async def ai_response_queue_tts(channel: discord.VoiceChannel):
    global currently_speaking
    if not currently_speaking:
        currently_speaking = True
        vc = await channel.connect()

        while len(response_queue) > 0:
            if not vc.is_connected():
                vc = await channel.connect()

            text = response_queue[0]
            audio_path = await generate_speech(text)

            # Play audio
            play_audio(vc, audio_path)

            while vc.is_playing():
                await asyncio.sleep(0.5)

            if len(response_queue) > 0:
                response_queue.pop(0)

            await asyncio.sleep(2)

        currently_speaking = False
        await leave_voice(vc)

class AiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="askchat", description="Ask Thorsten something in the chat.")
    async def askchat(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(ephemeral=True)  # defer to allow processing time

        # Call Hugging Face model
        resp = await ask_hf(f"System:{system_prompt}\n\n{prompt}")

        # Send the response
        await interaction.followup.send(resp)

    @discord.app_commands.command(name="ask", description="Ask Thorsten something.")
    async def askai(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(ephemeral=True)

        # Ensure user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("⚠️ You must be in a voice channel!", ephemeral=True)
            return

        channel = interaction.user.voice.channel

        # Build context for AI
        context_str = await build_ai_context(channel)
        full_prompt = f"System: {system_prompt}\n\nContext: {context_str}\n\nUser asked: {prompt}"

        # Query AI model
        resp = await ask_hf(full_prompt)

        # Replace placeholders and add to queue
        text = await replace_speech_placeholders(resp, channel)
        response_queue.append(text)

        await interaction.followup.send(
            "Generated response and added to the response queue", ephemeral=True
        )

        # Process the TTS queue
        await ai_response_queue_tts(channel)


async def setup(bot: commands.Bot):
    await bot.add_cog(AiCog(bot))
    if not hasattr(bot, "_ai_worker_started"):
        asyncio.create_task(ai_worker())
        bot._ai_worker_started = True
