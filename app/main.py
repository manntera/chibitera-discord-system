from discord.ext import commands
from discord import Intents

from demo import keep_alive

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

cogs = ["auth_system"]


class Main(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="ch!", intents=intents)

    async def setup_hook(self):
        for cog in cogs:
            module = f"cogs.{cog}"
            await self.load_extension(module)
            print(module, "読み込み完了")

    async def on_ready(self):
        print(f"{client.user}を起動しました。")


if __name__ == "__main__":
    import os

    TOKEN = os.getenv("DISCORD_TOKEN_SECRET")
    bot = Main()
    keep_alive()
    bot.run(TOKEN)
