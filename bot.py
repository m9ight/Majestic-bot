import os
import logging
import config

import disnake
from disnake.ext import commands
from utils import database  # Предположим, что у вас есть модуль для работы с базой данных

# Настройка логирования
logging.basicConfig(level=logging.WARNING)

# Настройка интентов
intents = disnake.Intents.default()
intents.members = True  # Доступ к информации о членах
intents.message_content = True  # Доступ к содержимому сообщений

class MyBot(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.db = database.DataBase()  # Инициализация базы данных

	async def on_ready(self):
		print(f"Logged in as {self.user} (ID: {self.user.id}) | Logged in to {self.guilds[0].name} (ID: {self.guilds[0].id})")

bot = MyBot(command_prefix=".", intents=intents)


@bot.command()
@commands.is_owner()
async def load(ctx, extension):
	bot.load_extension(f"cogs.{extension}")
	await ctx.message.add_reaction("✅")


@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
	bot.reload_extension(f"cogs.{extension}")
	await ctx.message.add_reaction("✅")


@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
	bot.unload_extension(f"cogs.{extension}")
	await ctx.message.add_reaction("✅")


for filename in os.listdir("./cogs"):
	if filename.endswith(".py"):
		bot.load_extension(f"cogs.{filename[:-3]}")
  
@bot.event
async def on_command_error(ctx, error):
	# Логируем ошибку
	logging.error(f"Ошибка в команде {ctx.command}: {error}")

	# Отправляем сообщение об ошибке пользователю
	if isinstance(error, commands.CommandInvokeError):
		await ctx.send(f"Произошла ошибка при выполнении команды: {str(error.original)}")
	else:
		await ctx.send(f"Произошла ошибка: {str(error)}")

bot.run(config.TOKEN)
