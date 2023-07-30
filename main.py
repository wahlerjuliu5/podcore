import discord
from discord.ext import commands
from pydub import AudioSegment
import asyncio

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# A dictionary to store user's voice streams
user_audio_data = {}


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


@bot.command()
async def record(ctx):
    if not ctx.author.voice:
        return await ctx.send("You are not connected to a voice channel.")

    if ctx.voice_client:
        return await ctx.send("I'm already recording in another voice channel.")

    voice_channel = ctx.author.voice.channel

    # Join the voice channel
    vc = await voice_channel.connect()

    # Start recording for all users in the voice channel
    for member in voice_channel.members:
        if member.bot:
            continue

        user_audio_data[member.id] = []

    vc.listen(record_audio)

    await ctx.send("Recording started. Use '!stop' to stop recording.")


def record_audio(before, after):
    if before.channel is None or before.afk or before.bot:
        return

    if after.channel is None or after.afk or after.bot:
        user_audio_data.pop(before.id, None)
        return

    if before.channel == after.channel:
        return

    user_audio_data.pop(before.id, None)
    user_audio_data[after.id] = []


@bot.command()
async def stop(ctx):
    vc = ctx.voice_client
    if vc and vc.is_listening():
        vc.stop_listening()
        await ctx.send("Recording stopped.")
        await process_and_send_audio(ctx)


async def process_and_send_audio(ctx):
    # Get all recorded user audio data
    recorded_audio_data = user_audio_data.values()

    # Merge all recorded audio data into a single audio file
    merged_audio_data = b"".join(recorded_audio_data)
    audio = AudioSegment(merged_audio_data, sample_width=2, frame_rate=48000, channels=2)

    # Convert the audio data to MP3
    audio.export('recording.mp3', format='mp3')

    # Send the MP3 file in the text channel
    with open('recording.mp3', 'rb') as f:
        await ctx.send(file=discord.File(f))

    # Clean up the files and reset the user_audio_data dictionary
    import os
    os.remove('recording.mp3')
    user_audio_data.clear()

    # Disconnect from the voice channel
    await ctx.voice_client.disconnect()


bot.run('YOUR_BOT_TOKEN')
