import sys

import sentry_sdk
from config import DEBUG_MODE, SENTRY_SDK, TOKEN
from discord import Intents
from discord.ext import commands
from sentry_sdk.integrations.asyncio import AsyncioIntegration

intents = Intents.default()
intents.message_content = True

cogs = ["pomodoro-timer", "auth_system"]


class Main(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="ch!", intents=intents)

        sentry_sdk.init(
            dsn=SENTRY_SDK,
            integrations=[
                AsyncioIntegration(),
            ],
        )
        self.is_debug_mode = DEBUG_MODE

    async def setup_hook(self):
        await super().setup_hook()

    async def on_ready(self):
        for cog in cogs:
            module = f"cogs.{cog}"
            await self.load_extension(module)
            print(module, "読み込み完了")

        await self.tree.sync()

        # self.userがオプショナルになってたので
        # self.userがNoneの場合は起動中止
        if not self.user:
            await self.close()
            print("#######self.userがNoneのため起動を中止しました#############")
            return

        print(str(self.user), self.user.id, "起動完了")


if __name__ == "__main__":
    bot = Main()

    if not TOKEN:
        print("#######TOKENが見つからないため、処理をを中止しました#############")
        sys.exit()

    bot.run(TOKEN)
