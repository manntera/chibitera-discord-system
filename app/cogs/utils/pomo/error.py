import discord
from config import PATH_ACTOR_JSON


async def send_not_found_actor_json(bot, timekeeper_name: str) -> None:
    if not bot.is_debug_mode:
        return

    e = discord.Embed(
        title="NOT FOUND actor.json",
        description=f"{PATH_ACTOR_JSON.format(timekeeper_name=timekeeper_name)}が見つかりません。",
        color=discord.Color.red(),
    )
    await bot.debug_channel.send(embeds=[e])
    return


async def send_not_found_actor_voice(bot, timekeeper_name: str) -> None:
    if not bot.is_debug_mode:
        return

    e = discord.Embed(
        title="NOT FOUND actor.json",
        description=f"{PATH_ACTOR_JSON.format(timekeeper_name=timekeeper_name)}が見つかりません。",
        color=discord.Color.red(),
    )
    await bot.debug_channel.send(embeds=[e])
    return


class NotFoundActorJson(Exception):
    def __init__(self, timekeeper_name: str):
        """actor.jsonが見つからなかった時のエラー"""
        super().__init__()
        self.message = f"{timekeeper_name}の`actor.json`が見つかりませんでした"


class NotFoundActorListJson(Exception):
    def __init__(self):
        """actorlist.jsonが見つからなかった時のエラー"""
        super().__init__()
        self.message = f"actorlist.jsonが見つかりませんでした"


class NotFoundVoice(Exception):
    def __init__(self, timekeeper_name: str, voice_id: str):
        super().__init__()
        """再生しようとしたファイルが見つからなかった時のエラー"""
        self.message = f"`{timekeeper_name}`の`{voice_id}`が見つかりませんでした"


class FailedDisConnect(Exception):
    def __init__(self):
        """VCから退出する処理に失敗した時のエラー"""
        super().__init__()
        self.message = "VCから退出する処理に失敗しました"


class NotFoundATimekeeperInfo(Exception):
    def __init__(self, timekeeper=None):
        """タイムキーパーの情報を取得できなかった時のエラー"""
        super().__init__()
        self.message = f"{timekeeper.name if timekeeper else 'Unknown'}の情報が見つかりませんでした"
