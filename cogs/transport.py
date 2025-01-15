import disnake
from disnake.ext import commands
from utils import database

class TransportType:
    def __init__(self, name, description, cost, influence):
        self.name = name
        self.description = description
        self.cost = cost
        self.influence = influence

class Transport(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database.DataBase()
        self.transport_types = [
            TransportType("Авиасообщение", "Грузовые и гражданские самолёты для перевозки грузов и пассажиров.", 1000, "Высокий"),
            TransportType("Железная дорога", "Поезда для перевозки грузов и пассажиров по суше.", 500, "Средний"),
            TransportType("Порты", "Грузовые и гражданские порты для перевозки по воде.", 800, "Высокий")
        ]

    @commands.command(
        name="transport_list",
        brief="Список доступных видов транспорта"
    )
    async def transport_list(self, ctx):
        embed = disnake.Embed(title="Доступные виды транспорта", color=disnake.Color.blue())
        for transport in self.transport_types:
            embed.add_field(
                name=transport.name,
                value=f"Описание: {transport.description}\nСтоимость: {transport.cost}\nВлияние: {transport.influence}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(
        name="build_transport",
        brief="Построить транспортное сообщение",
        usage="build_transport <transport_type>"
    )
    async def build_transport(self, ctx, transport_type: str):
        transport = next((t for t in self.transport_types if t.name.lower() == transport_type.lower()), None)
        if not transport:
            embed = disnake.Embed(title="Транспорт", description="Неверный тип транспорта.", color=disnake.Color.red())
            await ctx.send(embed=embed)
            return

        user_data = await self.db.get_data(ctx.author.id)
        if not user_data or user_data[0]['balance'] < transport.cost:
            embed = disnake.Embed(title="Транспорт", description="Недостаточно средств для строительства.", color=disnake.Color.red())
            await ctx.send(embed=embed)
            return

        await self.db.update_user("UPDATE users SET balance = balance - ? WHERE member_id = ?", [transport.cost, ctx.author.id])
        embed = disnake.Embed(title="Транспорт", description=f"Вы построили {transport.name}.", color=disnake.Color.green())
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Transport(bot)) 