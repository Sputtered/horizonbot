from datetime import datetime

import parsedatetime
from bot import HorizonBot
from discord import app_commands
from discord.ext import commands
import discord

from hbp_types.tournament import Tournament


class TournamentCog(commands.Cog):
    def __init__(self, bot: HorizonBot):
        self.bot = bot

    @app_commands.command(
        name="tournament",
        description="Create a tournament",
    )
    @app_commands.describe(
        name="Name of the tournament",
        signups_close_at="Date and time when sign-ups will close (e.g., '2025-05-01 18:00')",
        tournament_start_at="Date and time when the tournament starts (e.g., '2025-05-02 15:00')",
        team_count="Total number of teams participating in the tournament",
        team_size="Number of players per team",
    )
    @app_commands.default_permissions(administrator=True)
    async def create_tournament(
        self,
        interaction: discord.Interaction,
        name: str,
        signups_close_at: str,
        tournament_start_at: str,
        team_count: int,
        team_size: int,
    ) -> None:
        cal = parsedatetime.Calendar()
        struct_time, parse_status = cal.parse(signups_close_at)
        if parse_status == 0:
            return await interaction.response.send_message(
                "⚠️ Could not parse the singups close date. Please use a valid format.",
                ephemeral=True,
            )
        signups_close_date = datetime(*struct_time[:6])

        struct_time, parse_status = cal.parse(tournament_start_at)
        if parse_status == 0:
            return await interaction.response.send_message(
                "⚠️ Could not parse the tournament start date. Please use a valid format.",
                ephemeral=True,
            )
        tournament_start_date = datetime(*struct_time[:6])

        try:
            await self.bot.tournament_service.create_tournament(
                Tournament(
                    tournament_id=-1,  # Placeholder, will be set by the database
                    tournament_name=name,
                    signups_close_date=signups_close_date,
                    tournament_start_date=tournament_start_date,
                    team_count=team_count,
                    team_size=team_size,
                )
            )
            await self.bot.signup_service.clear_and_backup()
            return await interaction.response.send_message(
                f"✅ Tournament **{name}** created successfully! Sign-ups close on <t:{int(signups_close_date.timestamp())}:F> and the tournament starts on <t:{int(tournament_start_date.timestamp())}:F>.",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(f"⚠️ {str(e)}", ephemeral=True)
            print(f"Error creating tournament for {interaction.user}: {e}")
            return


async def setup(bot: HorizonBot):
    await bot.add_cog(TournamentCog(bot))
