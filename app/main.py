import os
import discord
from demo import keep_alive

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 後でtokenをどうにかする
TOKEN = os.environ['DISCORD_TOKEN']

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await message.channel.send(message.content)
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

keep_alive()
client.run(TOKEN)
