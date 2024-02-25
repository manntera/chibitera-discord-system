import asyncio
import json
import random

import discord
from config import PATH_ACTOR_JSON, PATH_ACTORLIST_JSON
from google.cloud import storage

from .error import NotFoundActorJson, NotFoundActorListJson, send_not_found_actor_json
from .types import TActor, TActors

__all__ = ("Timekeeper",)


class Timekeeper:
    def __init__(self, bot, bucket: storage.Bucket):
        self.bot = bot
        self.bucket = bucket
        self.name: str | None = None
        self.info: TActor | None = None

    async def get_name(self) -> None:
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

            e = discord.Embed(
                title="NOT FOUND actorlist.json",
                description=f"`{PATH_ACTORLIST_JSON}`が見つかりません",
                color=discord.Color.red(),
            )

            await self.bot.debug_channel.send(embeds=[e])
            raise NotFoundActorListJson()

        # ダウンロードせずにファイルの中身を文字列で取得
        actor_file = await asyncio.to_thread(
            _actors_file.download_as_text, encoding="utf-8"
        )

        actors_info: TActors = json.loads(actor_file)

        actors = actors_info["actor_info"]

        self.name = (random.choice(actors))["name"]

    async def get_info(self) -> None:
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

        if not self.name:
            raise

        _actor_file = self.bucket.get_blob(
            PATH_ACTOR_JSON.format(timekeeper_name=self.name)
        )

        if not _actor_file:
            await send_not_found_actor_json(self.bot, self.name)
            raise NotFoundActorJson(self.name)

        # ダウンロードせずにファイルの中身を文字列で取得
        actor_file = await asyncio.to_thread(
            _actor_file.download_as_text, encoding="utf-8"
        )

        actor_info: TActor = json.loads(actor_file)
        self.info = actor_info

    def clear(self):
        self.name = None
        self.info = None
