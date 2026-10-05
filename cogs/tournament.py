import discord
from discord.ext import commands
from chyllonge.api import ChallongeApi
from state import tournament

api = ChallongeApi()

class Tournament(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setuptournament(self, ctx, challonge_tournament_id: str, stadium_amount: int, battlestart_time: int):
        """
        Usage: !setuptournament my-tournament-url-id 4 3
        Fetches the tournament from Challonge and sets up the bot.
        The challonge_tournament_id is the URL slug from challonge.com/my-tournament-url-id
        """
        if tournament.active:
            await ctx.send("⚠️ A tournament is already active! End it first with `!endtournament`")
            return

        await ctx.send(f"🔍 Fetching tournament `{challonge_tournament_id}` from Challonge...")

        # Pull the tournament info
        try:
            challonge_tournament = api.tournaments.get(challonge_tournament_id)
        except Exception as e:
            await ctx.send(f"❌ Couldn't find that tournament on Challonge: `{e}`\nDouble-check the ID/URL slug.")
            return

        # Pull all participants
        try:
            participants = api.participants.get_all(challonge_tournament_id)
        except Exception as e:
            await ctx.send(f"❌ Couldn't fetch participants: `{e}`")
            return

        if not participants:
            await ctx.send("⚠️ That tournament has no participants yet on Challonge.")
            return

        # Store everything
        tournament.active = True
        tournament.name = challonge_tournament["name"]
        tournament.challonge_tournament_id = challonge_tournament_id
        tournament.stadium_count = stadium_amount
        tournament.battle_start_time = battlestart_time
        tournament.participants = {}
        for p in participants:
            for group_id in p["group_player_ids"]:
                tournament.participants[group_id] = p["name"]
        guild = ctx.guild
        contestant_role_name = f"{tournament.name} - Contestant"
        judge_role_name = f"{tournament.name} - Judge"
        contestant_role = discord.utils.get(guild.roles, name=contestant_role_name)
        judge_role = discord.utils.get(guild.roles, name=judge_role_name)

        # Check if roles exist
        if not contestant_role:
            await guild.create_role(name=contestant_role_name)
        if not judge_role:
            await guild.create_role(name=judge_role_name)

        # Build participant list for the confirmation message
        participant_names = "\n".join(f"• {p['name']}" for p in participants)

        await ctx.send(
            f"🏆 Tournament **{tournament.name}** is ready!\n"
            f"🎯 stadiums: **{stadium_amount}**\n"
            f"⏱️ Start timer: **{battlestart_time} minutes**\n"
            f"👥 **{len(participants)} participants loaded:**\n{participant_names}\n\n"
            f"Roles created: `{tournament.name} - Contestant` and `{tournament.name} - Judge`"
        )

    @commands.hybrid_command(name="endtournament", description="ADMIN: End the tournament")
    @commands.has_permissions(administrator=True)
    async def endtournament(self, ctx):
        if not tournament.active:
            await ctx.send("No active tournament.")
            return
        await ctx.send(f"⚠️ Are you sure you want to end **{tournament.name}**? Type `!confirmend` to confirm.")

    @commands.hybrid_command(name="confirmend", description="ADMIN: Confirm ending the tournament")
    @commands.has_permissions(administrator=True)
    async def confirmend(self, ctx):
        if not tournament.active:
            await ctx.send("No active tournament.")
            return

        name = tournament.name
        tournament.active = False
        tournament.name = ""
        tournament.challonge_tournament_id = ""
        tournament.participants.clear()
        tournament.contestants_available.clear()
        tournament.contestants_busy.clear()
        tournament.judges_available.clear()
        tournament.judges_busy.clear()
        tournament.matches.clear()
        tournament.match_counter = 0
        tournament.stadiums_in_use.clear()

        await ctx.send(f"✅ Tournament **{name}** has been ended. All data cleared.")

    @commands.hybrid_command(name="status", description="Check tournament status")
    async def status(self, ctx):
        if not tournament.active:
            await ctx.send("No active tournament.")
            return

        await ctx.send(
            f"🏆 **{tournament.name}**\n"
            f"👥 Contestants: {len(tournament.contestants_available)} available, {len(tournament.contestants_busy)} in a match\n"
            f"⚖️ Judges: {len(tournament.judges_available)} available\n"
            f"🎯 Active matches: {len(tournament.matches)}\n"
            f"⏱️ Battle start timer: {tournament.battle_start_time} min\n"
            f"📋 Total participants on Challonge: {len(tournament.participants)}"
        )

async def setup(bot):
    await bot.add_cog(Tournament(bot))