import discord
import http.server
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 後でtokenをどうにかする
TOKEN = "MTAxMzE2NjMwNjgzMDM0MDEzNw.GGDFdB.Lb8YPeN973-0EL4j_7gYq6Vvu9LuzJdDHdWk9Y"


PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler


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

def run_http_server():
    print("start http server")
    with http.server.HTTPServer(("/", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
        
http_thread = Thread(target=run_http_server)
http_thread.start()
http_thread.join()
        
bot_thread = Thread(target=client.run, args=(TOKEN, ))
bot_thread.start()
bot_thread.join()
