import disnake
from disnake.ext import commands
import io
import requests
from PIL import Image, ImageDraw, ImageFont

class UserCard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="usercard",
        aliases=["карточка"],
        brief="Показать карточку пользователя",
        usage="usercard <@user>"
    )
    async def user_card(self, ctx, member: disnake.Member = None):
        if member is None:
            member = ctx.author

        # Получение данных пользователя из базы данных
        user_data = await self.bot.db.get_data(member.id)
        if not user_data:
            await ctx.send("Не удалось получить данные о пользователе.")
            return

        # Создание изображения
        card_image = self.create_user_card(member, user_data[0])

        # Отправка изображения в канал
        with io.BytesIO() as image_binary:
            card_image.save(image_binary, format='PNG')
            image_binary.seek(0)
            await ctx.send(file=disnake.File(fp=image_binary, filename='user_card.png'))

    def create_user_card(self, member, user_data):
        user_data_dict = dict(user_data)

        # Создаем изображение
        width, height = 1000, 300
        image = Image.new('RGB', (width, height), color=(0, 0, 0))

        # Добавление градиентного фона
        gradient = Image.new('RGB', (width, height), color=0)
        for y in range(height):
            color = (139 + int(y / height * (255 - 139)), 69 + int(y / height * (105 - 69)), 19 + int(y / height * (55 - 19)))
            ImageDraw.Draw(gradient).line([(0, y), (width, y)], fill=color)
        image.paste(gradient, (0, 0))

        draw = ImageDraw.Draw(image)

        # Загрузка шрифта
        try:
            font_large = ImageFont.truetype("arial.ttf", 50)
            font_small = ImageFont.truetype("arial.ttf", 35)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Загрузка и отображение аватарки
        avatar_asset = member.display_avatar.url if member.display_avatar else member.default_avatar.url
        avatar_image = Image.open(io.BytesIO(requests.get(avatar_asset).content)).convert("RGBA")
        avatar_image = avatar_image.resize((150, 150))
        mask = Image.new("L", avatar_image.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 150, 150), fill=255)
        avatar_image.putalpha(mask)
        image.paste(avatar_image, (30, 75), avatar_image)

        # Добавление текста
        draw.text((220, 30), f"{member.name}", font=font_large, fill='white')
        draw.text((850, 30), f"Баланс: {user_data_dict.get('balance', 0):,}", font=font_large, fill='white', anchor="ra")
        draw.text((850, 90), f"EXP: {user_data_dict.get('xp', 0)}/{self.calculate_experience_for_next_level(user_data_dict.get('level', 0))}", font=font_small, fill='white', anchor="ra")
        draw.text((220, 100), f"Уровень: {user_data_dict.get('level', 0)}", font=font_small, fill='white')

        # Прогресс-бар для опыта
        next_level_exp = self.calculate_experience_for_next_level(user_data_dict.get('level', 0))
        current_exp = user_data_dict.get('xp', 0)
        progress = current_exp / next_level_exp if next_level_exp > 0 else 0

        bar_x_start = 220
        bar_x_end = 850
        bar_y = 250
        bar_height = 20

        draw.rectangle((bar_x_start, bar_y, bar_x_end, bar_y + bar_height), fill=(139, 69, 19))
        draw.rectangle((bar_x_start, bar_y, bar_x_start + int((bar_x_end - bar_x_start) * progress), bar_y + bar_height), fill=(255, 165, 0))
        draw.rectangle((bar_x_start, bar_y, bar_x_end, bar_y + bar_height), outline=(255, 255, 255), width=2)

        return image

    def calculate_experience_for_next_level(self, current_level):
        base_experience = 100
        return int(base_experience * (1.5 ** current_level))

def setup(bot):
    bot.add_cog(UserCard(bot))
