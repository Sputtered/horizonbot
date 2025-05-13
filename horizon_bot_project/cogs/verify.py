from bot import HorizonBot
from discord import app_commands
from discord.ext import commands
import discord

from services.minecraft import (
    DiscordTagMismatch,
    DiscordTagNotFound,
)
from minecraft import mojang


class VerifyCog(commands.Cog):
    def __init__(self, bot: HorizonBot):
        self.bot: HorizonBot = bot

    @app_commands.command(
        name="verify",
        description="Link your Minecraft account to your Discord account.",
    )
    @app_commands.describe(username="Minecraft username")
    async def verify(self, interaction: discord.Interaction, username: str) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        uuid, canonical_ign = await mojang.fetch_mojang_profile(username)
        if uuid is None or canonical_ign is None:
            await interaction.followup.send(
                f"Could not find a Minecraft account with the username `{username}`."
            )
            return

        if await self.bot.minecraft_link_service.get_minecraft_uuid(interaction.user):
            await interaction.followup.send(
                "You already have a linked Minecraft account. Please contact support if you want to change it."
            )
            return

        try:
            await self.bot.minecraft_link_service.link_account(
                interaction.user, uuid, canonical_ign
            )
        except DiscordTagNotFound:
            await interaction.followup.send(
                f"❌ Could not find a Discord link on the Hypixel profile for **{username}**. "
                "Make sure you've linked your account in-game using `/discord link`."
            )
        except DiscordTagMismatch as e:
            await interaction.followup.send(
                f"❌ The Discord account linked on Hypixel (**{e.actual}**) "
                f"does not match your Discord account (**{e.expected}**)."
            )
        except Exception as e:
            await interaction.followup.send(
                f"⚠️ Unexpected error occurred{f': {str(e)}' if self.bot.can_view_detailed_errors(interaction.user) else '. Please try again later and contact support.'}"
            )
            print(f"Unexpected error linking account for {interaction.user}: {e}")
        else:
            await interaction.followup.send(
                f"✅ Successfully linked your account to **{username}**!"
            )


async def setup(bot: HorizonBot):
    await bot.add_cog(VerifyCog(bot))
