import disnake
from disnake.ext import commands, tasks
import random
from utils import database

class Company:
    def __init__(self, name, sector, risk, success_chance):
        self.name = name
        self.sector = sector
        self.risk = risk
        self.success_chance = success_chance
        self.investments = {}

    def add_investment(self, user_id, amount):
        if user_id in self.investments:
            self.investments[user_id] += amount
        else:
            self.investments[user_id] = amount

    def calculate_returns(self):
        success = random.random() < self.success_chance
        returns = {}
        for user_id, amount in self.investments.items():
            if success:
                returns[user_id] = int(amount * (1 + random.uniform(0.1, 0.5)))
            else:
                returns[user_id] = int(amount * random.uniform(0.5, 0.9))
        return returns, success

class Investment(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database.DataBase()
        self.companies = []
        self.create_companies.start()

    @tasks.loop(hours=24)
    async def create_companies(self):
        # Известные компании
        company_names = ["YouTube", "TikTok", "Facebook", "X", "Discord", "Netflix", "Amazon", "Google", "Apple", "Microsoft"]
        sectors = ["Социальные сети", "Видео платформа", "Электронная коммерция", "Технологии", "Развлечения"]
        self.companies.clear()  # Очищаем список компаний перед созданием новых
        selected_names = random.sample(company_names, 10)  # Выбираем уникальные имена компаний
        for name in selected_names:
            sector = random.choice(sectors)
            risk = random.uniform(0.1, 0.5)
            success_chance = random.uniform(0.5, 0.9)
            company = Company(name, sector, risk, success_chance)
            self.companies.append(company)

        embed = disnake.Embed(title="Новые компании для инвестирования", description="Вы можете инвестировать в эти компании, чтобы получить прибыль", color=disnake.Color.blue())
        for i, company in enumerate(self.companies):
            embed.add_field(
                name=f"{i+1}. {company.name}",
                value=f"Сектор: {company.sector}\nРиск: {company.risk:.2f}\nШанс на успех: {company.success_chance:.2f}",
                inline=True
            )
        await self.bot.get_channel(1316794609283895306).send(embed=embed)

    @commands.command(
        name="invest",
        brief="Инвестировать в компанию",
        usage="invest <company_number> <amount>"
    )
    async def invest(self, ctx, company_number: int, amount: int):
        if company_number < 1 or company_number > len(self.companies):
            embed = disnake.Embed(title="Инвестиции", description="Неверный номер компании.", color=disnake.Color.red())
            await ctx.send(embed=embed)
            return

        company = self.companies[company_number - 1]
        user_data = await self.db.get_data(ctx.author.id)
        if not user_data or user_data[0]['balance'] < amount:
            embed = disnake.Embed(title="Инвестиции", description="Недостаточно средств.", color=disnake.Color.red())
            await ctx.send(embed=embed)
            return

        await self.db.update_user("UPDATE users SET balance = balance - ? WHERE member_id = ?", [amount, ctx.author.id])
        company.add_investment(ctx.author.id, amount)
        embed = disnake.Embed(title="Инвестиция", description=f"Вы инвестировали {amount} в {company.name}.", color=disnake.Color.green())
        await ctx.send(embed=embed)

    @commands.command(
        name="investcheck",
        aliases=["checkinvest"],
        brief="Проверить инвестиции"
    )
    async def investcheck(self, ctx):
        user_has_investments = False
        for company in self.companies:
            returns, success = company.calculate_returns()
            if ctx.author.id in company.investments:
                user_has_investments = True
                return_amount = returns[ctx.author.id]
                embed = disnake.Embed(title="Инвестиции", description=f"Компания {company.name} {'успешна' if success else 'потерпела неудачу'}. Возврат: {return_amount}", color=disnake.Color.green())
                await ctx.send(embed=embed)
                await self.db.update_user("UPDATE users SET balance = balance + ? WHERE member_id = ?", [return_amount, ctx.author.id])
                del company.investments[ctx.author.id]  # Удаляем инвестицию после проверки

        if not user_has_investments:
            embed = disnake.Embed(title="Инвестиции", description="У вас нет активных инвестиций.", color=disnake.Color.red())
            await ctx.send(embed=embed)

    @commands.command(
        name="investlist",
        aliases=["invests"],
        brief="Список доступных компаний"
    )
    async def investlist(self, ctx):
        if not self.companies:
            embed = disnake.Embed(title="Инвестиции", description="Нет доступных компаний для инвестирования.", color=disnake.Color.red())
            await ctx.send(embed=embed)
            return

        embed = disnake.Embed(title="Доступные компании для инвестирования", color=disnake.Color.green())
        for i, company in enumerate(self.companies):
            embed.add_field(
                name=f"{i+1}. {company.name}",
                value=f"Сектор: {company.sector}\nРиск: {company.risk:.2f}\nШанс на успех: {company.success_chance:.2f}",
                inline=True
            )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Investment(bot)) 