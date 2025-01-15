import disnake
from disnake.ext import commands
import random
import emoji
import json

from utils import database
from countries import countries_data  # Импортируем данные из countries.py

class UserCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database.DataBase()
        self.db_name = "test-database.db"
        self.countries_data = countries_data  # Используем импортированные данные

    def load_countries_data(self):
        with open('countries.js', 'r', encoding='utf-8') as file:
            return json.load(file)

    @commands.command(
        name="ping",
        aliases=["пинг"],
        brief="Проверка соединения"
    )
    async def ping(self, ctx):
        embed = disnake.Embed(
            title="Pong!",
            description=f"Latency: {round(self.bot.latency * 1000)}ms",
            color=disnake.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="balance",
        aliases=["баланс", "cash", "bal"],
        brief="Баланс пользователя",
        usage="balance <@user>"
    )
    async def user_balance(self, ctx, member: disnake.Member=None):
        balance_data = await self.db.get_data(ctx.author.id)
        
        if not balance_data:
            await ctx.send("Не удалось получить данные о балансе.")
            return

        balance_row = balance_data[0]
        balance = balance_row['balance']

        embed = disnake.Embed(
            title="Баланс пользователя",
            description=f"Баланс *{ctx.author}*: {balance:,}",
            color=disnake.Color.blue()
        )

        if member is not None:
            member_balance_data = await self.db.get_data(member.id)
            if not member_balance_data:
                await ctx.send("Не удалось получить данные о балансе пользователя.")
                return

            member_balance_row = member_balance_data[0]
            member_balance = member_balance_row['balance']
            embed.description = f"Баланс *{member}*: {member_balance:,}"
        
        await ctx.send(embed=embed)

    @commands.command(
        name="givemoney",
        aliases=["give-money", "give-cash", "givecash", "дать-деньги", "датьденьги"],
        brief="Дать пользователя суммой денег",
        usage="givemoney <@user> <amount>"
    )
    async def award_user(self, ctx, member: disnake.Member, amount: int):
        if amount < 1:
            embed = disnake.Embed(
                title="Ошибка",
                description="Сумма не должна быть меньше 1",
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            await self.db.update_user("UPDATE users SET balance = balance + ? WHERE member_id = ?", [amount, member.id])
            embed = disnake.Embed(
                title="Успешно",
                description=f"Вы дали {amount} монет пользователю {member.display_name}.",
                color=disnake.Color.green()
            )
            await ctx.send(embed=embed)

    @commands.command(
        name="takemoney",
        aliases=["take-money", "take-cash", "takecash", "забрать-деньги", "забратьденьги"],
        brief="Забрать сумму денег у пользователя",
        usage="takemoney <@user> <amount (int or all)>"
    )
    async def take_cash(self, ctx, member: disnake.Member, amount):
        if amount == "all":
            await self.db.update_user("UPDATE users SET balance = ? WHERE member_id = ?", [0, member.id])
            embed = disnake.Embed(
                title="Успешно",
                description=f"Вы забрали все деньги у пользователя {member.display_name}.",
                color=disnake.Color.green()
            )
        elif int(amount) < 1:
            embed = disnake.Embed(
                title="Ошибка",
                description="Сумма не должна быть меньше 1",
                color=disnake.Color.red()
            )
        else:
            await self.db.update_user("UPDATE users SET balance = balance - ? WHERE member_id = ?", [amount, member.id])
            embed = disnake.Embed(
                title="Успешно",
                description=f"Вы забрали {amount} монет у пользователя {member.display_name}.",
                color=disnake.Color.green()
            )
        await ctx.send(embed=embed)

    @commands.command(
        name="pay",
        aliases=["transfer", "перевести"],
        brief="Перевести деньги пользователю",
        usage="pay <@user> <amount>"
    )
    async def pay_cash(self, ctx, member: disnake.Member, amount: int):
        balance_data = await self.db.get_data(ctx.author.id)
        
        if not balance_data:
            await ctx.send("Не удалось получить данные о балансе.")
            return

        try:
            balance_row = balance_data[0]
            balance = balance_row['balance']

            if amount > balance:
                embed = disnake.Embed(
                    title="Ошибка",
                    description="Недостаточно средств",
                    color=disnake.Color.red()
                )
            elif amount <= 0:
                    embed = disnake.Embed(
                        title="Ошибка",
                        description="Сумма не должна быть меньше 1",
                        color=disnake.Color.red()
                    )
            else:
                    await self.db.update_user("UPDATE users SET balance = balance - ? WHERE member_id = ?", [amount, ctx.author.id])
                    await self.db.update_user("UPDATE users SET balance = balance + ? WHERE member_id = ?",  [amount, member.id])
                    embed = disnake.Embed(
                        title="Успешно",
                        description=f"Вы перевели {amount:,} монет пользователю {member.display_name}.",
                        color=disnake.Color.green()
                    )
            await ctx.send(embed=embed)
        except KeyError as e:
            await ctx.send("Ошибка при обработке данных баланса.")

    @commands.command(
        name="rep",
        aliases=["репутация"],
        brief="Дать репутацию пользователю",
        usage="rep <@user>"
    )
    async def reputation(self, ctx, member: disnake.Member):
        if member.id == ctx.author.id:
            embed = disnake.Embed(
                title="Ошибка",
                description="Нельзя выдать репутацию себе",
                color=disnake.Color.red()
            )
        else:
            await self.db.update_user("UPDATE users SET reputation = reputation + ? WHERE member_id = ?", [1, member.id])
            embed = disnake.Embed(
                title="Успешно",
                description=f"Вы выдали репутацию пользователю {member.display_name}.",
                color=disnake.Color.green()
            )
        await ctx.send(embed=embed)

    @commands.command(
        name="leaderboard",
        aliases=["lb", "top", "лидеры"],
        brief="Таблица лидеров"
    )
    async def server_leaderboard(self, ctx):
        view = LeaderboardSelectView(self.db)
        await ctx.send("Выберите таблицу лидеров:", view=view)

    @commands.command(
        name="info",
        aliases=["search", "информация", "поиск"],
        brief="Информация о пользователе",
        usage="info <@user or name>"
    )
    async def info(self, ctx, *, query: str = None):
        if query is None:
            member = ctx.author
        else:
            # Поиск пользователей по имени или упоминанию
            members = [m for m in ctx.guild.members if query.lower() in m.display_name.lower()]

            if len(members) == 1:
                member = members[0]
            elif len(members) > 1:
                # Если найдено несколько пользователей, выводим список
                options = [f"{i + 1}. {m.display_name}" for i, m in enumerate(members)]
                message = await ctx.send(embed=disnake.Embed(
                    description=f"Найдено несколько пользователей:\n\n" + "\n".join(options) +
                                "\n\nВведите номер, чтобы выбрать пользователя.",
                    color=disnake.Color.yellow()
                ))

                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(members)

                try:
                    # Ожидание ответа пользователя
                    response = await self.bot.wait_for("message", timeout=30, check=check)
                    selected_index = int(response.content) - 1
                    member = members[selected_index]

                    # Удаляем сообщение с выбором
                    await message.delete()
                    await response.delete()

                except Exception:
                    await ctx.send(embed=disnake.Embed(
                        description="Вы не выбрали пользователя вовремя. Попробуйте снова.",
                        color=disnake.Color.red()
                    ))
                    return
            else:
                await ctx.send("Пользователь не найден.")
                return

        user_data = await self.db.get_data(member.id)
        
        if not user_data:
            await ctx.send("Не удалось получить данные о пользователе.")
            return

        user_row = user_data[0]
        required_keys = ['balance', 'reputation', 'level', 'territory', 'population', 'education_level', 'healthcare_level', 'tourism_level', 'economy_level', 'capital', 'sanctions_level']
        missing_keys = [key for key in required_keys if key not in user_row.keys()]
        if missing_keys:
            await ctx.send(f"Отсутствуют данные: {', '.join(missing_keys)}")
            return

        embed = disnake.Embed(title=f"Информация о {member.display_name}", color=disnake.Color.blue())
        embed.add_field(name="💵 Баланс", value=f"{user_row['balance']:,}")
        embed.add_field(name="⭐ Репутация", value=f"{user_row['reputation']}")
        embed.add_field(name="🏆 Уровень", value=f"{user_row['level']}")
        embed.add_field(name="🌍 Территория", value=f"{user_row['territory']:,}")
        embed.add_field(name="👥 Население", value=f"{user_row['population']:,}")

        inventory = await self.db.get_inventory(member.id)
        army_count = sum(item['quantity'] for item in inventory if item['item_name'] in ['Солдат', 'Танк'])
        embed.add_field(name="🛡️ Армия", value=f"{army_count:,}")

        max_level = 6
        embed.add_field(name="🎓 Образование", value=f"{user_row['education_level']}/{max_level}")
        embed.add_field(name="🏥 Здравоохранение", value=f"{user_row['healthcare_level']}/{max_level}")
        embed.add_field(name="🗺️ Туризм", value=f"{user_row['tourism_level']}/{max_level}")
        embed.add_field(name="💼 Экономика", value=f"{user_row['economy_level']}/{max_level}")
        embed.add_field(name="🏛️ Столица", value=f"{user_row['capital']}")
        embed.add_field(name="🚫 Уровень санкций", value=f"{user_row['sanctions_level']}")
        
        await ctx.send(embed=embed)

    @commands.command(
        name="work",
        aliases=["заработать"],
        brief="Заработать деньги",
    )
    @commands.cooldown(1, 900, commands.BucketType.user)  # 15 минут кулдаун
    async def work(self, ctx):
        await self.db.update_user("UPDATE users SET balance = balance + ? WHERE member_id = ?", [150000, ctx.author.id])
        embed = disnake.Embed(
            title="Успешно",
            description="Вы заработали 150000 монет.",
            color=disnake.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="improve",
        aliases=["улучшить"],
        brief="Улучшить уровень",
    )
    async def improve(self, ctx):
        view = ImproveSelectView(self.db, ctx.author)
        await ctx.send("Выберите, что вы хотите улучшить:", view=view)

    @commands.command(
        name="sanctions",
        aliases=["санкции"],
        brief="Наложить санкции на пользователя",
        usage="sanctions <@user> <уровень> <причина>"
    )
    async def impose_sanctions(self, ctx, member: disnake.Member, level: int, *, reason: str):
        if level < 1 or level > 3:
            await ctx.send("Уровень санкций должен быть от 1 до 3.")
            return

        await self.db.update_user("UPDATE users SET sanctions_level = ? WHERE member_id = ?", [level, member.id])
        await ctx.send(f"На {member.display_name} наложены санкции уровня {level} по причине: {reason}")

    def calculate_population_change(self, tourism_level, healthcare_level, education_level):
        # Определяем базовые изменения населения
        decrease_ranges = {
            1: (100000, 500000),
            2: (100000, 400000),
            3: (100000, 300000),
            4: (50000, 200000),
            5: (10000, 100000),
            6: (0, 0)  # На уровне 6 население не уменьшается
        }
        increase_ranges = {
            1: (10000, 100000),
            2: (100000, 300000),
            3: (300000, 600000),
            4: (500000, 800000),
            5: (800000, 1000000),
            6: (1000000, 1500000)  # На уровне 6 максимальное увеличение
        }

        # Подсчитываем количество уровней выше 1
        levels = [tourism_level, healthcare_level, education_level]
        high_levels = sum(1 for level in levels if level > 1)

        # Определяем изменение населения
        if high_levels == 0:
            # Все уровни равны 1
            change = -random.randint(*decrease_ranges[1])
        elif high_levels == 1:
            # Один из уровней выше 1
            change = -random.randint(*decrease_ranges[max(levels)])
        elif high_levels == 2:
            # Два из уровней выше 1
            change = random.randint(*increase_ranges[1])
        else:
            # Все уровни выше 1
            change = random.randint(*increase_ranges[max(levels)])

        return change

    @commands.command(
        name="collect",
        aliases=["collect-income", "collectincome", "собирать-доход", "собиратьдоход"],
        brief="Собрать доход от экономики"
    )
    @commands.cooldown(1, 1, commands.BucketType.user)  # 10 минут кулдаун
    async def collect_economy(self, ctx):
        user_data = await self.db.get_data(ctx.author.id)
        if not user_data:
            await ctx.send("Не удалось получить данные о пользователе.")
            return

        user_row = user_data[0]
        economy_level = user_row['economy_level']
        income = economy_level * 1000000  # Пример: каждый уровень экономики дает 1,000,000 монет

        # Вычисляем изменение населения
        population_change = self.calculate_population_change(
            user_row['tourism_level'],
            user_row['healthcare_level'],
            user_row['education_level']
        )

        # Обновляем данные пользователя
        await self.db.update_user(
            "UPDATE users SET balance = balance + ?, population = population + ? WHERE member_id = ?",
            [income, population_change, ctx.author.id]
        )

        # Отправляем сообщение
        embed = disnake.Embed(
            title="Доход собран",
            description=f"Вы собрали {income:,} монет от экономики уровня {economy_level}.\n Население изменилось на {population_change:,}.",
            color=disnake.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="change-capital",
        aliases=["changecapital", "поменять-столицу", "поменятьстолицу"],
        brief="Поменять столицу",
        usage="change-capital <new_capital>"
    )
    async def change_country(self, ctx, *, new_capital: str):
        user_data = await self.db.get_data(ctx.author.id)
        if not user_data:
            await ctx.send("Не удалось получить данные о пользователе.")
            return

        user_row = user_data[0]
        if user_row['balance'] < 300000:
            embed = disnake.Embed(
                title="Недостаточно средств",
                description="Не хватает 300,000 монет для изменения столицы.",
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed)
            return

        await self.db.update_user("UPDATE users SET capital = ?, balance = balance - 300000 WHERE member_id = ?", [new_capital, ctx.author.id])
        embed = disnake.Embed(
            title="Столица изменена",
            description=f"Ваша новая столица: {new_capital}.",
            color=disnake.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="register",
        aliases=["регистрация"],
        brief="Регистрация пользователя",
        usage="register <@user> <флаг государства>"
    )
    @commands.has_permissions(administrator=True)
    async def register(self, ctx, member: disnake.Member, flag: str):
        # Преобразование эмодзи в код страны
        flag_code = self.get_country_code_from_emoji(flag)

        # Поиск информации о стране
        country = next((c for c in self.countries_data if c.get('cca2') == flag_code), None)
        if country:
            country_name = country['name']['common']
            capital = country.get('capital', ['Неизвестно'])[0]
            population = country.get('population', 'Неизвестно')
            territory = country.get('area', 'Неизвестно')
        else:
            await ctx.send("Неизвестный флаг. Пожалуйста, укажите корректный флаг государства.")
            return

        if not ctx.guild.me.guild_permissions.manage_roles or not ctx.guild.me.guild_permissions.manage_nicknames:
            embed = disnake.Embed(
                title="Ошибка",
                description="У бота недостаточно прав для изменения ролей или никнеймов.",
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed)
            return

        await self.db.update_user(
            "UPDATE users SET capital = ?, population = ?, territory = ? WHERE member_id = ?",
            [capital, population, territory, member.id]
        )

        old_role = ctx.guild.get_role(1326265648338178068)
        new_role = ctx.guild.get_role(1326264461203345531)
        roles_changed = False
        if old_role in member.roles:
            await member.remove_roles(old_role)
            roles_changed = True
        if new_role not in member.roles:
            await member.add_roles(new_role)
            roles_changed = True

        new_display_name = f"{flag} | {country_name}"
        await member.edit(nick=new_display_name)

        embed = disnake.Embed(
            title="Регистрация завершена",
            description=f"Пользователь {member.mention} успешно зарегистрирован.",
            color=disnake.Color.green()
        )
        embed.add_field(name="Изменения", value=f"Никнейм изменен на: {new_display_name}", inline=False)
        embed.add_field(name="Столица", value=capital, inline=True)
        embed.add_field(name="Население", value=f"{population:,}", inline=True)
        embed.add_field(name="Территория", value=f"{territory:,}", inline=True)
        if roles_changed:
            embed.add_field(name="Роли", value=f"Удалена роль: {old_role.name}, добавлена роль: {new_role.name}", inline=False)
        await ctx.send(embed=embed)

    def get_country_code_from_emoji(self, emoji_flag):
        # Преобразование эмодзи флага в код страны
        return ''.join([chr(ord(c) - 0x1F1E6 + ord('A')) for c in emoji_flag])

class LeaderboardSelectView(disnake.ui.View):
    def __init__(self, db):
        super().__init__(timeout=60)
        self.db = db
        self.add_item(LeaderboardSelect(self.db))

class LeaderboardSelect(disnake.ui.Select):
    def __init__(self, db):
        options = [
            disnake.SelectOption(label="Баланс", description="Топ 10 по балансу", value="balance"),
            disnake.SelectOption(label="Население", description="Топ 10 по населению", value="population"),
            disnake.SelectOption(label="Территория", description="Топ 10 по территории", value="territory"),
            disnake.SelectOption(label="Армия", description="Топ 10 по армии", value="army"),
        ]
        super().__init__(placeholder="Выберите таблицу лидеров", min_values=1, max_values=1, options=options)
        self.db = db

    async def callback(self, interaction: disnake.Interaction):
        column = self.values[0]
        title = f"Топ 10 по {column.capitalize()}"
        embed = disnake.Embed(title=title, color=disnake.Color.gold())
        counter = 0

        if column == "army":
            data = await self.db.get_data(all_data=True)
            army_data = []
            for row in data:
                inventory = await self.db.get_inventory(row['member_id'])
                army_count = sum(item['quantity'] for item in inventory if item['name'] in ['Солдат', 'Танк'])
                army_data.append((row['member_id'], army_count))
            army_data.sort(key=lambda x: x[1], reverse=True)
            top_army = army_data[:10]

            for member_id, army_count in top_army:
                user = interaction.guild.get_member(member_id)
                if user is None:
                    continue
                counter += 1
                embed.add_field(
                    name=f"#{counter} | `{user.display_name}`",
                    value=f"Армия: {army_count}",
                    inline=False
                )
        else:
            data = await self.db.get_data(all_data=True, filters=f"ORDER BY {column} DESC LIMIT 10")
            if data is None:
                await interaction.response.send_message("Нет данных для отображения.", ephemeral=True)
                return

            for row in data:
                counter += 1
                user = interaction.guild.get_member(row['member_id'])
                if user is None:
                    continue

                embed.add_field(
                    name=f"#{counter} | `{user.display_name}`",
                    value=f"{column.capitalize()}: {row[column]}",
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class ImproveSelectView(disnake.ui.View):
    def __init__(self, db, user):
        super().__init__(timeout=60)
        self.db = db
        self.user = user

    @disnake.ui.select(
        placeholder="Выберите категорию для улучшения",
        options=[
            disnake.SelectOption(label="Образование", value="education"),
            disnake.SelectOption(label="Здравоохранение", value="healthcare"),
            disnake.SelectOption(label="Туризм", value="tourism"),
            disnake.SelectOption(label="Экономика", value="economy"),
        ]
    )
    async def select_improvement(self, select: disnake.ui.Select, interaction: disnake.Interaction):
        category = select.values[0]
        await interaction.response.defer()

        user_data = await self.db.get_data(self.user.id)
        if not user_data:
            await interaction.followup.send("Не удалось получить данные о пользователе.", ephemeral=True)
            return

        user_row = user_data[0]
        current_level = user_row[f'{category}_level']
        if current_level >= 6:
            await interaction.followup.send(f"Вы уже достигли максимального уровня {category}.", ephemeral=True)
            return

        requirements = self.calculate_requirements(category, current_level)
        inventory = await self.db.get_inventory(self.user.id)

        missing_resources = self.check_requirements(inventory, user_row['balance'], requirements)
        if missing_resources:
            embed = disnake.Embed(
                title=f"Недостаточно ресурсов для улучшения {category}",
                description="Не хватает: " + ", ".join(missing_resources),
                color=disnake.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.db.update_user(
            f"UPDATE users SET {category}_level = {category}_level + 1, balance = balance - ? WHERE member_id = ?",
            [requirements['balance'], self.user.id]
        )
        embed = disnake.Embed(
            title="Успешно",
            description=f"Уровень {category} улучшен до {current_level + 1}.",
            color=disnake.Color.green()
        )
        await interaction.followup.send(embed=embed)

    def calculate_requirements(self, category, current_level):
        requirements = {
            "education": {"schools": 50 + (current_level * 10), "universities": 30 + (current_level * 10), "balance": 500000 + (current_level * 200000)},
            "healthcare": {"hospitals": 40 + (current_level * 10), "pharmacies": 25 + (current_level * 10), "balance": 600000 + (current_level * 250000)},
            "tourism": {"hotels": 30 + (current_level * 5), "museums": 20 + (current_level * 5), "balance": 700000 + (current_level * 300000)},
            "economy": {"factories": 5 + (current_level * 2), "banks": 3 + (current_level * 2), "balance": 200000 + (current_level * 70000)},
        }
        return requirements[category]

    def check_requirements(self, inventory, balance, requirements):
        items = {
            "schools": "Школа",
            "universities": "ВУЗ",
            "hospitals": "Больница",
            "pharmacies": "Аптека",
            "hotels": "Отель",
            "museums": "Музей",
            "factories": "Фабрика",
            "banks": "Банк",
        }
        missing_resources = []
        for key, value in requirements.items():
            if key == "balance":
                if balance < value:
                    missing_resources.append(f"Деньги: {value - balance}")
            else:
                item_name = items[key]
                item_count = sum(item['quantity'] for item in inventory if item['item_name'] == item_name)
                if item_count < value:
                    missing_resources.append(f"{item_name}: {value - item_count}")
        return missing_resources

def setup(bot):
    bot.add_cog(UserCommands(bot))
