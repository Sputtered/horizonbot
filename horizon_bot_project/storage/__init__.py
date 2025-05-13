from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncGenerator, List, Optional

import discord

from hbp_types.team import Team
from hbp_types.tournament import Tournament


class MessageStorage(ABC):
    @abstractmethod
    async def log_message(
        self,
        message: discord.Message,
    ) -> None: ...

    async def bulk_log_message(
        self,
        messages: List[discord.Message],
    ) -> None:
        for msg in messages:
            await self.log_message(msg)


class MinecraftLinkStorage(ABC):
    @abstractmethod
    async def link_account(
        self, discord_user_id: int, minecraft_uuid: str, canonical_ign: str
    ) -> None: ...

    @abstractmethod
    async def unlink_account(self, discord_user_id: int) -> None: ...

    @abstractmethod
    async def get_minecraft_uuid(self, discord_user_id: int) -> str | None: ...

    @abstractmethod
    async def get_minecraft_username(self, discord_user_id: int) -> str | None: ...

    @abstractmethod
    async def get_discord_user_id(self, minecraft_uuid: str) -> int | None: ...


class SignupStorage(ABC):
    @abstractmethod
    async def load_signups_closed(self, guild_id: int) -> bool: ...

    @abstractmethod
    async def set_signups_closed(self, guild_id: int, closed: bool) -> None: ...

    @abstractmethod
    async def all_teams_generator(self) -> AsyncGenerator[Team, None]: ...

    @abstractmethod
    async def add_team(self, team: Team) -> None: ...

    @abstractmethod
    async def get_team_for_member(self, member_id: int) -> Optional[Team]: ...

    @abstractmethod
    async def get_team_for_signup_message(
        self, message: discord.Message
    ) -> Optional[Team]: ...

    @abstractmethod
    async def set_team_denied(self, team: Team, user: int) -> None: ...

    @abstractmethod
    async def set_pending(self, team: Team, pending: bool) -> None: ...

    @abstractmethod
    async def set_team_role(self, team: Team, role_id: int) -> None: ...

    @abstractmethod
    async def set_approved_at(self, team: Team, date: datetime) -> None: ...

    @abstractmethod
    async def backup(self) -> None: ...

    @abstractmethod
    async def clear(self) -> None: ...


class TournamentStorage(ABC):
    @abstractmethod
    async def get_current_tournament(self) -> Optional[Tournament]: ...

    @abstractmethod
    async def is_signups_open(self) -> bool: ...

    @abstractmethod
    async def insert_tournament(self, tournament: Tournament) -> None: ...


class Storage:
    def __init__(
        self,
        message_storage: MessageStorage,
        minecraft_link_storage: MinecraftLinkStorage,
        signup_storage: SignupStorage,
        tournament_storage: TournamentStorage,
    ):
        self._message_storage = message_storage
        self._minecraft_link_storage = minecraft_link_storage
        self._signup_storage = signup_storage
        self._tournament_storage = tournament_storage

    @property
    def message_storage(self):
        return self._message_storage

    @property
    def minecraft_link_storage(self):
        return self._minecraft_link_storage

    @property
    def signup_storage(self):
        return self._signup_storage

    @property
    def tournament_storage(self):
        return self._tournament_storage
