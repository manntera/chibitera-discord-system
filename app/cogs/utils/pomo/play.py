from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from discord import FFmpegPCMAudio, VoiceChannel, VoiceClient

if TYPE_CHECKING:
    from main import Main


class Play(VoiceClient):
    def __init__(self, bot: Main, voice_channel: VoiceChannel):
        super().__init__(bot, voice_channel)

        self.bot = bot
        self.played = asyncio.Event()

    async def wait_play(self) -> None:
        await self.played.wait()

    def setplayed(self, _) -> None:
        self.played.set()

    async def __play(self, filename: str):
        self.played.clear()
        while self.is_playing():
            await asyncio.sleep(1)

        source = FFmpegPCMAudio(filename)
        source.read()

        self.play(source, after=self.setplayed)

    async def greeting(self, filename: str):
        await self.__play(filename)

    async def before_work_time(self, filename: str):
        await self.__play(filename)

    async def work_time(self, filename: str):
        await self.__play(filename)

    async def before_break_time(self, filename: str):
        await self.__play(filename)

    async def break_time(self, filename: str):
        await self.__play(filename)

    async def join_member(self, filename: str) -> None:
        await self.__play(filename)
