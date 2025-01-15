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

        view = ShopView(shop_data)
        await ctx.send("Выберите категорию:", view=view)

    @commands.command(
        name="buy-item",
        aliases=["buyitem", "купить-предмет", "купитьпредмет"],
        brief="Купить предмет",
        usage="buy-item <item_name> <quantity>"
    )
    async def buy_item(self, ctx, name: str, quantity: int = 1):
        try:
            item_data = await self.db.get_item_by_name(name.capitalize())
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
                    description=f"Вы успешно купили {quantity}x **{name.capitalize()}** за {total_cost} монет.",
                    color=disnake.Color.green()
                )
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("Произошла ошибка при покупке предмета.")
            print(f"Ошибка при покупке предмета: {e}")


class ShopView(disnake.ui.View):
    def __init__(self, shop_data):
        super().__init__(timeout=60)
        self.shop_data = shop_data
        self.page = 0
        self.items_per_page = 5
        self.categories = list(set(item['type'] for item in shop_data))
        self.current_category = self.categories[0]
        self.update_view()

    def update_view(self):
        self.clear_items()
        self.add_item(CategorySelect(self.categories, self))
        self.add_item(PreviousPageButton(self))
        self.add_item(NextPageButton(self))

    def get_current_page_items(self):
        category_items = [item for item in self.shop_data if item['type'] == self.current_category]
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        return category_items[start:end]


class CategorySelect(disnake.ui.Select):
    def __init__(self, categories, view):
        options = [disnake.SelectOption(label=category, value=category) for category in categories]
        super().__init__(placeholder="Выберите категорию", options=options)
        self.view = view

    async def callback(self, interaction: disnake.Interaction):
        self.view.current_category = self.values[0]
        self.view.page = 0
        self.view.update_view()
        await interaction.response.edit_message(content="Выберите категорию:", view=self.view)


class PreviousPageButton(disnake.ui.Button):
    def __init__(self, view):
        super().__init__(label="Предыдущая", style=disnake.ButtonStyle.blurple)
        self.view = view

    async def callback(self, interaction: disnake.Interaction):
        if self.view.page > 0:
            self.view.page -= 1
            self.view.update_view()
            await interaction.response.edit_message(content="Выберите категорию:", view=self.view)


class NextPageButton(disnake.ui.Button):
    def __init__(self, view):
        super().__init__(label="Следующая", style=disnake.ButtonStyle.blurple)
        self.view = view

    async def callback(self, interaction: disnake.Interaction):
        category_items = [item for item in self.view.shop_data if item['type'] == self.view.current_category]
        if (self.view.page + 1) * self.view.items_per_page < len(category_items):
            self.view.page += 1
            self.view.update_view()
            await interaction.response.edit_message(content="Выберите категорию:", view=self.view)


def setup(bot):
    bot.add_cog(Shop(bot))
