from discord import RawReactionActionEvent
from discord.ext import commands


class Auth_System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.auth_message_id = 744216836173725846
        self.member_role_id = 618101618935857205

        self.reaction_to_role = {
            744209790837850122: 587175233899724801,  # デザイナー
            744209790661820438: 587175050571022337,  # プログラマー
            832489218546335764: 832617526005071923,  # サウンド
            797122177794441248: 797121076827258890,  # VTUBER
            800480624770154537: self.member_role_id,  # メンバー
        }

    @commands.Cog.listener("on_raw_reaction_add")
    async def auth_system_reaction_add(self, payload: RawReactionActionEvent):
        """リアクションが付いた時に発火するイベント
        `on_reaction_add`との違いはキャッシュに残ってないメッセージにも対応できる
        """
        # リアクションを付けたメッセージのIDが指定したものじゃなければ処理を中断
        if payload.message_id != self.auth_message_id:
            return

        # GUILDオブジェクトを取得
        guild = self.bot.get_guild(payload.guild_id)
        # GuildChannelオブジェクトを取得
        channel = guild.get_channel(payload.channel_id)
        # Messageオブジェクトを取得
        message = await channel.fetch_message(payload.message_id)

        # カスタム絵文字じゃ無かったらそれ以降処理しない
        if not payload.emoji.is_custom_emoji():
            return

        # 押されたリアクションのIDが辞書のキーにあるか調べる
        # もしあれば、対応したロールIDを取得する
        
        custom_emoji_id = payload.emoji.id
        # pylanceを黙らせる用処理
        if not custom_emoji_id:
            custom_emoji_id = 0

        if not (position_role_id := self.reaction_to_role.get(custom_emoji_id)):
            return

        # 取得したロールIDからロールオブジェクトを取得
        position_role = guild.get_role(position_role_id)

        if not position_role:
            print(f"{position_role_id} がサーバーに見つかりませんでした。")
            return

        member_role = guild.get_role(self.member_role_id)

        if not member_role:
            print(f"{self.member_role_id}がサーバーに見つかりませんでした。")
            return

        # たまーにpayload.memberがNoneになることがある
        # Noneになったらリアクションを押したユーザーのIDを元にサーバーに入ってるメンバー一覧から押したユーザーを取得する
        if not (member := payload.member):
            member = guild.get_member(payload.user_id)

        # 取得したロールをリアクションを押したメンバーに付与する

        roles = [position_role, member_role]
        await member.add_roles(*roles)

        # リアクションを削除
        await message.remove_reaction(payload.emoji, member)


async def setup(bot):
    await bot.add_cog(Auth_System(bot))
