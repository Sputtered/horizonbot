from datetime import datetime
import json
import os
import aiosqlite
from typing import AsyncGenerator, List, Optional

import discord

from hbp_types.team import Team
from hbp_types.tournament import Tournament

from . import (
    MessageStorage,
    MinecraftLinkStorage,
    SignupStorage,
    Storage,
    TournamentStorage,
)


class SQLiteStorage(Storage):
    def __init__(self):
        super().__init__(
            SQLiteMessageStorage(),
            SQLiteMinecraftLinkStorage(),
            SQLiteSignupsStorage(),
            SQLiteTournamentStorage(),
        )

    async def setup(self):
        await self.message_storage._initialize_database()
        await self.minecraft_link_storage._initialize_database()
        await self.signup_storage._initialize_database()
        await self.tournament_storage._initialize_database()


class SQLiteMessageStorage(MessageStorage):
    def __init__(self, db_path: str = "messages.db"):
        self.db_path = db_path

    async def _initialize_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            await db.commit()

    async def log_message(self, message: discord.Message) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO messages (message_id, author_id, content, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (
                    str(message.id),
                    str(message.author.id),
                    message.content,
                    message.created_at.isoformat(),
                ),
            )
            await db.commit()

    async def bulk_log_messages(self, messages: List[discord.Message]) -> None:
        if not messages:
            return
        data = [
            (
                str(m.id),
                str(m.author.id),
                m.content,
                m.created_at.isoformat(),
            )
            for m in messages
        ]
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                """
                INSERT INTO messages (message_id, author_id, content, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                data,
            )
            await db.commit()


class SQLiteMinecraftLinkStorage(MinecraftLinkStorage):
    def __init__(self, db_path: str = "messages.db"):
        self.db_path = db_path

    async def _initialize_database(self):
        """Initialize the SQLite database and create the account_links table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_links (
                    discord_user_id TEXT PRIMARY KEY,
                    minecraft_uuid TEXT UNIQUE NOT NULL,
                    minecraft_username TEXT NOT NULL
                )
            """)
            await conn.commit()

    async def link_account(
        self, discord_user_id: int, minecraft_uuid: str, canonical_ign: str
    ) -> None:
        """Link a Discord user ID with a Minecraft UUID."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                INSERT OR REPLACE INTO account_links (discord_user_id, minecraft_uuid, minecraft_username)
                VALUES (?, ?, ?)
            """,
                (str(discord_user_id), minecraft_uuid, canonical_ign),
            )
            await conn.commit()

    async def unlink_account(self, discord_user_id: int) -> None:
        """Unlink a Discord user ID from any Minecraft UUID."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                DELETE FROM account_links WHERE discord_user_id = ?
            """,
                (str(discord_user_id),),
            )
            await conn.commit()

    async def get_minecraft_uuid(self, discord_user_id: int) -> Optional[str]:
        """Get the linked Minecraft UUID for a given Discord user ID."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT minecraft_uuid FROM account_links WHERE discord_user_id = ?
            """,
                (str(discord_user_id),),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def get_minecraft_username(self, discord_user_id: int) -> Optional[str]:
        """Get the linked Minecraft username for a given Discord user ID."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT minecraft_username FROM account_links WHERE discord_user_id = ?
            """,
                (str(discord_user_id),),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def get_discord_user_id(self, minecraft_uuid: str) -> Optional[int]:
        """Get the linked Discord user ID for a given Minecraft UUID."""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT discord_user_id FROM account_links WHERE minecraft_uuid = ?
            """,
                (minecraft_uuid,),
            )
            row = await cursor.fetchone()
            return int(row[0]) if row else None


