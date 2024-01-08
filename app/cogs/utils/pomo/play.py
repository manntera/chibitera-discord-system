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

    async def __play(self, category_id: int):
        while self.is_playing():
            await asyncio.sleep(1)

        self.play(FFmpegPCMAudio(f"voices/{category_id:03}.wav"))

    async def greeting(self):
        await self.__play(1)

    async def before_work_time(self):
        await self.__play(2)

    async def work_time(self):
        await self.__play(3)

    async def before_break_time(self):
        await self.__play(4)

    async def break_time(self):
        await self.__play(5)

    async def join_member(self):
        await self.__play(6)
