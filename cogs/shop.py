import disnake
from disnake.ext import commands

from utils import database


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database.DataBase()

    @commands.command(
        name="shop",
        aliases=["магазин"],
        brief="Показать доступные предметы в магазине"
    )
    async def show_shop(self, ctx):
        shop_data = await self.db.get_shop_data(all_data=True)
        if not shop_data:
            await ctx.send("Магазин пуст.")
            return

        embed = disnake.Embed(title="Магазин", color=disnake.Color.green())
        for item in shop_data:
            embed.add_field(
                name=item['name'],
                value=f"Стоимость: {item['cost']}, Тип: {item['type']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(
        name="buy-item",
        aliases=["buyitem", "купить-предмет", "купитьпредмет"],
        brief="Купить предмет",
        usage="buy-item <item_name> <quantity>"
    )
    async def buy_item(self, ctx, name: str, quantity: int = 1):
        try:
            item_data = await self.db.get_item_by_name(name)
            if not item_data:
                embed = disnake.Embed(
                    title="Ошибка",
                    description="Такого предмета не существует",
                    color=disnake.Color.red()
                )
                await ctx.send(embed=embed)
                return

            total_cost = item_data["cost"] * quantity
            user_data = await self.db.get_data(ctx.author.id)

            if not user_data:
                await ctx.send("Не удалось получить данные о пользователе.")
                return

            user_row = user_data[0]
            if user_row["balance"] < total_cost:
                embed = disnake.Embed(
                    title="Ошибка",
                    description="Недостаточно средств",
                    color=disnake.Color.red()
                )
                await ctx.send(embed=embed)
            else:
                await self.db.update_user(
                    "UPDATE users SET balance = balance - ? WHERE member_id = ?",
                    [total_cost, ctx.author.id]
                )

                await self.db.add_item_to_inventory(ctx.author.id, item_data["item_id"], quantity, ctx.author.name, ctx.author.display_name)
                embed = disnake.Embed(
                    title="Успешно",
                    description=f"Вы успешно купили {quantity}x **{name}** за {total_cost} монет.",
                    color=disnake.Color.green()
                )
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("Произошла ошибка при покупке предмета.")
            print(f"Ошибка при покупке предмета: {e}")


def setup(bot):
    bot.add_cog(Shop(bot))
