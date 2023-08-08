from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal, TypedDict

import config
from discord import (
    FFmpegPCMAudio,
    Member,
    TextChannel,
    VoiceChannel,
    VoiceClient,
    VoiceState,
    utils,
)
from discord.ext import commands, tasks
from google.cloud import storage

if TYPE_CHECKING:
    from main import Main

class __TActors(TypedDict):
    id: str

class TActors(TypedDict):
    actor_info: list[__TActors]
    
class __TActor_Voices(TypedDict):
    category: str
    id_list: list[str]
    
class TActor(TypedDict):
    actor_name: str
    profile: str
    voice_list: list[__TActor_Voices]
    
    
class NotFoundActorJson(Exception):
    def __init__(self, timekeeper_id: str):
        super().__init__()
        self.message = f"{timekeeper_id}の`actor.json`が見つかりませんでした"


class GCStorageClient:
    def __init__(self, bot: Main):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket("pomodorotimer")

        self.bot = bot
    
    async def get_timekeeper_id(self) -> str | None:
        """タイムキーパーをランダムに一人取得する

        Returns
        -------
        int | None
            タイムキーパーのID
        """
        _actors_file = self.bucket.get_blob("actors/actorlist.json")
        
        if not _actors_file:
            print("not actors file")
            return None
        
        #ダウンロードせずにファイルの中身を文字列で取得
        actor_file = await asyncio.to_thread(_actors_file.download_as_text, encoding="utf-8")
        
        actors_info: TActors = json.loads(actor_file)
        
        actors = actors_info["actor_info"]
        
        return (random.choice(actors))["id"]


    async def get_timekeeper_info(self, timekeeper_id: str) -> TActor | None:
        """タイムキーパーのIDから名前・ボイス一覧を取得する

        Parameters
        ----------
        timekeeper_id : int
            タイムキーパーのID

        Returns
        -------
        TActor | None
            _description_ : タイムキーパーの名前とボイス一覧
        """
        _actor_file = self.bucket.get_blob(f"actors/actor{timekeeper_id}/actor.json")
        
        if not _actor_file:
            return None
        
        #ダウンロードせずにファイルの中身を文字列で取得
        actor_file = await asyncio.to_thread(_actor_file.download_as_text, encoding="utf-8")
        
        actor_info: TActor = json.loads(actor_file)        
        return actor_info
    
    async def get_timekeeper_icon(self, timekeeper_id: str) -> bytes | None:
        """タイムキーパーのアイコンを取得する

        Parameters
        ----------
        timekeeper_id : int
            タイムキーパーのID

        Returns
        -------
        bytes | None
            画像のバイト
        """
        _actor_icon = self.bucket.get_blob(f"actors/actor{timekeeper_id}/icon.png")
        
        if not _actor_icon:
            return None
        
        #ダウンロードせずにファイルの中身を文字列で取得
        actor_icon = await asyncio.to_thread(_actor_icon.download_as_bytes)
        return actor_icon


    async def __download_voice_file(self, timekeeper_id: str, voice_id: str):
        voice_blob = self.bucket.get_blob(f"actors/actor{timekeeper_id}/{voice_id}.wav")
        
        if not voice_blob:
            return None
        
        #ダウンロードせずにファイルの中身を文字列で取得
        await asyncio.to_thread(voice_blob.download_to_filename, filename="voice.wav")
        return None


    async def download_voice_file(self, index: int, timekeepeer_id: str):
        actor_info = await self.get_timekeeper_info(timekeepeer_id)
        
        if not actor_info:
            raise NotFoundActorJson(timekeepeer_id)
        
        voices = actor_info["voice_list"][index]["id_list"]
        # idリストからランダムに取得
        voice_id = random.choice(voices)

        await self.__download_voice_file(timekeepeer_id, voice_id)


    async def download_greeting_voice(self, timekeeper_id: str) -> None:
        """タイムキーパーの挨拶ボイスをDLする

        Parameters
        ----------
        timekeeper_id : int
            タイムキーパーのID

        Returns
        -------
        None
        """
        
        await self.download_voice_file(0, timekeeper_id)
    
    
    async def download_first_work_voice(self, timekeeper_id: str) -> None:
        """初回作業開始ボイスをDLする

        Parameters
        ----------
        timekeeper_id : int
            タイムキーパーのID

        Returns
        -------
        None
        """
        
        await self.download_voice_file(1, timekeeper_id)
    
    
    async def download_before_complete_of_work_voice(self, timekeeper_id: str) -> None:
        """作業終了前ボイスをDLする

        Parameters
        ----------
        timekeeper_id : int
            タイムキーパーのID

        Returns
        -------
        None
        """
        
        await self.download_voice_file(2, timekeeper_id)


    async def download_complete_of_work_voice(self, timekeeper_id: str) -> None:
        """作業終了(休憩開始)ボイスをDLする

        Parameters
        ----------
        timekeeper_id : int
            タイムキーパーのID

        Returns
        -------
        None
        """
        
        await self.download_voice_file(3, timekeeper_id)


    async def download_before_complete_of_break_voice(self, timekeeper_id: str) -> None:
        """休憩終了前ボイスをDLする

        Parameters
        ----------
        timekeeper_id : int
            タイムキーパーのID

        Returns
        -------
        None
        """
        
        await self.download_voice_file(4, timekeeper_id)


    async def download_complete_of_break_voice(self, timekeeper_id: str) -> None:
        """休憩終了(作業開始)ボイスをDLする

        Parameters
        ----------
        timekeeper_id : int
            タイムキーパーのID

        Returns
        -------
        None
        """
        
        await self.download_voice_file(5, timekeeper_id)


