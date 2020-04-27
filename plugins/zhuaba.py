from nonebot import on_command, CommandSession

# on_command 装饰器将函数声明为一个命令处理器
@on_command('爪巴',only_to_me = False)
async def pa(session: CommandSession):
    await session.send('我爪巴')