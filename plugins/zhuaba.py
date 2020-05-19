from nonebot import on_command, CommandSession
import asyncio
import json
# on_command 装饰器将函数声明为一个命令处理器
@on_command('爪巴',only_to_me = False)
async def pa(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    await asyncio.sleep(0.2)
    await session.send('我爪巴')
    