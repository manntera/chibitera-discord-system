from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal, TypedDict

import config
from discord import (
    ButtonStyle,
    Color,
    Embed,
    FFmpegPCMAudio,
    Interaction,
    Member,
    TextChannel,
    VoiceChannel,
    VoiceClient,
    VoiceState,
    ui,
    utils,
)
from discord.ext import commands, tasks
from google.cloud import storage

from .utils import excepter

if TYPE_CHECKING:
    from main import Main

class __TActors(TypedDict):
    name: str

class TActors(TypedDict):
    actor_info: list[__TActors]
    
class __TActor_Voices(TypedDict):
    category: str
    id_list: list[str]
    
class TActor(TypedDict):
    actor_name: str
    profile: str
    leave: str
    voice_list: list[__TActor_Voices]
    
    
class NotFoundActorJson(Exception):
    def __init__(self, timekeeper_name: str):
        super().__init__()
        self.message = f"{timekeeper_name}の`actor.json`が見つかりませんでした"

class NotFoundActorListJson(Exception):
    def __init__(self):
        super().__init__()
        self.message = f"actorlist.jsonが見つかりませんでした"

class NotFoundVoice(Exception):
    def __init__(self, timekeeper_name: str, voice_id: str):
        super().__init__()
        self.message = f"`{timekeeper_name}`の`{voice_id}`が見つかりませんでした"

BUCKET_NAME = "pomodorotimer"
PATH_ACTORLIST_JSON = "actors/actorlist.json"
PATH_ACTOR_JSON = "actors/{timekeeper_name}/actor.json"
PATH_ACTOR_VOICE_FILE_NAME = "actors/{timekeeper_name}/{voice_id}.wav" # actor.jsonのid_listから取得したボイスIDのファイルを取得
PATH_PLAY_VOICE_FILE_NAME = "voice.wav" # 動作環境上に保存されたボイスファイル(これを再生)


