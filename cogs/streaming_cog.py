# cogs/voice_transcribe_cog.py
import discord
from discord.ext import commands
from discord.ext.voice_recv import VoiceRecvClient, sinks
from vosk import Model, KaldiRecognizer
import numpy as np
import asyncio
import json
import time
from main import generate_speech, play_audio

VOSK_MODEL_PATH = "models/vosk-model-small-de-0.15"

class StreamingSink(sinks.WaveSink):
    """Single-user Vosk sink with pause-based sentence detection."""
    def __init__(self, sample_rate=48000, pause_threshold=0.7, min_pcm_length=100):
        super().__init__("recordings/recordings.wav")
        self.sample_rate = sample_rate
        self.model = Model(VOSK_MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        self.buffer = b""
        self.last_voice_time = 0
        self.pause_threshold = pause_threshold
        self.min_pcm_length = min_pcm_length

    def write(self, source, data):
        try:
            pcm = np.frombuffer(data.pcm, dtype=np.int16)
        except Exception:
            return

        if len(pcm) * 2 < self.min_pcm_length:
            return

        # Convert stereo to mono if needed
        if len(pcm) % 2 == 0:
            pcm = pcm.reshape(-1, 2).mean(axis=1).astype(np.int16)

        self.buffer += pcm.tobytes()

        # simple voice activity detection
        amplitude = np.abs(pcm).mean()
        if amplitude > 500:  # threshold for speech
            self.last_voice_time = time.time()


class VoiceTranscribeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_clients = {}      # guild_id -> VoiceRecvClient
        self.sinks = {}           # guild_id -> StreamingSink
        self.tasks = {}           # guild_id -> monitoring task

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"VoiceTranscribeCog ready as {self.bot.user}")

    async def _monitor_transcription(self, guild_id, vc, sink):
        """Background task that checks for silence and speaks sentences."""
        while guild_id in self.vc_clients:
            await asyncio.sleep(0.1)
            try:
                if (time.time() - sink.last_voice_time) > sink.pause_threshold:
                    if sink.recognizer.AcceptWaveform(sink.buffer):
                        result_json = sink.recognizer.Result()
                    else:
                        result_json = sink.recognizer.PartialResult()
                    text = json.loads(result_json).get("text", "").strip()
                    if text:
                        print(f"[Bot says] {text}")
                        audio_path = await generate_speech(text)
                        play_audio(vc, audio_path)
                    sink.buffer = b""
            except Exception as e:
                print(f"[Transcription Monitor] Error: {e}")

    async def _monitor_voice(self, guild_id, channel):
        """Reconnect VC if disconnected."""
        while guild_id in self.vc_clients:
            try:
                vc = self.vc_clients[guild_id]
                sink = self.sinks[guild_id]
                if not vc.is_connected():
                    vc = await channel.connect(cls=VoiceRecvClient)
                    vc.listen(sink)
                    self.vc_clients[guild_id] = vc
                    print(f"[VoiceMonitor] Reconnected to {channel.name}")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[VoiceMonitor] Error: {e}")
                await asyncio.sleep(5)

    @commands.command(name="start_transcribe")
    async def start_transcribe(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("⚠️ You must be in a voice channel!")
            return

        guild_id = ctx.guild.id
        if guild_id in self.vc_clients:
            await ctx.send("Already transcribing!")
            return

        channel = ctx.author.voice.channel
        try:
            vc = await channel.connect(cls=VoiceRecvClient)
            sink = StreamingSink()
            vc.listen(sink)
            self.vc_clients[guild_id] = vc
            self.sinks[guild_id] = sink

            # Start both background tasks
            monitor_task = self.bot.loop.create_task(self._monitor_transcription(guild_id, vc, sink))
            reconnect_task = self.bot.loop.create_task(self._monitor_voice(guild_id, channel))
            self.tasks[guild_id] = [monitor_task, reconnect_task]

            await ctx.send(f"🎙️ Started transcribing in {channel.name}")
        except Exception as e:
            await ctx.send(f"Could not start transcription: {e}")

    @commands.command(name="stop_transcribe")
    async def stop_transcribe(self, ctx):
        guild_id = ctx.guild.id
        vc = self.vc_clients.get(guild_id)
        task_list = self.tasks.get(guild_id)

        if task_list:
            for t in task_list:
                t.cancel()
        if vc:
            try:
                vc.stop_listening()
            except Exception:
                pass
            try:
                await vc.disconnect()
            except Exception:
                pass

        self.vc_clients.pop(guild_id, None)
        self.sinks.pop(guild_id, None)
        self.tasks.pop(guild_id, None)
        await ctx.send("🛑 Stopped transcription.")


async def setup(bot):
    await bot.add_cog(VoiceTranscribeCog(bot))
