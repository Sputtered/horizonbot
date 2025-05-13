from pathlib import Path
import discord
from discord.ext.commands import Bot
from services.tournament import TournamentService
from services.signups import SignupService
from services.minecraft import MinecraftLinkService
from services.message import MessageService
from storage import Storage
from settings import Settings


class HorizonBot(Bot):
    def __init__(self, settings: Settings, intents: discord.Intents, storage: Storage):
        super().__init__(command_prefix=settings.command_prefix, intents=intents)
        self.settings: Settings = settings

        self.message_service = MessageService(storage.message_storage)
        self.minecraft_link_service = MinecraftLinkService(
            storage.minecraft_link_storage
        )
        self.signup_service = SignupService(storage.signup_storage)
        self.tournament_service = TournamentService(storage.tournament_storage)

    async def setup_hook(self):
        folder = Path(__file__).resolve().parent / "cogs"

        for cog_path in folder.glob("*.py"):
            await self.load_extension(f"cogs.{cog_path.stem}")

    async def on_ready(self):
        print(f"Logged in as {self.user.name} - {self.user.id}")  # type: ignore

        for guild in self.guilds:
            if guild.id not in self.settings.allowed_guilds:
                print(f"Leaving guild {guild.name} ({guild.id})")
                await guild.leave()
            else:
                for cmd in await self.tree.sync(guild=guild):
                    print(
                        f"Synced command {cmd.name} for guild {guild.name} ({guild.id})"
                    )
                print(f"Synced commands for guild {guild.name} ({guild.id})")

    async def on_guild_join(self, guild: discord.Guild):
        print(f"Joined guild: {guild.name} (ID: {guild.id}) | Owner: {guild.owner_id}")

        if guild.id not in self.settings.allowed_guilds:
            print(f"Leaving guild: {guild.name} (ID: {guild.id}) - Not in whitelist.")
            await guild.leave()

    async def on_message(self, message: discord.Message):
        await self.message_service.log_message(message)

    def can_view_detailed_errors(self, member: discord.Member) -> bool:
        return member.id == self.settings
