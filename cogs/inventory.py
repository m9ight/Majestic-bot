import disnake
from disnake.ext import commands

from utils import database


class Inventory(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database.DataBase()

    @commands.command(
        name="inventory",
        aliases=["inv", "инвентарь"],
        brief="Показать инвентарь",
        usage="inventory <@user>"
    )
    async def show_inventory(self, ctx, member: disnake.Member = None):
        member = member or ctx.author
        try:
            inventory = await self.db.get_inventory(member.id)

            if not inventory:
                embed = disnake.Embed(
                    title=f"Инвентарь {member.display_name}",
                    description="Ваш инвентарь пуст. Купите предметы, чтобы они появились здесь.",
                    color=disnake.Color.orange()
                )
                await ctx.send(embed=embed)
                return

            embed = disnake.Embed(
                title=f"Инвентарь {member.display_name}",
                color=disnake.Color.blurple()
            )
            for item in inventory:
                embed.add_field(
                    name=f"Предмет: {item['name']}",
                    value=f"Количество: {item['quantity']}, Стоимость: {item['cost']}",
                    inline=False
                )

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("Произошла ошибка при получении инвентаря.")
            print(f"Ошибка при получении инвентаря: {e}")

    @commands.command(
        name="add-item",
        aliases=["additem", "добавить-предмет", "добавитьпредмет"],
        brief="Добавить предмет в инвентарь пользователя",
        usage="add-item <@user> <item_name> <quantity>"
    )
    async def add_item(self, ctx, member: disnake.Member, item_name: str, quantity: int):
        if quantity < 1:
            await ctx.send("Количество должно быть больше 0.")
            return

        item = await self.db.get_item_by_name(item_name)
        if not item:
            await ctx.send("Предмет не найден.")
            return

        await self.db.add_item_to_inventory(member.id, item['item_id'], quantity, member.name, member.display_name)
        await ctx.send(f"Добавлено {quantity} {item_name} в инвентарь {member.display_name}.")

    @commands.command(
        name="remove-item",
        aliases=["removeitem", "удалить-предмет", "удалитьпредмет"],
        brief="Удалить предмет из инвентаря пользователя",
        usage="remove-item <@user> <item_name> <quantity>"
    )
    async def remove_item(self, ctx, member: disnake.Member, item_name: str, quantity: int):
        if quantity < 1:
            await ctx.send("Количество должно быть больше 0.")
            return

        item = await self.db.get_item_by_name(item_name)
        if not item:
            await ctx.send("Предмет не найден.")
            return

        inventory = await self.db.get_inventory(member.id)
        for inv_item in inventory:
            if inv_item['name'] == item_name:
                if inv_item['quantity'] < quantity:
                    await ctx.send(f"У {member.display_name} недостаточно {item_name}.")
                    return
                new_quantity = inv_item['quantity'] - quantity
                await self.db.update_inventory_quantity(member.id, item['item_id'], new_quantity)
                await ctx.send(f"Удалено {quantity} {item_name} из инвентаря {member.display_name}.")
                return

        await ctx.send(f"У {member.display_name} нет {item_name} в инвентаре.")


def setup(bot):
    bot.add_cog(Inventory(bot))
