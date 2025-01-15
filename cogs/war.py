import disnake
from disnake.ext import commands
from utils.database import DataBase

class BattleState:
    def __init__(self, attacker, defender):
        self.attacker = attacker
        self.defender = defender
        self.attacker_units = {1: 0, 2: 0}  # 1: Солдат, 2: Танк
        self.defender_units = {1: 0, 2: 0}
        self.turn = attacker
        self.log = []  # Журнал действий

    async def load_units(self, db, member_id, is_attacker=True):
        inventory = await db.get_inventory(member_id)
        for item in inventory:
            if 'item_id' not in item:
                continue

            if item['item_id'] == 1:  # ID для Солдата
                if is_attacker:
                    self.attacker_units[1] += item['quantity']
                else:
                    self.defender_units[1] += item['quantity']
            elif item['item_id'] == 2:  # ID для Танка
                if is_attacker:
                    self.attacker_units[2] += item['quantity']
                else:
                    self.defender_units[2] += item['quantity']

    def switch_turn(self):
        self.turn = self.defender if self.turn == self.attacker else self.attacker

    def is_battle_over(self):
        return self.attacker_units[1] <= 0 or self.defender_units[1] <= 0

    def get_winner(self):
        if self.attacker_units[1] > 0:
            return self.attacker
        else:
            return self.defender

    def attack(self, unit_id, quantity):
        if unit_id == 1:  # Солдат
            damage = 5 * quantity
            if self.turn == self.attacker:
                self.defender_units[1] -= damage
                self.log.append(f"{self.attacker.display_name} атаковал {self.defender.display_name} с {quantity} солдатами и нанес {damage} урона.")
            else:
                self.attacker_units[1] -= damage
                self.log.append(f"{self.defender.display_name} атаковал {self.attacker.display_name} с {quantity} солдатами и нанес {damage} урона.")
        elif unit_id == 2:  # Танк
            damage = 10 * quantity
            if self.turn == self.attacker:
                self.defender_units[2] -= damage
                self.log.append(f"{self.attacker.display_name} атаковал {self.defender.display_name} с {quantity} танками и нанес {damage} урона.")
            else:
                self.attacker_units[2] -= damage
                self.log.append(f"{self.defender.display_name} атаковал {self.attacker.display_name} с {quantity} танками и нанес {damage} урона.")

    def defend(self, unit_id, quantity):
        if unit_id == 1:  # Солдат
            recovery = 3 * quantity
            if self.turn == self.attacker:
                self.attacker_units[1] += recovery
                self.log.append(f"{self.attacker.display_name} защищался с {quantity} солдатами и восстановил {recovery} солдат.")
            else:
                self.defender_units[1] += recovery
                self.log.append(f"{self.defender.display_name} защищался с {quantity} солдатами и восстановил {recovery} солдат.")
        elif unit_id == 2:  # Танк
            recovery = 5 * quantity
            if self.turn == self.attacker:
                self.attacker_units[2] += recovery
                self.log.append(f"{self.attacker.display_name} защищался с {quantity} танками и восстановил {recovery} танков.")
            else:
                self.defender_units[2] += recovery
                self.log.append(f"{self.defender.display_name} защищался с {quantity} танками и восстановил {recovery} танков.")

