import os
import discord
from demo import keep_alive

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 後でtokenをどうにかする
TOKEN = os.getenv('DISCORD_TOKEN_SECRET')

def exit(msg: str) -> None:
    """
    処理を中断する時に実行される関数

    Parameters
    ----------
    msg: str
        終了する時に出力するメッセージ

    Returns
    -------
    None

    """
    print(msg)
    import sys
    sys.exit()


if TOKEN is None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        exit("TOKENが見つからなかったため、処理を中断しました。")

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN_SECRET')

    if TOKEN is None:
        exit("TOKENが見つからなかったため、処理を中断しました。")


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
