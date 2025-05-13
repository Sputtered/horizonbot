import discord
from minecraft import hypixel
from storage import MinecraftLinkStorage


class DiscordTagNotFound(Exception):
    pass


class DiscordTagMismatch(Exception):
    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Expected: {expected}, Got: {actual}")


class MinecraftLinkService:
    def __init__(self, minecraft_link_storage: MinecraftLinkStorage):
        self._minecraft_link_storage = minecraft_link_storage

    async def link_account(
        self, member: discord.Member, minecraft_uuid: str, canonical_ign: str
    ) -> None:
        fetched_discord_tag = await hypixel.fetch_hypixel_discord_tag(minecraft_uuid)
        if fetched_discord_tag is None:
            raise DiscordTagNotFound()

        if member.discriminator == "0":
            expected_tag = member.name
        else:
            expected_tag = f"{member.name}#{member.discriminator}"

        if fetched_discord_tag.lower() != expected_tag.lower():
            raise DiscordTagMismatch(expected=expected_tag, actual=fetched_discord_tag)

        await self._minecraft_link_storage.link_account(
            member.id, minecraft_uuid, canonical_ign
        )

    async def get_minecraft_uuid(self, member: discord.Member) -> str | None:
        return await self._minecraft_link_storage.get_minecraft_uuid(member.id)

    async def get_minecraft_username(self, member: discord.Member) -> str | None:
        return await self._minecraft_link_storage.get_minecraft_username(member.id)
