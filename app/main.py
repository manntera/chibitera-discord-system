import discord
from flask import Flask

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 後でtokenをどうにかする
TOKEN = "MTAxMzE2NjMwNjgzMDM0MDEzNw.GGDFdB.Lb8YPeN973-0EL4j_7gYq6Vvu9LuzJdDHdWk9Y"

PORT = 8000

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
app = Flask(__name__)
print("2")
client.run(TOKEN)
print ("3")

@app.route('/', methods=['###'])
def index():
    return 'hello world'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False)