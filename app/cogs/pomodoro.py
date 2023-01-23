from discord.ext import commands
from discord import Member, VoiceState, utils


class Pomodoro_Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.time = {"s": 30, "k": 5, "j": None}

    @commands.Cog.listener("on_voice_state_update")
    async def vc_entry(self, member: Member, before: VoiceState, after: VoiceState):
        # VCに入室したアカウントがBOTだったら弾く
        if member.bot:
            return

        # ユーザーがVCにインしてなければ弾く
        if not after.channel:
            return

        # ユーザーが入ったVCが作業部屋じゃなければ弾く
        if after.channel.id != 1067009073247158392:
            return

        # 既にちびてらちゃんが作業部屋に入ってたら弾く
        if member.guild.me in after.channel:
            return

        # VCに接続
        await after.channel.connect(self_deaf=True)
        # 接続した時間を保存
        self.time["j"] = utils.utcnow()

    @commands.Cog.listener("on_voice_state_update")
    async def vc_exit(self, member: Member, before: VoiceState, after: VoiceState):
        pass


async def setup(bot):
    await bot.add_cog(Pomodoro_Timer(bot))
