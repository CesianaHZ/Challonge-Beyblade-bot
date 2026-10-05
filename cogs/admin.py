import discord
from discord.ext import commands
from state import tournament

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="addjudge", description="ADMIN: Add judge")
    @commands.has_permissions(manage_roles=True)
    async def addjudge(self, ctx, member: discord.Member):
        if member.id in tournament.judges_available or member.id in tournament.judges_busy:
            await ctx.send(f"{member.mention} is already a judge.")
            return
        tournament.judges_available.append(member.id)
        await ctx.send(f"✅ {member.mention} added as a judge.")

    @commands.hybrid_command(name="removejudge", description="ADMIN: remove judge")
    @commands.has_permissions(manage_roles=True)
    async def removejudge(self, ctx, member: discord.Member):
        for pool in [tournament.judges_available, tournament.judges_busy]:
            if member.id in pool:
                pool.remove(member.id)
                await ctx.send(f"✅ {member.mention} removed from judges.")
                return
        await ctx.send(f"{member.mention} is not a judge.")

    @commands.hybrid_command(name="addcontestant", description="ADMIN: Add contestant")
    @commands.has_permissions(manage_roles=True)
    async def addcontestant(self, ctx, member: discord.Member):
        if member.id in tournament.contestants_available or member.id in tournament.contestants_busy:
            await ctx.send(f"{member.mention} is already a contestant.")
            return
        tournament.contestants_available.append(member.id)
        await ctx.send(f"✅ {member.mention} added as a contestant.")

    @commands.hybrid_command(name="removecontestant", description="ADMIN: Remove contestant")
    @commands.has_permissions(manage_roles=True)
    async def removecontestant(self, ctx, member: discord.Member):
        for pool in [tournament.contestants_available, tournament.contestants_busy]:
            if member.id in pool:
                pool.remove(member.id)
                await ctx.send(f"✅ {member.mention} removed from contestants.")
                return
        await ctx.send(f"{member.mention} is not a contestant.")

    @commands.hybrid_command(name="setarenas", description="ADMIN: Change Arena Amount")
    @commands.has_permissions(administrator=True)
    async def setarenas(self, ctx, amount: int):
        tournament.arena_count = amount
        await ctx.send(f"✅ stadium count updated to **{amount}**.")

    @commands.hybrid_command(name="settimer", description="ADMIN: Change global match start wait time")
    @commands.has_permissions(administrator=True)
    async def settimer(self, ctx, minutes: int):
        tournament.battle_start_time = minutes
        await ctx.send(f"✅ Battle start timer updated to **{minutes} minutes**.")

    @commands.hybrid_command(name="judges", description="List all judges")
    async def judges(self, ctx):
        """Lists all judges and their status."""
        if not tournament.judges_available and not tournament.judges_busy:
            await ctx.send("No judges registered.")
            return
        available = " ".join(f"<@{j}>" for j in tournament.judges_available) or "none"
        busy = " ".join(f"<@{j}>" for j in tournament.judges_busy) or "none"
        await ctx.send(f"⚖️ **Judges**\n✅ Available: {available}\n🔴 Busy: {busy}")

    @commands.hybrid_command(name="contestants", description="Lists all contestants")
    async def contestants(self, ctx):
        """Lists all contestants and their status."""
        if not tournament.contestants_available and not tournament.contestants_busy:
            await ctx.send("No contestants registered.")
            return
        available = " ".join(f"<@{c}>" for c in tournament.contestants_available) or "none"
        busy = " ".join(f"<@{c}>" for c in tournament.contestants_busy) or "none"
        await ctx.send(f"👥 **Contestants**\n✅ Available: {available}\n🔴 In match: {busy}")

async def setup(bot):
    await bot.add_cog(Admin(bot))