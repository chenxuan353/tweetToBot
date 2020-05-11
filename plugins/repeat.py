import nonebot
from config import entertainment_config
bot = nonebot.get_bot()
previousMessages= []


@bot.on_message('group')
async def repeat():

    pass