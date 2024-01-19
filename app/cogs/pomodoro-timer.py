from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

import config
from config import (
    LEAVE_CHANNEL_ID,
    NOTICE_CHANNEL_ID,
    POMO_DEBUG_CHANNEL_ID,
    SAGYOU_CHANNEL_ID,
    VoiceInfos,
)
from discord import (
    ButtonStyle,
    Color,
    Embed,
    Interaction,
    Member,
    TextChannel,
    VoiceState,
    ui,
    utils,
)
from discord.ext import commands, tasks
from pydantic import BaseModel

from .utils import excepter
from .utils.pomo import Play as PomoPlay
from .utils.pomo import PomodoroTimer
from .utils.pomo import error as PomoERROR

if TYPE_CHECKING:
    from main import Main


class PomodoroTimerCog(commands.Cog):
    def __init__(self, bot: Main):
        self.bot = bot

        self.sagyou_vc_id: int = SAGYOU_CHANNEL_ID  # type: ignore
        self.notice_channel_id: int = NOTICE_CHANNEL_ID  # type: ignore

        self.pomo = PomodoroTimer(bot)
        self.play: PomoPlay | None = None
        self.latest_time: datetime | None = None
        self.now_mode: Literal[
            "before_work_time", "work_time", "before_break_time", "break_time"
        ] | None = None

        self.now_mode_to_jp = {
            "before_work_time": "作業前",
            "work_time": "作業",
            "before_break_time": "休憩前",
            "break_time": "休憩",
        }

        self.admin_panel_view = AdminPanelView()

        self.bot.add_view(self.admin_panel_view)

        self.voice_info = VoiceInfos()

    async def cog_unload(self) -> None:
        self.speak.cancel()
        self.admin_panel_view.stop()

    async def send_debug(self, *messages) -> None:
        """
        デバッグ時にメッセージを送信する
        """
        if not self.bot.is_debug_mode:
            return

        debug_channel = self.bot.get_channel(POMO_DEBUG_CHANNEL_ID)

        if not isinstance(debug_channel, TextChannel):
            return None

        e = Embed(
            description=" ".join(message for message in messages),
            color=Color.from_str("#85d0f3"),
        )

        await debug_channel.send(embeds=[e])
        return None

    async def send_debug_embed(self, embed: Embed) -> None:
        """
        デバッグ時にメッセージを送信する
        """
        if not self.bot.is_debug_mode:
            return

        debug_channel = self.bot.get_channel(POMO_DEBUG_CHANNEL_ID)

        if not isinstance(debug_channel, TextChannel):
            return None

        await debug_channel.send(embeds=[embed])
        return None

    @tasks.loop(seconds=10)
    @excepter
    async def speak(self):
        """
        挨拶ボイスと2人目以降入室ボイス以外を再生する
        """

        await self.bot.wait_until_ready()

        if not self.latest_time or not self.now_mode or not self.play:
            return

        now = utils.utcnow()

        # VoiceInfoモデルをdictに変換し、現在のモードのinfoを取得する

        prm = self.voice_info.model_dump()[self.now_mode]

        if self.latest_time + timedelta(**prm["timedelta"]) >= now:
            return

        # エラーが出たとき5回トライする
        # 5回トライしてエラーが出たら諦める
        print("waiting...", self.pomo.download.events.is_all_download.is_set())
        await self.pomo.download.events.wait_all_download()
        print("download ok")

        filename = self.pomo.download.get_filename(prm["category"])

        for _ in range(5):
            try:
                play = getattr(self.play, self.now_mode)
                await play(filename)

                await self.pomo.download.send.play_embed(
                    POMO_DEBUG_CHANNEL_ID, self.now_mode_to_jp[self.now_mode]
                )

                break
            except Exception:
                await asyncio.sleep(1)

        # 現在のモードを次のモードに変更する
        # exp: before_work_time -> work_time
        self.now_mode = prm["next_mode"]

        if prm["is_update_latest_time"]:
            self.latest_time = utils.utcnow()
            await self.play.guild.me.edit(nick=f"{self.now_mode_to_jp[self.now_mode]}中だよ～")


    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        # ミュート切替、画面共有切替等でも発火するので
        # 移動意外は除外

        if member.bot:
            return

        if (before.channel and after.channel) and (
            before.channel.id == after.channel.id
        ):
            return

        if after.channel and after.channel.id == self.sagyou_vc_id:
            if len(after.channel.members) == 1 or (
                not self.play and self.bot.is_debug_mode
            ):
                self.bot.dispatch("first_join", member, after)
            else:
                self.bot.dispatch("join_member", member, after)

        elif before.channel and before.channel.id == self.sagyou_vc_id:
            self.bot.dispatch("leave", member, before, after)

    @commands.Cog.listener()
    @excepter
    async def on_first_join(self, member: Member, after: VoiceState):
        """
        ①該当のボイスチャンネルに誰かが入ったら、BOTがチャンネルに入る
        ②BOTがチャンネルに入ったら、タイムキーパーを担当させて貰う旨と共に挨拶を行う。

        Parameters
        ----------
        member : Member
            VCに参加したメンバー
        before : VoiceState
            _description_
        after : VoiceState
            _description_
        """

        if not after.channel:
            return

        guild = after.channel.guild

        if not self.play and guild.voice_client:
            try:
                await guild.voice_client.disconnect(force=True)
            except Exception:
                raise PomoERROR.FailedDisConnect()

        self.play = await after.channel.connect(cls=PomoPlay)  # type: ignore

        # timekeeperを抽選
        await self.pomo.timekeeper.get_name()
        await self.pomo.timekeeper.get_info()

        if not self.pomo.timekeeper.info:
            raise PomoERROR.NotFoundATimekeeperInfo()

        # timekeeperのあいさつ文を投稿
        notice_channel: TextChannel = self.bot.get_channel(self.notice_channel_id)  # type: ignore
        await notice_channel.send(self.pomo.timekeeper.info["profile"])

        # 初回挨拶DL・再生

        await self.pomo.download.all(
            timekeeper=self.pomo.timekeeper, only_categories=(config.GREETING_CATEGORY,)
        )
        await self.pomo.download.send.download_embed(POMO_DEBUG_CHANNEL_ID, "初回挨拶")
        filename = self.pomo.download.get_filename(config.GREETING_CATEGORY)
        await self.play.greeting(filename)
        await self.pomo.download.send.play_embed(POMO_DEBUG_CHANNEL_ID, "初回挨拶")
        
        async def edit_nick():
            if not self.play:
                return
            await self.play.wait_play()
            await member.guild.me.edit(nick="作業中だよ～")
            
        self.bot.loop.create_task(edit_nick())
        
        await self.pomo.download.all(
            timekeeper=self.pomo.timekeeper,
            ignore_categories=(config.GREETING_CATEGORY,),
        )
        await self.pomo.download.send.download_embed(
            POMO_DEBUG_CHANNEL_ID, "全て(初回挨拶以外)"
        )

        # while self.vclient.is_playing():
        #     await asyncio.sleep(1)

        self.speak.start()
        self.latest_time = utils.utcnow()
        self.now_mode = "work_time"

        # 全ファイルをDL

    @commands.Cog.listener()
    @excepter
    async def on_join_member(self, member: Member, after: VoiceState):
        if not after.channel:
            return

        if not self.play:
            return

        await self.pomo.download.events.wait_all_download()

        file_name = self.pomo.download.get_filename(config.JOIN_MEMBER_CATEGORY)

        await self.play.join_member(file_name)

    @commands.Cog.listener()
    @excepter
    async def on_leave(self, member: Member, before: VoiceState, after: VoiceState):
        """
        作業通話から誰もいなくなったらBOTを切断する

        Parameters
        ----------
        member : Member
            VCに参加したメンバー
        before : VoiceState
            _description_
        after : VoiceState
            _description_
        """

        # ミュート切替、画面共有切替等でも発火するので
        # 移動意外は除外
        if (before.channel and after.channel) and (
            before.channel.id == after.channel.id
        ):
            return

        if not before.channel:
            return

        if not self.play:
            return

        humans = [member for member in before.channel.members if not member.bot]

        if humans:
            return

        channel = self.bot.get_channel(LEAVE_CHANNEL_ID)

        if not isinstance(channel, TextChannel):
            return

        if timekeeper_info := self.pomo.timekeeper.info:
            message = timekeeper_info.get("leave", "またね～")
        else:
            message = "またね～"

        await channel.send(message)

        await self.play.disconnect(force=True)

        self.play = None
        self.latest_time = None
        self.now_mode = None
        self.pomo.clear()
        self.speak.cancel()

    @commands.command(name="デバッグ切替")
    @excepter
    async def change_debug_mode(
        self, ctx: commands.Context, enable: bool | None = None
    ):
        if enable is None:
            self.bot.is_debug_mode = not self.bot.is_debug_mode
        else:
            self.bot.is_debug_mode = enable

        await ctx.send(f"デバッグモード{self.bot.is_debug_mode}に変更したよ")

    @commands.command(name="退出")
    async def disconnect(self, ctx: commands.Context):
        if not ctx.guild:
            return

        if not ctx.guild.owner:
            return

        if ctx.author.id not in [ctx.guild.owner.id, 386289367955537930]:
            return

        if not self.play:
            return

        await self.play.disconnect(force=True)

        self.play = None
        self.latest_time = None
        self.now_mode = None
        self.pomo.clear()
        self.speak.cancel(
        )


class MockVoiceChannel(BaseModel):
    id: int


class MockVoiceState(BaseModel):
    channel: MockVoiceChannel = MockVoiceChannel(id=1)


class AdminPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.voice_client: PomoPlay

    @ui.button(label="入室", style=ButtonStyle.green, custom_id="pomo-join")
    async def join(self, interaction: Interaction, _):
        await interaction.response.defer()

        if not isinstance(interaction.user, Member):
            return

        interaction.client.dispatch(
            "first_join", interaction.user, interaction.user.voice
        )


async def setup(bot: Main):
    await bot.add_cog(PomodoroTimerCog(bot))
