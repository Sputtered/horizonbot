from datetime import datetime
from typing import AsyncGenerator
import discord

from hbp_types.team import Team
from hbp_types.tournament import Tournament
from storage import SignupStorage


class SignupService:
    def __init__(self, storage: SignupStorage):
        self._storage = storage

    async def all_teams_generator(self) -> AsyncGenerator[Team, None]:
        async for team in self._storage.all_teams_generator():
            yield team

    async def add_team(self, team: Team) -> None:
        # Optional: Normalize name before storing
        team.canonical_name = self.normalize_team_name(team.team_name)
        await self._storage.add_team(team)

    async def get_team_for_member(self, member: discord.Member) -> Team | None:
        return await self._storage.get_team_for_member(member.id)

    async def get_team_for_signup_message(
        self, message: discord.Message
    ) -> Team | None:
        return await self._storage.get_team_for_signup_message(message.id)

    async def deny_team(self, team: Team, user: discord.User) -> None:
        await self._storage.set_team_denied(team, user.id)

    async def approve_team(
        self, tournament: Tournament, team: Team, role: discord.Role
    ) -> bool:
        await self._storage.set_pending(team, False)
        await self._storage.set_team_role(team, role.id)
        await self._storage.set_approved_at(team, datetime.now())

        approved_team_count = 0
        async for t in self._storage.all_teams_generator():
            if not t.signup_pending:
                approved_team_count += 1
            if approved_team_count >= tournament.team_count:
                return True
        return False

    async def clear_and_backup(self) -> None:
        await self._storage.backup()
        await self._storage.clear()

    def normalize_team_name(self, team_name: str) -> str:
        return team_name.lower().replace(" ", "_").replace("-", "_")
