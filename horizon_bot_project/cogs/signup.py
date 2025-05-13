import re
from typing import List, Optional
from bot import HorizonBot
from discord import app_commands
from discord.ext import commands
import discord

from hbp_types.team import Team


class SignupCog(commands.Cog):
    def __init__(self, bot: HorizonBot):
        self.bot: HorizonBot = bot

    @app_commands.command(
        name="cancel",
        description="Cancel your signup",
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if not await self.bot.tournament_service.is_signups_open():
            return await interaction.followup.send("❌ Signups are currently closed.")

        team: Team = await self.bot.signup_service.get_team_for_member(interaction.user)
        if team is None:
            return await interaction.followup.send("❌ You are not signed up.")

        try:
            await self.bot.signup_service.deny_team(team, interaction.user)
        except Exception as e:
            print(f"Error denying team: {e}")
            return await interaction.followup.send(
                "❌ An error occurred while canceling your signup."
            )

        for m in team.members:
            user = self.bot.get_user(m)
            if user is None:
                user = await self.bot.fetch_user(m)
            self.send_team_signup_dm(
                user, False, f"Signup canceled by {interaction.user.mention}."
            )

    @app_commands.command(
        name="signup",
        description="Register your team",
    )
    @app_commands.describe(
        team_name="Your team’s name (≤20 chars)",
        p1="Team member 1 (must be verified)",
        p2="Team member 2 (must be verified)",
        p3="Team member 3 (must be verified)",
        p4="Team member 4 (must be verified, default: you)",
    )
    async def signup(
        self,
        interaction: discord.Interaction,
        team_name: str,
        p1: discord.Member,
        p2: discord.Member,
        p3: discord.Member,
        p4: Optional[discord.Member] = None,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not await self.bot.tournament_service.is_signups_open():
            return await interaction.followup.send("❌ Signups are currently closed.")

        if len(team_name) > 20:
            return await interaction.followup.send(
                "❌ Team name must be 20 characters or less."
            )

        # probably can be optimized by just getting a team with the name from the service and if it's None we are good to go
        canonical_name = self.bot.signup_service.normalize_team_name(team_name)
        async for team in self.bot.signup_service.all_teams_generator():
            if (not team.denied_by) and team.canonical_name == canonical_name:
                return await interaction.followup.send(
                    "❌ That team name is already taken."
                )

        members: List[discord.Member | discord.User] = [
            p4 if p4 else interaction.user,
            p1,
            p2,
            p3,
        ]
        if len({m.id for m in members}) < 4:
            return await interaction.followup.send(
                "❌ All four members must be unique."
            )

        for m in members:
            if await self.bot.minecraft_link_service.get_minecraft_uuid(m) is None:
                return await interaction.followup.send(
                    f"❌ {m.mention} has not run `/verify` yet!"
                )
            else:
                t = await self.bot.signup_service.get_team_for_member(m)
                if t is None or t.denied_by:
                    continue
                return await interaction.followup.send(
                    f"❌ {m.mention} is already on another team."
                )

        signup_chan = interaction.guild.get_channel(
            self.bot.settings.channels.signup_channel_id
        )
        if not signup_chan:
            return await interaction.followup.send(
                "❌ Signup channel not found. Ask an admin to run /setup.",
                ephemeral=True,
            )
        embed = await self._create_embed(team_name, members)
        ping_content = " ".join(m.mention for m in members)
        msg = await signup_chan.send(ping_content, embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("⛔")

        for m in members:
            try:
                await msg.forward(m)
                await m.send(
                    "*Your signup message needs 4 ✅ reactions, one from each team member to be approved!*"
                )
            except:  # noqa: E722
                pass

        await self.bot.signup_service.add_team(
            Team(
                canonical_name=canonical_name,
                team_name=team_name,
                members=[member.id for member in members],
                signup_pending=True,
                signup_message_id=msg.id,
            )
        )

        await interaction.followup.send("✅ Succesfully signed-up.")

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = self.bot.get_user(payload.user_id)
        if not user:
            user = await self.bot.fetch_user(payload.user_id)
        if (
            not (message.guild and message.guild.id in self.bot.settings.allowed_guilds)
        ) or user.bot:
            return

        team = await self.bot.signup_service.get_team_for_signup_message(message)
        if not team or team.signup_pending is False:
            return

        if user.id not in team.members or team.denied_by:
            return await message.remove_reaction(payload.emoji, user)

        if str(payload.emoji) == "⛔":
            await self.bot.signup_service.deny_team(team, user)

            if message.embeds:
                e = message.embeds[0]
                e.color = self.bot.settings.colors.error_color
                e.set_footer(
                    text=f"Denied by {user.name}",
                    icon_url=self.bot.settings.icon_url,
                )
                await message.edit(embed=e)
            await message.clear_reactions()

            class MockUser:
                def __init__(self, id):
                    self.id = id

            desc_lines = []
            for mid in team.members:
                member = await message.guild.fetch_member(mid)
                username = await self.bot.minecraft_link_service.get_minecraft_username(
                    MockUser(id=mid)
                )
                desc_lines.append(
                    f"<:pr_enter:1370057653606154260> `👤` {member.mention} {username}"
                )

            desc = "\n".join(desc_lines)

            for member_id in team.members:
                mem = message.guild.get_member(member_id)
                if not mem:
                    continue
                try:
                    dm_embed = discord.Embed(
                        title=f"**{team.team_name}** — Signup Denied",
                        description=desc,
                        color=self.bot.settings.colors.error_color,
                    )
                    dm_embed.set_footer(
                        text="A teammate denied your signup.",
                        icon_url=self.bot.settings.icon_url,
                    )
                    await mem.send(embed=dm_embed)
                    await mem.send(f"🔗 Signup was here: {message.jump_url}")
                except:  # noqa: E722
                    pass

        elif str(payload.emoji) == "✅":
            for r in message.reactions:
                if r.emoji == "✅":
                    raw_users = r.users()
                    break

            users = [u async for u in raw_users if not u.bot]
            reaction_count = len(users)
            if reaction_count == 1:
                await message.remove_reaction(payload.emoji, self.bot.user)
            for u in users:
                if u.id not in team.members:
                    await message.remove_reaction(payload.emoji, u)
                    reaction_count -= 1

            if reaction_count == 4:
                try:
                    await message.clear_reactions()
                    await message.add_reaction("🟢")
                except Exception as e:
                    print(f"Error updating reactions: {e}")

                try:
                    if message.embeds:
                        new_embed = message.embeds[0]
                        new_embed.color = self.bot.settings.colors.finished_color
                        new_embed.set_footer(
                            text="Team Approved!", icon_url=self.bot.settings.icon_url
                        )
                        await message.edit(embed=new_embed)
                    else:
                        await message.reply("Team Approved!")
                except Exception as e:
                    print("Error editing message:", e)

                team_role = discord.utils.get(
                    message.guild.roles, name=f"Team: {team.team_name}"
                )
                if not team_role:
                    try:
                        team_role = await message.guild.create_role(
                            name=f"Team: {team.team_name}", mentionable=True
                        )
                    except Exception as e:
                        print("Error creating team role:", e)

                is_substitute = await self.bot.signup_service.approve_team(
                    await self.bot.tournament_service.get_current_tournament(),
                    team,
                    team_role,
                )

                for member_id in team.members:
                    mem = message.guild.get_member(member_id)
                    if mem is None:
                        mem = await message.guild.fetch_member(member_id)
                    if team_role:
                        try:
                            await mem.add_roles(team_role)
                        except Exception as e:
                            print("Error adding role:", e)
                        try:
                            await mem.send(
                                f"Your team **{team.team_name}** has been **accepted**!\n"
                                f"You now have the role {team_role.mention}."
                                f"\nBecause the maximum number of teams has been reached, you are now a **substitute**. We will contact you if you will play!\n"
                                if is_substitute
                                else ""
                            )
                        except Exception as e:
                            print("Error sending DM:", e)

    @commands.Cog.listener(name="on_raw_reaction_remove")
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id or str(payload.emoji) != "✅":
            return

        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            channel = await self.bot.fetch_channel(payload.channel_id)

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            print("Message not found.")
            return

        team = await self.bot.signup_service.get_team_for_signup_message(message)
        if not team or team.signup_pending is False:
            return

        emoji = payload.emoji
        found = False
        for reaction in message.reactions:
            if (
                reaction.emoji == emoji.name
                if isinstance(emoji, discord.PartialEmoji)
                and not emoji.is_custom_emoji()
                else reaction.emoji == emoji
            ):
                found = True
                break

        if not found:
            try:
                await message.add_reaction(emoji)
            except discord.Forbidden:
                print("Bot lacks permission to add reaction.")
            except discord.HTTPException as e:
                print(f"Failed to add reaction: {e}")

    async def _create_embed(
        self, team_name, members: list[discord.Member | discord.User]
    ) -> discord.Embed:
        lines_list = [
            f"<:pr_enter:1361851517942104085> `👤` {m.mention} {await self.bot.minecraft_link_service.get_minecraft_username(m)}"
            for m in members
        ]
        lines = "\n".join(lines_list)

        embed = discord.Embed(
            title=f"**{team_name}**",
            description=lines,
            color=self.bot.settings.colors.default_color,
        )
        embed.set_footer(
            text="React ✅ to approve or ⛔ to deny",
            icon_url=self.bot.settings.icon_url,
        )

        return embed

    async def send_team_signup_dm(
        user: discord.User, approved: bool, reason: str = None
    ):
        try:
            if approved:
                message = (
                    f"✅ Your team signup was **successful**! 🎉\n"
                    f"You're now registered for the event."
                )
            else:
                message = (
                    f"❌ Your team signup was **denied**.\n"
                    f"Reason: {reason if reason else 'No reason provided.'}"
                )

            await user.send(message)

        except discord.Forbidden:
            print(f"Cannot send DM to {user}. They might have DMs disabled.")
        except Exception as e:
            print(f"Error sending DM: {e}")


async def setup(bot: HorizonBot):
    await bot.add_cog(SignupCog(bot))
