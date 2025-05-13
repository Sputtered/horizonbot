import asyncio
from discord import Intents
from bot import HorizonBot
from storage.sqlite import SQLiteStorage
from settings import settings

storage = SQLiteStorage()
asyncio.run(storage.setup())

intents = Intents.default()
intents.reactions = True

bot = HorizonBot(settings, intents, storage)

bot.run(settings.discord_token)