class GCStorageClient:
    def __init__(self, bot: Main):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)

        self.bot = bot
        self.debug_channel: TextChannel = self.bot.get_channel(config.POMO_DEBUG_CHANNEL_ID) # type: ignore

        # DEBUG_MODE有効時、DEBUG_CHANNEL_IDが不正な値だったら、起動時にエラーが出る
        if bot.is_debug_mode and not isinstance(self.debug_channel, TextChannel):
            raise Exception(f"debug channelはテキストチャンネルである必要があります {self.debug_channel=}")
    
    async def get_timekeeper_name(self) -> str:
        """タイムキーパーをランダムに一人取得する

        Returns
        -------
        str | None
            タイムキーパーの名前
        """
        _actors_file = self.bucket.get_blob(PATH_ACTORLIST_JSON)
        
        if not _actors_file:
            if not self.bot.is_debug_mode:
                raise NotFoundActorListJson()
            
            e = Embed(
                title="NOT FOUND actorlist.json",
                description=f"`{PATH_ACTORLIST_JSON}`が見つかりません",
                color=Color.red()
            )
            
            await self.debug_channel.send(embeds=[e])
            raise NotFoundActorListJson()
        
        #ダウンロードせずにファイルの中身を文字列で取得
        actor_file = await asyncio.to_thread(_actors_file.download_as_text, encoding="utf-8")
        
        actors_info: TActors = json.loads(actor_file)
        
        actors = actors_info["actor_info"]
        
        return (random.choice(actors))["name"]
    
    async def __send_not_found_actor_json(self, timekeeper_name: str) -> None:
        if not self.bot.is_debug_mode:
            return

        e = Embed(
            title="NOT FOUND actor.json",
            description=f"{PATH_ACTOR_JSON.format(timekeeper_name=timekeeper_name)}が見つかりません。",
            color=Color.red()
        )
        await self.debug_channel.send(embeds=[e])
        return

    async def get_timekeeper_info(self, timekeeper_name: str) -> TActor:
        """タイムキーパーの名前から名前・ボイス一覧を取得する

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        TActor | None
            _description_ : タイムキーパーの名前とボイス一覧
        """
        _actor_file = self.bucket.get_blob(PATH_ACTOR_JSON.format(timekeeper_name=timekeeper_name))
        
        if not _actor_file:
            await self.__send_not_found_actor_json(timekeeper_name)
            raise NotFoundActorJson(timekeeper_name)

        #ダウンロードせずにファイルの中身を文字列で取得
        actor_file = await asyncio.to_thread(_actor_file.download_as_text, encoding="utf-8")
        
        actor_info: TActor = json.loads(actor_file)        
        return actor_info
    
    async def __download_voice_file(self, timekeeper_name: str, voice_id: str) -> None:
        """指定したボイスIDのファイルをダウンロードする

        Parameters
        ----------
        timekeeper_name : str
            タイムキーパーの名前
        voice_id : str
            ボイスID

        Returns
        -------
        _type_
            ダウンロードするだけなので戻り値無し
        """
        
        voice_blob = self.bucket.get_blob(PATH_ACTOR_VOICE_FILE_NAME.format(timekeeper_name=timekeeper_name, voice_id=voice_id))
        
        if not voice_blob:
            if not self.bot.is_debug_mode:
                raise NotFoundVoice(timekeeper_name, voice_id)
            
            e = Embed(
                title="NOT FOUND actor voice file",
                description=f"{PATH_ACTOR_VOICE_FILE_NAME.format(timekeeper_name=timekeeper_name, voice_id=voice_id)}が見つかりません。",
                color=Color.red()
            )
            await self.debug_channel.send(embeds=[e])
            
            raise NotFoundVoice(timekeeper_name, voice_id)

        #ダウンロードせずにファイルの中身を文字列で取得
        await asyncio.to_thread(voice_blob.download_to_filename, filename="voice.wav")
        return None


    async def download_voice_file(self, index: int, timekeepeer_name: str) -> tuple[int, str, str]:
        """actor.jsonのid_listから一つボイスIDを取得し、ダウンロードする

        Parameters
        ----------
        index : int
            "001 ~ 006までのindex"
        timekeepeer_name : str
            ボイスファイルを取得するタイムキーパーの名前

        Raises
        ------
        NotFoundActorJson
            actor.jsonが無かった場合
            
        Returns
        -------
        None
            ダウンロードするだけなので戻り値無し
        """
        
        actor_info = await self.get_timekeeper_info(timekeepeer_name)
        
        voices = actor_info["voice_list"][index]["id_list"]
        # idリストからランダムに取得
        voice_id = random.choice(voices)

        await self.__download_voice_file(timekeepeer_name, voice_id)
        return index, actor_info["voice_list"][index]["category"], voice_id


    async def download_greeting_voice(self, timekeeper_name: str) -> tuple[int, str, str]:
        """タイムキーパーの挨拶ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """
        
        return await self.download_voice_file(0, timekeeper_name)
    
    async def download_before_complete_of_work_voice(self, timekeeper_name: str) -> tuple[int, str, str]:
        """作業終了前ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """
        
        return await self.download_voice_file(1, timekeeper_name)


    async def download_complete_of_work_voice(self, timekeeper_name: str) -> tuple[int, str, str]:
        """作業終了(休憩開始)ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """
        
        return await self.download_voice_file(2, timekeeper_name)


    async def download_before_complete_of_break_voice(self, timekeeper_name: str) -> tuple[int, str, str]:
        """休憩終了前ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """
        
        return await self.download_voice_file(3, timekeeper_name)


    async def download_complete_of_break_voice(self, timekeeper_name: str) -> tuple[int, str, str]:
        """休憩終了(作業開始)ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """
        
        return await self.download_voice_file(4, timekeeper_name)
    
    
    async def download_join_voice(self, timekeeper_name: str) -> None:
        """2人目以降入室ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """
        
        await self.download_voice_file(5, timekeeper_name)



class PomodoroTimerClient(VoiceClient):
    def __init__(self, bot: Main, voice_channel: VoiceChannel):
        super().__init__(bot, voice_channel)
        
        self.bot = bot
        
        self.timekeeper: str
        
        
    def play(self):
        super().play(FFmpegPCMAudio(PATH_PLAY_VOICE_FILE_NAME))


