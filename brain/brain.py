import asyncio
import discord
from brain.SpeachPhrase import SpeachPhrase
from main import generate_speech, replace_speech_placeholders, play_audio, leave_voice

queue: list[SpeachPhrase] = []

current_channel = None

def add_text_to_queue(text: str, interaction):
    queue.append(SpeachPhrase(text, interaction))

last_voicechannel = None

##channel afk timout
WAIT_TILL_LEAVE_TIME = 4
waiting_till_leave = 0

async def think_loop():
    global last_voicechannel, WAIT_TILL_LEAVE_TIME, waiting_till_leave, current_channel
    while True:
        #print("Thinking...")
        try:
            if len(queue) > 0:
                if last_voicechannel is not None:
                    print(last_voicechannel, "   ", queue[0].interaction.user.voice.channel)

                    if last_voicechannel is not queue[0].interaction.user.voice.channel:
                        print("Channel changed")
                        await manage_interaction(queue[0].interaction)
                    else:
                        print("Same channel")
                        if current_channel is None:
                            await manage_interaction(queue[0].interaction)
                else:
                    print("First interaction")
                    await manage_interaction(queue[0].interaction)

                last_voicechannel = queue[0].interaction.user.voice.channel
                waiting_till_leave = 0
                await talk(queue[0].interaction.user.voice.channel)  # also pops the phrase#
            else:
                ##nothing to say
                print("waiting_till_leave:",waiting_till_leave)
                if current_channel is not None:
                    if not current_channel.is_playing():
                        waiting_till_leave += 1
                        if waiting_till_leave >= WAIT_TILL_LEAVE_TIME:
                            try:
                                await leave_voice(current_channel)
                            except Exception as e:
                                print("error leaving channel",e)
                            current_channel = None
                    else:
                        waiting_till_leave = 0
                else:
                    waiting_till_leave = 0
        except Exception as e:
            print(e)

        await asyncio.sleep(1)

async def talk(channel):
    global current_channel

    text = queue[0].phrase
    print("taked:",text)
    text = await replace_speech_placeholders(text, channel)
    audio_path = await generate_speech(text)
    try:
        play_audio(current_channel, audio_path)

        while current_channel.is_playing():
            print("playing")
            await asyncio.sleep(0.5)

    except Exception as e:
        print("error talking:",e)

    queue.pop(0)

async def manage_interaction(interaction):
    global current_channel
    print("channel:",interaction.user.voice.channel)
    channel = interaction.user.voice.channel

    # Disconnect from current voice channel if connected
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()

    # Connect to the new voice channel
    try:
        current_channel = await channel.connect()
        print(f"Connected to voice channel: {channel.name}")
    except Exception as e:
        print(f"Failed to connect to voice channel: {e}")