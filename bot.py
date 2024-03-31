from aiogram import executor
from dispatcher import dp
import personal_actions

from db import BotDB
BotDB = BotDB('accountant.db')

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=personal_actions.on_startup)
