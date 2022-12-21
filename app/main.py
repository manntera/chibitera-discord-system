import os
import discord
from demo import keep_alive


def exit(msg: str) -> None:
    """
    処理を中断する時に実行される関数

    Parameters
    ----------
    msg: str
        終了する時に出力するメッセージ

    Returns
    -------
    None

    """
    print(msg)
    import sys

    sys.exit()


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

AUTH_MESSAGE_ID = 744216836173725846

REACTION_TO_ROLE = {
    744209790837850122: 587175233899724801,  # デザイナー
    744209790661820438: 587175050571022337,  # プログラマー
    832489218546335764: 832617526005071923,  # サウンド
    797122177794441248: 797121076827258890,  # VTUBER
}

TOKEN = os.getenv("DISCORD_TOKEN_SECRET")

# システム環境変数にTOKENが見つからなかった時に.envから読み取るようにする
# .envに記載が無い時も処理を中断
# .envにXX="YY"と記載したとき、XXが変数名になる
# TOKEN = os.getenv('XX')と記載したらYYを取得できる

# XX is Noneとnot XXは同じ


if not TOKEN:
    from dotenv import load_dotenv

    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN_SECRET")
    print(".envからTOKENを取得しました。")

    if not TOKEN:
        exit("TOKENが見つからなかったため、処理を中断しました。")


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    await message.channel.send(message.content)
    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # リアクションを付けたメッセージのIDが指定したものじゃなければ処理を中断
    if payload.message_id != AUTH_MESSAGE_ID:
        return

    # GUILDオブジェクトを取得
    guild = client.get_guild(payload.guild_id)
    # GuildChannelオブジェクトを取得
    channel = guild.get_channel(payload.channel_id)
    # Messageオブジェクトを取得
    message = await channel.fetch_message(payload.message_id)

    # カスタム絵文字じゃ無かったらそれ以降処理しない
    if not payload.emoji.is_custom_emoji():
        return

    # 押されたリアクションのIDが辞書のキーにあるか調べる
    # もしあれば、対応したロールIDを取得する
    if not (role_id := REACTION_TO_ROLE.get(payload.emoji.id)):
        return

    # 取得したロールIDからロールオブジェクトを取得
    role = guild.get_role(role_id)

    if not role:
        print(f"{role_id} がサーバーに見つかりませんでした。")
        return

    # たまーにpayload.memberがNoneになることがある
    # Noneになったらリアクションを押したユーザーのIDを元にサーバーに入ってるメンバー一覧から押したユーザーを取得する
    if not (member := payload.member):
        member = guild.get_member(payload.user_id)

    # 取得したロールをリアクションを押したメンバーに付与する
    await member.add_roles(role)

    # リアクションを削除
    await message.remove_reaction(payload.emoji, member)

keep_alive()
client.run(TOKEN)
