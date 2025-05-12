import discord
from discord.ext import commands
from .utils import embed_ok, staff, ALLOWED

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="check the bots ping within discord")
    async def ping(self, ctx: commands.Context):
        if ctx.guild is None or ctx.guild.id not in ALLOWED or not staff(ctx.author):
            return
        start = discord.utils.utcnow().timestamp()
        msg = await ctx.reply(embed=embed_ok("Pinging…"), ephemeral=True)
        diff = (discord.utils.utcnow().timestamp() - start) * 1000
        gw = self.bot.latency * 1000
        await msg.edit(embed=embed_ok("Pong!", f"Gateway {gw:.1f} ms\nResponse {diff:.1f} ms"))

async def setup(bot):
    await bot.add_cog(Ping(bot))
