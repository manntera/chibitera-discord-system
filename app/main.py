from discord.ext import commands
from discord import Intents

intents = Intents.default()
intents.message_content = True

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
        print(str(self.user), self.user.id, "起動完了")


if __name__ == "__main__":
    import os

    TOKEN = os.getenv("DISCORD_TOKEN_SECRET")
    bot = Main()
    bot.run(TOKEN)
