from __future__ import annotations

import asyncio
import glob
import logging
import os
import random
import shutil
from typing import TYPE_CHECKING

import discord
from config import (
    BEFORE_COMPLETE_OF_BREAK_INDEX,
    BEFORE_COMPLETE_OF_WORK_INDEX,
    COMPLETE_OF_BREAK_INDEX,
    COMPLETE_OF_WORK_INDEX,
    GREETING_INDEX,
    JOIN_MEMBER_INDEX,
    PATH_ACTOR_VOICE_FILE_NAME,
)
from google.cloud import storage

from .error import NotFoundVoice
from .timekepper import Timekeeper
from .types import NowVoiceInfo

if TYPE_CHECKING:
    from main import Main

__all__ = ("Download",)


class Download:
    def __init__(self, bot: Main, bucket: storage.Bucket):
        self.bot = bot
        self.bucket = bucket
        self.events = Events()
        self.send = Send(bot)

    def get_filename(self, category_id: str, is_random: bool = True) -> str:
        files = glob.glob(f"voices/{category_id}/*.mp3")

        if is_random:
            return random.choice(files)
        return files[0]

    async def all(
        self,
        timekeeper: Timekeeper,
        ignore_categories: tuple[str, ...] = (),
        only_categories: tuple[str, ...] = (),
    ):
        """タイムキーパーのVoiceFileを全てDLする"""
        self.events.is_all_download.clear()

        timekeeper_name = timekeeper.name

        if not timekeeper_name or not timekeeper.info:
            return

        if ignore_categories and only_categories:
            raise Exception("除外カテゴリーとカテゴリー指定が両立してます。どちらかにしてください.")

        voice_list = timekeeper.info["voice_list"]
        prefix = f"actors/{timekeeper_name}"
        print("======== DOWNLOAD START =============")
        print(f"         {prefix}  ")
        files: list[storage.Blob] = self.bucket.list_blobs(prefix=prefix)

        def get_category(file_name: str) -> str | None:
            for data in voice_list:
                if not data.get("id_list", []):
                    continue

                if file_name in data["id_list"]:
                    return data["category"]
            return None

        if not os.path.exists("voices"):
            os.makedirs("voices")

        for _file in files:
            if not _file.name:
                continue

            _file_name = _file.name.split("/")[-1]  # フォルダー名を除外
            file_name = _file_name.split(".")[0]  # 拡張子を除外 voice_idのみを取得

            if file_name.endswith(".mp3"):
                continue

            if not (category := get_category(file_name)):
                continue

            if ignore_categories:
                if category in ignore_categories:
                    continue
            if only_categories:
                if category not in only_categories:
                    continue

            if not os.path.exists(f"voices/{category}"):
                os.mkdir(f"voices/{category}")

            await asyncio.to_thread(
                _file.download_to_filename,
                filename=f"voices/{category}/{file_name}.mp3",
            )
            print("download: ", category, " - ", file_name)

        self.events.is_all_download.set()

        return voice_list

    async def __voice_file(
        self, timekeeper_name: str, voice_id: str, category_id: str
    ) -> None:
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

        voice_blob = self.bucket.get_blob(
            PATH_ACTOR_VOICE_FILE_NAME.format(
                timekeeper_name=timekeeper_name, voice_id=voice_id
            )
        )

        if not voice_blob:
            if not self.bot.is_debug_mode:
                raise NotFoundVoice(timekeeper_name, voice_id)

            e = discord.Embed(
                title="NOT FOUND actor voice file",
                description=f"{PATH_ACTOR_VOICE_FILE_NAME.format(timekeeper_name=timekeeper_name, voice_id=voice_id)}が見つかりません。",
                color=discord.Color.red(),
            )
            await self.bot.debug_channel.send(embeds=[e])

            raise NotFoundVoice(timekeeper_name, voice_id)

        if not os.path.exists("voices"):
            os.makedirs("voices")

        # ダウンロードせずにファイルの中身を文字列で取得
        await asyncio.to_thread(
            voice_blob.download_to_filename, filename=f"voices/{category_id}.wav"
        )
        return None

    async def voice_file(self, index: int, timekeeper: Timekeeper) -> NowVoiceInfo:
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
            index, 001, 001
        """

        if not timekeeper.info or not timekeeper.name:
            raise

        voices = timekeeper.info["voice_list"][index]["id_list"]
        # idリストからランダムに取得
        voice_id = random.choice(voices)
        category_id = timekeeper.info["voice_list"][index]["category"]

        await self.__voice_file(timekeeper.name, voice_id, category_id)
        return NowVoiceInfo(
            index=index,
            category_id=timekeeper.info["voice_list"][index]["category"],
            voice_id=voice_id,
        )

    async def greeting(self, timekeeper: Timekeeper) -> NowVoiceInfo:
        """タイムキーパーの挨拶ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """
        self.events.is_greeting_download.clear()

        return await self.voice_file(GREETING_INDEX, timekeeper)

    async def before_work_time(self, timekeeper: Timekeeper) -> NowVoiceInfo:
        """作業終了前ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """

        return await self.voice_file(BEFORE_COMPLETE_OF_WORK_INDEX, timekeeper)

    async def work_time(self, timekeeper: Timekeeper) -> NowVoiceInfo:
        """作業終了ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """

        return await self.voice_file(COMPLETE_OF_WORK_INDEX, timekeeper)

    async def before_break_time(self, timekeeper: Timekeeper) -> NowVoiceInfo:
        """休憩終了前ボイスをDLする

        Parameters
        ----------
        timekeeper_name : int
            タイムキーパーの名前

        Returns
        -------
        None
        """

        return await self.voice_file(BEFORE_COMPLETE_OF_BREAK_INDEX, timekeeper)

    async def break_time(self, timekeeper: Timekeeper) -> NowVoiceInfo:
        """休憩終了ボイスをDLする

        Parameters
        ----------
        timekeeper: Timekeeper
            タイムキーパーの名前

        Returns
        -------
        None
        """

        return await self.voice_file(COMPLETE_OF_BREAK_INDEX, timekeeper)

    async def join_member_voice(self, timekeeper: Timekeeper) -> NowVoiceInfo:
        """2人目以降入室ボイスをDLする

        Parameters
        ----------
        timekeeper: Timekeeper
            タイムキーパーの名前

        Returns
        -------
        None
        """

        self.events.is_join_member_download.clear()

        return await self.voice_file(JOIN_MEMBER_INDEX, timekeeper)

    def clear(self):
        shutil.rmtree("voices/")


class Events:
    def __init__(self):
        self.is_all_download = asyncio.Event()
        self.is_greeting_download = asyncio.Event()
        self.is_join_member_download = asyncio.Event()

    async def wait_all_download(self) -> None:
        await self.is_all_download.wait()

    async def wait_greeting_download(self) -> None:
        await self.is_greeting_download.wait()

    async def wait_join_member_download(self) -> None:
        await self.is_join_member_download.wait()


class Send:
    def __init__(self, bot: Main):
        self.bot = bot

    def get_debug_channel(self, channel_id: int) -> discord.TextChannel | None:
        if not self.bot.is_debug_mode:
            return None

        channel = self.bot.get_channel(channel_id)

        if not isinstance(channel, discord.TextChannel):
            return None

        return channel

    async def download_embed(self, debug_channel_id: int, voice_type: str) -> None:
        e = discord.Embed(
            title="Download",
            description=f"{voice_type}DL完了",
            color=discord.Color.yellow(),
            timestamp=discord.utils.utcnow(),
        )
        debug_channel = self.get_debug_channel(debug_channel_id)
        if debug_channel:
            await debug_channel.send(embeds=[e])

    async def play_embed(self, debug_channel_id: int, voice_type: str) -> None:
        e = discord.Embed(
            title="Play",
            description=f"{voice_type}再生完了",
            color=discord.Color.from_str("#85d0f3"),
            timestamp=discord.utils.utcnow(),
        )
        debug_channel = self.get_debug_channel(debug_channel_id)
        if debug_channel:
            await debug_channel.send(embeds=[e])
