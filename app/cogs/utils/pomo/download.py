from __future__ import annotations

import asyncio
import logging
import os
import random
import shutil

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
from .types import NowVoiceInfo, TActor

__all__ = ("Download",)


class Download:
    def __init__(self, bot, bucket: storage.Bucket):
        self.bot = bot
        self.bucket = bucket

    async def all(self, timekeeper: TActor):
        """タイムキーパーのVoiceFileを全てDLする"""

        timekeeper_name = timekeeper["actor_name"]

        voice_list = timekeeper["voice_list"]
        files: list[storage.Blob] = self.bucket.list_blobs(prefix=timekeeper_name)

        for _file in files:
            if not _file.name:
                continue

            _file_name = _file.name.split("/")[-1]  # フォルダー名を除外
            file_name = _file.name.split(".")[0]  # 拡張子を除外 voice_idのみを取得

            if _file_name.endswith(".wav"):
                continue

            await asyncio.to_thread(
                _file.download_to_filename, filename=f"voices/{file_name}.wav"
            )
            logging.info("download: ", file_name)

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

        return await self.voice_file(JOIN_MEMBER_INDEX, timekeeper)

    def clear(self):
        shutil.rmtree("voices/")