class PomodoroTimerClient(VoiceClient):
    def __init__(self, bot: Main, voice_channel: VoiceChannel):
        super().__init__(bot, voice_channel)
        
        self.bot = bot
        
        self.timekeeper: str
        
    
    def play(self):
        super().play(FFmpegPCMAudio("voice.wav"))


class PomodoroTimer(commands.Cog):
    def __init__(self, bot: Main):
        self.bot = bot
        
        self.sagyou_vc_id: str = config.SAGYOU_CHANNEL_ID #type: ignore
        self.notice_channel_id: str = config.NOTICE_CHANNEL_ID #type: ignore

        self.gcloud = GCStorageClient(bot)
        self.latest_time: datetime | None = None
        self.now_mode: Literal["before_work", "work", "before_break", "break"] | None = None
        self.vclient: PomodoroTimerClient | None = None
        
        self.speak.start()
        
    async def cog_unload(self) -> None:
        self.speak.cancel()


    @tasks.loop(minutes=1)
    async def speak(self):
        await self.bot.wait_until_ready()
        
        if not self.latest_time or not self.now_mode or not self.vclient:
            return
    
        now = utils.utcnow()
        
        if self.now_mode == "before_work":
            if self.latest_time + timedelta(minutes=27) >= now:
                return
            
            self.now_mode = "work"
            
            try:
                await self.gcloud.download_before_complete_of_work_voice(self.vclient.timekeeper)
            except NotFoundActorJson:
                return
            
            print("作業終了3分前です", now)
        
        
        elif self.now_mode == "work":
            if self.latest_time + timedelta(minutes=30) >= now:
                return
            self.now_mode = "before_break"
            self.latest_time = now
            
            try:
                await self.gcloud.download_complete_of_work_voice(self.vclient.timekeeper)
            except NotFoundActorJson:
                return
            
            print("作業終了です", now)
        
        elif self.now_mode == "before_break":
            if self.latest_time + timedelta(minutes=3) >= now:
                return
            self.now_mode = "break"

            try:
                await self.gcloud.download_before_complete_of_break_voice(self.vclient.timekeeper)
            except NotFoundActorJson:
                return

        elif self.now_mode == "break":
            if self.latest_time + timedelta(minutes=5) >= now:
                return
            self.now_mode = "before_work"
            self.latest_time = now
            
            try:
                await self.gcloud.download_complete_of_break_voice(self.vclient.timekeeper)
            except NotFoundActorJson:
                return
            
            print("休憩終了です", now)
        else:
            return

        # エラーが出たとき5回トライする
        # 5回トライしてエラーが出たら諦める
        
        for _ in range(5):
            try:
                self.vclient.play()
                break
            except Exception:
                await asyncio.sleep(1)


    async def _on_join(self, before: VoiceState, after: VoiceState):
        #ミュート切替、画面共有切替等でも発火するので
        #移動意外は除外
        if (before.channel and after.channel) and (before.channel.id == after.channel.id):
            return
        
        if not after.channel:
            return
        
        guild = after.channel.guild
        
        if not guild:
            return
        
        if after.channel.id != int(self.sagyou_vc_id):
            return
        
        
        if len(after.channel.members) not in [1,2]:
            return
        
        self.vclient = await after.channel.connect(cls=PomodoroTimerClient) #type: ignore
        timekeeper_id = await self.gcloud.get_timekeeper_id()

        if not timekeeper_id:
            return
        
        self.vclient.timekeeper = timekeeper_id
        
        timekeeper = await self.gcloud.get_timekeeper_info(timekeeper_id)
        
        if not timekeeper:
            return
        
        timekeeper_icon = await self.gcloud.get_timekeeper_icon(timekeeper_id)
        
        if timekeeper_icon:
            return
                
        if not self.bot.user:
            return
        
        notice_channel = self.bot.get_channel(int(self.notice_channel_id))
        
        if not notice_channel:
            return
        
        if not isinstance(notice_channel, TextChannel):
            return
        
        await notice_channel.send(timekeeper["profile"])

        while self.vclient.is_playing():
            await asyncio.sleep(1)
        
        await self.gcloud.download_greeting_voice(timekeeper_id)
        self.vclient.play()

        while self.vclient.is_playing():
            await asyncio.sleep(1)

        await asyncio.sleep(1.5)

        await self.gcloud.download_first_work_voice(timekeeper_id)
        self.vclient.play()
        
        self.latest_time = utils.utcnow()
        self.now_mode = "before_work"
    

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        #ミュート切替、画面共有切替等でも発火するので
        #移動意外は除外

        if (before.channel and after.channel) and (before.channel.id == after.channel.id):
            return

        if after.channel and after.channel.id == int(self.sagyou_vc_id):
            self.bot.dispatch("join", member, before, after)
        
        elif before.channel and before.channel.id == int(self.sagyou_vc_id):
            self.bot.dispatch("leave", member, before, after)
        
        
    @commands.Cog.listener()
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
        
        #ミュート切替、画面共有切替等でも発火するので
        #移動意外は除外
        if (before.channel and after.channel) and (before.channel.id == after.channel.id):
            return
        
        if not before.channel:
            return
        
        if before.channel.id != int(self.sagyou_vc_id):
            return
        
        if not self.vclient:
            return
        
        members = [member for member in before.channel.members if not member.bot]
        
        if members:
            return
        
        await self.vclient.disconnect(force=True)
        
        self.vclient = None
        self.latest_time = None
        self.now_mode = None
        

async def setup(bot: Main):
    await bot.add_cog(PomodoroTimer(bot))
