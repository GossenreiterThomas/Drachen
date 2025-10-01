from discord import app_commands, Interaction, Embed
from discord.ext import commands
import discord

COMMANDS_PER_PAGE = 5  # how many commands per page

class HelpView(discord.ui.View):
    def __init__(self, bot, pages):
        super().__init__(timeout=120)
        self.bot = bot
        self.pages = pages
        self.current = 0

    async def update_message(self, interaction: Interaction):
        embed = self.pages[self.current]
        # update footer with page info
        embed.set_footer(text=f"Page {self.current + 1}/{len(self.pages)}")

        # enable/disable buttons based on page
        self.first.disabled = self.current == 0
        self.back.disabled = self.current == 0
        self.forward.disabled = self.current == len(self.pages) - 1
        self.last.disabled = self.current == len(self.pages) - 1

        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.errors.InteractionResponded:
            await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="⏮️", style=discord.ButtonStyle.secondary)
    async def first(self, interaction: Interaction, button: discord.ui.Button):
        self.current = 0
        await self.update_message(interaction)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: Interaction, button: discord.ui.Button):
        if self.current > 0:
            self.current -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def forward(self, interaction: Interaction, button: discord.ui.Button):
        if self.current < len(self.pages) - 1:
            self.current += 1
            await self.update_message(interaction)

    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.secondary)
    async def last(self, interaction: Interaction, button: discord.ui.Button):
        self.current = len(self.pages) - 1
        await self.update_message(interaction)


class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show dynamic help for all commands")
    async def help_command(self, interaction: Interaction):
        categories = {}
        # walk through slash commands
        for cmd in self.bot.tree.walk_commands():
            if cmd.parent is not None:
                continue  # only top-level commands
            # determine package from module
            module_path = getattr(cmd.callback, "__module__", "No Category")
            package = module_path.split(".")[1] if "." in module_path else "No Category"
            categories.setdefault(package, []).append(cmd)

        pages = []
        for package_name, cmds in categories.items():
            # paginate
            for i in range(0, len(cmds), COMMANDS_PER_PAGE):
                embed = Embed(
                    title=f"📚 Commands - {package_name}",
                    color=discord.Color.blurple()
                )
                for cmd in cmds[i:i+COMMANDS_PER_PAGE]:
                    embed.add_field(
                        name=f"/{cmd.name}",
                        value=cmd.description or "No description",
                        inline=False
                    )
                # footer is updated dynamically in update_message
                pages.append(embed)

        if not pages:
            embed = Embed(title="No commands found.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        view = HelpView(self.bot, pages)
        # initialize button states for first page
        view.first.disabled = True
        view.back.disabled = True
        if len(pages) == 1:
            view.forward.disabled = True
            view.last.disabled = True

        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))
