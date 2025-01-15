import disnake
from disnake.ext import commands
from utils import database


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database.DataBase()

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            await self.db.create_table()

            for guild in self.bot.guilds:
                for member in guild.members:
                    await self.db.insert_new_member(member.id, member.name, member.display_name)
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            await self.db.insert_new_member(member.id, member.name, member.display_name)
        except Exception as e:
            print(f"Ошибка при добавлении нового участника: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.display_name != after.display_name:
            try:
                await self.db.update_member_display_name(after.id, after.display_name)
                print(f"Updated display name for {after.name} to {after.display_name} in users table.")
                
                await self.db.update_inventory_display_name(after.id, after.display_name)
                print(f"Updated display name for {after.name} to {after.display_name} in inventory table.")
            except Exception as e:
                print(f"Ошибка при обновлении отображаемого имени: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_data = await self.db.get_data(message.author.id)
        
        if not user_data:
            return

        user_row = user_data[0]
        xp = user_row['xp']

        if isinstance(message.author, disnake.Member):
            try:
                if xp == 500 + 100 * user_row['level']:
                    await self.db.update_user(
                        "UPDATE users SET level = level + 1, xp = 0 WHERE member_id = ?",
                        [message.author.id]
                    )
                    channel = self.bot.get_channel(1326576577324253184)
                    if channel:
                        await channel.send(f"{message.author.mention} +1 LVL")
                else:
                    new_xp = xp + 50
                    await self.db.update_user("UPDATE users SET xp = ? WHERE member_id = ?", [new_xp, message.author.id])
            except Exception as e:
                print(f"Ошибка при обновлении опыта пользователя: {e}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = disnake.Embed(
                title="Кулдаун",
                description=f"Пожалуйста, подождите {round(error.retry_after, 2)} секунд перед повторным использованием команды.",
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.UserInputError):
            embed = disnake.Embed(
                title="Ошибка ввода",
                description=f"Правильное использование команды: `{ctx.prefix}{ctx.command.name}` ({ctx.command.brief}): `{ctx.prefix}{ctx.command.usage}`",
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(
                title="Недостаточно прав",
                description="У вас нет прав для выполнения этой команды.",
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandNotFound):
            embed = disnake.Embed(
                title="Команда не найдена",
                description="Команда не найдена. Проверьте правильность ввода.",
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(
                title="Неизвестная ошибка",
                description=f"Произошла ошибка при выполнении команды: {str(error)}",
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Events(bot))
