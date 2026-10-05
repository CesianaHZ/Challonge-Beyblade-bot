import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from chyllonge.api import ChallongeApi
from state import tournament, MatchData

api = ChallongeApi()  # reads CHALLONGE_USER and CHALLONGE_KEY from env automatically

class Matches(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_next_stadium(self):
        for i in range(1, tournament.stadium_count + 1):
            if i not in tournament.stadiums_in_use:
                return i
        return None

    @commands.hybrid_command(name="newmatch", description="Start the next available match from Challonge")
    async def newmatch(self, ctx):
        if not tournament.active:
            await ctx.send("No active tournament.")
            return

        if not tournament.judges_available:
            await ctx.send("❌ No judges available right now.")
            return

        stadium = self._get_next_stadium()
        if stadium is None:
            await ctx.send("❌ All stadiums are currently in use.")
            return

        try:
            matches = api.matches.get_all(tournament_id=tournament.challonge_tournament_id, state="open")
        except Exception as e:
            await ctx.send(f"❌ Challonge error: {e}")
            return

        if not matches:
            await ctx.send("✅ No open matches on Challonge right now!")
            return

        challonge_match = matches[0]
        p1_challonge_id = int(challonge_match["player1_id"])
        p2_challonge_id = int(challonge_match["player2_id"])

        p1_name = tournament.participants.get(p1_challonge_id, f"Player {p1_challonge_id}")
        p2_name = tournament.participants.get(p2_challonge_id, f"Player {p2_challonge_id}")

        try:
            api.matches.set_underway(tournament.challonge_tournament_id, challonge_match["id"])
        except Exception as e:
            await ctx.send(f"❌ Could not mark match as underway on Challonge: `{e}`\nMatch has NOT been started. Try again.")
            # Roll back the judge and stadium assignments
            tournament.judges_busy.remove(judge_discord_id)
            tournament.judges_available.insert(0, judge_discord_id)
            tournament.stadiums_in_use.remove(stadium)
            return

        judge_discord_id = tournament.judges_available.pop(0)
        tournament.judges_busy.append(judge_discord_id)
        tournament.stadiums_in_use.append(stadium)

        tournament.match_counter += 1
        match_num = tournament.match_counter
        match = MatchData(
            match_number=match_num,
            contestant1_id=p1_challonge_id,
            contestant2_id=p2_challonge_id,
            judge_id=judge_discord_id,
            stadium=stadium,
            challonge_match_id=challonge_match["id"]
        )
        tournament.matches[match_num] = match

        judge_mention = f"<@{judge_discord_id}>"
        await ctx.send(
            f"⚔️ **Match #{match_num}** — Stadium **{stadium}**\n"
            f"🪀 **{p1_name}** vs **{p2_name}**\n"
            f"⚖️ Judge: {judge_mention}\n"
            f"⏱️ You have **{tournament.battle_start_time} minutes** to get to the stadium!\n"
            f"Judge: type `!matchstart {match_num}` when the match begins."
        )

        await asyncio.sleep(tournament.battle_start_time * 60)
        if match_num in tournament.matches and not tournament.matches[match_num].started:
            await ctx.send(
                f"⏰ Match #{match_num} timer expired! "
                f"Judge {judge_mention}, confirm with `!matchstart {match_num}` if it's underway."
            )
            
    @commands.hybrid_command(name="matchstart", description="Start a specific match indicated by a number")
    async def matchstart(self, ctx, match_number: int):
        match = tournament.matches.get(match_number)
        if not match:
            await ctx.send(f"❌ Match #{match_number} not found.")
            return
        if ctx.author.id != match.judge_id:
            await ctx.send("❌ Only the assigned judge can confirm this.")
            return

        match.started = True
        await ctx.send(
            f"✅ Match #{match_number} is **underway**! "
            f"Type `!matchend {match_number} [p1_score] [p2_score]` when it's done."
        )

    @commands.hybrid_command(name="matchend", description="End a match and report scores to Challonge")
    @app_commands.describe(
        match_number="The match number shown when the match was created",
        p1_score="Player 1's score (1-5)",
        p2_score="Player 2's score (1-5)"
    )
    async def matchend(self, ctx, match_number: int, p1_score: int, p2_score: int):
        """
        Usage: !matchend [match_number] [p1_score] [p2_score]
        Example: !matchend 1 5 3
        The player with score 5 is automatically reported as the winner to Challonge.
        Scores must be between 1-5 and exactly one player must have 5.
        """
        match = tournament.matches.get(match_number)
        if not match:
            await ctx.send(f"❌ Match #{match_number} not found.")
            return
        if ctx.author.id != match.judge_id:
            await ctx.send("❌ Only the assigned judge can end this match.")
            return

        # Validate scores
        if not (1 <= p1_score <= 5) or not (1 <= p2_score <= 5):
            await ctx.send("❌ Scores must be between 1 and 5.")
            return
        if p1_score != 5 and p2_score != 5:
            await ctx.send("❌ One player must have a score of 5 (the winner).")
            return
        if p1_score == 5 and p2_score == 5:
            await ctx.send("❌ Both players can't have a score of 5.")
            return

        p1_name = tournament.participants.get(match.contestant1_id, f"Player {match.contestant1_id}")
        p2_name = tournament.participants.get(match.contestant2_id, f"Player {match.contestant2_id}")

        # Determine winner's Challonge participant ID
        if p1_score == 5:
            winner_challonge_id = match.contestant1_id
            winner_name = p1_name
        else:
            winner_challonge_id = match.contestant2_id
            winner_name = p2_name

        # Report to Challonge
        try:
            api.matches.update(
                tournament.challonge_tournament_id,
                match.challonge_match_id,
                match_scores_csv=f"{p1_score}-{p2_score}",
                match_winner_id=winner_challonge_id
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to report result to Challonge: `{e}`\nMatch data NOT cleared — fix the error and try again.")
            return

        # Only clean up after Challonge confirms
        if match.stadium in tournament.stadiums_in_use:
            tournament.stadiums_in_use.remove(match.stadium)

        del tournament.matches[match_number]

        await ctx.send(
            f"🏁 **Match #{match_number}** complete!\n"
            f"🪀 **{p1_name}** {p1_score} — {p2_score} **{p2_name}**\n"
            f"🏆 Winner: **{winner_name}** *(reported to Challonge)*\n"
            f"⚖️ Judge <@{match.judge_id}> on cooldown for 5 minutes."
        )

        await asyncio.sleep(5 * 60)
        if match.judge_id in tournament.judges_busy:
            tournament.judges_busy.remove(match.judge_id)
            tournament.judges_available.append(match.judge_id)
            await ctx.send(f"⚖️ Judge <@{match.judge_id}> is available again!")
            
    @commands.hybrid_command(name="debug", description="Developer: Debug tournament state")
    async def debug(self, ctx):
        first_few = dict(list(tournament.participants.items())[:3])
        await ctx.send(
            f"active: {tournament.active}\n"
            f"tournament_id: `{tournament.challonge_tournament_id}`\n"
            f"judges available: {tournament.judges_available}\n"
            f"stadiums: {tournament.stadium_count}\n"
            f"participants loaded: {len(tournament.participants)}\n"
            f"participant sample: `{first_few}`"
        )

async def setup(bot):
    await bot.add_cog(Matches(bot))