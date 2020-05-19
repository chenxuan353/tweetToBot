from nonebot import on_command, CommandSession
import asyncio
import json
import random
# on_command 装饰器将函数声明为一个命令处理器
@on_command('爪巴',only_to_me = False)
async def pa(session: CommandSession):
    # stripped_arg = session.current_arg_text.strip()
    await asyncio.sleep(0.2)
    str = ['我爬 我现在就爬','我爪巴','你给爷爬','呜呜呜别骂了 再骂BOT就傻了']
    index = random.randint(0,len(str)-1)
    await session.send(str[index])
    