class War(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DataBase()
        self.battle = None  # Хранит текущее состояние битвы
        self.battle_channel = None  # Канал, в котором происходит битва
        self.unit_id = None  # Хранит выбранный юнит
        self.action = None  # Хранит текущее действие (атака или защита)

    @commands.command(
        name="declare-war",
        aliases=["declarewar", "объявить-войну", "объявитьвойну"],
        brief="Объявить войну другому пользователю",
        usage="declare-war <@user>"
    )
    async def declare_war(self, ctx, member: disnake.Member):
        if ctx.channel.id != 1221441808400257065:
            await ctx.send("Эту команду можно использовать только в специальном канале.")
            return

        if member.id == ctx.author.id:
            await ctx.send("Вы не можете объявить войну самому себе.")
            return

        embed = disnake.Embed(
            title="Объявление войны",
            description=f"{ctx.author.mention} объявил войну {member.mention}.",
            color=disnake.Color.red()
        )
        view = WarAcceptView(ctx.author, member, self.db)
        await ctx.send(embed=embed, view=view)

class WarAcceptView(disnake.ui.View):
    def __init__(self, author, target, db):
        super().__init__(timeout=60)
        self.author = author
        self.target = target
        self.db = db
        self.battle = BattleState(author, target)

    @disnake.ui.button(label="Принять вызов", style=disnake.ButtonStyle.green)
    async def accept(self, _: disnake.ui.Button, interaction: disnake.Interaction):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("Только вызванный пользователь может принять вызов.", ephemeral=True)
            return

        await self.battle.load_units(self.db, self.author.id, is_attacker=True)
        await self.battle.load_units(self.db, self.target.id, is_attacker=False)

        await interaction.response.send_message(f"{self.target.mention} принял вызов. Битва начинается!", view=BattleView(self.battle, self.db))

class BattleView(disnake.ui.View):
    def __init__(self, battle, db):
        super().__init__(timeout=60)
        self.battle = battle
        self.db = db

    @disnake.ui.button(label="Атаковать", style=disnake.ButtonStyle.red)
    async def attack(self, _: disnake.ui.Button, interaction: disnake.Interaction):
        if interaction.user.id != self.battle.turn.id:
            await interaction.response.send_message("Сейчас не ваш ход.", ephemeral=True)
            return

        self.battle.action = "attack"
        self.battle_channel = interaction.channel
        await interaction.response.send_message("Выберите юнит для атаки:", view=UnitSelectView(self.battle, self.db))

    @disnake.ui.button(label="Защищаться", style=disnake.ButtonStyle.green)
    async def defend(self, _: disnake.ui.Button, interaction: disnake.Interaction):
        if interaction.user.id != self.battle.turn.id:
            await interaction.response.send_message("Сейчас не ваш ход.", ephemeral=True)
            return

        self.battle.action = "defend"
        self.battle_channel = interaction.channel
        await interaction.response.send_message("Выберите юнит для защиты:", view=UnitSelectView(self.battle, self.db))

class UnitSelectView(disnake.ui.View):
    def __init__(self, battle, db):
        super().__init__(timeout=60)
        self.battle = battle
        self.db = db

    @disnake.ui.select(placeholder="Выберите юнит", options=[
        disnake.SelectOption(label="Солдат", value="1"),  # ID для Солдата
        disnake.SelectOption(label="Танк", value="2")     # ID для Танка
    ])
    async def select_unit(self, select: disnake.ui.Select, interaction: disnake.Interaction):
        self.battle.unit_id = int(select.values[0])
        await interaction.response.send_message("Выберите количество юнитов:", view=QuantitySelectView(self.battle, self.db))

class QuantitySelectView(disnake.ui.View):
    def __init__(self, battle, db):
        super().__init__(timeout=60)
        self.battle = battle
        self.db = db
        self.add_item(disnake.ui.Select(
            placeholder="Выберите количество",
            options=self.generate_quantity_options()
        ))

    def generate_quantity_options(self):
        unit_id = self.battle.unit_id
        available_units = self.battle.attacker_units if self.battle.turn == self.battle.attacker else self.battle.defender_units
        max_quantity = available_units.get(unit_id, 0)
        
        # Определяем название юнита
        unit_name = "Солдат" if unit_id == 1 else "Танк"
        
        # Фиксированные опции
        fixed_options = [1, 10, 100]
        options = [disnake.SelectOption(label=f"{unit_name}: {i}", value=str(i)) for i in fixed_options if i <= max_quantity]
        
        # Если максимальное количество больше 100 и не включено в опции, добавляем его
        if max_quantity > 100 and max_quantity not in fixed_options:
            options.append(disnake.SelectOption(label=f"{unit_name}: Максимум ({max_quantity})", value=str(max_quantity)))
        
        return options

    @disnake.ui.select()
    async def select_quantity(self, select: disnake.ui.Select, interaction: disnake.Interaction):
        quantity = int(select.values[0])
        if self.battle.action == "attack":
            self.battle.attack(self.battle.unit_id, quantity)
            await interaction.response.send_message(f"{interaction.user.display_name} атаковал с {quantity} юнитами.")
        elif self.battle.action == "defend":
            self.battle.defend(self.battle.unit_id, quantity)
            await interaction.response.send_message(f"{interaction.user.display_name} защищался с {quantity} юнитами.")

        # Переключение хода
        self.battle.switch_turn()
        await interaction.response.send_message(f"Теперь ходит {self.battle.turn.display_name}.")

def setup(bot):
    bot.add_cog(War(bot)) 