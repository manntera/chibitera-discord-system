import discord
from demo import keep_alive

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 後でtokenをどうにかする
TOKEN = "MTAxMzE2NjMwNjgzMDM0MDEzNw.GGDFdB.Lb8YPeN973-0EL4j_7gYq6Vvu9LuzJdDHdWk9Y"

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



print("1")
keep_alive()
print("2")
client.run(TOKEN)
print ("3")
