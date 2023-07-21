from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from main import Main
    

class Insider(commands.Cog):
    def __init__(self, bot: Main):
        self.bot = bot
        self.poll_lock = asyncio.Lock()

    @commands.hybrid_command(name="インサイダー")
    @discord.app_commands.rename(question_time="質問時間分")
    @discord.app_commands.rename(insider_time="インサイダー議論時間分")
    async def insider(self, ctx: commands.Context[Main], question_time: int = 3, insider_time: int = 3):
        """インサイダーゲーム
        
        コマンド入力方法:
            /インサイダー
            or
            ch!インサイダー
        
        パラメーター
            question_time: ゲームマスターに質問をする時間
            insider_time: インサイダーを議論する時間
        
        例:)
            /インサイダー 3 2
            or
            ch!インサイダー 3 2
        
        --------------------------
        
        ・VCに入室してからコマンドを実行してください
        ・コマンド実行者と同じVCに最低4人必要です
        
        
        ・ゲームマスターとインサイダーはコマンドを実行するたびにランダムで決まります。
        その際に ニックネームに【観戦】と入ってる人は除外されます。
        ・ゲームマスターに個人チャット(以下DM)でお題を入力してくださいと送信するので、ゲームマスターはお題をDMに入力してください。
        ・ゲームマスターがお題を入力した後、インサイダーにそのお題が送信されます。
        ・その後は質問タイムです。庶民とインサイダーはゲームマスターに質問をしてお題を当ててください。
        ・お題を当てずに制限時間になったら、ゲームマスターはお題を公開してください。
        ・その後は、インサイダーはだれかを話し合ってください。
        ・投票が完了するか、時間切れになったらインサイダーを公開します。"""
        
        if not isinstance(ctx.author, discord.Member):
            return
        
        if not (voice := ctx.author.voice):
            e = discord.Embed(
                title="VCに入室してからコマンドを実行してね!"
            )
            await ctx.send(embeds=[e])
            return
        
        if not isinstance(voice.channel, discord.VoiceChannel):
            return
        
        members = [member for member in voice.channel.members if not member.bot or "観戦" not in member.display_name]
        
        # if len(members) < 5: # 最低人数: ゲームマスター、インサイダー、庶民 × 2
            
        #     e = discord.Embed(
        #         title="インサイダーゲームを開始するには最低4人以上必要です!"
        #     )
        #     await ctx.send(embeds=[e])
        #     return
        
        game_master = random.choice(members)
        #members.remove(game_master)
        
        insider = random.choice(members)
        #members.remove(insider)
        
        try:
            game_master_private_message = await game_master.send("ゲームマスターに選ばれました。ここにお題を入力してください。\nここでゲームを終了するときは【キャンセル】と入力してください")
            m = await ctx.send("ゲームマスターの個人チャットにアナウンスメッセージを送信しました。ゲームマスターは個人チャットの案内に従ってください。", mention_author=False)
        except discord.errors.Forbidden:
            await ctx.send(f"ゲームマスターの個人チャットにDMを送信できませんでした。{game_master.mention}はDMをフレンドのみ受け取る設定になってないか確認してください。このゲームを終了します。", mention_author=False)
            return
        
        question = await self.bot.wait_for("message", check=lambda m: m.author.id == game_master.id and m.channel.id == game_master_private_message.channel.id)
        await m.delete()
        
        
        if "キャンセル" in question.content:
            await ctx.send("ゲームマスターがゲームを終了しました。このゲームを終了します。", mention_author=False)
            return
        
        e = discord.Embed(
            title="お題",
            description=question.content
        )
        
        try:
            await insider.send("インサイダーに選ばれました。", embeds=[e])
        except:
            await ctx.send(f"インサイダーの個人チャットにDMを送信できませんでした。{insider.mention}はDMをフレンドのみ受け取る設定になってないか確認してください。このゲームを終了します。", mention_author=False)
            return
        
        m = await ctx.send(f"ゲームマスター: {game_master.mention}\nそれでは,{question_time}分間質問を始めてください。\n質問時間を終了するときは、ゲームマスターの{game_master.mention}が【質問終了】と入力してください。",mention_author=False)
        
        try:
            await self.bot.wait_for("message", check=lambda m: m.author.id == game_master.id and m.channel.id == ctx.channel.id and "質問終了" in m.content, timeout=question_time * 60)
        except asyncio.TimeoutError:
            pass
        
        e = discord.Embed(title="投票")
        for member in members:
            e.add_field(
                name=member.display_name,
                value="未投票",
                inline=False
            )
        
        m = await ctx.send(f"質問タイムを終了します。{insider_time}分以内にインサイダーは誰かを投票してください。\n{insider_time}分後に結果を表示します。", embeds=[e],mention_author=False)
    
        view = discord.ui.View(timeout=insider_time * 60)
        
        async def end_btn_callback(interaction: discord.Interaction):
            """投票終了ボタンが押されたら発火する

            Parameters
            ----------
            interaction : discord.Interaction
                _description_
            """
            
            if not interaction.data:
                return
            
            if not interaction.message:
                return
            
            if not interaction.user.id != game_master.id:
                await ctx.send("このボタンはゲームマスターのみが押せるよ!")
                return
            
            view.stop()
        
        end_btn = discord.ui.Button(label="投票終了", style=discord.ButtonStyle.red)
        end_btn.callback = end_btn_callback
        
        async def btn_callback(interaction: discord.Interaction):
            """誰が誰に投票したかを更新する

            Parameters
            ----------
            interaction : discord.Interaction
                _description_
            """
            if not interaction.data:
                return
            
            if not interaction.message:
                return
            
            await interaction.response.defer()
            #ボタンが複数人に同時に押された時バグるのでその対策
            await self.poll_lock.acquire()
            
            embeds = interaction.message.embeds
            embed = embeds[0].to_dict()
                        
            for i, field in enumerate(embed.get("fields") or []):
                if field["name"] == interaction.data.get("custom_id"):
                    (embed.get("fields") or [])[i]["value"] = member.display_name
            
            await m.edit(embeds=[discord.Embed.from_dict(embed)])
            self.poll_lock.release()
        
        for member in members:
            btn = discord.ui.Button(label=f"{member.display_name}に投票", custom_id=f"{member.display_name}")
            btn.callback = btn_callback
            view.add_item(btn)
            
        await m.edit(embeds=[e], view=view)
        
        await view.wait()
        
        await ctx.send(f"インサイダーは{insider.mention}でした")
        
async def setup(bot: Main):
    await bot.add_cog(Insider(bot))