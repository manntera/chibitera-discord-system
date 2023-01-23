from discord.ext import commands
from discord import Member, VoiceState


class Pomodoro_Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_voice_state_update")
    async def vc_entry(self, member: Member, before: VoiceState, after: VoiceState):
        pass

    @commands.Cog.listener("on_voice_state_update")
    async def vc_exit(self, member: Member, before: VoiceState, after: VoiceState):
        pass


async def setup(bot):
    await bot.add_cog(Pomodoro_Timer(bot))