class PomodoroTimer(commands.Cog):
    def __init__(self, bot: Main):
        self.bot = bot
        
        self.sagyou_vc_id: int = config.SAGYOU_CHANNEL_ID #type: ignore
        self.notice_channel_id: int = config.NOTICE_CHANNEL_ID #type: ignore

        self.gcloud = GCStorageClient(bot)
        self.latest_time: datetime | None = None
        self.now_mode: Literal["before_work", "work", "before_break", "break"] | None = None
        self.vclient: PomodoroTimerClient | None = None
        
        #self.speak.start()
        
        self.admin_panel_view = AdminPanelView()
        
        self.bot.add_view(self.admin_panel_view)
        
        
        self.voice_dict = {
            "before_work": {
                "desc": "作業終了前",
                "download_func": None,
                "timedelta": {
                    "minutes": 2 # 作業終了3分前
                },
                "next_mode": "work",
                "debug_message": "作業終了予告ボイス再生完了",
                "is_update_latest_time": False
            },
            "work": {
                "desc": "作業終了",
                "download_func": None,
                "timedelta": {
                    "minutes": 5 # 作業終了(作業時間X分)
                },
                "next_mode": "before_break",
                "debug_message": "作業終了ボイス再生完了",
                "is_update_latest_time": True
            },
            "before_break": {
                "desc": "休憩終了前",
                "download_func": None,
                "timedelta": {
                    "minutes": 2 # 休憩終了3分前
                },
                "next_mode": "break",
                "debug_message": "休憩終了予告ボイス再生完了",
                "is_update_latest_time": False
            },
            "break": {
                "desc": "休憩終了",
                "download_func": None,
                "timedelta": {
                    "minutes": 5 # 休憩終了(休憩時間X分)
                },
                "next_mode": "before_work",
                "debug_message": "休憩終了ボイス再生完了",
                "is_update_latest_time": True
            },
            
            
        }
        
        
    async def cog_load(self) -> None:
        self.speak.start()
    async def cog_unload(self) -> None:
        self.speak.cancel()
        self.admin_panel_view.stop()
        
    
    async def send_debug(self, *messages) -> None:
        if not self.bot.is_debug_mode:
            return
        
        debug_channel = self.bot.get_channel(config.POMO_DEBUG_CHANNEL_ID)
        
        if not isinstance(debug_channel, TextChannel):
            return None
        
        e = Embed(
            description=" ".join(message for message in messages),
            color=Color.from_str("#85d0f3")
        )
        
        await debug_channel.send(embeds=[e])
        return None


    @tasks.loop(seconds=10)
    @excepter
    async def speak(self):
        await self.bot.wait_until_ready()
        
        if not self.latest_time or not self.now_mode or not self.vclient:
            return
    
        now = utils.utcnow()

        prm = self.voice_dict[self.now_mode]
        
        if self.latest_time + timedelta(**prm["timedelta"]) >= now:
            return
        
        self.now_mode = prm["next_mode"]
        try:
            index, category, voice_id = await prm["download_func"](self.vclient.timekeeper)
        except NotFoundActorJson:
            return
        
        debug_message = prm["debug_message"]

        # エラーが出たとき5回トライする
        # 5回トライしてエラーが出たら諦める
        
        for _ in range(5):
            try:
                self.vclient.play()
                break
            except Exception:
                await asyncio.sleep(1)

        debug_message += f"\n\n{index=}"
        debug_message += f"\n{category=}"
        debug_message += f"\n{voice_id=}"
        debug_message += f"\n\n{now=}"
                
        await self.send_debug(debug_message)


    async def _on_join(self, before: VoiceState | None, after: VoiceState):
        #ミュート切替、画面共有切替等でも発火するので
        #移動意外は除外
        if before and (before.channel and after.channel) and (before.channel.id == after.channel.id):
            return
        
        if not after.channel:
            return
        
        guild = after.channel.guild
        
        if not guild:
            return
        
        if after.channel.id != self.sagyou_vc_id:
            return
        
        humans = [member for member in after.channel.members if not member.bot]
        
        if len(humans) >= 2 and self.vclient and not self.vclient.is_playing():
            try:
                await self.gcloud.download_join_voice(self.vclient.timekeeper)
            except NotFoundActorJson:
                return

            self.vclient.play()
            return
        
        elif not humans:
            return
        
        if not self.vclient and guild.voice_client:
            try:
                await guild.voice_client.disconnect(force=True)
            except:
                raise
        
        self.vclient = await after.channel.connect(cls=PomodoroTimerClient) #type: ignore
        timekeeper_name = await self.gcloud.get_timekeeper_name()

        if not timekeeper_name:
            return
        
        self.vclient.timekeeper = timekeeper_name
        
        timekeeper = await self.gcloud.get_timekeeper_info(timekeeper_name)
        
        if not timekeeper:
            return
        
        notice_channel = self.bot.get_channel(self.notice_channel_id)
        
        if not notice_channel:
            return
        
        if not isinstance(notice_channel, TextChannel):
            return
        
        await notice_channel.send(timekeeper["profile"])

        await self.gcloud.download_greeting_voice(timekeeper_name)
        self.vclient.play()

        # while self.vclient.is_playing():
        #     await asyncio.sleep(1)
        
        self.latest_time = utils.utcnow()
        self.now_mode = "before_work"
    

    @commands.Cog.listener()
    @excepter
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        #ミュート切替、画面共有切替等でも発火するので
        #移動意外は除外

        if after.channel and after.channel.id == self.sagyou_vc_id:
            self.bot.dispatch("join", member, before, after)
        
        elif before.channel and before.channel.id == self.sagyou_vc_id:
            self.bot.dispatch("leave", member, before, after)
        
        
    @commands.Cog.listener()
    @excepter
    async def on_join(self, member: Member, before: VoiceState, after: VoiceState):
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
        
        if member.bot:
            return

        await self._on_join(before, after)


    @commands.Cog.listener()
    @excepter
    async def on_leave(self, member: Member, before: VoiceState, after: VoiceState | None):
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
        
        #ミュート切替、画面共有切替等でも発火するので
        #移動意外は除外
        if after and (before.channel and after.channel) and (before.channel.id == after.channel.id):
            return

        if not before.channel:
            return
        
        if not self.vclient:
            return
        
        humans = [member for member in before.channel.members if not member.bot]
        
        if humans:
            timekeeper = await self.gcloud.get_timekeeper_info(self.vclient.timekeeper)
            
            channel = self.bot.get_channel(config.LEAVE_CHANNEL_ID)

            if not isinstance(channel, TextChannel):
                return
            await channel.send(timekeeper.get("leave") or f"またね～")

            return
        
        await self.vclient.disconnect(force=True)
        
        self.vclient = None
        self.latest_time = None
        self.now_mode = None
    

    @commands.command(name="デバッグ切替")
    @excepter
    async def change_debug_mode(self, ctx: commands.Context, enable: bool | None = None):
        if enable is None:
            self.bot.is_debug_mode = not self.bot.is_debug_mode
        else:
            self.bot.is_debug_mode = enable
        
        await ctx.send(f"デバッグモード{self.bot.is_debug_mode}に変更したよ")
        
    
        


class AdminPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @ui.button(label="入室", style=ButtonStyle.green, custom_id="pomo-join")
    async def join(self, interaction: Interaction, _):
        await interaction.response.defer()
        
        if not isinstance(interaction.user, Member):
            return
        
        interaction.client.dispatch("join", None, interaction.user.voice)
            
    @ui.button(label="退出", style=ButtonStyle.red, custom_id="pomo-leave")
    async def leave(self, interaction: Interaction, _):
        await interaction.response.defer()
        
        if not isinstance(interaction.user, Member):
            return
        
        interaction.client.dispatch("leave", interaction.user.voice, None)
            
    

async def setup(bot: Main):
    await bot.add_cog(PomodoroTimer(bot))