class SQLiteSignupsStorage(SignupStorage):
    def __init__(self, db_path: str = "signups.db"):
        self.db_path = db_path

    async def _initialize_database(self):
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        guild_id TEXT PRIMARY KEY,
                        signups_closed INTEGER NOT NULL DEFAULT 0
                    )
                """)
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS teams (
                        canonical_name TEXT PRIMARY KEY,
                        team_name TEXT NOT NULL,
                        member_ids TEXT NOT NULL,
                        signup_pending INTEGER NOT NULL DEFAULT 1,
                        signup_message_id INTEGER NOT NULL,
                        denied_by INTEGER,
                        team_role_id INTEGER,
                        approved_at TEXT
                    )
                """)
                await conn.commit()

    async def load_signups_closed(self, guild_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT signups_closed FROM settings WHERE guild_id = ?",
                    (str(guild_id),),
                )
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    async def set_signups_closed(self, guild_id: int, closed: bool) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO settings (guild_id, signups_closed)
                    VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET signups_closed=excluded.signups_closed
                """,
                    (str(guild_id), int(closed)),
                )
                await conn.commit()

    async def all_teams_generator(self) -> AsyncGenerator[Team, None]:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT canonical_name, team_name, member_ids, signup_message_id, denied_by FROM teams"
                )
                rows = await cursor.fetchall()
                for (
                    canonical_name,
                    team_name,
                    member_ids_json,
                    signup_message_id,
                    denied_by,
                ) in rows:
                    member_ids = json.loads(member_ids_json)
                    yield Team(
                        canonical_name=canonical_name,
                        team_name=team_name,
                        members=member_ids,
                        signup_message_id=signup_message_id,
                        denied_by=denied_by,
                    )

    async def add_team(self, team: Team) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT OR REPLACE INTO teams (canonical_name, team_name, signup_message_id, member_ids)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        team.canonical_name,
                        team.team_name,
                        team.signup_message_id,
                        json.dumps(team.members),
                    ),
                )
                await conn.commit()

    async def get_team_for_member(self, member_id: int) -> Optional[Team]:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT canonical_name, team_name, member_ids, signup_message_id, denied_by FROM teams"
                )
                async for (
                    canonical_name,
                    team_name,
                    member_ids_json,
                    signup_message_id,
                    denied_by,
                ) in cursor:
                    member_ids = json.loads(member_ids_json)
                    if member_id in member_ids:
                        return Team(
                            canonical_name=canonical_name,
                            team_name=team_name,
                            members=member_ids,
                            signup_message_id=signup_message_id,
                            denied_by=denied_by,
                        )
        return None

    async def get_team_for_signup_message(self, message_id: int) -> Optional[Team]:
        return next(iter((await self._get_teams(signup_message_id=message_id))), None)

    async def _get_teams(
        self,
        canonical_name: Optional[str] = None,
        signup_pending: Optional[bool] = None,
        signup_message_id: Optional[int] = None,
    ) -> list[Team]:
        query = "SELECT canonical_name, team_name, member_ids, signup_pending, signup_message_id, denied_by FROM teams"
        conditions = []
        params = []

        if canonical_name is not None:
            conditions.append("canonical_name = ?")
            params.append(canonical_name)
        if signup_pending is not None:
            conditions.append("signup_pending = ?")
            params.append(int(signup_pending))
        if signup_message_id is not None:
            conditions.append("signup_message_id = ?")
            params.append(signup_message_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                rows = await cursor.fetchall()

                teams = [
                    Team(
                        canonical_name=row[0],
                        team_name=row[1],
                        members=list(map(int, row[2][1:-1].split(","))),
                        signup_pending=bool(row[3]),
                        signup_message_id=row[4],
                        denied_by=int(row[5]) if row[5] else None,
                    )
                    for row in rows
                ]
                return teams

    async def set_team_denied(self, team: Team, user: int) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    UPDATE teams
                    SET denied_by = ?
                    WHERE canonical_name = ?
                    """,
                    (user, team.canonical_name),
                )
                await conn.commit()

    async def set_pending(self, team: Team, pending: bool) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE teams SET signup_pending = ? WHERE canonical_name = ?",
                    (int(pending), team.canonical_name),
                )
                await conn.commit()

    async def set_team_role(self, team: Team, role_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE teams SET team_role_id = ? WHERE canonical_name = ?",
                    (role_id, team.canonical_name),
                )
                await conn.commit()

    async def set_approved_at(self, team: Team, date: datetime) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE teams SET approved_at = ? WHERE canonical_name = ?",
                    (date.isoformat(), team.canonical_name),
                )
                await conn.commit()

    async def backup(self) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT * FROM teams")
                rows = await cursor.fetchall()
                os.makedirs("backup", exist_ok=True)
                with open(
                    f"backup/backup-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json",
                    "w",
                ) as f:
                    json.dump(rows, f)

    async def clear(self) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM teams")
                await conn.commit()


class SQLiteTournamentStorage(TournamentStorage):
    def __init__(self, db_path: str = "tournament.db"):
        self.db_path = db_path

    async def _initialize_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_name TEXT NOT NULL,
                    signups_close_date TEXT NOT NULL,
                    tournament_start_date TEXT NOT NULL,
                    team_count INTEGER NOT NULL,
                    team_size INTEGER NOT NULL
                )
            """)
            await db.commit()

    async def insert_tournament(self, tournament: Tournament) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO tournaments (tournament_name, signups_close_date, tournament_start_date, team_count, team_size)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    tournament.tournament_name,
                    tournament.signups_close_date.isoformat(),
                    tournament.tournament_start_date.isoformat(),
                    tournament.team_count,
                    tournament.team_size,
                ),
            )
            await db.commit()

    async def get_current_tournament(self) -> Optional[Tournament]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT tournament_id, tournament_name, signups_close_date,
                       tournament_start_date, team_count, team_size
                FROM tournaments
                ORDER BY tournament_start_date DESC
                LIMIT 1
            """) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Tournament(
                        tournament_id=row[0],
                        tournament_name=row[1],
                        signups_close_date=datetime.fromisoformat(row[2]),
                        tournament_start_date=datetime.fromisoformat(row[3]),
                        team_count=row[4],
                        team_size=row[5],
                    )
        return None

    async def is_signups_open(self) -> bool:
        tournament = await self.get_current_tournament()
        if not tournament:
            return False
        return datetime.utcnow() < tournament.signups_close_date
